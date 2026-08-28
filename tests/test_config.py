from backend.config import classify_materiality, map_severity


def test_classify_materiality_defaults():
    thresholds = {"LOW": 1000, "MEDIUM": 25000, "HIGH": 100000}
    assert classify_materiality(0, thresholds) == "LOW"
    assert classify_materiality(999, thresholds) == "LOW"
    assert classify_materiality(1000, thresholds) == "MEDIUM"
    assert classify_materiality(24999, thresholds) == "MEDIUM"
    assert classify_materiality(25000, thresholds) == "HIGH"
    assert classify_materiality(99999, thresholds) == "HIGH"
    assert classify_materiality(100000, thresholds) == "CRITICAL"
    assert classify_materiality(None, thresholds) == "UNKNOWN"
    assert classify_materiality("abc", thresholds) == "UNKNOWN"


def test_map_severity_rules():
    assert map_severity("CRITICAL", 0.1) == "CRITICAL"
    assert map_severity("HIGH", 0.5) == "HIGH"
    assert map_severity("HIGH", 0.9) == "MEDIUM"
    assert map_severity("MEDIUM", 0.5) == "MEDIUM"
    assert map_severity("MEDIUM", 0.95) == "LOW"
    assert map_severity("LOW", 0.0) == "LOW"
    assert map_severity("UNKNOWN", 0.5) == "MEDIUM"
