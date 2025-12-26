#!/usr/bin/env bash
set -euo pipefail
cd /workspace/git/S2S-chain-MM/app
source .venv312/bin/activate
# Hard-disable CUDA for now (avoids cuDNN mismatches)
export CUDA_VISIBLE_DEVICES="-1"
export ORT_DISABLE_CUDA=1
export CT2_FORCE_CPU=1
exec python main.py
