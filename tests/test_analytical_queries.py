"""
Testes automatizados para a camada analítica (DuckDB + Parquet) e regras de negócio semi-aditivas.
"""

import os
import duckdb
import pytest
from src.analytics.service import AnalyticsEngine, AnalyticalFilters


@pytest.fixture(scope="module")
def engine():
    """Instancia o motor analítico apontando para os dados dev gerados."""
    return AnalyticsEngine(data_dir="data")


def test_engine_initialization(engine):
    """Valida se as views do DuckDB foram devidamente criadas sobre os arquivos Parquet."""
    views = [r[0] for r in engine.con.execute("SHOW TABLES").fetchall()]
    assert "v_beneficiarios" in views
    assert "v_financeiro" in views
    assert "v_demandas" in views
    assert "v_operadoras" in views
    assert "v_populacao_uf" in views


def test_semi_additive_kpis(engine):
    """
    Testa se o KPI de beneficiários reflete a medida de estoque (snapshot da última competência)
    e não a soma de todas as competências.
    """
    latest_comp = engine.get_latest_competence()
    kpis = engine.get_kpis(AnalyticalFilters())

    assert kpis["competencia_atual"] == latest_comp
    curr_lives = kpis["beneficiarios"]["valor"]
    
    # Verifica que o valor do KPI é exatamente o total da última competência
    expected_snapshot = engine.con.execute(
        f"SELECT SUM(beneficiarios) FROM v_beneficiarios WHERE competencia = '{latest_comp}'"
    ).fetchone()[0]
    
    assert curr_lives == expected_snapshot
    # E muito menor do que a soma de todos os meses (evita soma cumulativa errônea)
    total_all_months = engine.con.execute("SELECT SUM(beneficiarios) FROM v_beneficiarios").fetchone()[0]
    assert curr_lives < total_all_months
    assert len(kpis["beneficiarios"]["sparkline"]) > 0


def test_filter_pushdown_uf(engine):
    """Valida se o filtro por UF restringe corretamente os totais e operadores."""
    filters_sp = AnalyticalFilters(sigla_uf="SP")
    kpis_sp = engine.get_kpis(filters_sp)
    kpis_brasil = engine.get_kpis(AnalyticalFilters())

    assert kpis_sp["beneficiarios"]["valor"] < kpis_brasil["beneficiarios"]["valor"]
    # SP concentra ~36% das vidas
    ratio_sp = kpis_sp["beneficiarios"]["valor"] / kpis_brasil["beneficiarios"]["valor"]
    assert 0.30 <= ratio_sp <= 0.45


def test_profile_breakdown_percentages(engine):
    """Valida se a decomposição de contratações e modalidades soma 100%."""
    breakdown = engine.get_profile_breakdown(AnalyticalFilters())
    
    sum_cont = sum(c["pct"] for c in breakdown["contratacao"])
    assert 99.0 <= sum_cont <= 101.0  # tolerância de arredondamento

    sum_mod = sum(m["pct"] for m in breakdown["modalidade"])
    assert 99.0 <= sum_mod <= 101.0


def test_geographic_distribution_all_ufs(engine):
    """Valida se o retorno geográfico contém todas as 27 UFs com taxas de cobertura calculadas."""
    geo = engine.get_geographic_distribution(AnalyticalFilters())
    assert len(geo) == 27
    
    ufs = {g["sigla_uf"] for g in geo}
    assert "SP" in ufs and "RJ" in ufs and "DF" in ufs
    
    for g in geo:
        assert g["populacao"] > 0
        assert g["taxa_cobertura"] >= 0.0


def test_export_data_csv_and_parquet(engine, tmp_path):
    """Valida exportação direta via DuckDB para CSV e Parquet."""
    csv_file = str(tmp_path / "export_test.csv")
    parquet_file = str(tmp_path / "export_test.parquet")

    engine.export_data(AnalyticalFilters(sigla_uf="RJ"), csv_file, format_type="csv")
    engine.export_data(AnalyticalFilters(sigla_uf="RJ"), parquet_file, format_type="parquet")

    assert os.path.exists(csv_file)
    assert os.path.getsize(csv_file) > 100

    assert os.path.exists(parquet_file)
    assert os.path.getsize(parquet_file) > 100

    # Valida conteúdo do parquet exportado via DuckDB
    con = duckdb.connect()
    res = con.execute(f"SELECT DISTINCT sigla_uf FROM '{parquet_file}'").fetchall()
    assert res == [("RJ",)]


def test_analytical_cube(engine):
    """Valida se o cubo analítico multidimensional é compacto e consistente com as métricas globais."""
    import json
    cube = engine.get_analytical_cube()
    
    expected_keys = {
        "competencia_atual", "snap", "snap_prev", "trend", "trend_seg",
        "pop_map", "fin", "dem_time", "dem_temas", "ops"
    }
    assert expected_keys.issubset(set(cube.keys()))
    
    # Valida limite de 1 MB para o canal mo-value do marimo-studio
    payload_size = len(json.dumps(cube).encode("utf-8"))
    assert payload_size < 1_000_000, f"Cubo excedeu limite do marimo-studio: {payload_size} bytes"

    # Valida se a soma das vidas do snapshot coincide exatamente com o KPI global
    snap_vidas = sum(r["vidas"] for r in cube["snap"])
    kpi_vidas = engine.get_kpis(AnalyticalFilters())["beneficiarios"]["valor"]
    assert snap_vidas == kpi_vidas

    # Valida se o mapa de população contém as 27 UFs
    assert len(cube["pop_map"]) == 27

    # Valida campo tipo_assistencia nas operadoras
    assert len(cube["ops"]) > 0
    for op in cube["ops"]:
        assert "tipo_assistencia" in op
        assert op["tipo_assistencia"] in ("Médica", "Odontológica")

