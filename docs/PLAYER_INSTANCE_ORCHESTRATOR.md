# Player Instance Orchestrator API

## Overview

The orchestrator is a Python/Flask API service that manages isolated Docker challenge instances for each team. Every challenge instance runs in its own Docker Compose project with a fixed lifetime (TTL), and are automatically cleaned up when expired.

**Core responsibilities:**
- Start/stop Docker Compose challenge instances per team
- Track instance lifecycle with TTL-based automatic cleanup
- Enforce per-team quotas (max concurrent instances)
- Authenticate and authorize API requests
- Audit all operations (event logging)
- Expose webhook endpoint for CTFd integration

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Client / CTFd                                               │
│ (requests to start/stop instances)                          │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼ (HTTP on 8181 via nginx)
┌─────────────────────────────────────────────────────────────┐
│ nginx Reverse Proxy (0.0.0.0:8181)                          │
│ - Forwards X-Forwarded-For headers                          │
│ - Proxies to localhost:18181                                │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼ (Local socket 127.0.0.1:18181)
┌─────────────────────────────────────────────────────────────┐
│ Orchestrator API (player-instance-api.py)                  │
│ - Authentication (token validation)                         │
│ - HMAC signature verification                              │
│ - Rate limiting (per-client & per-team)                    │
│ - Instance quota enforcement                                │
│ - Audit logging (JSON)                                      │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼ (subprocess calls)
┌─────────────────────────────────────────────────────────────┐
│ Manager Script (player-instance-manager.sh)                 │
│ - Compose CLI wrapper                                       │
│ - Docker Compose project management                         │
│ - Lease file tracking                                       │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ Docker Compose Instances                                    │
│ (/opt/ctf/instances/inst_<challenge>_<team_id>/)           │
│ - Each team gets isolated containers                        │
│ - Challenge-specific port mapping (6100-6999)              │
│ - Fixed TTL (default: 60 minutes)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### GET Endpoints (Token Auth Only)

#### `GET /health`
Health check endpoint.

**Headers:**
```
GET /health HTTP/1.1
```

**Response (200 OK):**
```json
{"status": "ok"}
```

---

#### `GET /status`
Get status of all orchestrator instances.

**Headers:**
```
GET /status HTTP/1.1
X-Orchestrator-Token: ChangeMe-Orchestrator-Token
```

**Response (200 OK):**
```json
{
  "ok": true,
  "stdout": "<docker ps output>",
  "stderr": ""
}
```

**Response (401 Unauthorized):**
```json
{"ok": false, "error": "unauthorized"}
```

---

### POST Endpoints (Token + HMAC Signature Required)

#### `POST /start`
Start a new challenge instance for a team.

**Headers:**
```
POST /start HTTP/1.1
X-Orchestrator-Token: ChangeMe-Orchestrator-Token
X-Signature-Timestamp: 1775258542
X-Signature: <HMAC-SHA256>
Content-Type: application/json
```

**Body:**
```json
{
  "challenge": "web-01-test",
  "team_id": "1",
  "ttl_min": 60
}
```

**Parameters:**
- `challenge` (string, required): Challenge name (folder in `/vagrant/challenges/`)
- `team_id` (string, required): Team identifier for quota tracking
- `ttl_min` (integer, optional): Lifetime in minutes (default: 60)

**Response (200 OK):**
```json
{
  "ok": true,
  "challenge": "web-01-test",
  "team": "1",
  "port": 6101,
  "ttl_min": 60,
  "url": "http://192.168.56.10:6101"
}
```

**Response (409 Conflict - Quota Exceeded):**
```json
{
  "ok": false,
  "error": "team_quota_exceeded",
  "detail": "Team 1 already has 3 active instances (max 3)"
}
```

**Response (401 Unauthorized):**
```json
{"ok": false, "error": "missing_signature_headers"}
```

---

#### `POST /stop`
Stop a running challenge instance.

**Headers:**
```
POST /stop HTTP/1.1
X-Orchestrator-Token: ChangeMe-Orchestrator-Token
X-Signature-Timestamp: 1775258542
X-Signature: <HMAC-SHA256>
Content-Type: application/json
```

**Body:**
```json
{
  "challenge": "web-01-test",
  "team_id": "1"
}
```

**Response (200 OK):**
```json
{"ok": true}
```

---

#### `POST /cleanup`
Cleanup expired instances (TTL exceeded).

**Headers:**
```
POST /cleanup HTTP/1.1
X-Orchestrator-Token: ChangeMe-Orchestrator-Token
X-Signature-Timestamp: 1775258542
X-Signature: <HMAC-SHA256>
Content-Type: application/json
```

