#!/usr/bin/env python3
"""Wrapper script to run holdem CLI with proper PYTHONPATH."""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run holdem CLI with proper environment setup."""
    script_dir = Path(__file__).parent
    src_dir = script_dir / "src"
    venv_python = script_dir / "venv" / "bin" / "python3"
    
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_dir)
    
    # Build command
    cmd = [str(venv_python), "-m", "holdem_cli.main"] + sys.argv[1:]
    
    # Run command
    try:
        result = subprocess.run(cmd, env=env)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print(f"Error running holdem: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
