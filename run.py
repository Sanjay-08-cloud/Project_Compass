#!/usr/bin/env python3
"""
Single-Command Dev Launcher for Project Compass
1. Verifies/starts internal Ollama instance (bound strictly to 127.0.0.1:11434).
2. Verifies frontend static export (builds via Next.js if missing or out-of-date).
3. Launches unified Django server on port 8000 serving all pages, static assets, and APIs.
"""

import os
import sys
import time
import shutil
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_BUILD_DIR = BASE_DIR / "frontend_build"
VENV_PYTHON = BASE_DIR / ".venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)


def check_ollama() -> bool:
    """Check if internal Ollama service is reachable on 127.0.0.1:11434."""
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_ollama_if_needed():
    """Verify or launch Ollama bound to 127.0.0.1:11434."""
    print("[1/3] Checking internal Ollama service (127.0.0.1:11434)...")
    if check_ollama():
        print("  -> Ollama is already active on 127.0.0.1:11434 (Internal-only).")
        return

    print("  -> Ollama not responding. Attempting to start 'ollama serve'...")
    try:
        # Launch ollama serve in background detached process
        flags = 0
        if sys.platform == "win32":
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        for _ in range(10):
            time.sleep(1)
            if check_ollama():
                print("  -> Ollama service successfully started on 127.0.0.1:11434.")
                return
    except Exception as e:
        print(f"  [Warning] Could not auto-start Ollama: {e}")

    if not check_ollama():
        print("  [Note] Proceeding. Ensure Ollama is running if queries require local LLM generation.")


def build_frontend_if_needed():
    """Ensure Next.js static export exists in frontend_build/."""
    print("[2/3] Checking frontend static export...")
    index_html = FRONTEND_BUILD_DIR / "index.html"
    build_needed = not index_html.exists() or "--rebuild" in sys.argv

    if build_needed:
        print("  -> Building Next.js static export (out/)...")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        ret = subprocess.call([npm_cmd, "run", "build"], cwd=str(FRONTEND_DIR))
        if ret != 0:
            print("  [Error] Failed to build Next.js frontend export.")
            sys.exit(1)

        out_dir = FRONTEND_DIR / "out"
        if not out_dir.exists():
            print("  [Error] Expected 'out/' directory not found after build.")
            sys.exit(1)

        print("  -> Syncing static export to frontend_build/...")
        if FRONTEND_BUILD_DIR.exists():
            shutil.rmtree(FRONTEND_BUILD_DIR, ignore_errors=True)
        shutil.copytree(out_dir, FRONTEND_BUILD_DIR)
        print("  -> Frontend static export prepared successfully.")
    else:
        print("  -> Frontend static export is present in frontend_build/.")


def run_django():
    """Launch Django unified server on 127.0.0.1:8000."""
    print("[3/3] Starting Project Compass consolidated server on http://127.0.0.1:8000 ...")
    print("      (Serving all Next.js pages, static assets, and REST APIs on a single port)")
    cmd = [str(VENV_PYTHON), "manage.py", "runserver", "127.0.0.1:8000"]
    try:
        subprocess.call(cmd, cwd=str(BASE_DIR))
    except KeyboardInterrupt:
        print("\nStopping Project Compass server...")


if __name__ == "__main__":
    start_ollama_if_needed()
    build_frontend_if_needed()
    run_django()