**Body:** (empty or {})
```json
{}
```

**Response (200 OK):**
```json
{
  "ok": true,
  "cleaned": 3,
  "stdout": "<cleanup output>"
}
```

---

#### `POST /ctfd/event`
Webhook endpoint for CTFd integration. Maps CTFd events to orchestrator actions.

**Headers:**
```
POST /ctfd/event HTTP/1.1
X-CTFd-Webhook-Token: ChangeMe-CTFd-Webhook-Token
X-Signature-Timestamp: 1775258542
X-Signature: <HMAC-SHA256>
Content-Type: application/json
```

**Body:**
```json
{
  "event": "challenge.start",
  "team_id": "1",
  "challenge_id": "web-01-test"
}
```

**Event Mapping:**
| CTFd Event | Action |
|-----------|--------|
| `challenge.start`, `instance.start`, `start` | Start instance |
| `challenge.stop`, `instance.stop`, `stop` | Stop instance |
| `cleanup`, `instance.cleanup` | Cleanup expired |

**Response (200 OK):**
```json
{"ok": true, "action": "start", "result": {...}}
```

---

## Authentication & Security

### Token Authentication

Every request requires the `X-Orchestrator-Token` header:

```bash
curl -H "X-Orchestrator-Token: ChangeMe-Orchestrator-Token" http://127.0.0.1:8181/status
```

For GET endpoints, token is the only requirement. For POST requests, token + HMAC signature are required.

**Development default:** `ChangeMe-Orchestrator-Token`  
**Environment variable:** `ORCHESTRATOR_TOKEN`

### HMAC-SHA256 Request Signing

POST requests (start, stop, cleanup) require HMAC-SHA256 signatures to prevent tampering.

#### Signature Format

**Message to sign:**
```
<timestamp>.<raw_request_body>
```

**Example:**
```
Body: {"challenge": "web-01-test", "team_id": "1"}
Timestamp: 1775258542
Message: 1775258542.{"challenge": "web-01-test", "team_id": "1"}
```

**Headers:**
```
X-Signature-Timestamp: 1775258542
X-Signature: a1b2c3d4e5f6... (hex-encoded HMAC-SHA256)
```

**Timestamp Validation:**
- Must be Unix timestamp (numeric only)
- Must be within 300 seconds of server time
- Prevents replay attacks

#### Signature Generation (Example)

**bash/curl:**
```bash
#!/bin/bash

SIGNING_SECRET="ChangeMe-Orchestrator-Signing-Secret"
ENDPOINT="http://127.0.0.1:8181/start"
TOKEN="ChangeMe-Orchestrator-Token"
BODY='{"challenge": "web-01-test", "team_id": "1"}'

# Generate timestamp
ts=$(date +%s)

# Generate signature: HMAC-SHA256(timestamp + "." + body)
sig=$(printf "%s.%s" "$ts" "$body" | openssl dgst -sha256 -hmac "$SIGNING_SECRET" -binary | xxd -p -c 256)

# Make request
curl -X POST "$ENDPOINT" \
  -H "X-Orchestrator-Token: $TOKEN" \
  -H "X-Signature-Timestamp: $ts" \
  -H "X-Signature: $sig" \
  -H "Content-Type: application/json" \
  -d "$BODY"
```

**Python:**
```python
import hmac
import hashlib
import time
import requests
import json

signing_secret = "ChangeMe-Orchestrator-Signing-Secret"
token = "ChangeMe-Orchestrator-Token"
body = {"challenge": "web-01-test", "team_id": "1"}
timestamp = int(time.time())

# Create signature
message = f"{timestamp}.{json.dumps(body)}"
signature = hmac.new(
    signing_secret.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()

# Make request
headers = {
    "X-Orchestrator-Token": token,
    "X-Signature-Timestamp": str(timestamp),
    "X-Signature": signature,
    "Content-Type": "application/json"
}

response = requests.post(
    "http://127.0.0.1:8181/start",
    headers=headers,
    json=body
)

print(response.json())
```

---

## Rate Limiting

The orchestrator enforces two levels of rate limiting:

### Per-Client Rate Limiting
- **Limit:** 60 requests per minute per client IP
- **Default:** Configurable via `ORCHESTRATOR_RATE_LIMIT_PER_MIN`
- **Tracking:** Uses X-Forwarded-For header (via nginx proxy) or direct client IP
- **Behavior:** Returns 429 too_many_requests when exceeded

### Per-Team Rate Limiting
- **Limit:** 30 requests per minute per team_id
- **Default:** Configurable via `ORCHESTRATOR_TEAM_RATE_LIMIT_PER_MIN`
- **Tracking:** Extracted from request body (team_id field)
- **Behavior:** Returns 429 too_many_requests when exceeded

