# CTF Platform Custom

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Vagrant](https://img.shields.io/badge/Vagrant-2.4%2B-blue)](https://www.vagrantup.com/)
[![Ansible](https://img.shields.io/badge/Ansible-2.14%2B-red)](https://www.ansible.com/)

## Overview

Single-repository platform for running a fully automated CTF with per-team Docker instances, custom dashboard, and challenge sync.

**Capabilities:**

- **Infrastructure** — Reproducible VM via Vagrant + Ansible, fully re-provisionable
- **Platform** — CTFd on Docker Compose with automated challenge sync
- **Challenges** — 6 Linux privesc challenges + web/osint/sandbox templates, all with writeups in `/soluce`
- **Orchestration** — Per-team Docker instances, TTL-based cleanup, SSH/web launch pages
- **Dashboard** — Custom CTFd plugin with instance cards, live activity, quick launch
- **Security** — HMAC-SHA256 signing, per-team rate limiting, instance quotas, Ansible Vault
- **Monitoring** — Prometheus + Grafana + cAdvisor

---

## Quick Start

### First boot

```bash
git clone https://github.com/USERNAME/ctfd-platform-custom.git
cd ctfd-platform-custom
cp ansible/vars/vault.example.yml ansible/vars/vault.yml
# Edit vault.yml — fill in passwords and tokens (see Secrets section below)
vagrant up --provision
```

`vagrant up` runs the full Ansible playbook automatically:
- Starts CTFd, MariaDB, Redis, Prometheus, Grafana
- Starts `player-instance-api` systemd service (orchestrator)
- Configures nginx reverse proxy
- Pre-builds all challenge Docker images
- Creates the `container-escape` flag on the host
- Syncs all challenges to CTFd (if `ctfd_api_token` is set in vault.yml)

Access points after provisioning:

| Service | URL |
|---------|-----|
| CTFd | http://192.168.56.10 |
| Orchestrator Dashboard | http://192.168.56.10/plugins/orchestrator/dashboard |
| Orchestrator API | http://192.168.56.10:8181 |
| Grafana | http://192.168.56.10:3000 |
| OSINT static challenges | http://192.168.56.10/osint/\<challenge\>/resources/ |

---

### One-time CTFd setup (required on first boot)

1. Open http://192.168.56.10 → complete the CTFd setup wizard (admin account + CTF name)
2. In CTFd: **Admin → Settings → Access Tokens → Generate** — copy the token
3. Add it to `ansible/vars/vault.yml`:
   ```yaml
   ctfd_api_token: "your-token-here"
   ```
4. Re-run the playbook to sync challenges:
   ```bash
   vagrant ssh -c "cd /vagrant/ansible && ansible-playbook -i inventory playbooks/main.yml --ask-vault-pass"
   ```

After this, every subsequent `vagrant up` or playbook run will sync challenges automatically.

---

### Re-provisioning an existing VM

```bash
# Full re-provision (same as first boot)
vagrant provision

# Or via Ansible directly (faster, skips VM setup)
vagrant ssh -c "cd /vagrant/ansible && ansible-playbook -i inventory playbooks/main.yml --ask-vault-pass"
```

---

## Secrets Setup

Copy the example vault file and fill in your values:

```bash
cp ansible/vars/vault.example.yml ansible/vars/vault.yml
```

Edit `ansible/vars/vault.yml`:

```yaml
DB_ROOT_PASSWORD: "strong-password"
DB_PASSWORD: "strong-password"
orchestrator_api_token: "generate: openssl rand -hex 32"
orchestrator_signing_secret: "generate: openssl rand -hex 32"
orchestrator_ctfd_webhook_token: "generate: openssl rand -hex 32"
grafana_admin_password: "strong-password"
ctfd_api_token: ""   # fill after first CTFd setup (see Quick Start)
```

To encrypt with Ansible Vault (recommended for production):
```bash
ansible-vault encrypt ansible/vars/vault.yml
```

---

## Challenge Sync

Challenges are synced to CTFd via the API using `sync_challenges_ctfd.py`.

**Automatic** (runs at end of every Ansible playbook if `ctfd_api_token` is set):
- Creates/updates all challenges from `challenge.yml` files
- Sets flags, descriptions, hints, point values
- Links Docker challenges to the orchestrator launch page

**Manual sync** (useful during development):
```bash
vagrant ssh -c "python3 /vagrant/scripts/sync_challenges_ctfd.py \
  --ctfd-url http://127.0.0.1:8900 \
  --api-token YOUR_TOKEN \
  --challenges-root /vagrant/challenges \
  --instance-base-url http://192.168.56.10 \
  --connection-mode launch-link"
```

---

## Challenge Authoring

### Create a new challenge

```bash
# Linux/macOS
bash ./scripts/new-challenge.sh my-challenge --family linux

# Windows
./scripts/new-challenge.ps1 -Name my-challenge -Family linux
```

Each challenge needs at minimum:
```
challenges/<category>/<name>/
  Dockerfile          # Ubuntu base + vulnerability setup
  docker-compose.yml  # port mapping + image: ctf-<category>-<name>:latest
  challenge.yml       # name, category, value, flag, hints
```

### The image: field is required

Every `docker-compose.yml` must have an explicit `image:` tag:

```yaml
services:
  my-challenge:
    build: .
    image: ctf-linux-my-challenge:latest   # required for pre-build caching
    ports:
      - "5030:22"
    restart: unless-stopped
```

This allows the Ansible playbook to pre-build the image once at deploy time.
When a player launches the challenge, the orchestrator reuses the cached image — **launch is instant**.

### Start a challenge container manually (dev/test)

```bash
vagrant ssh -c "cd /vagrant/challenges/linux/01-suid-classic && docker compose up --build -d"
ssh player@192.168.56.10 -p 5020   # password: player2026
```

### Writeups

All challenge writeups live in `/soluce/<category>/<challenge>/README.md`.
These are for organizers and post-CTF disclosure — never exposed to players.

---

## Linux Privesc Challenge Series

Six SSH-based challenges with increasing difficulty, all in `challenges/linux/`:

| # | Name | Difficulty | Points | Port | Technique |
|---|------|------------|--------|------|-----------|
| 01 | suid-classic | Easy | 100 | 5020 | `find` SUID → GTFOBins |
| 02 | sudo-misconfig | Easy | 150 | 5021 | `sudo vim` → shell escape |
| 03 | cron-wildcard | Medium | 250 | 5022 | `tar *` wildcard injection |
| 04 | path-hijack | Medium | 300 | 5023 | Custom SUID binary + PATH |
| 05 | capabilities | Hard | 400 | 5024 | `python3 cap_setuid+ep` |
| 06 | container-escape | Hard | 500 | 5025 | Docker socket → host FS |

Credentials: `player` / `player2026`

**Note for container-escape:** The flag lives on the Vagrant VM host at `/opt/ctf-flags/container-escape.txt`. This is created automatically by the Ansible playbook.

---

## Operations Commands

```bash
# Check all running containers
vagrant ssh -c "docker ps --format 'table {{.Names}}\t{{.Status}}'"

# Restart CTFd (after plugin changes)
vagrant ssh -c "docker restart ctfd"

# Restart orchestrator API
vagrant ssh -c "sudo systemctl restart player-instance-api.service"

# Check orchestrator API logs
vagrant ssh -c "sudo journalctl -u player-instance-api.service -n 50"

# Reload nginx (after config changes)
vagrant ssh -c "sudo nginx -t && sudo systemctl reload nginx"

# Pre-build a specific challenge image
vagrant ssh -c "cd /vagrant/challenges/linux/01-suid-classic && docker compose build"
```

---

## Repository Structure

```
.
├── ansible/
│   ├── playbooks/main.yml          # Full deploy playbook
│   ├── templates/                  # Jinja2 templates (nginx, docker-compose, systemd)
│   └── vars/
│       ├── main.yml                # Default config values
│       ├── vault.yml               # Secrets (gitignored, create from vault.example.yml)
│       └── vault.example.yml       # Template for vault.yml
├── challenges/
│   ├── linux/                      # Linux privesc series (01-06)
│   ├── web/                        # Web challenges
│   ├── osint/                      # OSINT challenges (static files)
│   ├── sandbox/                    # Sandbox/misc challenges
│   └── _templates/                 # Challenge authoring templates
├── scripts/
│   ├── player-instance-api.py      # Orchestrator HTTP API (systemd service)
│   ├── player-instance-manager.sh  # Docker lifecycle manager (start/stop/extend/status)
│   ├── sync_challenges_ctfd.py     # Challenge sync script (CTFd API)
│   ├── sync_osint_static.py        # OSINT static file sync
│   └── ctfd-orchestrator-plugin/   # CTFd plugin (dashboard, launch pages, API endpoints)
├── soluce/
│   └── linux/                      # Writeups for all linux challenges
├── docs/                           # Extended documentation
└── README.md                       # This file
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/README_CHALLENGES.md](docs/README_CHALLENGES.md) | Challenge authoring, templates, validation |
| [docs/PLAYER_INSTANCE_ORCHESTRATOR.md](docs/PLAYER_INSTANCE_ORCHESTRATOR.md) | Orchestrator API reference |
| [docs/VAULT_SETUP.md](docs/VAULT_SETUP.md) | Ansible Vault setup for production |
| [docs/SECURITY_BASELINE.md](docs/SECURITY_BASELINE.md) | Security model and threat mapping |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues and fixes |
| [docs/MONITORING.md](docs/MONITORING.md) | Prometheus + Grafana setup |
| [docs/WORKFLOW_PRIORITIES.md](docs/WORKFLOW_PRIORITIES.md) | Dev workflow cheatsheet |
