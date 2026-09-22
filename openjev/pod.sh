#!/bin/bash
# Open-Jev on one rented GPU pod (run 2026-09-22): install Open-Jev, download the pinned adapter, start NSERV server
# copies on the card (one request at a time each), and run one run.py shard per copy through this repo's own Jev
# request builders (rerankers/jev.py, pointed at the local server by JEV_URL).
#
# env: SIZE=2B|9B  NSERV=<server copies>  RATE=<pod USD per hour>  SHARDS="<one shard index per copy>"  NSHARDS=<n>
#      RUNFLAGS="" | "--slice 1/4" | "--slice 3/4 --reverse" | "--reverse --skip-file /workspace/overrides/skip.txt"
# needs /workspace/overrides/docs.tgz: tar of candidates/*.docs.jsonl (the passage texts are not in the repo; build them
# with candidates/build.py or upload them). Optional /workspace/overrides/{run.py,jev.py} override the repo's copies.
set -x
cd /workspace
export PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_BREAK_SYSTEM_PACKAGES=1 TOKENIZERS_PARALLELISM=false
[ -d Open-Jev ] || git clone --depth 1 https://github.com/Zefan-Cai/Open-Jev.git
cd Open-Jev
python -c "import transformers, peft" 2>/dev/null || pip install -q -e '.[train]' requests python-dotenv tqdm 2>&1 | tail -3
if [ "$SIZE" = "9B" ]; then REV=47e966881e489511c0c7f5633a9e1960a676a551; else REV=0c7aa498b1627be8da4acf34c863ff0ee0a92785; fi
[ -d models/Open-Jev-$SIZE/package ] || python -c "from huggingface_hub import snapshot_download; print(snapshot_download('ZefanCai/Open-Jev-$SIZE', revision='$REV', local_dir='models/Open-Jev-$SIZE'))"
cd /workspace
[ -d bench ] || { git clone --depth 1 --filter=blob:none --sparse https://github.com/anessbelbati/jev-rerank-bench.git bench && cd bench && git sparse-checkout set candidates rerankers openjev && cd ..; }
[ -f /workspace/overrides/run.py ] && cp /workspace/overrides/run.py bench/run.py; [ -f /workspace/overrides/jev.py ] && cp /workspace/overrides/jev.py bench/rerankers/jev.py
[ -f bench/candidates/scifact.docs.jsonl ] || (cd bench && tar xzf /workspace/overrides/docs.tgz)
mkdir -p bench/results bench/cache
cd /workspace/Open-Jev
CKPT=models/Open-Jev-$SIZE/package/checkpoint
for j in $(seq 0 $((NSERV-1))); do
  PORT=$((8791+j))
  curl -sf http://127.0.0.1:$PORT/health > /dev/null && continue
  nohup python -m jev.server --checkpoint $CKPT --device cuda:0 --max-length 4096 --batch-size 32 --port $PORT > /workspace/server_$j.log 2>&1 &
  until curl -sf http://127.0.0.1:$PORT/health; do sleep 5; done; echo " server $j ready"
done
nvidia-smi --query-gpu=memory.used --format=csv
size=$(echo $SIZE | tr A-Z a-z)
cd /workspace/bench
PER=$(python -c "print($RATE/$NSERV)")
j=-1
for K in $SHARDS; do
  j=$((j+1))
  JEV_URL=http://127.0.0.1:$((8791+j))/v1/systemone JEV_MODEL=open-jev JEV_GPU_RATE=$PER nohup bash -c "python run.py --model jev-noul-pair --cache-as open-jev-$size-noul-pair --dataset all --workers 2 --shard $K/$NSHARDS $RUNFLAGS; python run.py --model jev-noul-pair --cache-as open-jev-$size-noul-pair --dataset nevir --workers 2 --shard $K/$NSHARDS $RUNFLAGS; echo RUN_DONE" > /workspace/run_$j.log 2>&1 &
done
wait
echo ALL_DONE