### Checking Rate Limits

Check if you're being rate limited:

```bash
curl -v -H "X-Orchestrator-Token: $(YOURE_TOKEN)" http://127.0.0.1:8181/status 2>&1 | grep -i "x-ratelimit\|429"
```

Response headers (if rate limit header implemented):
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1775258602
```

---

## Team Instance Quotas

Each team can have a maximum number of concurrent instances:

- **Default:** 3 instances per team
- **Configurable:** `ORCHESTRATOR_TEAM_MAX_ACTIVE`
- **Enforcement:** Checked before `/start` action
- **Error:** 409 Conflict if quota exceeded

### Example Quota Behavior

```bash
# Team 1 starts instance 1
curl -X POST http://127.0.0.1:8181/start \
  -H "X-Orchestrator-Token: TOKEN" \
  -H "X-Signature-Timestamp: $ts" \
  -H "X-Signature: $sig" \
  -d '{"challenge": "web-01", "team_id": "1"}'
# Response: 200 OK, port 6101

# Team 1 starts instance 2
# Response: 200 OK, port 6102

# Team 1 starts instance 3
# Response: 200 OK, port 6103

# Team 1 tries to start instance 4
# Response: 409 Conflict - quota exceeded (max 3 active)
```

To start another instance, team must stop one first:

```bash
curl -X POST http://127.0.0.1:8181/stop \
  -H "X-Orchestrator-Token: TOKEN" \
  -H "X-Signature-Timestamp: $ts" \
  -H "X-Signature: $sig" \
  -d '{"challenge": "web-01", "team_id": "1"}'
```

---

## Audit Logging

All orchestrator events are logged as JSON lines to `/var/log/ctf/orchestrator-audit.log`:

### Log Format

Each line is a complete JSON object:

```json
{
  "ts": 1775258542,
  "event": "start",
  "http_status": 200,
  "path": "/start",
  "client": "192.168.1.100",
  "team": "1",
  "challenge": "web-01-test",
  "detail": ""
}
```

### Fields

- `ts` - Unix timestamp
- `event` - Action type (start, stop, cleanup, status, unauthorized, signature_rejected, ctfd_event)
- `http_status` - HTTP response code (200, 401, 409, 429, etc)
- `path` - API endpoint path
- `client` - Client IP address (from X-Forwarded-For or direct)
- `team` - Team ID from request body
- `challenge` - Challenge name from request body
- `detail` - Additional context (error message, reason)

### Sample Log

```bash
$ sudo tail /var/log/ctf/orchestrator-audit.log

{"ts": 1775258542, "event": "status", "http_status": 200, "path": "/status", "client": "127.0.0.1", "team": "", "challenge": "", "detail": ""}
{"ts": 1775258543, "event": "start", "http_status": 200, "path": "/start", "client": "127.0.0.1", "team": "1", "challenge": "web-01-test", "detail": ""}
{"ts": 1775258545, "event": "cleanup", "http_status": 200, "path": "/cleanup", "client": "127.0.0.1", "team": "", "challenge": "", "detail": ""}
{"ts": 1775258546, "event": "unauthorized", "http_status": 401, "path": "/start", "client": "127.0.0.1", "team": "", "challenge": "", "detail": "missing_or_invalid_token"}
{"ts": 1775258547, "event": "signature_rejected", "http_status": 401, "path": "/stop", "client": "127.0.0.1", "team": "1", "challenge": "web-01", "detail": "timestamp_too_old"}
```

### Monitoring Audit Logs

```bash
# Real-time tail
vagrant ssh -- sudo tail -f /var/log/ctf/orchestrator-audit.log

# Count errors in last hour
vagrant ssh -- sudo grep "http_status.*[45]" /var/log/ctf/orchestrator-audit.log | tail -n 3600 | wc -l

# Find all failed signature attempts
vagrant ssh -- sudo grep "signature_rejected" /var/log/ctf/orchestrator-audit.log

# Count events by type
vagrant ssh -- sudo grep -o '"event":"[^"]*"' /var/log/ctf/orchestrator-audit.log | sort | uniq -c
```

---

## Configuration

All orchestrator settings are environment variables in `/opt/ctf/orchestrator.env`:

```bash
# Authentication
ORCHESTRATOR_TOKEN=ChangeMe-Orchestrator-Token
ORCHESTRATOR_SIGNING_SECRET=ChangeMe-Orchestrator-Signing-Secret
ORCHESTRATOR_CTFD_WEBHOOK_TOKEN=ChangeMe-CTFd-Webhook-Token

