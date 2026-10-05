"""
Testes automatizados para a Camada Semântica (semantic_model.py e beneficiarios.yaml).
"""

import pytest
from src.analytics.semantic_model import SemanticModel


def test_semantic_model_loading():
    model = SemanticModel.load_from_yaml("semantic/beneficiarios.yaml")
    assert model.dataset_name == "beneficiarios"
    assert model.latest_competencia == "2022-12-01"
    assert len(model.measures) == 3
    assert "beneficiarios" in model.measures
    assert "adesoes" in model.measures
    assert "cancelamentos" in model.measures


def test_semi_additive_rules():
    model = SemanticModel.load_from_yaml("semantic/beneficiarios.yaml")

    benef = model.get_measure("beneficiarios")
    assert benef.is_semi_additive is True
    assert benef.semi_additive.dimension == "competencia"
    assert benef.semi_additive.position == "last"

    ades = model.get_measure("adesoes")
    assert ades.is_semi_additive is False

    canc = model.get_measure("cancelamentos")
    assert canc.is_semi_additive is False


def test_dimensions_catalog():
    model = SemanticModel.load_from_yaml("semantic/beneficiarios.yaml")

    expected_dims = [
        "competencia", "uf", "municipio", "sexo", "faixa_etaria",
        "faixa_etaria_reaj", "titularidade", "cobertura", "tipo_contratacao",
        "segmentacao", "abrangencia", "vigencia", "modalidade", "operadora"
    ]
    for d in expected_dims:
        dim = model.get_dimension(d)
        assert dim.name == d
        assert dim.column != ""


def test_frontend_spec_export():
    model = SemanticModel.load_from_yaml("semantic/beneficiarios.yaml")
    spec = model.to_frontend_spec()

    assert "dataset" in spec
    assert "measures" in spec
    assert "dimension_groups" in spec
    assert "dimensions" in spec
    assert "templates" in spec
    assert len(spec["templates"]) >= 5
