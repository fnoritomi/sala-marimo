"""
Testes automatizados para o QueryPlanner (query_planner.py).
Valida pushdown, segurança de SQL, pivoteamento e limites de cardinalidade.
"""

import pytest
from src.analytics.semantic_model import SemanticModel
from src.analytics.query_model import FilterSpec, SemanticQuery
from src.analytics.query_planner import CardinalityExceededException, QueryPlanner


@pytest.fixture
def planner():
    model = SemanticModel.load_from_yaml("semantic/beneficiarios.yaml")
    return QueryPlanner(model)


def test_plan_q1_time_series(planner):
    # Q1: beneficiários por competência
    q = SemanticQuery(measure="beneficiarios", rows=["competencia"])
    sql, params, semi_applied, eff_comp, headers = planner.plan(q)

    assert "SELECT COMPETENCIA AS \"Mês Competência\", SUM(QT_ATIVOS) AS \"Quantidade de Beneficiários Ativos\"" in sql
    assert "GROUP BY 1" in sql
    assert "ORDER BY 1" in sql
    assert semi_applied is False  # Como 'competencia' está nas linhas, não precisa forçar snapshot único
    assert len(headers) == 2
    assert "SELECT *" not in sql


def test_plan_q2_categorical_uf_semi_additive(planner):
    # Q2: beneficiários por UF (sem competencia no agrupamento) -> deve aplicar regra semi-aditiva
    q = SemanticQuery(measure="beneficiarios", rows=["uf"])
    sql, params, semi_applied, eff_comp, headers = planner.plan(q)

    assert "SELECT SG_UF AS \"UF de Residência\", SUM(QT_ATIVOS)" in sql
    assert "WHERE COMPETENCIA = ?" in sql
    assert params == ["2022-12-01"]
    assert semi_applied is True
    assert eff_comp == "2022-12-01"


def test_plan_q3_pivot(planner):
    # Q3: competência nas linhas e tipo_contratação nas colunas (pivot)
    q = SemanticQuery(
        measure="beneficiarios",
        rows=["competencia"],
        columns=["tipo_contratacao"],
    )
    sql, params, semi_applied, eff_comp, headers = planner.plan(q)

    assert "SELECT COMPETENCIA AS \"Mês Competência\"" in sql
    assert "SUM(CASE WHEN DE_CONTRATACAO_PLANO = 'COLETIVO EMPRESARIAL' THEN QT_ATIVOS ELSE 0 END)" in sql
    assert "Total" in headers
    assert len(headers) > 3


def test_plan_q6_filtered(planner):
    # Q6: competência x contratação com filtro UF=RJ
    q = SemanticQuery(
        measure="beneficiarios",
        rows=["competencia"],
        columns=["tipo_contratacao"],
        filters=[FilterSpec(dimension="uf", operator="in", values=["RJ"])],
    )
    sql, params, semi_applied, eff_comp, headers = planner.plan(q)

    assert "SG_UF IN (?)" in sql
    assert params == ["RJ"]


def test_sql_injection_defense(planner):
    # Tentativa de injetar SQL em dimensão ou medida
    with pytest.raises(KeyError):
        q = SemanticQuery(measure="beneficiarios; DROP TABLE users;--", rows=["competencia"])
        planner.plan(q)

    with pytest.raises(KeyError):
        q = SemanticQuery(measure="beneficiarios", rows=["uf; SELECT 1;--"])
        planner.plan(q)


def test_cardinality_limit_protection(planner):
    # Forçar combinação que exceda o limite de cardinalidade
    # Exemplo: município (5310) * operadora (988) = 5.246.280 grupos > 150.000
    q = SemanticQuery(measure="beneficiarios", rows=["municipio", "operadora"])
    with pytest.raises(CardinalityExceededException):
        planner.plan(q)
