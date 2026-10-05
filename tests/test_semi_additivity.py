"""
Testes automatizados estritos para garantir o tratamento correto de medidas semi-aditivas.
Comprova que medidas de estoque (snapshot) não são somadas indiscriminadamente ao longo do tempo.
"""

import duckdb
import pytest
from src.analytics.semantic_model import SemanticModel
from src.analytics.query_model import FilterSpec, SemanticQuery
from src.analytics.query_planner import QueryPlanner


@pytest.fixture
def controlled_db():
    """Cria banco DuckDB em memória com 3 meses controlados (Jan=50M, Fev=51M, Mar=52M)."""
    con = duckdb.connect(":memory:")
    con.execute("""
        CREATE TABLE v_test_beneficiarios (
            COMPETENCIA DATE,
            SG_UF VARCHAR,
            QT_ATIVOS DOUBLE,
            QT_ADESOES DOUBLE,
            QT_CANCELAMENTOS DOUBLE
        );
        -- Jan/2022: SP=30M, RJ=20M -> Total 50M
        INSERT INTO v_test_beneficiarios VALUES
            ('2022-01-01', 'SP', 30000000, 1000000, 800000),
            ('2022-01-01', 'RJ', 20000000, 600000, 500000);

        -- Fev/2022: SP=31M, RJ=20M -> Total 51M
        INSERT INTO v_test_beneficiarios VALUES
            ('2022-02-01', 'SP', 31000000, 1100000, 700000),
            ('2022-02-01', 'RJ', 20000000, 700000, 600000);

        -- Mar/2022: SP=32M, RJ=20M -> Total 52M (Último Snapshot)
        INSERT INTO v_test_beneficiarios VALUES
            ('2022-03-01', 'SP', 32000000, 1200000, 600000),
            ('2022-03-01', 'RJ', 20000000, 800000, 500000);
    """)
    return con


def test_semi_additivity_invariants(controlled_db):
    model = SemanticModel.load_from_yaml("semantic/beneficiarios.yaml")
    # Atualiza temporariamente para o cenário controlado
    model.latest_competencia = "2022-03-01"
    planner = QueryPlanner(model)

    # 1. Consulta por competência (série temporal) -> Deve retornar os 3 valores mensais independentes
    q_tempo = SemanticQuery(measure="beneficiarios", rows=["competencia"])
    sql, params, semi_applied, eff_comp, _ = planner.plan(q_tempo, "v_test_beneficiarios")
    assert semi_applied is False
    rows_tempo = controlled_db.execute(sql, params).fetchall()
    assert len(rows_tempo) == 3
    # Jan = 50M, Fev = 51M, Mar = 52M
    assert rows_tempo[0][1] == 50000000.0
    assert rows_tempo[1][1] == 51000000.0
    assert rows_tempo[2][1] == 52000000.0

    # 2. Consulta por UF sem competência no agrupamento -> DEVE usar o último snapshot (Março)
    # NÃO deve somar Jan + Fev + Mar (que daria SP=93M, RJ=60M, Total=153M)
    # Deve retornar exatamente SP=32M e RJ=20M (Total=52M)
    q_uf = SemanticQuery(measure="beneficiarios", rows=["uf"])
    sql_uf, params_uf, semi_applied_uf, eff_comp_uf, _ = planner.plan(q_uf, "v_test_beneficiarios")
    assert semi_applied_uf is True
    assert eff_comp_uf == "2022-03-01"

    rows_uf = dict(controlled_db.execute(sql_uf, params_uf).fetchall())
    assert rows_uf["SP"] == 32000000.0
    assert rows_uf["RJ"] == 20000000.0
    assert sum(rows_uf.values()) == 52000000.0  # 52 milhões (e NÃO 153 milhões!)

    # 3. Consulta de Adesões (medida aditiva de fluxo) -> DEVE somar todos os meses no período
    q_adesoes = SemanticQuery(measure="adesoes", rows=["uf"])
    sql_ad, params_ad, semi_ad, _, _ = planner.plan(q_adesoes, "v_test_beneficiarios")
    assert semi_ad is False  # Adesões é medida aditiva
    rows_ad = dict(controlled_db.execute(sql_ad, params_ad).fetchall())
    # SP: 1M + 1.1M + 1.2M = 3.3M
    assert rows_ad["SP"] == 3300000.0
    # RJ: 0.6M + 0.7M + 0.8M = 2.1M
    assert rows_ad["RJ"] == 2100000.0
