#!/bin/bash
echo "=== Testing Orchestrator Endpoints ==="
echo ""
echo "1. GET /status (no token - expect 401):"
curl -s -i http://127.0.0.1:8181/status | head -n 12
echo ""
echo "2. GET /status (with valid token):"
curl -s -i -H "X-Orchestrator-Token: ChangeMe-Orchestrator-Token" http://127.0.0.1:8181/status | head -n 12
echo ""
echo "3. POST /cleanup (no signature - expect 401):"
curl -s -i -X POST -H "X-Orchestrator-Token: ChangeMe-Orchestrator-Token" http://127.0.0.1:8181/cleanup | head -n 15
echo ""
echo "4. POST /cleanup (with valid signature):"
ts=$(date +%s)
sig=$(printf "%s." "$ts" | openssl dgst -sha256 -hmac "ChangeMe-Orchestrator-Signing-Secret" -binary | xxd -p -c 256)
curl -s -i -X POST -H "X-Orchestrator-Token: ChangeMe-Orchestrator-Token" -H "X-Signature-Timestamp: $ts" -H "X-Signature: $sig" http://127.0.0.1:8181/cleanup | head -n 15
echo ""
echo "5. Check audit logs:"
sudo tail -n 5 /var/log/ctf/orchestrator-audit.log
