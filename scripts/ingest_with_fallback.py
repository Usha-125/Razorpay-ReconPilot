"""Wrapper: try to install backend requirements and run real ingestion.
If installation or ingestion fails, run a mock ingestion fallback.
"""
import subprocess
import sys
import os


def run_command(cmd, cwd=None):
    try:
        print(f"Running: {' '.join(cmd)}")
        res = subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(res.stdout)
        return True, res.stdout
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        return False, e.stderr


def main():
    data_dir = "data/generated"
    # Step 1: try to install requirements
    ok, out = run_command([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"]) 
    if not ok:
        print("Dependency installation failed; running mock ingestion.")
        return run_command([sys.executable, "scripts/mock_ingest.py", "--data-dir", data_dir])

    # Step 2: run real ingestion
    ok, out = run_command([sys.executable, "scripts/ingest_batch.py", "--data-dir", data_dir])
    if not ok:
        print("Real ingestion failed; running mock ingestion.")
        return run_command([sys.executable, "scripts/mock_ingest.py", "--data-dir", data_dir])

    return True, out


if __name__ == "__main__":
    main()
