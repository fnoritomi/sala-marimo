#!/usr/bin/env python3
"""
Script de Benchmark de Concorrência e Memória para a Sala de Situação da ANS.

Simula sessões concorrentes (1, 10, 25, 50, 100) consultando o motor analítico DuckDB,
medindo consumo de memória (RSS total e por sessão), CPU, latência (média, p50, p95),
erros e taxa de throughput (queries/segundo).

Uso:
  python scripts/benchmark_concurrency.py
  python scripts/benchmark_concurrency.py --data-dir data_realistic
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time
import numpy as np
import psutil
from src.analytics.service import AnalyticsEngine, AnalyticalFilters


def execute_simulated_user_journey(engine: AnalyticsEngine, rng: np.random.Generator):
    """Simula uma jornada típica de um usuário interagindo com o painel."""
    ufs = [
        "SP", "RJ", "MG", "RS", "PR", "BA", "SC", "PE", "CE", "GO",
        "ES", "DF", None, None, None,
    ]
    mods = [
        "Cooperativa médica", "Medicina de grupo",
        "Seguradora especializada em saúde", None, None,
    ]
    assists = ["Médica", "Odontológica", None, None]

    uf = rng.choice(ufs)
    mod = rng.choice(mods)
    assist = rng.choice(assists)

    filters = AnalyticalFilters(
        sigla_uf=uf,
        modalidade=mod,
        tipo_assistencia=assist,
    )

    t0 = time.perf_counter()
    con = engine.get_cursor()
    kpis = engine.get_kpis(filters, con=con)
    evo = engine.get_evolution_time_series(filters, horizon_months=24, con=con)
    geo = engine.get_geographic_distribution(filters, con=con)
    fin = engine.get_financial_evolution(filters, horizon_months=12, con=con)
    ops = engine.get_top_operators(filters, limit=10, con=con)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    return duration_ms


def run_concurrency_test(concurrency_levels=[1, 10, 25, 50, 100], data_dir="data", requests_per_level=100):
    print("=" * 80)
    print("BENCHMARK DE CONCORRÊNCIA E ESCALABILIDADE DE SESSÕES - ANS")
    print(f"Diretório de dados: {data_dir} | Requisições por nível: {requests_per_level}")
    print("=" * 80)

    process = psutil.Process(os.getpid())
    mem_base_mb = process.memory_info().rss / (1024 * 1024)
    print(f"Memória base do processo inicial: {mem_base_mb:.2f} MB\n")

    engine = AnalyticsEngine(data_dir=data_dir)

    print(f"{'Concorrência':<12} | {'Lat Média':<10} | {'P50 (ms)':<9} | {'P95 (ms)':<9} | {'QPS':<8} | {'Mem Total':<10} | {'Mem/Sessão':<10} | {'Erros'}")
    print("-" * 80)

    results_table = []

    for c in concurrency_levels:
        latencies = []
        errors = 0
        cpu_readings = []

        t_start = time.perf_counter()
        psutil.cpu_percent(interval=None)

        with ThreadPoolExecutor(max_workers=c) as executor:
            futures = []
            for i in range(requests_per_level):
                rng = np.random.default_rng(c * 1000 + i)
                futures.append(executor.submit(execute_simulated_user_journey, engine, rng))

            for fut in as_completed(futures):
                try:
                    lat_ms = fut.result()
                    latencies.append(lat_ms)
                except Exception as ex:
                    errors += 1

        t_total = time.perf_counter() - t_start
        cpu_usage = psutil.cpu_percent(interval=None)
        mem_rss_mb = process.memory_info().rss / (1024 * 1024)
        mem_per_session = (mem_rss_mb - mem_base_mb) / c if c > 0 else 0

        avg_lat = np.mean(latencies) if latencies else 0
        p50_lat = np.percentile(latencies, 50) if latencies else 0
        p95_lat = np.percentile(latencies, 95) if latencies else 0
        qps = len(latencies) / t_total if t_total > 0 else 0

        print(
            f"{c:<12} | {avg_lat:>8.2f} ms | {p50_lat:>7.2f}  | {p95_lat:>7.2f}  | {qps:>6.1f}   | {mem_rss_mb:>7.1f} MB | {mem_per_session:>7.2f} MB | {errors}"
        )

        results_table.append({
            "concurrency": c,
            "avg_lat": avg_lat,
            "p50_lat": p50_lat,
            "p95_lat": p95_lat,
            "qps": qps,
            "mem_total_mb": mem_rss_mb,
            "mem_per_session_mb": mem_per_session,
            "cpu_pct": cpu_usage,
            "errors": errors,
        })

    print("-" * 80)
    print("✓ Teste de concorrência finalizado com sucesso!")
    print("=" * 80)
    return results_table


def main():
    parser = argparse.ArgumentParser(description="Benchmark de concorrência para a Sala de Situação ANS")
    parser.add_argument("--data-dir", default="data", help="Diretório de dados (data ou data_realistic)")
    parser.add_argument("--requests", type=int, default=100, help="Requisições por nível de concorrência")
    args = parser.parse_args()

    run_concurrency_test(
        concurrency_levels=[1, 10, 25, 50, 100],
        data_dir=args.data_dir,
        requests_per_level=args.requests,
    )


if __name__ == "__main__":
    main()
