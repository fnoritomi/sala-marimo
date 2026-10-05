"""
Repositório DuckDB: Gerencia o acesso ao arquivo Parquet (remoto via HTTPS ou cache local),
executa consultas analíticas planejadas e provê exportação nativa de dados.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional
import duckdb

from src.analytics.semantic_model import SemanticModel
from src.analytics.query_model import QueryResult, SemanticQuery
from src.analytics.query_planner import CardinalityExceededException, QueryPlanner


class DuckDBRepository:
    """Repositório de dados analíticos com DuckDB."""

    def __init__(
        self,
        model: SemanticModel,
        parquet_mode: Optional[str] = None,
    ):
        self.model = model
        self.planner = QueryPlanner(model)
        self.mode = parquet_mode or os.environ.get("PARQUET_MODE", "remote")
        self.con = duckdb.connect(":memory:")
        self._init_connection()

    def _init_connection(self):
        """Configura extensões HTTP e cria a view sobre o arquivo Parquet."""
        try:
            self.con.execute("INSTALL httpfs; LOAD httpfs;")
        except Exception:
            pass  # httpfs já pode estar embutido nas versões recentes do DuckDB

        # Ajustes de performance de rede e threads
        self.con.execute("SET http_keep_alive = true;")
        self.con.execute("SET http_timeout = 60;")
        self.con.execute("SET threads = 4;")

        # Seleção da fonte de dados (remota vs. local)
        local_exists = os.path.exists(self.model.local_cache_path)
        if self.mode == "local-cache" and local_exists:
            source_path = self.model.local_cache_path
            self.active_source = f"local-cache ({source_path})"
        else:
            source_path = self.model.remote_source
            self.active_source = f"remote HTTPS ({source_path})"

        self.con.execute(
            f"CREATE OR REPLACE VIEW v_beneficiarios_parquet AS SELECT * FROM read_parquet('{source_path}')"
        )

    def execute_query(self, query: SemanticQuery) -> QueryResult:
        """
        Executa uma consulta semântica OLAP e retorna o resultado estruturado.
        """
        measure = self.model.get_measure(query.measure)
        try:
            sql, params, semi_applied, eff_comp, headers = self.planner.plan(
                query, table_expression="v_beneficiarios_parquet"
            )
            estimated_groups = self.planner.estimate_cardinality(query)

            t0 = time.time()
            cursor = self.con.cursor()
            res = cursor.execute(sql, params).fetchall()
            t1 = time.time()

            # Formata registros para serialização JSON
            formatted_rows = []
            for r in res:
                row_items = []
                for val in r:
                    if hasattr(val, "isoformat"):
                        row_items.append(val.isoformat())
                    else:
                        row_items.append(val)
                formatted_rows.append(row_items)

            warning = None
            if query.limit and len(formatted_rows) >= query.limit:
                warning = f"Mostrando os primeiros {query.limit:,} registros. A consulta completa pode conter mais linhas."

            # Gera SQL legível interpolando parâmetros (apenas para exibição/debug na UI)
            debug_sql = sql
            for p in params:
                val_rep = f"'{p}'" if isinstance(p, str) else str(p)
                debug_sql = debug_sql.replace("?", val_rep, 1)

            return QueryResult(
                columns=headers,
                rows=formatted_rows,
                total_rows=len(formatted_rows),
                estimated_groups=estimated_groups,
                query_ms=(t1 - t0) * 1000.0,
                sql=debug_sql,
                semi_additive_applied=semi_applied,
                effective_competencia=eff_comp,
                measure_name=measure.name,
                measure_label=measure.label,
                is_pivoted=len(query.columns) > 0,
                warning=warning,
            )

        except CardinalityExceededException as ce:
            return QueryResult(
                columns=[],
                rows=[],
                total_rows=0,
                estimated_groups=0,
                query_ms=0,
                sql="",
                semi_additive_applied=False,
                measure_name=measure.name,
                measure_label=measure.label,
                warning=str(ce),
            )
        except Exception as e:
            return QueryResult(
                columns=[],
                rows=[],
                total_rows=0,
                estimated_groups=0,
                query_ms=0,
                sql="",
                semi_additive_applied=False,
                measure_name=measure.name,
                measure_label=measure.label,
                error="Não foi possível acessar a fonte de dados neste momento. Verifique a conexão com a internet.",
            )

    def get_distinct_values(
        self,
        dimension_name: str,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[str]:
        """Busca valores distintos sob demanda para dimensões de alta cardinalidade."""
        dim = self.model.get_dimension(dimension_name)
        col = dim.column
        cursor = self.con.cursor()

        if search:
            sql = f"SELECT DISTINCT {col} FROM v_beneficiarios_parquet WHERE {col} ILIKE ? ORDER BY 1 LIMIT {int(limit)}"
            res = cursor.execute(sql, [f"%{search}%"]).fetchall()
        else:
            sql = f"SELECT DISTINCT {col} FROM v_beneficiarios_parquet ORDER BY 1 LIMIT {int(limit)}"
            res = cursor.execute(sql).fetchall()

        return [str(r[0]) for r in res if r[0] is not None]

    def export_to_csv(self, query: SemanticQuery, output_path: str) -> None:
        """Exporta diretamente o resultado da consulta para CSV via streaming do DuckDB."""
        sql, params, _, _, _ = self.planner.plan(
            query, table_expression="v_beneficiarios_parquet"
        )
        debug_sql = sql
        for p in params:
            val_rep = f"'{p}'" if isinstance(p, str) else str(p)
            debug_sql = debug_sql.replace("?", val_rep, 1)

        copy_sql = f"COPY ({debug_sql}) TO '{output_path}' (HEADER, DELIMITER ',')"
        self.con.execute(copy_sql)

    def export_to_parquet(self, query: SemanticQuery, output_path: str) -> None:
        """Exporta diretamente o resultado da consulta para Parquet compactado via DuckDB."""
        sql, params, _, _, _ = self.planner.plan(
            query, table_expression="v_beneficiarios_parquet"
        )
        debug_sql = sql
        for p in params:
            val_rep = f"'{p}'" if isinstance(p, str) else str(p)
            debug_sql = debug_sql.replace("?", val_rep, 1)

        copy_sql = f"COPY ({debug_sql}) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        self.con.execute(copy_sql)
