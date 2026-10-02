# /// script
# requires-python = ">=3.10,<3.15"
#
# [tool.marimo-studio]
# default = "dashboard"
#
# [tool.marimo-studio.cells]
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="full")


@app.cell
def setup():
    import json
    import marimo as mo
    from src.analytics.service import AnalyticsEngine, AnalyticalFilters

    engine = AnalyticsEngine("data")
    return AnalyticsEngine, AnalyticalFilters, engine, json, mo


@app.cell
def controls(mo):
    # Controles reativos nativos do marimo
    sel_assistencia = mo.ui.dropdown(
        options=["Todas", "Médica", "Odontológica"],
        value="Todas",
        label="Assistência",
    )
    sel_contratacao = mo.ui.dropdown(
        options=[
            "Todas",
            "Coletivo Empresarial",
            "Individual ou Familiar",
            "Coletivo por Adesão",
        ],
        value="Todas",
        label="Contratação",
    )
    sel_modalidade = mo.ui.dropdown(
        options=[
            "Todas",
            "Cooperativa médica",
            "Medicina de grupo",
            "Seguradora especializada em saúde",
            "Autogestão",
            "Filantropia",
            "Cooperativa odontológica",
            "Odontologia de grupo",
        ],
        value="Todas",
        label="Modalidade",
    )
    sel_uf = mo.ui.dropdown(
        options=[
            "Todas", "SP", "RJ", "MG", "RS", "PR", "BA", "SC", "PE", "CE",
            "GO", "ES", "DF", "PA", "MT", "MA", "MS", "AM", "RN", "PB",
            "AL", "PI", "SE", "RO", "TO", "AC", "AP", "RR"
        ],
        value="Todas",
        label="UF",
    )
    return sel_assistencia, sel_contratacao, sel_modalidade, sel_uf


@app.cell
def active_filters(
    AnalyticalFilters,
    sel_assistencia,
    sel_contratacao,
    sel_modalidade,
    sel_uf,
):
    current_filters = AnalyticalFilters(
        tipo_assistencia=None if sel_assistencia.value == "Todas" else sel_assistencia.value,
        tipo_contratacao=None if sel_contratacao.value == "Todas" else sel_contratacao.value,
        modalidade=None if sel_modalidade.value == "Todas" else sel_modalidade.value,
        sigla_uf=None if sel_uf.value == "Todas" else sel_uf.value,
    )
    return (current_filters,)


@app.cell
def compute_kpis(current_filters, engine):
    kpis_data = engine.get_kpis(current_filters)
    return (kpis_data,)


@app.cell
def compute_evolution(current_filters, engine):
    evolution_data = engine.get_evolution_time_series(current_filters, horizon_months=36)
    return (evolution_data,)


@app.cell
def compute_profile(current_filters, engine):
    profile_data = engine.get_profile_breakdown(current_filters)
    return (profile_data,)


@app.cell
def compute_geographic(current_filters, engine):
    geographic_data = engine.get_geographic_distribution(current_filters)
    return (geographic_data,)


@app.cell
def compute_financial(current_filters, engine):
    financial_data = engine.get_financial_evolution(current_filters, horizon_months=24)
    return (financial_data,)


@app.cell
def compute_demands(current_filters, engine):
    demands_data = engine.get_consumer_demands(current_filters)
    return (demands_data,)


@app.cell
def compute_operators(current_filters, engine):
    operators_data = engine.get_top_operators(current_filters, limit=15)
    return (operators_data,)


@app.cell
def compute_cube(engine):
    cube_data = engine.get_analytical_cube()
    return (cube_data,)


@app.cell
def build_payload(
    cube_data,
    current_filters,
    demands_data,
    evolution_data,
    financial_data,
    geographic_data,
    kpis_data,
    operators_data,
    profile_data,
):
    # Pacote consolidado projetado para consumo rápido no frontend Svelte
    dashboard_payload = {
        "filters": current_filters.to_dict(),
        "kpis": kpis_data,
        "evolution": evolution_data,
        "profile": profile_data,
        "geographic": geographic_data,
        "financial": financial_data,
        "demands": demands_data,
        "operators": operators_data,
        "cube": cube_data,
    }
    return (dashboard_payload,)


@app.cell
def render_controls(
    sel_assistencia,
    sel_contratacao,
    sel_modalidade,
    sel_uf,
):
    # Célula para projeção do bloco de controles nativos
    filter_controls = [sel_assistencia, sel_contratacao, sel_modalidade, sel_uf]
    return (filter_controls,)


if __name__ == "__main__":
    app.run()
