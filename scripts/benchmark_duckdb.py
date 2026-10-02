#!/usr/bin/env python3
"""
Script de Benchmark Independente do DuckDB para a Sala de Situação da ANS.

Mede latências de execução (cold vs warm), throughput de agregação,
efetividade do predicate pushdown e medidas semi-aditivas sobre os arquivos Parquet.

Uso:
  python scripts/benchmark_duckdb.py
  python scripts/benchmark_duckdb.py --data-dir data_realistic
"""

import argparse
import os
import time
import duckdb
from src.analytics.service import AnalyticsEngine, AnalyticalFilters


def run_benchmark(data_dir: str = "data", iterations: int = 5):
    print("=" * 70)
    print(f"BENCHMARK DUCKDB - SALA DE SITUAÇÃO ANS")
    print(f"Diretório de dados: {data_dir} | Iterações warm: {iterations}")
    print("=" * 70)

    if not os.path.exists(os.path.join(data_dir, "parquet")):
        print(f"Erro: Diretório {data_dir}/parquet não encontrado!")
        return

    # 1. Medição de Inicialização e Registro de Views
    t0 = time.perf_counter()
    engine = AnalyticsEngine(data_dir=data_dir)
    init_time_ms = (time.perf_counter() - t0) * 1000.0
    print(f"\n1. Inicialização do DuckDB e registro de Views: {init_time_ms:.2f} ms")

    # Contagem total de registros
    total_benef = engine.con.execute("SELECT COUNT(*) FROM v_beneficiarios").fetchone()[0]
    total_fin = engine.con.execute("SELECT COUNT(*) FROM v_financeiro").fetchone()[0]
    total_dem = engine.con.execute("SELECT COUNT(*) FROM v_demandas").fetchone()[0]
    print(f"   - Volume Beneficiários: {total_benef:,} linhas")
    print(f"   - Volume Financeiro:    {total_fin:,} linhas")
    print(f"   - Volume Demandas:      {total_dem:,} linhas")

    queries = [
        (
            "KPIs Executivos (Snapshot Semi-Aditivo + 12m Deltas)",
            lambda: engine.get_kpis(AnalyticalFilters()),
        ),
        (
            "Filtro Pushdown por UF (SP) - KPIs",
            lambda: engine.get_kpis(AnalyticalFilters(sigla_uf="SP")),
        ),
        (
            "Filtro Combinado (UF=RJ + Modalidade + Contratação)",
            lambda: engine.get_kpis(AnalyticalFilters(
                sigla_uf="RJ",
                modalidade="Medicina de grupo",
                tipo_contratacao="Coletivo Empresarial",
            )),
        ),
        (
            "Série Temporal de Evolução (36 meses - Médica x Odonto)",
            lambda: engine.get_evolution_time_series(AnalyticalFilters(), horizon_months=36),
        ),
        (
            "Perfil Contratação e Modalidade (Última Competência)",
            lambda: engine.get_profile_breakdown(AnalyticalFilters()),
        ),
        (
            "Distribuição Geográfica Completa (27 UFs + Taxa Cobertura)",
            lambda: engine.get_geographic_distribution(AnalyticalFilters()),
        ),
        (
            "Evolução Financeira (Receita x Despesa x Sinistralidade 24m)",
            lambda: engine.get_financial_evolution(AnalyticalFilters(), horizon_months=24),
        ),
        (
            "Demandas dos Consumidores (Série + Agrupamento por Tema)",
            lambda: engine.get_consumer_demands(AnalyticalFilters()),
        ),
        (
            "Ranking Top 15 Operadoras com Métricas Cruzadas",
            lambda: engine.get_top_operators(AnalyticalFilters(), limit=15),
        ),
    ]

    print("\n2. Execução das Consultas Analíticas:")
    print("-" * 70)
    print(f"{'Operação Analítica':<52} | {'Cold (ms)':<9} | {'Warm Méd (ms)'}")
    print("-" * 70)

    results = []

    for name, query_fn in queries:
        # Cold run
        t_cold_start = time.perf_counter()
        query_fn()
        cold_ms = (time.perf_counter() - t_cold_start) * 1000.0

        # Warm runs
        warm_times = []
        for _ in range(iterations):
            t_warm_start = time.perf_counter()
            query_fn()
            warm_times.append((time.perf_counter() - t_warm_start) * 1000.0)

        avg_warm_ms = sum(warm_times) / len(warm_times)
        min_warm_ms = min(warm_times)
        max_warm_ms = max(warm_times)

        print(f"{name:<52} | {cold_ms:>8.2f}  | {avg_warm_ms:>8.2f} (min: {min_warm_ms:.1f})")
        results.append({
            "name": name,
            "cold_ms": cold_ms,
            "warm_ms": avg_warm_ms,
        })

    print("-" * 70)
    avg_all_warm = sum(r["warm_ms"] for r in results) / len(results)
    print(f"Média Geral Warm: {avg_all_warm:.2f} ms")
    print(f"Meta de Engenharia (Warm < 500 ms): {'✓ ATENDIDA' if avg_all_warm < 500 else '✗ NÃO ATENDIDA'}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Benchmark DuckDB para Sala de Situação ANS")
    parser.add_argument("--data-dir", default="data", help="Diretório dos dados Parquet (data ou data_realistic)")
    parser.add_argument("--iterations", type=int, default=5, help="Número de iterações warm")
    args = parser.parse_args()

    run_benchmark(data_dir=args.data_dir, iterations=args.iterations)


if __name__ == "__main__":
    main()
