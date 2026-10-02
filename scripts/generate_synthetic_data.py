#!/usr/bin/env python3
"""
Gerador de Dados Sintéticos Plausíveis para a Sala de Situação da ANS.

Gera dados de Beneficiários, Financeiro (DIOPS), Demandas (NIP),
Operadoras (CADOP) e População (IBGE) em formato Parquet particionado com compressão ZSTD.

Perfis:
  --profile dev: Rápido e compacto (~100k a 300k linhas totais).
  --profile realistic: Volume representativo (~2 a 4 milhões de linhas) para benchmark.

Uso:
  python scripts/generate_synthetic_data.py --profile dev
  python scripts/generate_synthetic_data.py --profile realistic --seed 42
"""

import argparse
from datetime import datetime
import os
import shutil
import sys
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

# 27 Unidades da Federação com pesos empíricos baseados em dados reais ANS / IBGE
UF_DATA = [
    # (Sigla, Nome, Região, População Estimada, Peso de Concentração na Saúde Suplementar)
    ("SP", "São Paulo", "Sudeste", 44411238, 0.365),
    ("RJ", "Rio de Janeiro", "Sudeste", 16054524, 0.115),
    ("MG", "Minas Gerais", "Sudeste", 20538718, 0.100),
    ("RS", "Rio Grande do Sul", "Sul", 10880506, 0.058),
    ("PR", "Paraná", "Sul", 11443208, 0.056),
    ("BA", "Bahia", "Nordeste", 14136417, 0.038),
    ("SC", "Santa Catarina", "Sul", 7609601, 0.040),
    ("PE", "Pernambuco", "Nordeste", 9058155, 0.027),
    ("CE", "Ceará", "Nordeste", 8791688, 0.024),
    ("GO", "Goiás", "Centro-Oeste", 7055228, 0.024),
    ("ES", "Espírito Santo", "Sudeste", 3833486, 0.023),
    ("DF", "Distrito Federal", "Centro-Oeste", 2817068, 0.032),
    ("PA", "Pará", "Norte", 8116132, 0.016),
    ("MT", "Mato Grosso", "Centro-Oeste", 3658813, 0.014),
    ("MA", "Maranhão", "Nordeste", 6775152, 0.011),
    ("MS", "Mato Grosso do Sul", "Centro-Oeste", 2756700, 0.012),
    ("AM", "Amazonas", "Norte", 3941175, 0.013),
    ("RN", "Rio Grande do Norte", "Nordeste", 3302406, 0.009),
    ("PB", "Paraíba", "Nordeste", 3974495, 0.008),
    ("AL", "Alagoas", "Nordeste", 3127511, 0.006),
    ("PI", "Piauí", "Nordeste", 3269200, 0.005),
    ("SE", "Sergipe", "Nordeste", 2209558, 0.004),
    ("RO", "Rondônia", "Norte", 1581016, 0.003),
    ("TO", "Tocantins", "Norte", 1511459, 0.002),
    ("AC", "Acre", "Norte", 830026, 0.001),
    ("AP", "Amapá", "Norte", 733508, 0.001),
    ("RR", "Roraima", "Norte", 636303, 0.001),
]

FAIXAS_ETARIAS = [
    "00 a 18",
    "19 a 23",
    "24 a 28",
    "29 a 33",
    "34 a 38",
    "39 a 43",
    "44 a 48",
    "49 a 53",
    "54 a 58",
    "59 ou mais",
]

PESOS_FAIXAS = [0.18, 0.07, 0.09, 0.10, 0.10, 0.10, 0.09, 0.08, 0.07, 0.12]

MODALIDADES = [
    ("Cooperativa médica", 0.38, "Médica"),
    ("Medicina de grupo", 0.39, "Médica"),
    ("Seguradora especializada em saúde", 0.12, "Médica"),
    ("Autogestão", 0.09, "Médica"),
    ("Filantropia", 0.02, "Médica"),
    ("Odontologia de grupo", 0.70, "Odontológica"),
    ("Cooperativa odontológica", 0.30, "Odontológica"),
]

