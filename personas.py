"""Load and filter illustrative synthetic investor profiles."""
import json
from pathlib import Path

DATA = Path(__file__).parent / "data" / "personas.json"


def load_personas():
    with DATA.open(encoding="utf-8") as handle:
        personas = json.load(handle)
    if len(personas) != 30 or len({p["id"] for p in personas}) != 30:
        raise ValueError("Expected 30 unique synthetic personas")
    return personas


def filter_personas(personas, age_bands, income_bands, risk_levels):
    return [p for p in personas if p["age_band"] in age_bands and p["income_band"] in income_bands and p["risk_tolerance"] in risk_levels]
