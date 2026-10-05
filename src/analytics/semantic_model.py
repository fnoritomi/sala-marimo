"""
Camada Semântica: Modelo declarativo de dados para o Cubo de Beneficiários da ANS.
Carrega e valida o catálogo semantic/beneficiarios.yaml.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class SemiAdditiveRule:
    dimension: str
    position: str = "last"
    window_choice: str = "last"


@dataclass
class Measure:
    name: str
    label: str
    column: str
    type: str = "number"
    aggregation: str = "sum"
    semi_additive: Optional[SemiAdditiveRule] = None
    description: str = ""
    format: str = "#,##0"

    @property
    def is_semi_additive(self) -> bool:
        return self.semi_additive is not None


@dataclass
class DimensionGroup:
    id: str
    label: str
    icon: str = "folder"


@dataclass
class Dimension:
    name: str
    group: str
    label: str
    column: str
    type: str = "categorical"  # categorical, date, search, numeric
    cardinality: int = 0
    code_column: Optional[str] = None
    format: Optional[str] = None
    values: List[Any] = field(default_factory=list)


@dataclass
class QueryTemplate:
    id: str
    title: str
    description: str
    measure: str
    rows: List[str]
    columns: List[str]
    filters: List[Dict[str, Any]]
    suggested_chart: str = "bar"


class SemanticModel:
    """Representação em memória do modelo semântico carregado a partir do YAML."""

    def __init__(
        self,
        dataset_name: str,
        label: str,
        remote_source: str,
        local_cache_path: str,
        description: str,
        latest_competencia: str,
        measures: Dict[str, Measure],
        dimension_groups: List[DimensionGroup],
        dimensions: Dict[str, Dimension],
        templates: List[QueryTemplate],
    ):
        self.dataset_name = dataset_name
        self.label = label
        self.remote_source = remote_source
        self.local_cache_path = local_cache_path
        self.description = description
        self.latest_competencia = latest_competencia
        self.measures = measures
        self.dimension_groups = dimension_groups
        self.dimensions = dimensions
        self.templates = templates

    @classmethod
    def load_from_yaml(cls, yaml_path: str) -> SemanticModel:
        if not os.path.exists(yaml_path):
            raise FileNotFoundError(f"Catálogo semântico não encontrado: {yaml_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        dataset = data.get("dataset", {})

        # Parse measures
        measures: Dict[str, Measure] = {}
        for m_name, m_data in data.get("measures", {}).items():
            semi_rule = None
            if m_data.get("semi_additive"):
                s_data = m_data["semi_additive"]
                semi_rule = SemiAdditiveRule(
                    dimension=s_data.get("dimension", "competencia"),
                    position=s_data.get("position", "last"),
                    window_choice=s_data.get("window_choice", "last"),
                )
            measures[m_name] = Measure(
                name=m_name,
                label=m_data.get("label", m_name),
                column=m_data.get("column", m_name),
                type=m_data.get("type", "number"),
                aggregation=m_data.get("aggregation", "sum"),
                semi_additive=semi_rule,
                description=m_data.get("description", ""),
                format=m_data.get("format", "#,##0"),
            )

        # Parse dimension groups
        dimension_groups = [
            DimensionGroup(
                id=g["id"],
                label=g.get("label", g["id"]),
                icon=g.get("icon", "folder"),
            )
            for g in data.get("dimension_groups", [])
        ]

        # Parse dimensions
        dimensions: Dict[str, Dimension] = {}
        for d_name, d_data in data.get("dimensions", {}).items():
            dimensions[d_name] = Dimension(
                name=d_name,
                group=d_data.get("group", "outros"),
                label=d_data.get("label", d_name),
                column=d_data.get("column", d_name),
                type=d_data.get("type", "categorical"),
                cardinality=d_data.get("cardinality", 0),
                code_column=d_data.get("code_column"),
                format=d_data.get("format"),
                values=d_data.get("values", []),
            )

        # Parse templates
        templates = [
            QueryTemplate(
                id=t["id"],
                title=t.get("title", t["id"]),
                description=t.get("description", ""),
                measure=t.get("measure", "beneficiarios"),
                rows=t.get("rows", []),
                columns=t.get("columns", []),
                filters=t.get("filters", []),
                suggested_chart=t.get("suggested_chart", "bar"),
            )
            for t in data.get("templates", [])
        ]

        return cls(
            dataset_name=dataset.get("name", "beneficiarios"),
            label=dataset.get("label", "Beneficiários"),
            remote_source=dataset.get("remote_source", ""),
            local_cache_path=dataset.get("local_cache_path", "data/cache/bene_2022-rg8m.parquet"),
            description=dataset.get("description", ""),
            latest_competencia=dataset.get("latest_competencia", "2022-12-01"),
            measures=measures,
            dimension_groups=dimension_groups,
            dimensions=dimensions,
            templates=templates,
        )

    def get_measure(self, name: str) -> Measure:
        if name not in self.measures:
            raise KeyError(f"Medida desconhecida no modelo semântico: '{name}'")
        return self.measures[name]

    def get_dimension(self, name: str) -> Dimension:
        if name not in self.dimensions:
            raise KeyError(f"Dimensão desconhecida no modelo semântico: '{name}'")
        return self.dimensions[name]

    def to_frontend_spec(self) -> Dict[str, Any]:
        """Exporta os metadados do modelo semântico estruturados para o frontend Svelte."""
        return {
            "dataset": {
                "name": self.dataset_name,
                "label": self.label,
                "description": self.description,
                "latest_competencia": self.latest_competencia,
            },
            "measures": [
                {
                    "id": m.name,
                    "label": m.label,
                    "type": m.type,
                    "aggregation": m.aggregation,
                    "is_semi_additive": m.is_semi_additive,
                    "description": m.description,
                    "format": m.format,
                }
                for m in self.measures.values()
            ],
            "dimension_groups": [
                {"id": g.id, "label": g.label, "icon": g.icon}
                for g in self.dimension_groups
            ],
            "dimensions": [
                {
                    "id": d.name,
                    "group": d.group,
                    "label": d.label,
                    "type": d.type,
                    "cardinality": d.cardinality,
                    "values": d.values,
                }
                for d in self.dimensions.values()
            ],
            "templates": [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "measure": t.measure,
                    "rows": t.rows,
                    "columns": t.columns,
                    "filters": t.filters,
                    "suggested_chart": t.suggested_chart,
                }
                for t in self.templates
            ],
        }
