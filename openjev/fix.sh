#!/bin/bash
# The fix pass: rows whose passage exceeds the 4,096-token window of the run servers (10 lists per size, BRIGHT robotics
# and StackOverflow) are redone on one server with Open-Jev's full 16,384-token window. /workspace/overrides/skip.txt
# lists every row already finished (dataset|variant|qid), so only the failed rows run.  env: SIZE RATE FIXFLAGS
pkill -f "bash -c python run.py"; pkill -f "python run.py --model"; pkill -f "jev.server"; sleep 4
cd /workspace/Open-Jev; CKPT=models/Open-Jev-$SIZE/package/checkpoint
nohup python -m jev.server --checkpoint $CKPT --device cuda:0 --max-length 16384 --batch-size 32 --port 8791 > /workspace/server_fix.log 2>&1 &
until curl -sf http://127.0.0.1:8791/health; do sleep 5; done; echo " fix server ready"
cp /workspace/overrides/run.py /workspace/bench/run.py; cd /workspace/bench; size=$(echo $SIZE | tr A-Z a-z)
mkdir -p cache_prev && mv cache/open-jev-$size-noul-pair cache_prev/ 2>/dev/null; mkdir -p cache/open-jev-$size-noul-pair
JEV_URL=http://127.0.0.1:8791/v1/systemone JEV_MODEL=open-jev JEV_GPU_RATE=$RATE python run.py --model jev-noul-pair --cache-as open-jev-$size-noul-pair --dataset all --workers 2 --skip-file /workspace/overrides/skip.txt $FIXFLAGS 2>&1 | tr "\r" "\n" | grep -E "100%|Error|Traceback" | cut -c1-120
JEV_URL=http://127.0.0.1:8791/v1/systemone JEV_MODEL=open-jev JEV_GPU_RATE=$RATE python run.py --model jev-noul-pair --cache-as open-jev-$size-noul-pair --dataset nevir --workers 2 --skip-file /workspace/overrides/skip.txt $FIXFLAGS 2>&1 | tr "\r" "\n" | grep -E "100%|Error|Traceback" | cut -c1-120
echo "fix rows: $(cat cache/open-jev-$size-noul-pair/*.jsonl | wc -l)  failed: $(cat cache/open-jev-$size-noul-pair/*.jsonl | grep -c '"ok": false')"
echo FIX_DONE
