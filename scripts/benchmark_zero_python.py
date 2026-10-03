#!/usr/bin/env python3
"""
Benchmark Automatizado de Publicação Estática Zero-Python e Volumetria Analítica.
Avalia os perfis XS, S, M, L, XL, mensurando:
  1. Volume Parquet de Origem (MB, linhas, arquivos)
  2. Volume Consultado no Build e Tamanho do Cubo Analítico (KB, registros)
  3. Desempenho de Consultas DuckDB (ms por query e total)
  4. Comparação Estratégia A (milhares de estados) vs Estratégia B (cubo compacto + filtragem Svelte)
  5. Tempo de Exportação do marimo-studio
  6. Tamanho do Dist (Raw, Gzip, Brotli)
  7. Simulação de Rede e Latência de Cross-Filter
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
import duckdb
import psutil

# Importa AnalyticsEngine e gerador sintético
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.analytics.service import AnalyticsEngine, AnalyticalFilters
from scripts.generate_synthetic_data import generate_dataset
from scripts.analyze_dist import analyze_directory, format_bytes


def get_dir_size(path: str) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            total += os.path.getsize(fp)
    return total


def benchmark_duckdb_queries(engine: AnalyticsEngine) -> dict:
    default_filters = AnalyticalFilters()

    queries = [
        ("kpis", lambda: engine.get_kpis(default_filters)),
        ("evolution", lambda: engine.get_evolution_time_series(default_filters, 36)),
        ("profile", lambda: engine.get_profile_breakdown(default_filters)),
        ("geographic", lambda: engine.get_geographic_distribution(default_filters)),
        ("financial", lambda: engine.get_financial_evolution(default_filters, 24)),
        ("demands", lambda: engine.get_consumer_demands(default_filters)),
        ("operators", lambda: engine.get_top_operators(default_filters, 15)),
        ("analytical_cube", lambda: engine.get_analytical_cube()),
    ]

    timings = {}
    total_time = 0.0

    # Warmup
    engine.get_kpis(default_filters)

    results = {}
    for name, q_func in queries:
        t0 = time.perf_counter()
        res = q_func()
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0
        timings[name] = round(elapsed_ms, 2)
        total_time += elapsed_ms
        results[name] = res

    timings["total_ms"] = round(total_time, 2)

    # Mede tamanho do cubo e do payload total serializado
    cube = results["analytical_cube"]
    cube_json = json.dumps(cube)
    payload = {
        "filters": default_filters.to_dict(),
        "kpis": results["kpis"],
        "evolution": results["evolution"],
        "profile": results["profile"],
        "geographic": results["geographic"],
        "financial": results["financial"],
        "demands": results["demands"],
        "operators": results["operators"],
        "cube": cube,
    }
    payload_json = json.dumps(payload)

    # Contagem de registros no cubo
    cube_counts = {
        "snap_rows": len(cube.get("snap", [])),
        "snap_prev_rows": len(cube.get("snap_prev", [])),
        "trend_rows": len(cube.get("trend", [])),
        "trend_seg_rows": len(cube.get("trend_seg", [])),
        "fin_rows": len(cube.get("fin", [])),
        "dem_time_rows": len(cube.get("dem_time", [])),
        "dem_temas_rows": len(cube.get("dem_temas", [])),
        "ops_rows": len(cube.get("ops", [])),
    }

    return {
        "timings_ms": timings,
        "cube_json_bytes": len(cube_json.encode("utf-8")),
        "payload_json_bytes": len(payload_json.encode("utf-8")),
        "cube_counts": cube_counts,
    }


def analyze_combinatorics(engine: AnalyticsEngine) -> dict:
    """Calcula o espaço amostral combinatório teórico vs combinações válidas no dataset."""
    con = engine.con

    # Contagens de valores distintos
    n_ufs = con.execute("SELECT COUNT(DISTINCT sigla_uf) FROM v_beneficiarios").fetchone()[0] or 27
    n_assist = con.execute("SELECT COUNT(DISTINCT tipo_assistencia) FROM v_beneficiarios").fetchone()[0] or 2
    n_contrat = con.execute("SELECT COUNT(DISTINCT tipo_contratacao) FROM v_beneficiarios").fetchone()[0] or 3
    n_modalid = con.execute("SELECT COUNT(DISTINCT modalidade) FROM v_beneficiarios").fetchone()[0] or 7
    n_comps = con.execute("SELECT COUNT(DISTINCT competencia) FROM v_beneficiarios").fetchone()[0] or 30

    # Espaço combinatório teórico cartesiano
    theoretical_total = n_ufs * (n_assist + 1) * (n_contrat + 1) * (n_modalid + 1) * n_comps

    # Combinações válidas existentes com dados no último snapshot
    latest_comp = engine.get_latest_competence()
    valid_combos_snap = con.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT sigla_uf, tipo_assistencia, tipo_contratacao, modalidade
            FROM v_beneficiarios
            WHERE competencia = '{latest_comp}'
            GROUP BY sigla_uf, tipo_assistencia, tipo_contratacao, modalidade
        )
    """).fetchone()[0]

    # Combinações válidas totais históricas
    valid_combos_all = con.execute("""
        SELECT COUNT(*) FROM (
            SELECT competencia, sigla_uf, tipo_assistencia, tipo_contratacao, modalidade
            FROM v_beneficiarios
            GROUP BY competencia, sigla_uf, tipo_assistencia, tipo_contratacao, modalidade
        )
    """).fetchone()[0]

    return {
        "dimensions": {
            "ufs": n_ufs,
            "assistencias": n_assist,
            "contratacoes": n_contrat,
            "modalidades": n_modalid,
            "competencias": n_comps,
        },
        "theoretical_total": theoretical_total,
        "valid_combos_snapshot": valid_combos_snap,
        "valid_combos_historical": valid_combos_all,
        "strategy_a_states": valid_combos_snap,  # Se cada fatia do snapshot fosse um arquivo
        "strategy_b_states": 1,                 # 1 cubo agregado compacto
    }


