import os
from typing import Dict

# Default materiality thresholds (INR)
DEFAULT_MATERIALITY = {
    "LOW": 1000,
    "MEDIUM": 25000,
    "HIGH": 100000,
}


def load_materiality_thresholds() -> Dict[str, int]:
    """Load thresholds from environment variables falling back to defaults."""
    def get_int(env_name, default):
        v = os.environ.get(env_name)
        try:
            return int(v) if v is not None else default
        except Exception:
            return default

    return {
        "LOW": get_int("MAT_LOW", DEFAULT_MATERIALITY["LOW"]),
        "MEDIUM": get_int("MAT_MEDIUM", DEFAULT_MATERIALITY["MEDIUM"]),
        "HIGH": get_int("MAT_HIGH", DEFAULT_MATERIALITY["HIGH"]),
    }


def classify_materiality(amount: int, thresholds: Dict[str, int] = None) -> str:
    if thresholds is None:
        thresholds = load_materiality_thresholds()
    if amount is None:
        return "UNKNOWN"
    try:
        a = abs(int(amount))
    except Exception:
        return "UNKNOWN"

    if a < thresholds["LOW"]:
        return "LOW"
    if a < thresholds["MEDIUM"]:
        return "MEDIUM"
    if a < thresholds["HIGH"]:
        return "HIGH"
    return "CRITICAL"


def map_severity(materiality: str, confidence: float) -> str:
    """Map materiality and confidence to a severity label.

    Rules (prototype):
    - CRITICAL materiality -> severity CRITICAL
    - HIGH materiality and confidence < 0.8 -> severity HIGH
    - MEDIUM materiality and confidence < 0.8 -> severity MEDIUM
    - LOW materiality or confidence >= 0.95 -> severity LOW
    - otherwise MEDIUM
    """
    if materiality == "CRITICAL":
        return "CRITICAL"
    if materiality == "HIGH":
        return "HIGH" if confidence < 0.8 else "MEDIUM"
    if materiality == "MEDIUM":
        return "MEDIUM" if confidence < 0.8 else "LOW"
    if materiality == "LOW":
        return "LOW"
    return "MEDIUM"
