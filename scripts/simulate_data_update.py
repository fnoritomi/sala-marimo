#!/usr/bin/env python3
"""
Simulação de Ciclo de Atualização de Dados e Verificação de Cache Busting.
Executa:
  1. Dataset v1 (competência 2026-06-01) -> Build /tmp/update_sim/v1
  2. Avanço de competência para 2026-07-01 -> Dataset v2
  3. Rebuild /tmp/update_sim/v2
  4. Comparação de hashes, caminhos de artefatos e integridade da atualização
  5. Medição do tempo total do ciclo de atualização
"""

import json
import os
import shutil
import subprocess
import time
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.generate_synthetic_data import generate_dataset


def run_cmd(cmd, env=None):
    t0 = time.perf_counter()
    p = subprocess.run(cmd, env=env, capture_output=True, text=True)
    t = time.perf_counter() - t0
    if p.returncode != 0:
        raise RuntimeError(f"Erro ao executar {' '.join(cmd)}: {p.stderr}")
    return t, p.stdout


def find_prepared_json(dist_dir: str):
    base = os.path.join(dist_dir, "_marimo-studio", "views", "dashboard", "zero-python")
    for root, dirs, files in os.walk(base):
        if "index.json" in files:
            path = os.path.join(root, "index.json")
            rel = os.path.relpath(path, dist_dir)
            hash_name = os.path.basename(os.path.dirname(path))
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            return path, rel, hash_name, data
    return None, None, None, None


def simulate_update():
    base_dir = "/tmp/update_sim"
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir, exist_ok=True)

    print("\n======================================================================")
    print(" SIMULAÇÃO DE CICLO DE ATUALIZAÇÃO E CACHE BUSTING")
    print("======================================================================")

    # 1. Dataset Versão 1 (até 2026-06-01)
    data_v1 = os.path.join(base_dir, "data_v1")
    dist_v1 = os.path.join(base_dir, "dist_v1")
    print("\n[Passo 1/4] Gerando dataset sintético v1 (competência 2026-06-01)...")
    t_gen_v1, _ = run_cmd([
        sys.executable, "scripts/generate_synthetic_data.py",
        "--profile", "static-xs",
        "--output", data_v1,
        "--start-date", "2025-07-01",
        "--end-date", "2026-06-01"
    ])
    print(f"✓ Dataset v1 gerado em {t_gen_v1:.2f}s")

    print("\n[Passo 2/4] Executando build zero-python para v1...")
    env_v1 = os.environ.copy()
    env_v1["SALA_DATA_DIR"] = data_v1
    t_build_v1, _ = run_cmd([
        "uv", "run", "marimo-studio", "view", "export", "dashboard",
        "--target", "sala_situacao.py",
        "-o", dist_v1,
        "--runtime", "zero-python",
        "--force"
    ], env=env_v1)
    path_v1, rel_v1, hash_v1, data_v1_json = find_prepared_json(dist_v1)
    print(f"✓ Build v1 concluído em {t_build_v1:.2f}s")
    print(f"  Hash do payload v1: {hash_v1}")
    print(f"  Caminho relativo:   {rel_v1}")

    # 2. Dataset Versão 2 (avanço para 2026-07-01)
    data_v2 = os.path.join(base_dir, "data_v2")
    dist_v2 = os.path.join(base_dir, "dist_v2")
    print("\n[Passo 3/4] Publicando nova competência mensal (avanço para 2026-07-01)...")
    t_gen_v2, _ = run_cmd([
        sys.executable, "scripts/generate_synthetic_data.py",
        "--profile", "static-xs",
        "--output", data_v2,
        "--start-date", "2025-07-01",
        "--end-date", "2026-07-01"
    ])
    print(f"✓ Dataset v2 (nova competência) gerado em {t_gen_v2:.2f}s")

    print("\n[Passo 4/4] Executando build zero-python para v2...")
    env_v2 = os.environ.copy()
    env_v2["SALA_DATA_DIR"] = data_v2
    t_build_v2, _ = run_cmd([
        "uv", "run", "marimo-studio", "view", "export", "dashboard",
        "--target", "sala_situacao.py",
        "-o", dist_v2,
        "--runtime", "zero-python",
        "--force"
    ], env=env_v2)
    path_v2, rel_v2, hash_v2, data_v2_json = find_prepared_json(dist_v2)
    print(f"✓ Build v2 concluído em {t_build_v2:.2f}s")
    print(f"  Hash do payload v2: {hash_v2}")
    print(f"  Caminho relativo:   {rel_v2}")

    # Verificação de Cache Busting
    is_hash_different = (hash_v1 != hash_v2)
    total_cycle_time = t_gen_v2 + t_build_v2

    print("\n----------------------------------------------------------------------")
    print(" RESULTADO DA AUDITORIA DE ATUALIZAÇÃO & CACHE BUSTING")
    print("----------------------------------------------------------------------")
    print(f"Tempo de geração de novos dados:   {t_gen_v2:.2f} s")
    print(f"Tempo de build estático zero-python: {t_build_v2:.2f} s")
    print(f"Tempo Total do Ciclo de Atualização: {total_cycle_time:.2f} s")
    print(f"Hash v1: {hash_v1}")
    print(f"Hash v2: {hash_v2}")
    print(f"Hashes são distintos (Cache Busting Nativo): {'SIM (OK)' if is_hash_different else 'NÃO (FALHA)'}")
    print("----------------------------------------------------------------------")

    result = {
        "t_gen_v2_s": round(t_gen_v2, 2),
        "t_build_v2_s": round(t_build_v2, 2),
        "total_cycle_s": round(total_cycle_time, 2),
        "hash_v1": hash_v1,
        "hash_v2": hash_v2,
        "cache_busting_ok": is_hash_different,
        "rel_path_v1": rel_v1,
        "rel_path_v2": rel_v2,
    }

    with open("docs/update_simulation_results.json", "w", encoding="utf-8") as fp:
        json.dump(result, fp, indent=2)

    return result


if __name__ == "__main__":
    simulate_update()
