from fastapi import FastAPI
from .health import get_health

app = FastAPI(title="Razorpay ReconPilot - Backend")


@app.get("/health")
def health():
    return get_health()


@app.get("/ready")
def ready():
    return {"ready": True}