def simulate_network_and_ux(payload_gzip_bytes: int, js_gzip_bytes: int, css_gzip_bytes: int) -> dict:
    """
    Simula tempo de transferência em diferentes redes:
      - Banda Larga (100 Mbps, RTT 10ms)
      - 4G Rápido (30 Mbps, RTT 40ms)
      - 4G Lento / Móvel Regular (10 Mbps, RTT 80ms)
      - 3G (1.5 Mbps, RTT 250ms)
    """
    total_transfer = payload_gzip_bytes + js_gzip_bytes + css_gzip_bytes

    profiles = {
        "Banda Larga (100 Mbps)": {"speed_mbps": 100.0, "rtt_ms": 10},
        "4G Rápido (30 Mbps)": {"speed_mbps": 30.0, "rtt_ms": 40},
        "4G Regular (10 Mbps)": {"speed_mbps": 10.0, "rtt_ms": 80},
        "3G (1.5 Mbps)": {"speed_mbps": 1.5, "rtt_ms": 250},
    }

    metrics = {}
    for name, p in profiles.items():
        speed_bps = p["speed_mbps"] * 1_000_000 / 8.0
        transfer_ms = (total_transfer / speed_bps) * 1000.0
        ttfb = p["rtt_ms"] * 2
        fcp = ttfb + (css_gzip_bytes / speed_bps) * 1000.0 + 50
        lcp = ttfb + transfer_ms + 120  # Parse JS + render inicial
        tti = lcp + 80
        metrics[name] = {
            "transfer_time_s": round(transfer_ms / 1000.0, 3),
            "ttfb_ms": round(ttfb, 1),
            "fcp_s": round(fcp / 1000.0, 2),
            "lcp_s": round(lcp / 1000.0, 2),
            "tti_s": round(tti / 1000.0, 2),
        }
    return metrics


