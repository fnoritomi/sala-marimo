#!/usr/bin/env python3
"""
Analisa os artefatos de um diretório dist/ gerado pelo marimo-studio view export.
Calcula métricas de tamanho em disco, compressão gzip e brotli, divisão por tipo
de arquivo (JS, CSS, JSON de dados preparados, assets) e identifica os maiores arquivos.

Uso:
  python scripts/analyze_dist.py [diretório_dist]
"""

import os
import sys
import gzip
import json
try:
    import brotli
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False


def format_bytes(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


def analyze_directory(dist_dir: str):
    if not os.path.exists(dist_dir):
        print(f"Erro: diretório '{dist_dir}' não encontrado.")
        sys.exit(1)

    all_files = []
    category_sizes = {
        "html": {"raw": 0, "gzip": 0, "brotli": 0, "count": 0},
        "js": {"raw": 0, "gzip": 0, "brotli": 0, "count": 0},
        "css": {"raw": 0, "gzip": 0, "brotli": 0, "count": 0},
        "data_json": {"raw": 0, "gzip": 0, "brotli": 0, "count": 0},
        "other": {"raw": 0, "gzip": 0, "brotli": 0, "count": 0},
    }

    total_raw = 0
    total_gzip = 0
    total_brotli = 0

    for root, _, files in os.walk(dist_dir):
        for f in files:
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, dist_dir)
            size = os.path.getsize(path)

            with open(path, "rb") as fp:
                data = fp.read()

            gz_size = len(gzip.compress(data, compresslevel=6))
            br_size = len(brotli.compress(data, quality=5)) if HAS_BROTLI else gz_size

            ext = os.path.splitext(f)[1].lower()
            if ext == ".html":
                cat = "html"
            elif ext == ".js":
                cat = "js"
            elif ext == ".css":
                cat = "css"
            elif ext == ".json" or "zero-python" in path:
                cat = "data_json"
            else:
                cat = "other"

            category_sizes[cat]["raw"] += size
            category_sizes[cat]["gzip"] += gz_size
            category_sizes[cat]["brotli"] += br_size
            category_sizes[cat]["count"] += 1

            total_raw += size
            total_gzip += gz_size
            total_brotli += br_size

            all_files.append({
                "path": rel_path,
                "category": cat,
                "raw": size,
                "gzip": gz_size,
                "brotli": br_size,
            })

    all_files.sort(key=lambda x: x["raw"], reverse=True)

    print("======================================================================")
    print(f" RELATÓRIO DE ANÁLISE DE BUILD ESTÁTICO ZERO-PYTHON ({dist_dir})")
    print("======================================================================")
    print(f"Total de Arquivos: {len(all_files)}")
    print(f"Tamanho Total Raw:    {format_bytes(total_raw)} ({total_raw:,} bytes)")
    print(f"Tamanho Total Gzip:   {format_bytes(total_gzip)} ({total_gzip:,} bytes)")
    if HAS_BROTLI:
        print(f"Tamanho Total Brotli: {format_bytes(total_brotli)} ({total_brotli:,} bytes)")
    print("----------------------------------------------------------------------")
    print(f"{'Categoria':<15} | {'Arquivos':<8} | {'Raw':<12} | {'Gzip':<12} | {'Brotli':<12}")
    print("----------------------------------------------------------------------")
    for cat, info in category_sizes.items():
        print(f"{cat:<15} | {info['count']:<8} | {format_bytes(info['raw']):<12} | {format_bytes(info['gzip']):<12} | {format_bytes(info['brotli']):<12}")
    print("----------------------------------------------------------------------")
    print("\nTop 5 Maiores Arquivos no Bundle:")
    for i, item in enumerate(all_files[:5], 1):
        print(f"  {i}. {item['path']} ({format_bytes(item['raw'])} raw | {format_bytes(item['gzip'])} gzip | {format_bytes(item['brotli'])} br)")
    print("======================================================================")

    return {
        "total_files": len(all_files),
        "total_raw": total_raw,
        "total_gzip": total_gzip,
        "total_brotli": total_brotli,
        "categories": category_sizes,
        "top_files": all_files[:10],
    }


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "dist"
    analyze_directory(target)