CONTRATACOES = [
    ("Coletivo Empresarial", 0.70),
    ("Individual ou Familiar", 0.17),
    ("Coletivo por Adesão", 0.13),
]

TEMAS_DEMANDA = [
    ("Rol de Procedimentos e Eventos em Saúde", "Assistencial", 0.42),
    ("Prazos de Atendimento e Rede Conveniada", "Assistencial", 0.31),
    ("Contratos e Regulamentos", "Não Assistencial", 0.14),
    ("Mensalidades e Reajustes", "Não Assistencial", 0.08),
    ("Cancelamento e Manutenção do Plano", "Não Assistencial", 0.05),
]


def generate_dates(start_str: str, end_str: str):
    """Gera lista de tuplas (data_str, ano, mes) no primeiro dia de cada mês."""
    start = datetime.strptime(start_str, "%Y-%m-%d")
    end = datetime.strptime(end_str, "%Y-%m-%d")

    dates = []
    cur_year = start.year
    cur_month = start.month

    while (cur_year < end.year) or (
        cur_year == end.year and cur_month <= end.month
    ):
        dt_str = f"{cur_year:04d}-{cur_month:02d}-01"
        dates.append((dt_str, cur_year, cur_month))
        cur_month += 1
        if cur_month > 12:
            cur_month = 1
            cur_year += 1

    return dates


def build_operator_dimension(num_operators: int, rng: np.random.Generator):
    """Gera a dimensão de operadoras com distribuição de Zipf realista."""
    records = []
    # Prefixos fictícios mas verossímeis
    nomes_base = [
        "Univida",
        "Saúde Total",
        "Amparo",
        "MedPlano",
        "Previna",
        "InterSaúde",
        "VidaMais",
        "NorteSaúde",
        "SulAssistência",
        "Paulista Saúde",
        "Metropolitana",
        "BioSaúde",
        "Viver Bem",
        "Planalto Saúde",
        "Aliança Médica",
        "Sinergia",
        "OdontoPlanalto",
        "DenteSaúde",
        "BeloDente",
        "OralMaster",
        "Rede Dourada",
        "BrasilSaúde",
        "Nacional Med",
        "Equilíbrio",
        "Vitalis",
    ]

    uf_siglas = [u[0] for u in UF_DATA]
    uf_probs = np.array([u[4] for u in UF_DATA])
    uf_probs /= uf_probs.sum()

    med_mods = [m[0] for m in MODALIDADES if m[2] == "Médica"]
    med_probs = np.array([m[1] for m in MODALIDADES if m[2] == "Médica"])
    med_probs /= med_probs.sum()

    odo_mods = [m[0] for m in MODALIDADES if m[2] == "Odontológica"]
    odo_probs = np.array([m[1] for m in MODALIDADES if m[2] == "Odontológica"])
    odo_probs /= odo_probs.sum()

    for i in range(num_operators):
        reg_ans = 300000 + i + 1
        is_odonto = i >= int(num_operators * 0.8)

        base_nome = (
            nomes_base[i % len(nomes_base)] + f" {chr(65 + (i // len(nomes_base)) % 26)}"
        )
        if is_odonto:
            mod = rng.choice(odo_mods, p=odo_probs)
            tipo_assist = "Odontológica"
            nome_fantasia = f"{base_nome} Dental"
            razao_social = f"{base_nome} Planos Odontológicos S.A."
        else:
            mod = rng.choice(med_mods, p=med_probs)
            tipo_assist = "Médica"
            nome_fantasia = f"{base_nome} Saúde"
            razao_social = f"{base_nome} Assistência Médica Ltda."

        if i < int(num_operators * 0.08):
            porte = "Grande"
        elif i < int(num_operators * 0.30):
            porte = "Médio"
        else:
            porte = "Pequeno"

        uf_sede = rng.choice(uf_siglas, p=uf_probs)
        situacao = "Ativa com beneficiários" if i < int(num_operators * 0.95) else "Ativa sem beneficiários"

        # Peso de mercado da operadora (distribuição tipo Zipf)
        weight = 1.0 / ((i + 1) ** 0.85)

        records.append({
            "codigo_operadora": reg_ans,
            "razao_social": razao_social,
            "nome_fantasia": nome_fantasia,
            "modalidade": mod,
            "tipo_assistencia": tipo_assist,
            "porte": porte,
            "uf_sede": uf_sede,
            "situacao_registro": situacao,
            "market_weight": weight,
        })

    return records


