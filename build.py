#!/usr/bin/env python3
"""Build Password Vault Pro desktop exe (Windows) or binary (other OS)."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv-build"
SPEC = ROOT / "PasswordVaultPro.spec"
IS_WIN = os.name == "nt"
VENV_PY = VENV / ("Scripts/python.exe" if IS_WIN else "bin/python")


def run(args):
    print("+", " ".join(str(a) for a in args), flush=True)
    result = subprocess.run(args, cwd=ROOT)
    if result.returncode != 0:
        print(f"[ERROR] Command failed with exit code {result.returncode}", flush=True)
        sys.exit(result.returncode)


def main():
    os.chdir(ROOT)

    if not SPEC.is_file():
        print("[ERROR] PasswordVaultPro.spec not found.", flush=True)
        sys.exit(1)

    print("============================================", flush=True)
    print(" Password Vault Pro - desktop exe build", flush=True)
    print("============================================", flush=True)
    print(flush=True)

    print("[1/4] Virtual environment...", flush=True)
    if not VENV_PY.is_file():
        run([sys.executable, "-m", "venv", str(VENV)])
    else:
        print(f"Using {VENV_PY}", flush=True)

    print("[2/4] Installing dependencies...", flush=True)
    run([str(VENV_PY), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(VENV_PY), "-m", "pip", "install", "-r", "requirements.txt", "pyinstaller"])

    print("[3/4] Running PyInstaller...", flush=True)
    for name in ("build", "dist"):
        path = ROOT / name
        if path.exists():
            shutil.rmtree(path)
    run([str(VENV_PY), "-m", "PyInstaller", "--noconfirm", "--clean", str(SPEC)])

    exe = ROOT / "dist" / "PasswordVaultPro.exe"
    other = ROOT / "dist" / "PasswordVaultPro"
    print("[4/4] Done.", flush=True)
    print(flush=True)

    if exe.is_file():
        print(f"Output: {exe}", flush=True)
        print("This is a desktop window, not a browser tab.", flush=True)
        print("database/ and backups/ are created next to the exe on first run.", flush=True)
        if IS_WIN:
            subprocess.Popen(["explorer", str(ROOT / "dist")])
        return

    if other.is_file():
        print(f"Output: {other}", flush=True)
        print("Windows .exe must be built on Windows (run build.bat there).", flush=True)
        return

    print("[ERROR] Build finished but the output file was not found.", flush=True)
    sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
