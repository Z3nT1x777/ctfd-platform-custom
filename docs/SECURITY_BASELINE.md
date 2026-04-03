# Security Baseline

## Deployment Model

**Development:** Demo/training with development defaults (ChangeMe-*, demo-*), Vault optional  
**Production:** All defaults overridden via encrypted Ansible Vault, strict preflight checks enabled

---

## Implemented Security Controls

### 1. API Authentication (Token-Based)

**What it does:** Every orchestrator API request requires the `X-Orchestrator-Token` header.

**How it works:**
- Tokens are opaque, randomly-generated strings (no JWT decoding overhead)
- Stored in `/opt/ctf/orchestrator.env` (managed by Ansible, externalized from code)
- Checked on all endpoints: GET, POST, webhooks

**Example:**
```bash
curl -H "X-Orchestrator-Token: ChangeMe-Orchestrator-Token" \
  http://127.0.0.1:8181/status
# Returns 200 OK if token matches, 401 Unauthorized otherwise
```

**Protection against:**
- Unauthorized access from external clients
- API misuse by unintended consumers

**Development default:** `ChangeMe-Orchestrator-Token`  
**Production:** Override via `orchestrator_token_vault` in Ansible Vault

---

### 2. HMAC-SHA256 Request Signing (POST Operations)

**What it does:** All state-changing operations (start, stop, cleanup) require cryptographic signatures.

**How it works:**
- Client computes: `HMAC-SHA256(signing_secret, timestamp.body)`
- Client sends signature in `X-Signature` header + timestamp in `X-Signature-Timestamp`
- Server re-computes signature and compares (constant-time comparison)
- Timestamp must be within 300 seconds (prevents replay attacks)

**Example:**
```bash
ts=$(date +%s)
body='{"challenge": "web-01", "team_id": "1"}'
sig=$(printf "%s.%s" "$ts" "$body" | \
  openssl dgst -sha256 -hmac "ChangeMe-Orchestrator-Signing-Secret" -binary | \
  xxd -p -c 256)

curl -X POST http://127.0.0.1:8181/start \
  -H "X-Orchestrator-Token: ChangeMe-Orchestrator-Token" \
  -H "X-Signature-Timestamp: $ts" \
  -H "X-Signature: $sig" \
  -d "$body"
# Returns 200 OK if signature valid, 401 Unauthorized if invalid/expired
```

**Protection against:**
- Request tampering (attacker cannot change body without invalidating signature)
- Replay attacks (timestamp validation prevents old requests from being replayed)
- Man-in-the-middle attacks (signature requires shared secret knowledge)

**Development default:** `ChangeMe-Orchestrator-Signing-Secret`  
**Production:** Override via `orchestrator_signing_secret_vault` in Ansible Vault  
**Recommendation:** Use 64-character random hex string: `openssl rand -hex 32`

---

### 3. Per-Client Rate Limiting

**What it does:** Limits each client (IP address) to 60 requests/minute, preventing abuse.

**How it works:**
- Uses in-memory token bucket algorithm
- Tracks client IP via X-Forwarded-For header (from nginx reverse proxy)
- Falls back to direct connection IP if header missing
- Returns 429 Too Many Requests when limit exceeded
- Configurable via `ORCHESTRATOR_RATE_LIMIT_PER_MIN`

**Example:**
```bash
# Make 61 requests rapidly from same IP
for i in {1..61}; do
  curl -H "X-Orchestrator-Token: TOKEN" http://127.0.0.1:8181/status
done
# Requests 1-60: 200 OK
# Request 61: 429 Too Many Requests
```

**Protection against:**
- Brute force attacks on authentication
- DoS attacks from single source
- Resource exhaustion

**Development default:** 60 req/min  
**Production:** Adjust based on expected load (e.g., 30 for stricter limits)

---

### 4. Per-Team Rate Limiting

**What it does:** Limits each team to 30 requests/minute, preventing any single team from monopolizing resources.

**How it works:**
- Extracts `team_id` from request body
- Maintains separate rate limit bucket per team
- Returns 429 Too Many Requests when limit exceeded
- Configurable via `ORCHESTRATOR_TEAM_RATE_LIMIT_PER_MIN`