def run_benchmark(target_profile: str = "all"):
    profiles_to_test = ["static-xs", "static-s", "static-m", "static-l", "static-xl"] if target_profile == "all" else [target_profile]

    results_summary = []
    base_tmp = "/tmp/bench_zero_python"
    os.makedirs(base_tmp, exist_ok=True)

    print(f"\n================================================================================")
    print(f" BENCHMARK EMPÍRICO ZERO-PYTHON - SALA DE SITUAÇÃO ANS")
    print(f" Perfis selecionados: {', '.join(profiles_to_test)}")
    print(f"================================================================================\n")

    for profile in profiles_to_test:
        print(f"\n>>> Executando perfil: {profile.upper()} ...")
        profile_dir = os.path.join(base_tmp, profile)
        os.makedirs(profile_dir, exist_ok=True)

        data_dir = os.path.join(profile_dir, "data")
        dist_dir = os.path.join(profile_dir, "dist")

        # 1. Geração de Dados
        t_gen_0 = time.perf_counter()
        meta_gen = generate_dataset(profile=profile, output_dir=data_dir, seed=42)
        t_gen = time.perf_counter() - t_gen_0

        parquet_size = get_dir_size(os.path.join(data_dir, "parquet"))

        # 2. Inicialização DuckDB e Consultas Analíticas
        t_duck_0 = time.perf_counter()
        engine = AnalyticsEngine(data_dir)
        t_duck_init = (time.perf_counter() - t_duck_0) * 1000.0

        query_bench = benchmark_duckdb_queries(engine)
        combo_bench = analyze_combinatorics(engine)

        # 3. Exportação Zero-Python (marimo-studio view export)
        # Executa export apenas para static-xs, dev ou static-s para testar o build do studio,
        # ou todos se solicitado
        export_time = None
        dist_stats = None
        if profile in ("static-xs", "static-s"):
            print(f"Executando marimo-studio view export com zero-python para {profile}...")
            env = os.environ.copy()
            env["SALA_DATA_DIR"] = data_dir
            t_exp_0 = time.perf_counter()
            try:
                cmd = [
                    "uv", "run", "marimo-studio", "view", "export", "dashboard",
                    "--target", "sala_situacao.py",
                    "-o", dist_dir,
                    "--runtime", "zero-python",
                    "--force"
                ]
                proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
                if proc.returncode == 0:
                    export_time = round(time.perf_counter() - t_exp_0, 2)
                    dist_stats = analyze_directory(dist_dir)
                else:
                    print(f"Aviso no export: {proc.stderr[:300]}")
            except Exception as e:
                print(f"Erro no export: {e}")

        # Se dist não foi gerado nesta iteração, usa os parâmetros medidos da query
        dist_payload_raw = query_bench["payload_json_bytes"]
        dist_payload_gzip = int(dist_payload_raw * 0.12)  # Taxa de compressão típica de JSON analítico

        results_summary.append({
            "profile": profile,
            "parquet_size_bytes": parquet_size,
            "parquet_size_formatted": format_bytes(parquet_size),
            "total_rows": meta_gen["total_rows"],
            "beneficiarios_rows": meta_gen["beneficiarios_rows"],
            "gen_time_s": round(t_gen, 2),
            "duckdb_init_ms": round(t_duck_init, 2),
            "duckdb_total_query_ms": query_bench["timings_ms"]["total_ms"],
            "cube_query_ms": query_bench["timings_ms"]["analytical_cube"],
            "cube_json_bytes": query_bench["cube_json_bytes"],
            "cube_json_formatted": format_bytes(query_bench["cube_json_bytes"]),
            "payload_json_bytes": query_bench["payload_json_bytes"],
            "payload_json_formatted": format_bytes(query_bench["payload_json_bytes"]),
            "cube_counts": query_bench["cube_counts"],
            "combinatorics": combo_bench,
            "export_time_s": export_time,
            "dist_stats": dist_stats,
        })

    # Imprime Tabela Consolidada
    print("\n\n==========================================================================================")
    print(" RESUMO CONSOLIDADO DE VOLUMETRIA E BENCHMARK ZERO-PYTHON")
    print("==========================================================================================")
    print(f"{'Perfil':<12} | {'Parquet':<10} | {'Linhas':<12} | {'DuckDB (ms)':<12} | {'Cubo JSON':<12} | {'Cubo Linhas':<12}")
    print("------------------------------------------------------------------------------------------")
    for r in results_summary:
        print(f"{r['profile']:<12} | {r['parquet_size_formatted']:<10} | {r['total_rows']:<12,d} | {r['duckdb_total_query_ms']:<12.1f} | {r['cube_json_formatted']:<12} | {r['cube_counts']['snap_rows']:<12,d}")
    print("==========================================================================================")

    # Salva relatório JSON completo
    out_json = "docs/benchmark_zero_python_results.json"
    with open(out_json, "w", encoding="utf-8") as fp:
        json.dump(results_summary, fp, indent=2, ensure_ascii=False)
    print(f"\nResultados salvos em {out_json}")

    return results_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="all", help="Perfil a testar (static-xs, static-s, static-m, static-l, static-xl ou all)")
    args = parser.parse_args()
    run_benchmark(args.profile)
