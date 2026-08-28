# Architecture (initial)

This document will evolve. For Phase 1 we create a minimal modular structure:

- backend/: FastAPI backend and services
- generator/: deterministic synthetic data generator
- data/: generated and processed datasets
- docs/: documentation and audit notes

Core concept:

Deterministic finance core (DuckDB, Python) -> Evidence graph -> AI investigator (optional)
