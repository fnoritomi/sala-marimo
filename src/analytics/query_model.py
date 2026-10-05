"""
Modelos de Dados para a Consulta Semântica OLAP e seus Resultados.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FilterSpec:
    dimension: str
    operator: str  # 'in', 'eq', 'between', 'like'
    values: List[Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "operator": self.operator,
            "values": self.values,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FilterSpec:
        return cls(
            dimension=data.get("dimension", ""),
            operator=data.get("operator", "in"),
            values=data.get("values", []),
        )


@dataclass
class SemanticQuery:
    measure: str = "beneficiarios"
    rows: List[str] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    filters: List[FilterSpec] = field(default_factory=list)
    limit: Optional[int] = 10000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "measure": self.measure,
            "rows": self.rows,
            "columns": self.columns,
            "filters": [f.to_dict() for f in self.filters],
            "limit": self.limit,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SemanticQuery:
        filters = [
            FilterSpec.from_dict(f) if isinstance(f, dict) else f
            for f in data.get("filters", [])
        ]
        return cls(
            measure=data.get("measure", "beneficiarios"),
            rows=data.get("rows", []),
            columns=data.get("columns", []),
            filters=filters,
            limit=data.get("limit", 10000),
        )


@dataclass
class QueryResult:
    columns: List[str]
    rows: List[List[Any]]
    total_rows: int
    estimated_groups: int
    query_ms: float
    sql: str
    semi_additive_applied: bool
    effective_competencia: Optional[str] = None
    measure_name: str = "beneficiarios"
    measure_label: str = "Quantidade de Beneficiários Ativos"
    is_pivoted: bool = False
    warning: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "columns": self.columns,
            "rows": self.rows,
            "total_rows": self.total_rows,
            "estimated_groups": self.estimated_groups,
            "query_ms": round(self.query_ms, 2),
            "sql": self.sql,
            "semi_additive_applied": self.semi_additive_applied,
            "effective_competencia": self.effective_competencia,
            "measure_name": self.measure_name,
            "measure_label": self.measure_label,
            "is_pivoted": self.is_pivoted,
            "warning": self.warning,
            "error": self.error,
        }