**Example:**
```bash
# Team 1 makes 31 requests in 60 seconds
for i in {1..31}; do
  curl -X POST http://127.0.0.1:8181/start \
    -H "X-Orchestrator-Token: TOKEN" \
    -H "X-Signature-Timestamp: $(date +%s)" \
    -H "X-Signature: $sig" \
    -d '{"team_id": "1", "challenge": "web-01"}'
done
# Requests 1-30: 200 OK
# Request 31: 429 Too Many Requests
```

**Protection against:**
- Runaway clients (bugs, accidental loops)
- Noisy neighbors in multi-team CTF
- Resource exhaustion from single team

**Development default:** 30 req/min per team

---

### 5. Per-Team Instance Quotas

**What it does:** Limits each team to a maximum of 3 concurrent instances, preventing resource exhaustion.

**How it works:**
- Before `/start`, queries running Docker instances
- Counts active instances for the team
- Returns 409 Conflict if already at max
- Configurable via `ORCHESTRATOR_TEAM_MAX_ACTIVE`

**Example:**
```bash
# Team 1 can start 3 instances
curl -X POST http://127.0.0.1:8181/start -d '{"team_id": "1", "challenge": "web-01"}'  # OK, port 6101
curl -X POST http://127.0.0.1:8181/start -d '{"team_id": "1", "challenge": "web-02"}'  # OK, port 6102
curl -X POST http://127.0.0.1:8181/start -d '{"team_id": "1", "challenge": "web-03"}'  # OK, port 6103

# But not a 4th
curl -X POST http://127.0.0.1:8181/start -d '{"team_id": "1", "challenge": "web-04"}'  
# Response: 409 Conflict - team quota exceeded
```

**Protection against:**
- Resource exhaustion from resource-hungry challenges
- Teams launching instances without cleanup
- Cascading failures from runaway systems

**Development default:** 3 instances per team

---

### 6. Centralized Audit Logging

**What it does:** Records all orchestrator events to a JSON audit log for forensics and compliance.

**How it works:**
- Every request (success or failure) is logged to `/var/log/ctf/orchestrator-audit.log`
- JSON format: one line per event with timestamp, endpoint, client IP, team, status
- No PII or sensitive data logged (only team_id, not names)
- Thread-safe write operations
- Configurable log path via `ORCHESTRATOR_AUDIT_LOG`

**Log Format:**
```json
{"ts": 1775258542, "event": "start", "http_status": 200, "path": "/start", "client": "192.168.1.100", "team": "1", "challenge": "web-01", "detail": ""}
{"ts": 1775258543, "event": "unauthorized", "http_status": 401, "path": "/stop", "client": "192.168.1.101", "team": "", "challenge": "", "detail": "missing_or_invalid_token"}
{"ts": 1775258544, "event": "rate_limited", "http_status": 429, "path": "/status", "client": "192.168.1.102", "team": "2", "challenge": "", "detail": "per_team_limit"}
```

**Example queries:**
```bash
# All requests from team 1
vagrant ssh -- sudo grep '"team":"1"' /var/log/ctf/orchestrator-audit.log

# All failed requests (4xx, 5xx status)
vagrant ssh -- sudo grep '"http_status":"[45]' /var/log/ctf/orchestrator-audit.log

# Count events by type
vagrant ssh -- sudo grep -o '"event":"[^"]*"' /var/log/ctf/orchestrator-audit.log | sort | uniq -c
```

**Protection against:**
- Undetected unauthorized access
- Incident response (timeline of events)
- Compliance audits (who did what, when)
- Security monitoring (detect suspicious patterns)

**Note:** Logs never leave the VM; consider shipping to SIEM in production.

---

### 7. CTFd Webhook Trigger Endpoint

**What it does:** Provides `/ctfd/event` endpoint for CTFd to trigger orchestrator actions (start/stop instances).

**How it works:**
- CTFd plugin/extension POSTs events to `/ctfd/event`
- Event body: `{"event": "challenge.start", "team_id": "1", "challenge_id": "web-01"}`
- Endpoint validates X-CTFd-Webhook-Token header (separate from orchestrator token)
- Maps events: `challenge.start` → `/start`, `challenge.stop` → `/stop`, etc.
- Requires same authentication (token + HMAC signature)

