"""Convenience runner to start Backend and Frontend in a single command."""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def main():
    print("==========================================================")
    print("   Starting YOLO + MCP Vision Platform (Backend + UI)     ")
    print("==========================================================")

    # Set PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)

    # 1. Start FastAPI Backend (Uvicorn)
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        "backend",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
    ]

    print("[*] Launching Backend Server on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(ROOT_DIR), env=env)

    # 2. Check if frontend dev server should run or if static dist is served
    print("[*] Backend automatically serves the built UI at http://127.0.0.1:8000/")
    print("[*] API Documentation available at http://127.0.0.1:8000/docs")

    time.sleep(2)

    # Automatically open browser
    try:
        webbrowser.open("http://127.0.0.1:8000/")
    except Exception:
        pass

    print("\n[+] System is RUNNING! Press Ctrl+C in this terminal to stop.")

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n[*] Stopping YOLO + MCP Platform...")
        backend_proc.terminate()
        backend_proc.wait()
        print("[+] Stopped.")


if __name__ == "__main__":
    main()
