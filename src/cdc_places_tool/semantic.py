"""Load and query the semantic layer."""

from dataclasses import dataclass
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEMANTIC_PATH = ROOT / "semantic" / "measures.yaml"


@dataclass(frozen=True)
class Measure:
    id: str
    label: str
    column: str
    unit: str
    universe: str
    plain_language: str
    synonyms: list[str]
    allowed_operations: list[str]
    caveats: list[str]


@dataclass(frozen=True)
class SemanticLayer:
    dataset: dict
    measures: dict[str, Measure]

    @property
    def default_caveats(self) -> list[str]:
        return self.dataset.get("default_caveats", [])

    def get_measure(self, measure_id: str) -> Measure:
        if measure_id in self.measures:
            return self.measures[measure_id]
        normalized = measure_id.lower().strip()
        for measure in self.measures.values():
            terms = [measure.id, measure.label, *measure.synonyms]
            if normalized in {term.lower() for term in terms}:
                return measure
        raise KeyError(f"Unknown measure: {measure_id}")


def load_semantic_layer(path: Path = DEFAULT_SEMANTIC_PATH) -> SemanticLayer:
    raw = yaml.safe_load(path.read_text())
    measures = {}
    for measure_id, item in raw["measures"].items():
        measures[measure_id] = Measure(
            id=measure_id,
            label=item["label"],
            column=item["column"],
            unit=item["unit"],
            universe=item["universe"],
            plain_language=item["plain_language"],
            synonyms=item.get("synonyms", []),
            allowed_operations=item.get("allowed_operations", []),
            caveats=item.get("caveats", []),
        )
    return SemanticLayer(dataset=raw["dataset"], measures=measures)

