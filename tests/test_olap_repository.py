"""
Testes de integração para OlapDuckDbRepository (duckdb_repository.py).
Executa consultas OLAP sobre o Parquet em cache local (data/cache/bene_2022-rg8m.parquet).
"""

import os
import pytest
from src.analytics.semantic_model import SemanticModel
from src.analytics.query_model import FilterSpec, SemanticQuery
from src.analytics.duckdb_repository import DuckDBRepository

CACHE_PATH = "data/cache/bene_2022-rg8m.parquet"


@pytest.fixture
def olap_repo():
    if not os.path.exists(CACHE_PATH):
        pytest.skip(f"Arquivo local de cache {CACHE_PATH} não encontrado.")
    model = SemanticModel.load_from_yaml("semantic/beneficiarios.yaml")
    return DuckDBRepository(model, parquet_mode="local-cache")


def test_repo_execute_time_series(olap_repo):
    # Executa Q1: Evolução temporal mensal de 2022
    q = SemanticQuery(measure="beneficiarios", rows=["competencia"])
    res = olap_repo.execute_query(q)

    assert res.error is None
    assert len(res.rows) == 12
    assert res.columns == ["Mês Competência", "Quantidade de Beneficiários Ativos"]
    # Verifica valor de janeiro e dezembro
    jan_row = res.rows[0]
    dez_row = res.rows[11]
    assert str(jan_row[0]).startswith("2022-01")
    assert jan_row[1] == 77679908
    assert str(dez_row[0]).startswith("2022-12")
    assert dez_row[1] == 80917358
    assert res.query_ms > 0


def test_repo_execute_semi_additive_uf(olap_repo):
    # Executa Q2: Beneficiários por UF sem competência -> semi-aditiva deve fixar dezembro de 2022
    q = SemanticQuery(measure="beneficiarios", rows=["uf"])
    res = olap_repo.execute_query(q)

    assert res.error is None
    assert res.semi_additive_applied is True
    assert res.effective_competencia == "2022-12-01"
    # 27 estados/DF + "XX" (exterior/ignorado) = 28 valores de UF
    assert len(res.rows) == 28
    # A soma de todas as UFs em dezembro deve ser exatamente 80.917.358
    total_uf_sum = sum(r[1] for r in res.rows)
    assert total_uf_sum == 80917358


def test_repo_execute_pivot(olap_repo):
    # Executa Q3: Pivot competência x tipo_contratacao
    q = SemanticQuery(
        measure="beneficiarios",
        rows=["competencia"],
        columns=["tipo_contratacao"],
    )
    res = olap_repo.execute_query(q)

    assert res.error is None
    assert res.is_pivoted is True
    assert len(res.rows) == 12
    assert "Total" in res.columns
    # 12 categorias de contratação catalogadas + 1 header + 1 Total = 14 colunas
    assert len(res.columns) == 14


def test_repo_get_dimension_values(olap_repo):
    # Teste de busca de valores distintos sob demanda
    ufs = olap_repo.get_distinct_values("uf")
    assert len(ufs) == 28
    assert "SP" in ufs
    assert "RJ" in ufs

    # Busca com termo de pesquisa
    ops = olap_repo.get_distinct_values("operadora", search="BRADESCO", limit=5)
    assert len(ops) > 0
    assert any("BRADESCO" in str(o).upper() for o in ops)


def test_repo_export_csv(olap_repo, tmp_path):
    q = SemanticQuery(measure="beneficiarios", rows=["competencia"])
    out_file = str(tmp_path / "test_export.csv")
    olap_repo.export_to_csv(q, out_file)
    assert os.path.exists(out_file)
    with open(out_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Mês Competência,Quantidade de Beneficiários Ativos" in content
    assert "2022-01-01,77679908" in content
    assert "2022-12-01,80917358" in content
