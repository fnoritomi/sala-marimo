"""
Testes automatizados para validação do gerador sintético e consistência dos dados.
"""

import duckdb
import pytest
from scripts.generate_synthetic_data import UF_DATA, generate_dataset


@pytest.fixture(scope="session")
def test_data(tmp_path_factory):
    """Gera um mini dataset para testes com seed fixa."""
    temp_dir = str(tmp_path_factory.mktemp("test_data"))
    generate_dataset(
        profile="dev",
        output_dir=temp_dir,
        seed=123,
        start_date="2025-01-01",
        end_date="2025-06-01",
    )
    return temp_dir


def test_uf_dimension_integrity(test_data):
    """Valida se a dimensão de UFs contém exatamente as 27 UFs com dados positivos."""
    con = duckdb.connect()
    pop_path = f"{test_data}/parquet/populacao_uf/populacao_uf.parquet"
    res = con.execute(f"SELECT sigla_uf, populacao_estimada FROM '{pop_path}'").fetchall()
    
    assert len(res) == 27
    expected_ufs = {u[0] for u in UF_DATA}
    retrieved_ufs = {r[0] for r in res}
    assert retrieved_ufs == expected_ufs
    for _, pop in res:
        assert pop > 500_000


def test_beneficiarios_invariants(test_data):
    """Valida invariantes dos fatos de beneficiários (valores não-negativos, UFs válidas, datas válidas)."""
    con = duckdb.connect()
    benef_path = f"{test_data}/parquet/beneficiarios/*/*.parquet"
    
    # 1. Total não negativo
    min_val = con.execute(f"SELECT MIN(beneficiarios) FROM '{benef_path}'").fetchone()[0]
    assert min_val >= 0

    # 2. Todas as UFs são válidas
    ufs = con.execute(f"SELECT DISTINCT sigla_uf FROM '{benef_path}'").fetchall()
    valid_ufs = {u[0] for u in UF_DATA}
    for (uf,) in ufs:
        assert uf in valid_ufs

    # 3. Competências mensais válidas
    competencias = con.execute(f"SELECT DISTINCT competencia FROM '{benef_path}' ORDER BY competencia").fetchall()
    assert len(competencias) == 6
    assert str(competencias[0][0]) == "2025-01-01"
    assert str(competencias[-1][0]) == "2025-06-01"


def test_fact_coherence_beneficiarios(test_data):
    """Valida se a soma das UFs e das contratações é estritamente consistente."""
    con = duckdb.connect()
    benef_path = f"{test_data}/parquet/beneficiarios/*/*.parquet"

    # Total geral por competência
    totais = con.execute(f"""
        SELECT competencia, SUM(beneficiarios) as total
        FROM '{benef_path}'
        GROUP BY competencia
        ORDER BY competencia
    """).fetchall()

    # Total por soma de UFs na competência
    soma_ufs = con.execute(f"""
        WITH por_uf AS (
            SELECT competencia, sigla_uf, SUM(beneficiarios) as uf_total
            FROM '{benef_path}'
            GROUP BY competencia, sigla_uf
        )
        SELECT competencia, SUM(uf_total)
        FROM por_uf
        GROUP BY competencia
        ORDER BY competencia
    """).fetchall()

    # Total por contratação na competência
    soma_contratacao = con.execute(f"""
        WITH por_c AS (
            SELECT competencia, tipo_contratacao, SUM(beneficiarios) as c_total
            FROM '{benef_path}'
            GROUP BY competencia, tipo_contratacao
        )
        SELECT competencia, SUM(c_total)
        FROM por_c
        GROUP BY competencia
        ORDER BY competencia
    """).fetchall()

    assert len(totais) == len(soma_ufs) == len(soma_contratacao)
    for (comp, tot), (_, tot_uf), (_, tot_c) in zip(totais, soma_ufs, soma_contratacao):
        assert tot == tot_uf
        assert tot == tot_c
        assert tot > 70_000_000  # ~51 mi med + ~32 mi odonto


def test_financial_invariants(test_data):
    """Valida consistência dos dados financeiros: receita e despesa positivas, sinistralidade plausível."""
    con = duckdb.connect()
    fin_path = f"{test_data}/parquet/financeiro/*/*.parquet"

    stats = con.execute(f"""
        SELECT 
            MIN(receita_contraprestacoes),
            MIN(despesa_assistencial),
            SUM(despesa_assistencial) / SUM(receita_contraprestacoes) as sinistralidade_geral
        FROM '{fin_path}'
    """).fetchone()

    min_rec, min_desp, sin_geral = stats
    assert min_rec >= 0
    assert min_desp >= 0
    # Sinistralidade consolidada geral deve estar na faixa plausível (0.65 a 0.90)
    assert 0.65 <= sin_geral <= 0.90


def test_reproducibility(tmp_path_factory):
    """Valida se a mesma seed gera exatamente o mesmo dataset."""
    dir1 = str(tmp_path_factory.mktemp("dir1"))
    dir2 = str(tmp_path_factory.mktemp("dir2"))

    generate_dataset("dev", dir1, seed=999, start_date="2025-01-01", end_date="2025-02-01")
    generate_dataset("dev", dir2, seed=999, start_date="2025-01-01", end_date="2025-02-01")

    con = duckdb.connect()
    sum1 = con.execute(f"SELECT SUM(beneficiarios) FROM '{dir1}/parquet/beneficiarios/*/*.parquet'").fetchone()[0]
    sum2 = con.execute(f"SELECT SUM(beneficiarios) FROM '{dir2}/parquet/beneficiarios/*/*.parquet'").fetchone()[0]
    assert sum1 == sum2
