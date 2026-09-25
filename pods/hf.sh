#!/bin/bash
# One rented GPU pod for the Hugging Face runner (inject/hf_runner.py): open rerankers and small open models, one
# process on the card, one model after another, over the 14 datasets and NevIR.
#
# Upload first: /workspace/bench.tgz = this repo's code, models.yaml and candidates/*.jsonl (the passage files are not
# in git; build them with candidates/build.py or pack them from a checkout that has them).
#   env: MODELS="qwen3-reranker-4b bge-reranker-v2-m3 mxbai-rerank-base-v2"  RATE=<card USD per hour>  PHASE=smoke|full
#        GPU_NOTE="RunPod community cloud, charged at the secure-cloud price" (saved with each row, after the card name)
# smoke: each model reproduces its card's printed example, then answers the first 20 SciFact questions.
# full:  every question; the smoke rows are kept and skipped. Rows land in /workspace/bench/cache/<model>/.
set -e
GPU_NOTE=${GPU_NOTE:-RunPod secure cloud}
cd /workspace
export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_BREAK_SYSTEM_PACKAGES=1 TOKENIZERS_PARALLELISM=false
[ -d bench ] || { mkdir bench && tar xzf bench.tgz -C bench --no-same-owner; }
python -c "import transformers, accelerate, fla" 2>/dev/null || \
  pip install -q "transformers>=4.57" accelerate flash-linear-attention requests python-dotenv tqdm pyyaml
# mxbai runs its card's Sentence Transformers recipe with the versions that reproduce the card's printed example
# (Sentence Transformers 5.4.0 on transformers 4.57.6), in an environment of its own on the pod's PyTorch; the Qwen3.5
# models need transformers 5.
MXBAI=mxbai-rerank-base-v2
if [[ " $MODELS " == *" $MXBAI "* ]] && [ ! -x venv-st/bin/python ]; then
  command -v uv > /dev/null || pip install -q uv
  uv venv -q --system-site-packages venv-st && uv pip install -q --python venv-st/bin/python "transformers==4.57.6" scikit-learn \
    && uv pip install -q --python venv-st/bin/python --no-deps "sentence-transformers==5.4.0"
fi
cd bench
DATASETS=$(python -c "from common import DATASETS; print(' '.join(DATASETS))")
run() {   # run <python> <model>...
  local py=$1; shift
  [ $# -gt 0 ] || return 0
  if [ "$PHASE" = smoke ]; then
    $py inject/hf_runner.py --root /workspace/bench --rate "$RATE" --gpu "$GPU_NOTE" --card-check \
      --models "$@" --dataset scifact --variants present --limit 20
  else
    $py inject/hf_runner.py --root /workspace/bench --rate "$RATE" --gpu "$GPU_NOTE" --card-check \
      --models "$@" --dataset $DATASETS nevir --variants present absent
  fi
}
run python $(printf '%s\n' $MODELS | grep -vx "$MXBAI" || true)
run /workspace/venv-st/bin/python $(printf '%s\n' $MODELS | grep -x "$MXBAI" || true)
echo PHASE_DONE
