#!/usr/bin/env bash
set -euo pipefail

exec xvfb-run -a env PYNPUT_BACKEND=xorg .venv/bin/python -m unittest discover -s tests