**Example:**
```bash
# CTFd webhook post when team clicks "Start Challenge"
ts=$(date +%s)
body='{"event": "challenge.start", "team_id": "1", "challenge_id": "web-01"}'
sig=$(printf "%s.%s" "$ts" "$body" | openssl dgst -sha256 -hmac "ChangeMe-Orchestrator-Signing-Secret" -binary | xxd -p -c 256)

curl -X POST http://127.0.0.1:8181/ctfd/event \
  -H "X-CTFd-Webhook-Token: ChangeMe-CTFd-Webhook-Token" \
  -H "X-Signature-Timestamp: $ts" \
  -H "X-Signature: $sig" \
  -d "$body"
# Response: 200 OK, instance started automatically
```

**Protection against:**
- CTFd UI accidental/intentional abuse (events still require authz)
- Decoupling CTFd from orchestrator (webhook can be routed/throttled)

**Development default:** `ChangeMe-CTFd-Webhook-Token`  
**Production:** Override via `orchestrator_ctfd_webhook_token_vault` in Ansible Vault

---

### 8. API Localhost Binding + nginx Reverse Proxy

**What it does:** API binds only on `127.0.0.1:18181` (internal), exposed via nginx on `0.0.0.0:8181` (external).

**How it works:**
- Python API: `app.run(host='127.0.0.1', port=18181)`
- nginx reverse proxy on port 8181 forwards all requests to 127.0.0.1:18181
- nginx adds X-Forwarded-For, X-Real-IP, X-Forwarded-Proto headers
- Direct API port 18181 cannot be reached from outside VM (firewall-like behavior)

**Benefit:**
- Defense in depth: even if nginx is compromised, API is still isolated
- Single point of ingress control (nginx can add auth middleware, WAF, etc.)
- Clean architecture separation

**Example:**
```bash
# From host, cannot connect directly to API
curl http://192.168.56.10:18181/status  # Timeout/refused

# Must go through nginx proxy
curl http://192.168.56.10:8181/status   # Works (with token)
```

**Configuration in nginx:**
```nginx
upstream orchestrator_backend {
    server 127.0.0.1:18181;
}

server {
    listen 8181;
    location / {
        proxy_pass http://orchestrator_backend;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

### 9. Ansible Vault for Secret Management

**What it does:** Encrypts sensitive values (passwords, tokens, secrets) in `ansible/vars/vault.yml`.

**How it works:**
- Vault file is encrypted at rest (AES256 by default)
- Playbook loads vault.yml (optional, `failed_when: false`)
- All `*_vault` variables are merged via `set_fact` with fallback to defaults
- Templates use `*_effective` variables (vault value if present, else default)

**Example vault.yml:**
```yaml
# Encrypted file at ansible/vars/vault.yml
db_root_password_vault: "production-db-root-secret"
orchestrator_signing_secret_vault: "64-character-random-hex-string"
orchestrator_ctfd_webhook_token_vault: "production-webhook-token"
```

**Type of values protected:**
- Database passwords (CTFd postgres, redis)
- API signing secrets (orchestrator HMAC)
- Webhook tokens (CTFd integration)
- Any sensitive configuration

**Playbook logic:**
```yaml
- name: Set effective secrets
  set_fact:
    db_root_password_effective: "{{ db_root_password_vault | default(db_root_password, true) }}"
    orchestrator_signing_secret_effective: "{{ orchestrator_signing_secret_vault | default(orchestrator_signing_secret, true) }}"
  no_log: true
```

**Protection against:**
- Accidental secret commits to git
- Unauthorized access to sensitive values
- CI/CD exposure (secret only provided at deploy time)

See [docs/VAULT_SETUP.md](VAULT_SETUP.md) for detailed setup instructions.

---

### 10. Security Preflight Checks

**What it does:** CI workflow to detect development defaults and security misconfigurations.

**How it works:**
- Script: `scripts/security-preflight.py`
- Checks for hardcoded development values: `ChangeMe-*`, `demo-*`, `password123`, etc.
- Checks for missing vault.yml (in strict mode)
- Warns on insecure practices (plaintext secrets, weak tokens)
- Can fail pipeline in strict mode for protected branches

**Run locally:**
```bash
# Development mode (warnings only)
python scripts/security-preflight.py

