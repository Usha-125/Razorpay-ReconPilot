from datetime import datetime


def get_health():
    """Health handler separated from FastAPI to allow import without dependencies.

    Returns a simple health dictionary that can be used by tests and scripts.
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
