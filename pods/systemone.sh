#!/bin/bash
# One rented GPU pod for a System One rebuild listed in models.yaml: install its server at the pinned version, start
# it, and run bench.py against it through rerankers/systemone.py.
#
# Upload first: /workspace/bench.tgz = this repo's code, models.yaml and candidates/*.jsonl (see pods/hf.sh).
#   env: NAME=reflex-4b|winnow-12b|decider-2b  PHASE=smoke|full
#        SYSTEMONE_GPU_RATE=<the card's USD per hour over the requests in flight>, when the card is not the one in models.yaml
# smoke: the first 20 SciFact questions and the projected time and cost of the full run.
# full:  the 14 datasets and NevIR; rows land in /workspace/bench/cache/<name>-noul-pair/, packed at the end.
# reflex installs PyTorch for CUDA 13: rent a host whose driver takes CUDA 13.
set -e
cd /workspace
export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_BREAK_SYSTEM_PACKAGES=1 TOKENIZERS_PARALLELISM=false
[ -d bench ] || { mkdir bench && tar xzf bench.tgz -C bench --no-same-owner; }
python -c "import yaml, requests, dotenv, tqdm, matplotlib" 2>/dev/null || pip install -q pyyaml requests python-dotenv tqdm matplotlib
ready() { curl -sf "$URL" 2>/dev/null | grep -q "$OK"; }
case "$NAME" in
  reflex-4b)                                     # /health answers once the model is loaded
    URL=http://127.0.0.1:8008/health OK=model
    [ -d reflex ] || { git clone -q https://github.com/kshetrajna12/reflex && git -C reflex checkout -q 19586a1374dca138eddf5d7b8889cae8dfa505f6; }
    command -v uv > /dev/null || pip install -q uv
    (cd reflex && uv sync -q)
    ready || (cd reflex && nohup uv run reflex-serve --stable --port 8008 > /workspace/server.log 2>&1 &) ;;
  winnow-12b)                                    # llama-server's /health is 503 while the model loads
    URL=http://127.0.0.1:8091/health OK=ok
    command -v cmake > /dev/null || { apt-get update -qq && apt-get install -y -qq build-essential cmake libssl-dev > /dev/null; }
    command -v nvcc > /dev/null || export PATH=/usr/local/cuda/bin:$PATH     # the CUDA images keep nvcc outside PATH
    [ -d winnow-inference ] || { git clone -q https://github.com/EldanRing/winnow-inference && git -C winnow-inference checkout -q 77d14580c6732ca2f3745750c1dc1fd446d8bcee; }
    (cd winnow-inference && { [ -x .build/bin/winnow-server ] || python3 scripts/setup.py --text-only; })
    ready || (cd winnow-inference && nohup python3 scripts/serve.py --text-only > /workspace/server.log 2>&1 &) ;;
  decider-2b)                                    # /health says "ok": true once the engine is up
    URL=http://127.0.0.1:8000/health OK='"ok":true'
    python -c "import fla, fastapi, uvicorn, transformers; assert int(transformers.__version__.split('.')[0]) >= 5" 2>/dev/null || \
      pip install -q "transformers>=5" flash-linear-attention fastapi uvicorn
    D=$(python -c "from huggingface_hub import snapshot_download; print(snapshot_download('Mapika/decider-2b', revision='533964dae8be954c5b5e19fa4948e48408094c1e'))")
    ready || (cd "$D" && DECIDER_MODEL="$D" nohup uvicorn decider.serve:app --host 127.0.0.1 --port 8000 > /workspace/server.log 2>&1 &) ;;
  *) echo "NAME must be reflex-4b, winnow-12b or decider-2b"; exit 1 ;;
esac
for i in $(seq 1 90); do ready && break; sleep 10; done
ready || { echo "server not ready after 15 minutes"; tail -30 /workspace/server.log; exit 1; }
cd /workspace/bench
if [ "$PHASE" = smoke ]; then python bench.py "$NAME" --smoke --all-datasets; else python bench.py "$NAME" --all-datasets; fi
echo PHASE_DONE