# Rate limiting (requests per minute)
ORCHESTRATOR_RATE_LIMIT_PER_MIN=60
ORCHESTRATOR_TEAM_RATE_LIMIT_PER_MIN=30

# Quotas
ORCHESTRATOR_TEAM_MAX_ACTIVE=3

# Logging
ORCHESTRATOR_AUDIT_LOG=/var/log/ctf/orchestrator-audit.log

# Security
ORCHESTRATOR_SIGNATURE_TTL_SEC=300

# Binding (changed in v2.0)
ORCHESTRATOR_API_HOST=127.0.0.1      # Was 0.0.0.0, now localhost only
ORCHESTRATOR_API_PORT=18181          # Internal, exposed via nginx
```

### Override via Ansible Vault

In production, override any value using Ansible Vault:

1. Create `ansible/vars/vault.yml` (encrypted)
2. Define `*_vault` variables (e.g., `orchestrator_signing_secret_vault`)
3. Playbook automatically uses vault values as `*_effective`

See [docs/VAULT_SETUP.md](VAULT_SETUP.md) for details.

---

## Runtime Model

### Directory Structure

```
/opt/ctf/
├── orchestrator.env                                      # Configuration
├── scripts/
│   ├── player-instance-api.py                           # Flask API
│   └── player-instance-manager.sh                        # Compose manager
├── instances/
│   ├── inst_web-01-test_team-1/                        # Per-team instance
│   │   ├── docker-compose.yml                           # Generated
│   │   └── ...
│   └── inst_web-01-test_team-2/
├── leases/
│   ├── inst_web-01-test_team-1.env                     # TTL tracking
│   └── inst_web-01-test_team-2.env
└── logs/
    └── orchestrator-audit.log (symlink to /var/log/ctf/)
```

### Lease File Format

Each instance has a lease file tracking expiration:

```bash
$ cat /opt/ctf/leases/inst_web-01-test_team-1.env

CHALLENGE=web-01-test
TEAM_ID=team-1
PROJECT_NAME=inst_web-01-test_team-1
PORT=6101
CONTAINER_ID=abc123...
EXPIRE_EPOCH=1775262142  # UnixTimestamp when TTL expires
TTL_MIN=60
```

### Instance Cleanup

- **Automatic:** systemd timer (`player-instance-cleanup.timer`) runs cleanup every 5 minutes
- **Manual:** `POST /cleanup` endpoint triggers immediate cleanup
- **Logic:** Removes instances where `EXPIRE_EPOCH < current_time`

---

## Examples

### Start Instance (curl)

```bash
challenge="web-01-test"
team_id="1"
ttl_min=60

ts=$(date +%s)
body="{\"challenge\": \"$challenge\", \"team_id\": \"$team_id\", \"ttl_min\": $ttl_min}"
sig=$(printf "%s.%s" "$ts" "$body" | openssl dgst -sha256 -hmac "ChangeMe-Orchestrator-Signing-Secret" -binary | xxd -p -c 256)

curl -X POST http://192.168.56.10:8181/start \
  -H "X-Orchestrator-Token: ChangeMe-Orchestrator-Token" \
  -H "X-Signature-Timestamp: $ts" \
  -H "X-Signature: $sig" \
  -H "Content-Type: application/json" \
  -d "$body" | jq '.'
```

### Test Challenge (in browser)

After `/start` returns port 6101:

```
http://192.168.56.10:6101
```

### Stop Instance when Done

```bash
challenge="web-01-test"
team_id="1"

ts=$(date +%s)
body="{\"challenge\": \"$challenge\", \"team_id\": \"$team_id\"}"
sig=$(printf "%s.%s" "$ts" "$body" | openssl dgst -sha256 -hmac "ChangeMe-Orchestrator-Signing-Secret" -binary | xxd -p -c 256)

curl -X POST http://192.168.56.10:8181/stop \
  -H "X-Orchestrator-Token: ChangeMe-Orchestrator-Token" \
  -H "X-Signature-Timestamp: $ts" \
  -H "X-Signature: $sig" \
  -H "Content-Type: application/json" \
  -d "$body"
```

---

## Troubleshooting

See [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) for debugging guidance:

- Connection refused errors
- nginx proxy issues
- Rate limiting problems
- Signature validation failures
- Audit log access
- Emergency restart procedures

---

## See Also

- [docs/VAULT_SETUP.md](VAULT_SETUP.md) - Production secrets configuration
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Debugging & operations
- [docs/SECURITY_BASELINE.md](SECURITY_BASELINE.md) - Security architecture & controls
- [docs/README_CHALLENGES.md](README_CHALLENGES.md) - Challenge authoring guide