def generate_dataset(
    profile: str,
    output_dir: str,
    seed: int,
    start_date: str = None,
    end_date: str = None,
):
    """Gera todo o ecossistema de dados sintéticos da ANS."""
    rng = np.random.default_rng(seed)

    if profile == "dev":
        start_date = start_date or "2024-01-01"
        end_date = end_date or "2026-06-01"
        num_operators = 45
        target_med_lives_base = 51_000_000
        target_odo_lives_base = 32_000_000
        sample_uf_factor = 0.65  # Seleciona subset de UFs por operadora média
    else:  # realistic
        start_date = start_date or "2021-01-01"
        end_date = end_date or "2026-06-01"
        num_operators = 320
        target_med_lives_base = 51_500_000
        target_odo_lives_base = 33_500_000
        sample_uf_factor = 0.85

    print(f"[{profile.upper()}] Iniciando geração de dados sintéticos...")
    print(f"Período: {start_date} a {end_date} | Seed: {seed} | Operadoras: {num_operators}")
    print(f"Diretório de saída: {output_dir}")

    os.makedirs(output_dir, exist_ok=True)
    parquet_dir = os.path.join(output_dir, "parquet")
    if os.path.exists(parquet_dir):
        shutil.rmtree(parquet_dir)

    dates = generate_dates(start_date, end_date)
    print(f"Competências temporais geradas: {len(dates)} meses.")

    # 1. Dimensão População UF
    pop_dir = os.path.join(parquet_dir, "populacao_uf")
    os.makedirs(pop_dir, exist_ok=True)
    pop_table = pa.Table.from_pylist(
        [
            {
                "sigla_uf": u[0],
                "nome_uf": u[1],
                "regiao": u[2],
                "populacao_estimada": u[3],
            }
            for u in UF_DATA
        ]
    )
    pq.write_table(pop_table, os.path.join(pop_dir, "populacao_uf.parquet"), compression="ZSTD")
    print(f"✓ Salva dimensão populacao_uf: {len(pop_table)} registros.")

    # 2. Dimensão Operadoras
    operators = build_operator_dimension(num_operators, rng)
    op_dir = os.path.join(parquet_dir, "operadoras")
    os.makedirs(op_dir, exist_ok=True)
    clean_ops = [
        {k: v for k, v in op.items() if k != "market_weight"}
        for op in operators
    ]
    op_table = pa.Table.from_pylist(clean_ops)
    pq.write_table(op_table, os.path.join(op_dir, "operadoras.parquet"), compression="ZSTD")
    print(f"✓ Salva dimensão operadoras: {len(op_table)} registros.")

    # Normaliza pesos de mercado das operadoras
    med_ops = [op for op in operators if op["tipo_assistencia"] == "Médica" and op["situacao_registro"] == "Ativa com beneficiários"]
    odo_ops = [op for op in operators if op["tipo_assistencia"] == "Odontológica" and op["situacao_registro"] == "Ativa com beneficiários"]

    med_total_w = sum(op["market_weight"] for op in med_ops)
    for op in med_ops:
        op["market_share"] = op["market_weight"] / med_total_w

    odo_total_w = sum(op["market_weight"] for op in odo_ops)
    for op in odo_ops:
        op["market_share"] = op["market_weight"] / odo_total_w

    uf_siglas = [u[0] for u in UF_DATA]
    uf_weights = np.array([u[4] for u in UF_DATA])
    uf_weights /= uf_weights.sum()

    contratacao_names = [c[0] for c in CONTRATACOES]
    contratacao_weights = np.array([c[1] for c in CONTRATACOES])
    contratacao_weights /= contratacao_weights.sum()

    faixa_names = FAIXAS_ETARIAS
    faixa_weights = np.array(PESOS_FAIXAS)
    faixa_weights /= faixa_weights.sum()

    # Preparar diretórios dos fatos particionados por ano
    years = sorted(list(set(d[1] for d in dates)))
    benef_dir = os.path.join(parquet_dir, "beneficiarios")
    fin_dir = os.path.join(parquet_dir, "financeiro")
    dem_dir = os.path.join(parquet_dir, "demandas")

    for yr in years:
        os.makedirs(os.path.join(benef_dir, f"ano={yr}"), exist_ok=True)
        os.makedirs(os.path.join(fin_dir, f"ano={yr}"), exist_ok=True)
        os.makedirs(os.path.join(dem_dir, f"ano={yr}"), exist_ok=True)

    total_benef_rows = 0
    total_fin_rows = 0
    total_dem_rows = 0

    print("Gerando fatos mensais para as competências...")

    # Gerar mês a mês com crescimento / sazonalidade realista
    for dt_str, yr, m in dates:
        month_idx = (yr - dates[0][1]) * 12 + (m - dates[0][2])
        # Tendência de crescimento suave (~1.5% ao ano) com ruído e sazonalidade
        growth_factor = 1.0 + (month_idx * 0.0014) + (0.003 * np.sin(2 * np.pi * m / 12)) + rng.normal(0, 0.001)

        cur_target_med = int(target_med_lives_base * growth_factor)
        cur_target_odo = int(target_odo_lives_base * growth_factor * 1.04)  # Odonto cresce um pouco mais rápido

        benef_rows_month = []
        fin_rows_month = []
        dem_rows_month = []

        # Para operadoras médicas
        for op in med_ops:
            op_lives = int(cur_target_med * op["market_share"])
            if op_lives < 10:
                continue

            # Distribuição da operadora por UFs
            # A UF sede da operadora recebe maior peso
            op_uf_weights = uf_weights.copy()
            sede_idx = uf_siglas.index(op["uf_sede"])
            op_uf_weights[sede_idx] *= 2.5
            op_uf_weights /= op_uf_weights.sum()

            # Escolhe UFs ativas para essa operadora
            if op["porte"] == "Grande":
                active_ufs = uf_siglas
            elif op["porte"] == "Médio":
                num_active = max(5, int(len(uf_siglas) * 0.4))
                active_ufs = [uf_siglas[sede_idx]] + list(rng.choice([u for u in uf_siglas if u != uf_siglas[sede_idx]], size=num_active, replace=False))
            else:
                active_ufs = [uf_siglas[sede_idx]]
                if rng.random() > 0.4:
                    neighbor = rng.choice(uf_siglas)
                    if neighbor not in active_ufs:
                        active_ufs.append(neighbor)

            active_weights = np.array([op_uf_weights[uf_siglas.index(u)] for u in active_ufs])
            active_weights /= active_weights.sum()

            op_lives_uf = rng.multinomial(op_lives, active_weights)

            # Ticket médio mensal por vida: ~R$ 440 a R$ 560
            ticket_medio = rng.normal(480.0, 35.0)
            if op["porte"] == "Grande":
                ticket_medio *= 1.05

            op_total_rec = 0.0
            op_total_desp = 0.0

            for u_idx, uf in enumerate(active_ufs):
                lives_uf = op_lives_uf[u_idx]
                if lives_uf == 0:
                    continue

                # Reparte por tipo de contratação
                lives_contratacao = rng.multinomial(lives_uf, contratacao_weights)

                for c_idx, c_name in enumerate(contratacao_names):
                    c_lives = lives_contratacao[c_idx]
                    if c_lives == 0:
                        continue

                    if profile == "realistic":
                        # Reparte por faixa etária no modo realistic
                        lives_faixa = rng.multinomial(c_lives, faixa_weights)
                        for f_idx, f_name in enumerate(faixa_names):
                            f_lives = lives_faixa[f_idx]
                            if f_lives > 0:
                                benef_rows_month.append({
                                    "competencia": dt_str,
                                    "ano": yr,
                                    "mes": m,
                                    "codigo_operadora": op["codigo_operadora"],
                                    "sigla_uf": uf,
                                    "tipo_assistencia": "Médica",
                                    "tipo_contratacao": c_name,
                                    "modalidade": op["modalidade"],
                                    "faixa_etaria": f_name,
                                    "beneficiarios": int(f_lives),
                                })
                    else:
                        # Modo dev agrega as faixas etárias principais para velocidade
                        f_name = faixa_names[c_idx % len(faixa_names)]
                        benef_rows_month.append({
                            "competencia": dt_str,
                            "ano": yr,
                            "mes": m,
                            "codigo_operadora": op["codigo_operadora"],
                            "sigla_uf": uf,
                            "tipo_assistencia": "Médica",
                            "tipo_contratacao": c_name,
                            "modalidade": op["modalidade"],
                            "faixa_etaria": f_name,
                            "beneficiarios": int(c_lives),
                        })

                # Fatos Financeiros por UF/Operadora
                rec_uf = lives_uf * ticket_medio
                # Sinistralidade realista com componente sazonal (pico no inverno jul/ago)
                sinistralidade_base = 0.835 + (0.025 * np.cos(2 * np.pi * (m - 7) / 12)) + rng.normal(0, 0.015)
                desp_assist = rec_uf * sinistralidade_base
                desp_admin = rec_uf * rng.uniform(0.08, 0.12)
                res_op = rec_uf - desp_assist - desp_admin

                fin_rows_month.append({
                    "competencia": dt_str,
                    "ano": yr,
                    "mes": m,
                    "codigo_operadora": op["codigo_operadora"],
                    "modalidade": op["modalidade"],
                    "sigla_uf": uf,
                    "receita_contraprestacoes": round(float(rec_uf), 2),
                    "despesa_assistencial": round(float(desp_assist), 2),
                    "despesa_administrativa": round(float(desp_admin), 2),
                    "resultado_operacional": round(float(res_op), 2),
                })

                # Demandas NIP (taxa média de 3.5 a 5.0 demandas por 10.000 vidas ao mês)
                taxa_demanda_10k = rng.uniform(2.8, 5.5)
                expected_dem = (lives_uf / 10_000.0) * taxa_demanda_10k
                num_dem = rng.poisson(expected_dem)

                if num_dem > 0:
                    for tema, nat, p_tema in TEMAS_DEMANDA:
                        t_dem = int(round(num_dem * p_tema))
                        if t_dem > 0:
                            # Resolutividade pré-processual NIP: ~84% a 92%
                            resolv = int(round(t_dem * rng.uniform(0.82, 0.93)))
                            resolv = min(resolv, t_dem)
                            dem_rows_month.append({
                                "competencia": dt_str,
                                "ano": yr,
                                "mes": m,
                                "codigo_operadora": op["codigo_operadora"],
                                "modalidade": op["modalidade"],
                                "sigla_uf": uf,
                                "natureza_demanda": nat,
                                "tema_demanda": tema,
                                "total_demandas": t_dem,
                                "demandas_resolvidas": resolv,
                            })

        # Para operadoras odontológicas
        for op in odo_ops:
            op_lives = int(cur_target_odo * op["market_share"])
            if op_lives < 10:
                continue

            sede_idx = uf_siglas.index(op["uf_sede"])
            active_ufs = [uf_siglas[sede_idx]]
            if op["porte"] in ("Grande", "Médio"):
                extra_ufs = [u for u in uf_siglas if u != uf_siglas[sede_idx]]
                chosen = rng.choice(extra_ufs, size=min(12, len(extra_ufs)), replace=False)
                active_ufs.extend(chosen)

            active_weights = np.array([uf_weights[uf_siglas.index(u)] for u in active_ufs])
            active_weights /= active_weights.sum()

            op_lives_uf = rng.multinomial(op_lives, active_weights)
            ticket_odonto = rng.normal(32.0, 3.5)

            for u_idx, uf in enumerate(active_ufs):
                lives_uf = op_lives_uf[u_idx]
                if lives_uf == 0:
                    continue

                benef_rows_month.append({
                    "competencia": dt_str,
                    "ano": yr,
                    "mes": m,
                    "codigo_operadora": op["codigo_operadora"],
                    "sigla_uf": uf,
                    "tipo_assistencia": "Odontológica",
                    "tipo_contratacao": "Coletivo Empresarial" if rng.random() > 0.25 else "Individual ou Familiar",
                    "modalidade": op["modalidade"],
                    "faixa_etaria": "29 a 33",
                    "beneficiarios": int(lives_uf),
                })

                rec_uf = lives_uf * ticket_odonto
                desp_assist = rec_uf * rng.uniform(0.45, 0.58)  # Odonto tem sinistralidade menor (~50%)
                desp_admin = rec_uf * rng.uniform(0.18, 0.25)
                res_op = rec_uf - desp_assist - desp_admin

                fin_rows_month.append({
                    "competencia": dt_str,
                    "ano": yr,
                    "mes": m,
                    "codigo_operadora": op["codigo_operadora"],
                    "modalidade": op["modalidade"],
                    "sigla_uf": uf,
                    "receita_contraprestacoes": round(float(rec_uf), 2),
                    "despesa_assistencial": round(float(desp_assist), 2),
                    "despesa_administrativa": round(float(desp_admin), 2),
                    "resultado_operacional": round(float(res_op), 2),
                })

        # Salva o particionamento do mês correspondente
        if benef_rows_month:
            b_tab = pa.Table.from_pylist(benef_rows_month)
            pq.write_table(
                b_tab,
                os.path.join(benef_dir, f"ano={yr}", f"part-{m:02d}.parquet"),
                compression="ZSTD",
            )
            total_benef_rows += len(b_tab)

        if fin_rows_month:
            f_tab = pa.Table.from_pylist(fin_rows_month)
            pq.write_table(
                f_tab,
                os.path.join(fin_dir, f"ano={yr}", f"part-{m:02d}.parquet"),
                compression="ZSTD",
            )
            total_fin_rows += len(f_tab)

        if dem_rows_month:
            d_tab = pa.Table.from_pylist(dem_rows_month)
            pq.write_table(
                d_tab,
                os.path.join(dem_dir, f"ano={yr}", f"part-{m:02d}.parquet"),
                compression="ZSTD",
            )
            total_dem_rows += len(d_tab)

    print("\n✓ Geração de Dados Concluída com Sucesso!")
    print(f"Total Beneficiários Fato: {total_benef_rows:,} linhas.")
    print(f"Total Financeiro Fato:    {total_fin_rows:,} linhas.")
    print(f"Total Demandas Fato:      {total_dem_rows:,} linhas.")
    total_rows = total_benef_rows + total_fin_rows + total_dem_rows + len(clean_ops) + len(UF_DATA)
    print(f"Total Geral de Registros: {total_rows:,} linhas.")

    return {
        "beneficiarios_rows": total_benef_rows,
        "financeiro_rows": total_fin_rows,
        "demandas_rows": total_dem_rows,
        "operadoras_rows": len(clean_ops),
        "total_rows": total_rows,
    }


def main():
    parser = argparse.ArgumentParser(description="Gerador de Dados Sintéticos para Sala de Situação ANS")
    parser.add_argument(
        "--profile",
        choices=["dev", "realistic"],
        default="dev",
        help="Perfil do dataset (dev: rápido/compacto; realistic: alto volume/benchmark)",
    )
    parser.add_argument(
        "--output",
        default="data",
        help="Diretório de saída (padrão: data)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed do gerador pseudo-aleatório (padrão: 42)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Data inicial no formato YYYY-MM-DD",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="Data final no formato YYYY-MM-DD",
    )

    args = parser.parse_args()
    generate_dataset(
        profile=args.profile,
        output_dir=args.output,
        seed=args.seed,
        start_date=args.start_date,
        end_date=args.end_date,
    )


if __name__ == "__main__":
    main()