# Strict mode (fails on warnings)
SECURITY_STRICT=1 python scripts/security-preflight.py
```

**Typical output:**
```
⚠️  SECURITY WARNING: Development default found in ansible/vars/main.yml
    - orchestrator_signing_secret = ChangeMe-Orchestrator-Signing-Secret
    
    In STRICT mode, this would fail. Override via:
    - Ansible Vault: ansible/vars/vault.yml
    - Environment variable: ORCHESTRATOR_SIGNING_SECRET

ℹ️  Vault file detected (ansible/vars/vault.yml), assuming overrides are active.
✅ Preflight check PASSED (non-strict mode)
```

**CI integration (GitHub Actions example):**
```yaml
- name: Security Preflight (non-strict)
  run: python scripts/security-preflight.py

- name: Security Preflight (strict on main)
  if: github.ref == 'refs/heads/main'
  run: SECURITY_STRICT=1 python scripts/security-preflight.py
```

**Protection against:**
- Accidental deployment of demo secrets to production
- CI leaks of sensitive values
- Human error in configuration

---

## Operational Requirements

### For Development

1. **Defaults only** (no vault needed):
   ```bash
   vagrant up --provision
   # Uses ChangeMe-* defaults, suitable for local testing only
   ```

### For Production / Shared Environments

1. **Create vault file:**
   ```bash
   cp ansible/vars/vault.example.yml ansible/vars/vault.yml
   ansible-vault encrypt ansible/vars/vault.yml
   ```

2. **Add production secrets to vault:**
   ```bash
   ansible-vault edit ansible/vars/vault.yml
   # Add all *_vault values with secure, production-grade secrets
   ```

3. **Store vault password securely** (NOT in git):
   - Use CI secrets manager (GitHub Secrets, GitLab CI Variables)
   - Use pass, 1password, or similar for local development
   - Rotate regularly

4. **Enable strict preflight** in CI:
   ```yaml
   SECURITY_STRICT=1 python scripts/security-preflight.py
   ```

5. **Provision with vault:**
   ```bash
   # Local with vault password file
   ansible-playbook playbooks/main.yml --vault-password-file=/path/to/vault-pass.txt
   
   # CI with vault password environment variable
   echo "$VAULT_PASSWORD" | ansible-playbook playbooks/main.yml --vault-password-file=/dev/stdin
   ```

### Secret Rotation

1. Update secret in vault:
   ```bash
   ansible-vault edit ansible/vars/vault.yml
   ```

2. Re-provision infrastructure:
   ```bash
   ansible-playbook playbooks/main.yml --vault-password-file=/path/to/vault-pass.txt
   ```

3. Verify service restart:
   ```bash
   vagrant ssh -- sudo systemctl status ctf-orchestrator-api.service
   ```

---

## Threat Model

| Threat | Mitigation |
|--------|-----------|
| Unauthorized API access | Token authentication + HMAC signatures |
| Request tampering | HMAC-SHA256 signatures + timestamp validation |
| Replay attacks | Timestamp expiration (300s TTL) |
| DoS from single client | Per-client rate limiting (60 req/min) |
| Resource exhaustion | Per-team rate limits + quotas |
| Audit trail gaps | Centralized JSON audit logging |
| Secret exposure | Ansible Vault + environment variables |
| Man-in-the-middle | HMAC signatures prevent tampering |
| Unauthorized instance launch | Token + signature required on /start |
| Runaway instance accumulation | Team quotas (max 3 active) |
| Undetected breaches | Audit logs enable forensics |

---

## References

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Ansible Vault Documentation](https://docs.ansible.com/ansible/latest/user_guide/vault.html)
- [HMAC Authentication](https://tools.ietf.org/html/rfc4868)
- [Rate Limiting Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Prevention_Cheat_Sheet.html)
- [Audit Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
