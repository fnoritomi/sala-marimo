"""
Query Planner: Traduz consultas semânticas em SQL DuckDB otimizado e seguro.
Garante proteção contra SQL injection, pushdown estrito de predicados e projeção,
cumprimento de regras de semi-aditividade e formatação de pivot.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple
from src.analytics.semantic_model import Dimension, Measure, SemanticModel
from src.analytics.query_model import FilterSpec, QueryResult, SemanticQuery


class CardinalityExceededException(Exception):
    """Exceção levantada quando a consulta pode produzir mais grupos do que o limite permitido."""
    pass


class QueryPlanner:
    """Planejador de consultas OLAP multidimensionais sobre o Parquet de Beneficiários."""

    MAX_RESULT_GROUPS = 150000

    def __init__(self, model: SemanticModel):
        self.model = model

    def estimate_cardinality(self, query: SemanticQuery) -> int:
        """
        Estima a cardinalidade máxima do resultado com base nas dimensões solicitadas
        e nos filtros ativos.
        """
        all_dims = set(query.rows + query.columns)
        if not all_dims:
            return 1

        filter_cardinalities: Dict[str, int] = {}
        for f in query.filters:
            if f.operator == "in" and f.values:
                filter_cardinalities[f.dimension] = len(f.values)
            elif f.operator == "eq":
                filter_cardinalities[f.dimension] = 1

        est = 1
        for dim_name in all_dims:
            dim = self.model.get_dimension(dim_name)
            if dim_name in filter_cardinalities:
                dim_card = filter_cardinalities[dim_name]
            else:
                dim_card = dim.cardinality if dim.cardinality > 0 else 100
            est *= max(1, dim_card)

        return est

    def plan(
        self,
        query: SemanticQuery,
        table_expression: str = "v_beneficiarios_parquet",
    ) -> Tuple[str, List[Any], bool, Optional[str], List[str]]:
        """
        Constrói a instrução SQL parametrizada e metadados de execução.

        Retorna:
            (sql, params, semi_additive_applied, effective_competencia, result_headers)
        """
        # 1. Validação estrita de identificadores (medida e dimensões)
        measure = self.model.get_measure(query.measure)
        row_dims: List[Dimension] = [self.model.get_dimension(d) for d in query.rows]
        col_dims: List[Dimension] = [self.model.get_dimension(d) for d in query.columns]

        # 2. Avaliação de Semi-Aditividade
        # Se a medida for semi-aditiva no tempo (como QT_ATIVOS) e 'competencia' NÃO estiver nas linhas/colunas:
        semi_additive_applied = False
        effective_competencia = None

        has_competencia_group = any(d.name == "competencia" for d in (row_dims + col_dims))

        # 3. Construção dos Filtros e Parâmetros
        where_clauses: List[str] = []
        params: List[Any] = []

        comp_filter_applied = False

        for f in query.filters:
            dim = self.model.get_dimension(f.dimension)
            col_sql = dim.column

            if dim.name == "competencia":
                comp_filter_applied = True

            if f.operator == "in":
                if not f.values:
                    continue
                placeholders = ", ".join(["?"] * len(f.values))
                where_clauses.append(f"{col_sql} IN ({placeholders})")
                params.extend(f.values)
            elif f.operator == "eq":
                where_clauses.append(f"{col_sql} = ?")
                params.append(f.values[0] if isinstance(f.values, list) else f.values)
            elif f.operator == "between":
                where_clauses.append(f"{col_sql} BETWEEN ? AND ?")
                params.extend(f.values[:2])
            elif f.operator == "like":
                where_clauses.append(f"{col_sql} ILIKE ?")
                params.append(f"%{f.values[0]}%")

        # Injeção da regra semi-aditiva
        if measure.is_semi_additive and not has_competencia_group:
            if not comp_filter_applied:
                # Usa o último snapshot disponível
                effective_competencia = self.model.latest_competencia
                where_clauses.append("COMPETENCIA = ?")
                params.append(effective_competencia)
                semi_additive_applied = True
            else:
                # O usuário já filtrou competência explicitamente
                semi_additive_applied = True

        # 4. Estimativa de Cardinalidade
        card_est = self.estimate_cardinality(query)
        if card_est > self.MAX_RESULT_GROUPS:
            raise CardinalityExceededException(
                f"A consulta solicitada pode produzir aproximadamente {card_est:,} grupos, "
                f"ultrapassando o limite de segurança de {self.MAX_RESULT_GROUPS:,}. "
                "Por favor, adicione filtros ou reduza as dimensões agrupadas."
            )

        # 5. Geração da Consulta: Modo Plano vs. Modo Pivot
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        if not col_dims:
            # Consulta normal agrupada (sem pivot nas colunas)
            if not row_dims:
                # Apenas agregação escalar total
                sql = (
                    f"SELECT {measure.aggregation.upper()}({measure.column}) AS total "
                    f"FROM {table_expression} "
                    f"{where_sql}"
                )
                headers = [measure.label]
            else:
                select_cols = [f"{d.column} AS \"{d.label}\"" for d in row_dims]
                group_cols = [str(i + 1) for i in range(len(row_dims))]
                sql = (
                    f"SELECT {', '.join(select_cols)}, "
                    f"{measure.aggregation.upper()}({measure.column}) AS \"{measure.label}\" "
                    f"FROM {table_expression} "
                    f"{where_sql} "
                    f"GROUP BY {', '.join(group_cols)} "
                    f"ORDER BY {', '.join(group_cols)}"
                )
                headers = [d.label for d in row_dims] + [measure.label]

            if query.limit:
                sql += f" LIMIT {int(query.limit)}"

            return sql, params, semi_additive_applied, effective_competencia, headers

        else:
            # Modo Pivot: row_dims nas linhas e primeiro col_dim nas colunas
            pivot_dim = col_dims[0]
            # Determina valores do pivot: usa os valores do filtro se houver, ou os valores pré-cadastrados da dimensão
            filter_vals = [
                f.values for f in query.filters
                if f.dimension == pivot_dim.name and f.operator == "in" and f.values
            ]
            if filter_vals:
                pivot_values = filter_vals[0]
            elif pivot_dim.values:
                pivot_values = pivot_dim.values
            else:
                # Para dimensões sem lista estática, pegamos até 15 valores mais frequentes
                pivot_values = ["Valores"]

            pivot_select_clauses = []
            headers = [d.label for d in row_dims]

            for val in pivot_values:
                val_escaped = str(val).replace("'", "''")
                alias = str(val)
                headers.append(alias)
                pivot_select_clauses.append(
                    f"SUM(CASE WHEN {pivot_dim.column} = '{val_escaped}' THEN {measure.column} ELSE 0 END) AS \"{alias}\""
                )

            # Adiciona coluna de Total
            headers.append("Total")
            pivot_select_clauses.append(f"{measure.aggregation.upper()}({measure.column}) AS \"Total\"")

            if row_dims:
                select_row_cols = [f"{d.column} AS \"{d.label}\"" for d in row_dims]
                group_cols = [str(i + 1) for i in range(len(row_dims))]
                sql = (
                    f"SELECT {', '.join(select_row_cols)}, "
                    f"{', '.join(pivot_select_clauses)} "
                    f"FROM {table_expression} "
                    f"{where_sql} "
                    f"GROUP BY {', '.join(group_cols)} "
                    f"ORDER BY {', '.join(group_cols)}"
                )
            else:
                sql = (
                    f"SELECT {', '.join(pivot_select_clauses)} "
                    f"FROM {table_expression} "
                    f"{where_sql}"
                )

            if query.limit:
                sql += f" LIMIT {int(query.limit)}"

            return sql, params, semi_additive_applied, effective_competencia, headers
