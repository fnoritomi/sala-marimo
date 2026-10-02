"""
Serviço Analítico da Sala de Situação da ANS.
Implementa a camada semântica com DuckDB sobre arquivos Parquet,
garantindo pushdown de predicados e respeito estrito a medidas semi-aditivas (snapshot).
"""

from dataclasses import dataclass, field
import os
from typing import Any, Dict, List, Optional
import duckdb


@dataclass
class AnalyticalFilters:
    """Estrutura tipada para os filtros analíticos da Sala de Situação."""
    tipo_assistencia: Optional[str] = None  # 'Médica', 'Odontológica' ou None (Todas)
    tipo_contratacao: Optional[str] = None  # 'Coletivo Empresarial', 'Individual ou Familiar', etc.
    modalidade: Optional[str] = None
    sigla_uf: Optional[str] = None          # 'SP', 'RJ', etc. ou None (Brasil)
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tipo_assistencia": self.tipo_assistencia,
            "tipo_contratacao": self.tipo_contratacao,
            "modalidade": self.modalidade,
            "sigla_uf": self.sigla_uf,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }


class AnalyticsEngine:
    """Motor analítico que gerencia a conexão DuckDB e consultas otimizadas."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.parquet_dir = os.path.join(data_dir, "parquet")
        self.con = duckdb.connect(":memory:")
        self._latest_comp: Optional[str] = None
        self._has_mod_dem: Optional[bool] = None
        self._init_views()

    def get_cursor(self) -> duckdb.DuckDBPyConnection:
        """Retorna um cursor isolado de thread para consultas concorrentes."""
        return self.con.cursor()

    def _init_views(self):
        """Inicializa views do DuckDB sobre o diretório particionado de Parquet."""
        benef_glob = os.path.join(self.parquet_dir, "beneficiarios", "*", "*.parquet")
        fin_glob = os.path.join(self.parquet_dir, "financeiro", "*", "*.parquet")
        dem_glob = os.path.join(self.parquet_dir, "demandas", "*", "*.parquet")
        op_path = os.path.join(self.parquet_dir, "operadoras", "operadoras.parquet")
        pop_path = os.path.join(self.parquet_dir, "populacao_uf", "populacao_uf.parquet")

        self.con.execute(f"CREATE OR REPLACE VIEW v_beneficiarios AS SELECT * FROM read_parquet('{benef_glob}')")
        self.con.execute(f"CREATE OR REPLACE VIEW v_financeiro AS SELECT * FROM read_parquet('{fin_glob}')")
        self.con.execute(f"CREATE OR REPLACE VIEW v_demandas AS SELECT * FROM read_parquet('{dem_glob}')")
        self.con.execute(f"CREATE OR REPLACE VIEW v_operadoras AS SELECT * FROM read_parquet('{op_path}')")
        self.con.execute(f"CREATE OR REPLACE VIEW v_populacao_uf AS SELECT * FROM read_parquet('{pop_path}')")

        # Pré-computa metadados estáticos para agilizar consultas
        res = self.con.execute("SELECT MAX(competencia) FROM v_beneficiarios").fetchone()
        self._latest_comp = str(res[0]) if res and res[0] else "2026-06-01"
        self._has_mod_dem = "modalidade" in [c[0] for c in self.con.execute("DESCRIBE v_demandas").fetchall()]

    def _build_where(self, filters: AnalyticalFilters, prefix: str = "") -> str:
        clauses = []
        p = f"{prefix}." if prefix else ""

        if filters.tipo_assistencia:
            clauses.append(f"{p}tipo_assistencia = '{filters.tipo_assistencia}'")
        if filters.tipo_contratacao:
            clauses.append(f"{p}tipo_contratacao = '{filters.tipo_contratacao}'")
        if filters.modalidade:
            clauses.append(f"{p}modalidade = '{filters.modalidade}'")
        if filters.sigla_uf:
            clauses.append(f"{p}sigla_uf = '{filters.sigla_uf}'")
        if filters.start_date:
            clauses.append(f"{p}competencia >= '{filters.start_date}'")
        if filters.end_date:
            clauses.append(f"{p}competencia <= '{filters.end_date}'")

        return f"WHERE {' AND '.join(clauses)}" if clauses else ""

    def get_latest_competence(self, con: Optional[duckdb.DuckDBPyConnection] = None) -> str:
        """Retorna a competência mais recente disponível no dataset."""
        if self._latest_comp is None:
            c = con or self.con.cursor()
            res = c.execute("SELECT MAX(competencia) FROM v_beneficiarios").fetchone()
            self._latest_comp = str(res[0]) if res and res[0] else "2026-06-01"
        return self._latest_comp

    def get_kpis(self, filters: AnalyticalFilters, con: Optional[duckdb.DuckDBPyConnection] = None) -> Dict[str, Any]:
        """
        Calcula os KPIs executivos respeitando regras semi-aditivas (snapshot na última competência).
        """
        c = con or self.con.cursor()
        latest_comp = self.get_latest_competence(c)
        
        # Filtro base sem data para calcular 12 meses atrás
        where_benef = self._build_where(filters)
        where_clause_latest = f"{where_benef} {'AND' if where_benef else 'WHERE'} competencia = '{latest_comp}'"

        # 1. Beneficiários atuais (snapshot)
        q_curr = f"SELECT COALESCE(SUM(beneficiarios), 0) FROM v_beneficiarios {where_clause_latest}"
        curr_benef = c.execute(q_curr).fetchone()[0]

        # 2. Beneficiários 12 meses atrás
        year_ago_dt = f"{int(latest_comp[:4]) - 1}{latest_comp[4:]}"
        where_clause_year_ago = f"{where_benef} {'AND' if where_benef else 'WHERE'} competencia = '{year_ago_dt}'"
        q_prev = f"SELECT COALESCE(SUM(beneficiarios), 0) FROM v_beneficiarios {where_clause_year_ago}"
        prev_benef = c.execute(q_prev).fetchone()[0]

        delta_benef_pct = round(((curr_benef - prev_benef) / prev_benef * 100.0), 2) if prev_benef > 0 else 0.0

        # 3. Operadoras ativas com beneficiários na última competência
        q_ops = f"""
            SELECT COUNT(DISTINCT codigo_operadora)
            FROM v_beneficiarios
            {where_clause_latest}
        """
        curr_ops = c.execute(q_ops).fetchone()[0]

        # Operadoras ativas há 12 meses
        q_ops_prev = f"""
            SELECT COUNT(DISTINCT codigo_operadora)
            FROM v_beneficiarios
            {where_clause_year_ago}
        """
        prev_ops = c.execute(q_ops_prev).fetchone()[0]
        delta_ops = curr_ops - prev_ops

        # 4. Receitas e Despesas acumuladas nos últimos 12 meses
        where_fin = self._build_where(AnalyticalFilters(
            tipo_assistencia=None,  # financeiro agrega por operadora/modalidade/uf
            modalidade=filters.modalidade,
            sigla_uf=filters.sigla_uf,
            start_date=year_ago_dt,
            end_date=latest_comp
        ))
        q_fin = f"""
            SELECT 
                COALESCE(SUM(receita_contraprestacoes), 0),
                COALESCE(SUM(despesa_assistencial), 0),
                COALESCE(SUM(resultado_operacional), 0)
            FROM v_financeiro
            {where_fin}
        """
        rec_12m, desp_12m, res_op_12m = c.execute(q_fin).fetchone()
        sinistralidade_12m = round((desp_12m / rec_12m * 100.0), 1) if rec_12m > 0 else 0.0

        # 5. Demandas NIP por 10k vidas nos últimos 12 meses
        has_mod_dem = self._has_mod_dem if self._has_mod_dem is not None else ("modalidade" in [col[0] for col in c.execute("DESCRIBE v_demandas").fetchall()])
        if filters.modalidade and not has_mod_dem:
            q_dem = f"""
                SELECT 
                    COALESCE(SUM(d.total_demandas), 0),
                    COALESCE(SUM(d.demandas_resolvidas), 0)
                FROM v_demandas d
                JOIN v_operadoras o ON d.codigo_operadora = o.codigo_operadora
                WHERE o.modalidade = '{filters.modalidade}'
                  AND d.competencia >= '{year_ago_dt}'
                  AND d.competencia <= '{latest_comp}'
                  {f"AND d.sigla_uf = '{filters.sigla_uf}'" if filters.sigla_uf else ""}
            """
        else:
            where_dem = self._build_where(AnalyticalFilters(
                modalidade=filters.modalidade,
                sigla_uf=filters.sigla_uf,
                start_date=year_ago_dt,
                end_date=latest_comp
            ))
            q_dem = f"""
                SELECT 
                    COALESCE(SUM(total_demandas), 0),
                    COALESCE(SUM(demandas_resolvidas), 0)
                FROM v_demandas
                {where_dem}
            """
        dem_12m, dem_res_12m = c.execute(q_dem).fetchone()
        resolutividade_pct = round((dem_res_12m / dem_12m * 100.0), 1) if dem_12m > 0 else 0.0
        taxa_demandas_10k = round((dem_12m / (curr_benef / 10_000.0)), 2) if curr_benef > 0 else 0.0

        # 6. Sparklines (últimos 12 meses)
        q_spark = f"""
            SELECT competencia, SUM(beneficiarios) as vidas
            FROM v_beneficiarios
            {where_benef} {'AND' if where_benef else 'WHERE'} competencia >= '{year_ago_dt}'
            GROUP BY competencia
            ORDER BY competencia
        """
        spark_rows = c.execute(q_spark).fetchall()
        sparkline_vidas = [r[1] for r in spark_rows]

        return {
            "competencia_atual": latest_comp,
            "beneficiarios": {
                "valor": curr_benef,
                "delta_12m_pct": delta_benef_pct,
                "delta_12m_abs": curr_benef - prev_benef,
                "sparkline": sparkline_vidas,
            },
            "operadoras": {
                "valor": curr_ops,
                "delta_12m": delta_ops,
            },
            "financeiro": {
                "receita_12m": rec_12m,
                "despesa_12m": desp_12m,
                "resultado_operacional_12m": res_op_12m,
                "sinistralidade_12m": sinistralidade_12m,
            },
            "demandas": {
                "taxa_10k": taxa_demandas_10k,
                "resolutividade_pct": resolutividade_pct,
                "total_demandas_12m": dem_12m,
            },
        }

    def get_evolution_time_series(self, filters: AnalyticalFilters, horizon_months: int = 36, con: Optional[duckdb.DuckDBPyConnection] = None) -> Dict[str, Any]:
        """
        Retorna série temporal contínua de beneficiários por competência e tipo de assistência.
        """
        c = con or self.con.cursor()
        where_clause = self._build_where(filters)
        query = f"""
            SELECT 
                competencia,
                tipo_assistencia,
                SUM(beneficiarios) as total_vidas
            FROM v_beneficiarios
            {where_clause}
            GROUP BY competencia, tipo_assistencia
            ORDER BY competencia, tipo_assistencia
        """
        rows = c.execute(query).fetchall()

        competencias = sorted(list(set(str(r[0]) for r in rows)))
        if horizon_months and len(competencias) > horizon_months:
            competencias = competencias[-horizon_months:]

        med_map = {}
        odo_map = {}
        for comp, assist, vidas in rows:
            c_str = str(comp)
            if assist == "Médica":
                med_map[c_str] = vidas
            else:
                odo_map[c_str] = vidas

        return {
            "competencias": competencias,
            "medica": [med_map.get(c, 0) for c in competencias],
            "odontologica": [odo_map.get(c, 0) for c in competencias],
            "total": [med_map.get(c, 0) + odo_map.get(c, 0) for c in competencias],
        }

    def get_profile_breakdown(self, filters: AnalyticalFilters, con: Optional[duckdb.DuckDBPyConnection] = None) -> Dict[str, Any]:
        """
        Retorna perfil por contratação e por modalidade na competência mais recente.
        """
        c = con or self.con.cursor()
        latest_comp = self.get_latest_competence(c)
        where_base = self._build_where(filters)
        where_latest = f"{where_base} {'AND' if where_base else 'WHERE'} competencia = '{latest_comp}'"

        # 1. Contratação
        q_cont = f"""
            SELECT 
                tipo_contratacao,
                SUM(beneficiarios) as vidas
            FROM v_beneficiarios
            {where_latest}
            GROUP BY tipo_contratacao
            ORDER BY vidas DESC
        """
        cont_rows = c.execute(q_cont).fetchall()
        total_cont = sum(r[1] for r in cont_rows) or 1
        contratacao = [
            {"categoria": r[0], "vidas": r[1], "pct": round(r[1] / total_cont * 100.0, 1)}
            for r in cont_rows
        ]

        # 2. Modalidade
        q_mod = f"""
            SELECT 
                modalidade,
                SUM(beneficiarios) as vidas
            FROM v_beneficiarios
            {where_latest}
            GROUP BY modalidade
            ORDER BY vidas DESC
        """
        mod_rows = c.execute(q_mod).fetchall()
        total_mod = sum(r[1] for r in mod_rows) or 1
        modalidade = [
            {"categoria": r[0], "vidas": r[1], "pct": round(r[1] / total_mod * 100.0, 1)}
            for r in mod_rows
        ]

        return {
            "competencia": latest_comp,
            "contratacao": contratacao,
            "modalidade": modalidade,
        }

    def get_geographic_distribution(self, filters: AnalyticalFilters, con: Optional[duckdb.DuckDBPyConnection] = None) -> List[Dict[str, Any]]:
        """
        Retorna distribuição geográfica de beneficiários e taxa de cobertura populacional por UF.
        """
        c = con or self.con.cursor()
        latest_comp = self.get_latest_competence(c)
        where_base = self._build_where(AnalyticalFilters(
            tipo_assistencia=filters.tipo_assistencia,
            tipo_contratacao=filters.tipo_contratacao,
            modalidade=filters.modalidade,
            sigla_uf=None,  # traz todas as UFs para o mapa / ranking
        ))
        where_latest = f"{where_base} {'AND' if where_base else 'WHERE'} b.competencia = '{latest_comp}'"

        query = f"""
            SELECT 
                p.sigla_uf,
                p.nome_uf,
                p.regiao,
                p.populacao_estimada,
                COALESCE(SUM(b.beneficiarios), 0) as vidas,
                ROUND(COALESCE(SUM(b.beneficiarios), 0) * 100.0 / p.populacao_estimada, 2) as taxa_cobertura
            FROM v_populacao_uf p
            LEFT JOIN v_beneficiarios b ON p.sigla_uf = b.sigla_uf
            {where_latest}
            GROUP BY p.sigla_uf, p.nome_uf, p.regiao, p.populacao_estimada
            ORDER BY vidas DESC
        """
        rows = c.execute(query).fetchall()
        return [
            {
                "sigla_uf": r[0],
                "nome_uf": r[1],
                "regiao": r[2],
                "populacao": r[3],
                "vidas": r[4],
                "taxa_cobertura": float(r[5]),
            }
            for r in rows
        ]

    def get_financial_evolution(self, filters: AnalyticalFilters, horizon_months: int = 24, con: Optional[duckdb.DuckDBPyConnection] = None) -> Dict[str, Any]:
        """
        Retorna evolução temporal de Receitas, Despesas Assistenciais e Sinistralidade (%).
        """
        c = con or self.con.cursor()
        where_clause = self._build_where(AnalyticalFilters(
            modalidade=filters.modalidade,
            sigla_uf=filters.sigla_uf,
            start_date=filters.start_date,
            end_date=filters.end_date,
        ))

        query = f"""
            SELECT 
                competencia,
                SUM(receita_contraprestacoes) as receita,
                SUM(despesa_assistencial) as despesa_assist,
                SUM(despesa_administrativa) as despesa_admin,
                SUM(resultado_operacional) as resultado_op,
                ROUND(SUM(despesa_assistencial) * 100.0 / NULLIF(SUM(receita_contraprestacoes), 0), 2) as sinistralidade
            FROM v_financeiro
            {where_clause}
            GROUP BY competencia
            ORDER BY competencia
        """
        rows = c.execute(query).fetchall()
        competencias = [str(r[0]) for r in rows]
        if horizon_months and len(competencias) > horizon_months:
            offset = len(competencias) - horizon_months
            rows = rows[offset:]
            competencias = competencias[offset:]

        return {
            "competencias": competencias,
            "receita": [round(float(r[1]), 2) for r in rows],
            "despesa_assistencial": [round(float(r[2]), 2) for r in rows],
            "despesa_administrativa": [round(float(r[3]), 2) for r in rows],
            "resultado_operacional": [round(float(r[4]), 2) for r in rows],
            "sinistralidade": [float(r[5]) if r[5] is not None else 0.0 for r in rows],
        }

    def get_consumer_demands(self, filters: AnalyticalFilters, con: Optional[duckdb.DuckDBPyConnection] = None) -> Dict[str, Any]:
        """
        Retorna série histórica de demandas NIP e distribuição por natureza/tema.
        """
        c = con or self.con.cursor()
        has_mod_dem = self._has_mod_dem if self._has_mod_dem is not None else ("modalidade" in [col[0] for col in c.execute("DESCRIBE v_demandas").fetchall()])
        
        if filters.modalidade and not has_mod_dem:
            from_clause = "FROM v_demandas d JOIN v_operadoras o ON d.codigo_operadora = o.codigo_operadora"
            where_parts = [f"o.modalidade = '{filters.modalidade}'"]
            if filters.sigla_uf:
                where_parts.append(f"d.sigla_uf = '{filters.sigla_uf}'")
            if filters.start_date:
                where_parts.append(f"d.competencia >= '{filters.start_date}'")
            if filters.end_date:
                where_parts.append(f"d.competencia <= '{filters.end_date}'")
            where_sql = f"WHERE {' AND '.join(where_parts)}"
            q_time = f"""
                SELECT 
                    d.competencia,
                    SUM(d.total_demandas) as total,
                    SUM(d.demandas_resolvidas) as resolvidas,
                    ROUND(SUM(d.demandas_resolvidas) * 100.0 / NULLIF(SUM(d.total_demandas), 0), 1) as taxa_resolucao
                {from_clause}
                {where_sql}
                GROUP BY d.competencia
                ORDER BY d.competencia
            """
            q_tema = f"""
                SELECT 
                    d.tema_demanda,
                    d.natureza_demanda,
                    SUM(d.total_demandas) as total
                {from_clause}
                {where_sql}
                GROUP BY d.tema_demanda, d.natureza_demanda
                ORDER BY total DESC
            """
        else:
            where_clause = self._build_where(AnalyticalFilters(
                modalidade=filters.modalidade,
                sigla_uf=filters.sigla_uf,
                start_date=filters.start_date,
                end_date=filters.end_date,
            ))
            q_time = f"""
                SELECT 
                    competencia,
                    SUM(total_demandas) as total,
                    SUM(demandas_resolvidas) as resolvidas,
                    ROUND(SUM(demandas_resolvidas) * 100.0 / NULLIF(SUM(total_demandas), 0), 1) as taxa_resolucao
                FROM v_demandas
                {where_clause}
                GROUP BY competencia
                ORDER BY competencia
            """
            q_tema = f"""
                SELECT 
                    tema_demanda,
                    natureza_demanda,
                    SUM(total_demandas) as total
                FROM v_demandas
                {where_clause}
                GROUP BY tema_demanda, natureza_demanda
                ORDER BY total DESC
            """
        time_rows = c.execute(q_time).fetchall()
        tema_rows = c.execute(q_tema).fetchall()

        return {
            "serie_temporal": {
                "competencias": [str(r[0]) for r in time_rows],
                "total": [int(r[1]) for r in time_rows],
                "resolvidas": [int(r[2]) for r in time_rows],
                "taxa_resolucao": [float(r[3]) if r[3] else 0.0 for r in time_rows],
            },
            "temas": [
                {"tema": r[0], "natureza": r[1], "total": int(r[2])}
                for r in tema_rows
            ],
        }

    def get_top_operators(self, filters: AnalyticalFilters, limit: int = 15, con: Optional[duckdb.DuckDBPyConnection] = None) -> List[Dict[str, Any]]:
        """
        Retorna o ranking analítico das maiores operadoras na última competência.
        """
        c = con or self.con.cursor()
        latest_comp = self.get_latest_competence(c)
        where_base = self._build_where(filters, prefix="b")
        where_latest = f"{where_base} {'AND' if where_base else 'WHERE'} b.competencia = '{latest_comp}'"

        query = f"""
            WITH vidas_op AS (
                SELECT 
                    b.codigo_operadora,
                    SUM(b.beneficiarios) as total_vidas
                FROM v_beneficiarios b
                {where_latest}
                GROUP BY b.codigo_operadora
            ),
            fin_op AS (
                SELECT 
                    f.codigo_operadora,
                    ROUND(SUM(f.despesa_assistencial) * 100.0 / NULLIF(SUM(f.receita_contraprestacoes), 0), 1) as sinistralidade
                FROM v_financeiro f
                WHERE f.competencia = '{latest_comp}'
                GROUP BY f.codigo_operadora
            ),
            dem_op AS (
                SELECT 
                    d.codigo_operadora,
                    SUM(d.total_demandas) as demandas
                FROM v_demandas d
                WHERE d.competencia = '{latest_comp}'
                GROUP BY d.codigo_operadora
            )
            SELECT 
                o.codigo_operadora,
                o.razao_social,
                o.nome_fantasia,
                o.modalidade,
                o.porte,
                o.uf_sede,
                v.total_vidas,
                COALESCE(f.sinistralidade, 82.5) as sinistralidade,
                ROUND(COALESCE(d.demandas, 0) * 10000.0 / NULLIF(v.total_vidas, 0), 2) as taxa_demandas_10k,
                o.tipo_assistencia
            FROM vidas_op v
            JOIN v_operadoras o ON v.codigo_operadora = o.codigo_operadora
            LEFT JOIN fin_op f ON v.codigo_operadora = f.codigo_operadora
            LEFT JOIN dem_op d ON v.codigo_operadora = d.codigo_operadora
            ORDER BY v.total_vidas DESC
            LIMIT {limit}
        """
        rows = c.execute(query).fetchall()
        return [
            {
                "codigo_operadora": r[0],
                "razao_social": r[1],
                "nome_fantasia": r[2],
                "modalidade": r[3],
                "porte": r[4],
                "uf_sede": r[5],
                "vidas": r[6],
                "sinistralidade": float(r[7]),
                "taxa_demandas_10k": float(r[8]) if r[8] else 0.0,
                "tipo_assistencia": r[9],
            }
            for r in rows
        ]

    def get_analytical_cube(self, con: Optional[duckdb.DuckDBPyConnection] = None) -> Dict[str, Any]:
        """
        Retorna cubo analítico pré-agregado compacto para cross-filter dinâmico a 60 FPS no frontend Svelte.
        """
        c = con or self.con.cursor()
        latest_comp = self.get_latest_competence(c)
        year_ago_dt = f"{int(latest_comp[:4]) - 1}{latest_comp[4:]}"
        two_years_ago_dt = f"{int(latest_comp[:4]) - 2}{latest_comp[4:]}"

        # 1. Snapshot Beneficiários
        snap_rows = c.execute(f"""
            SELECT sigla_uf, tipo_assistencia, tipo_contratacao, modalidade, SUM(beneficiarios) as vidas
            FROM v_beneficiarios
            WHERE competencia = '{latest_comp}'
            GROUP BY sigla_uf, tipo_assistencia, tipo_contratacao, modalidade
        """).fetchall()
        snap = [
            {"uf": r[0], "assist": r[1], "cont": r[2], "mod": r[3], "vidas": int(r[4])}
            for r in snap_rows
        ]

        # 1.1 Snapshot 12 meses atrás
        snap_prev_rows = c.execute(f"""
            SELECT sigla_uf, tipo_assistencia, tipo_contratacao, modalidade, SUM(beneficiarios) as vidas
            FROM v_beneficiarios
            WHERE competencia = '{year_ago_dt}'
            GROUP BY sigla_uf, tipo_assistencia, tipo_contratacao, modalidade
        """).fetchall()
        snap_prev = [
            {"uf": r[0], "assist": r[1], "cont": r[2], "mod": r[3], "vidas": int(r[4])}
            for r in snap_prev_rows
        ]

        # 2. Série Temporal Evolutiva
        trend_rows = c.execute("""
            SELECT competencia, sigla_uf, tipo_assistencia, SUM(beneficiarios) as vidas
            FROM v_beneficiarios
            GROUP BY competencia, sigla_uf, tipo_assistencia
            ORDER BY competencia
        """).fetchall()
        trend = [
            {"dt": str(r[0]), "uf": r[1], "assist": r[2], "vidas": int(r[3])}
            for r in trend_rows
        ]

        # 2.1 Série Temporal por Segmentação (Assistência, Contratação e Modalidade)
        trend_seg_rows = c.execute("""
            SELECT competencia, tipo_assistencia, tipo_contratacao, modalidade, SUM(beneficiarios) as vidas
            FROM v_beneficiarios
            GROUP BY competencia, tipo_assistencia, tipo_contratacao, modalidade
            ORDER BY competencia
        """).fetchall()
        trend_seg = [
            {"dt": str(r[0]), "assist": r[1], "cont": r[2], "mod": r[3], "vidas": int(r[4])}
            for r in trend_seg_rows
        ]

        # 3. População por UF
        pop_rows = c.execute("SELECT sigla_uf, nome_uf, regiao, populacao_estimada FROM v_populacao_uf").fetchall()
        pop_map = {r[0]: {"nome": r[1], "regiao": r[2], "pop": int(r[3])} for r in pop_rows}

        # 4. Fato Financeiro por competência, UF e modalidade
        fin_rows = c.execute(f"""
            SELECT competencia, sigla_uf, modalidade,
                   ROUND(SUM(receita_contraprestacoes)) as rec,
                   ROUND(SUM(despesa_assistencial)) as desp_assist,
                   ROUND(SUM(despesa_administrativa)) as desp_admin,
                   ROUND(SUM(resultado_operacional)) as res_op
            FROM v_financeiro
            WHERE competencia >= '{two_years_ago_dt}'
            GROUP BY competencia, sigla_uf, modalidade
            ORDER BY competencia
        """).fetchall()
        fin = [
            {
                "dt": str(r[0]), "uf": r[1], "mod": r[2],
                "rec": int(r[3]), "desp": int(r[4]),
                "adm": int(r[5]), "res": int(r[6])
            }
            for r in fin_rows
        ]

        # 5. Demandas temporais
        dem_time_rows = c.execute(f"""
            SELECT competencia, sigla_uf, modalidade,
                   SUM(total_demandas) as total,
                   SUM(demandas_resolvidas) as resolvidas
            FROM v_demandas
            WHERE competencia >= '{two_years_ago_dt}'
            GROUP BY competencia, sigla_uf, modalidade
            ORDER BY competencia
        """).fetchall()
        dem_time = [
            {"dt": str(r[0]), "uf": r[1], "mod": r[2], "tot": int(r[3]), "res": int(r[4])}
            for r in dem_time_rows
        ]

        # 5.1 Demandas por tema
        dem_tema_rows = c.execute(f"""
            SELECT sigla_uf, modalidade, tema_demanda, natureza_demanda,
                   SUM(total_demandas) as total
            FROM v_demandas
            WHERE competencia >= '{year_ago_dt}'
            GROUP BY sigla_uf, modalidade, tema_demanda, natureza_demanda
            ORDER BY total DESC
        """).fetchall()
        dem_temas = [
            {"uf": r[0], "mod": r[1], "tema": r[2], "nat": r[3], "tot": int(r[4])}
            for r in dem_tema_rows
        ]

        # 6. Operadoras ativas
        ops_rows = c.execute(f"""
            WITH vidas_op AS (
                SELECT b.codigo_operadora, SUM(b.beneficiarios) as total_vidas
                FROM v_beneficiarios b
                WHERE b.competencia = '{latest_comp}'
                GROUP BY b.codigo_operadora
            ),
            fin_op AS (
                SELECT f.codigo_operadora,
                       ROUND(SUM(f.despesa_assistencial) * 100.0 / NULLIF(SUM(f.receita_contraprestacoes), 0), 1) as sinistralidade
                FROM v_financeiro f
                WHERE f.competencia = '{latest_comp}'
                GROUP BY f.codigo_operadora
            ),
            dem_op AS (
                SELECT d.codigo_operadora, SUM(d.total_demandas) as demandas
                FROM v_demandas d
                WHERE d.competencia = '{latest_comp}'
                GROUP BY d.codigo_operadora
            )
            SELECT o.codigo_operadora, o.razao_social, o.nome_fantasia,
                   o.modalidade, o.porte, o.uf_sede,
                   COALESCE(v.total_vidas, 0) as total_vidas,
                   COALESCE(f.sinistralidade, 82.5) as sinistralidade,
                   ROUND(COALESCE(d.demandas, 0) * 10000.0 / NULLIF(v.total_vidas, 0), 2) as taxa_demandas_10k,
                   o.tipo_assistencia
            FROM v_operadoras o
            JOIN vidas_op v ON o.codigo_operadora = v.codigo_operadora
            LEFT JOIN fin_op f ON o.codigo_operadora = f.codigo_operadora
            LEFT JOIN dem_op d ON o.codigo_operadora = d.codigo_operadora
            ORDER BY v.total_vidas DESC
            LIMIT 50
        """).fetchall()
        ops = [
            {
                "codigo_operadora": r[0],
                "razao_social": r[1],
                "nome_fantasia": r[2],
                "modalidade": r[3],
                "porte": r[4],
                "uf_sede": r[5],
                "vidas": int(r[6]),
                "sinistralidade": float(r[7]),
                "taxa_demandas_10k": float(r[8]) if r[8] else 0.0,
                "tipo_assistencia": r[9],
            }
            for r in ops_rows
        ]

        return {
            "competencia_atual": latest_comp,
            "snap": snap,
            "snap_prev": snap_prev,
            "trend": trend,
            "trend_seg": trend_seg,
            "pop_map": pop_map,
            "fin": fin,
            "dem_time": dem_time,
            "dem_temas": dem_temas,
            "ops": ops,
        }

    def export_data(self, filters: AnalyticalFilters, output_path: str, format_type: str = "csv", con: Optional[duckdb.DuckDBPyConnection] = None):
        """Exporta os dados agregados diretamente pelo DuckDB em streaming."""
        c = con or self.con.cursor()
        where_clause = self._build_where(filters)
        format_spec = "CSV, HEADER" if format_type.lower() == "csv" else "PARQUET, COMPRESSION 'ZSTD'"
        query = f"""
            COPY (
                SELECT 
                    competencia,
                    sigla_uf,
                    tipo_assistencia,
                    tipo_contratacao,
                    modalidade,
                    SUM(beneficiarios) as total_beneficiarios
                FROM v_beneficiarios
                {where_clause}
                GROUP BY competencia, sigla_uf, tipo_assistencia, tipo_contratacao, modalidade
                ORDER BY competencia DESC, total_beneficiarios DESC
            ) TO '{output_path}' (FORMAT {format_spec})
        """
        c.execute(query)
