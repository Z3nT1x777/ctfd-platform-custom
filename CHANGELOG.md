# Changelog

## v2.5.0 - 2026-05-18

### Added
- **Sandbox category** — 2 new challenges:
  - `history-perms-ssh` (250 pts) — pivot via bash history breadcrumbs + sudo misconfiguration
  - `ssh-lab` / `local-service-recon` (150 pts) — enumerate localhost services, inspect monitoring agent source, curl `/metrics` endpoint
- **OSINT category** — 2 challenges finalized:
  - `metro-memory-trail` (150 pts) — extract GPS EXIF from Colonne de Juillet photo + DateTimeOriginal from vintage postcard → `CTF{paris_bastille_1989}`
  - `first-hacker` (100 pts, ex `template-example`) — social engineering pioneer OSINT → `CTF{kevin_mitnick}`
- Soluces for sandbox challenges: `soluce/sandbox/history-perms-ssh/` and `soluce/sandbox/ssh-lab/`
- EXIF injection utility: `challenges/osint/metro-memory-trail/inject_exif.py` (piexif — reproducible asset preparation)

### Changed
- OSINT `metro-memory-trail`: complete scenario rewrite — French narrative, dark UI redesign, real EXIF metadata injected into assets
- OSINT `template-example` directory renamed → `first-hacker`; value raised 75 → 100 pts
- **Ansible**: added blocking `fail` task when any secret is literally `REPLACE_ME` (vault.example.yml copied without modification); existing `debug` warning retained for default placeholder values

### Fixed
- `sync_challenges_ctfd.py`: YAML block scalar parser extended to all keys (was only `description:`) — hints defined with `|` now parse correctly
- `player-instance-api.py`: Python stdout unbuffering (`python3 -u` + `bufsize=1`) — sync log streams line-by-line instead of appearing all at once
- Admin plugin progress bar: replaced native `<progress>` element with custom 3px gradient div — no longer spans full log width
- `metro-memory-trail/resources/index.html`: fixed `clue.png` reference → `clue.jpg`
- `crypto/01-caesar-warmup`: value 50 → 100 pts
- `web/01-simple-login`: value 75 → 100 pts
- `crypto/02-base64-chain`: value 75 → 100 pts; added hint3
- `linux/01-suid-classic`: added hint3 (GTFOBins reference)
- `linux/05-capabilities`, `linux/06-container-escape`, `web/05-lfi-reader`: removed solution-revealing hints

---

## v2.4.0 - 2026-05-15

### Added
- Static file serving for forensics (6) and reverse (2) challenges via nginx `/files/` path
  - Files generated at provision time from Docker build artifacts — no per-team instance needed
  - Ansible tasks: build image → `docker cp` file → `/var/www/ctf/files/<category>/<name>/` → remove container
  - Idempotent: skipped if file already exists (`creates:` guard)
- `ORCHESTRATOR_PUBLIC_URL` env var — sets the base URL injected into CTFd challenge launch links
  (fixes links using `127.0.0.1` instead of `192.168.56.10`)
- nginx `/files/` location block in `ctfd-nginx.conf.j2`

### Changed
- `sync_challenges_ctfd.py`: static challenges now use `connection_info` from `challenge.yml` (was always empty)
- forensics (×6) and reverse/c-checker, reverse/xor-checker `challenge.yml`: `type: static` + `connection_info` direct download URL

### Fixed
- Challenge launch links used the loopback bind address (`127.0.0.1`) instead of the public VM IP

---

## v2.3.0 - 2026-05-14

### Added
- Forensics challenge series (6 challenges): apache-logs, pcap-http, stego-lsb, pcap-dns, strings-dump, zip-hidden
- Reverse challenge series (4 challenges): python-obfusc (static), c-checker, xor-checker, crackme-layers (static)
- Crypto challenge series (6 challenges): all static type, no Docker needed
- Web challenge series renamed to 01-06 convention (simple-login, ssti-notes, sqli-bypass, idor-profile, lfi-reader, jwt-forgery)
- Soluces for all new categories: soluce/crypto/, soluce/forensics/, soluce/reverse/, soluce/web/
- ORCHESTRATOR_CTFD_API_TOKEN and ORCHESTRATOR_CTFD_BASE_URL in orchestrator.env
- Rate-limit persistence: state dump to JSON every 30s + restore at boot
- Logrotate config for /var/log/ctf/*.log (daily, 14 days, compress)
- CTFd DB daily backup via mysqldump (3:30am, 14 backups retained)
- Admin plugin page (`/plugins/orchestrator/admin`): Sync, Pre-build, Kill-all, live instance table

### Fixed
- Admin panel CSRF: nonce injected server-side via `generate_csrf()` — POST actions now work
- `DOCKER_CONFIG` redirected to `/opt/ctf/orchestrator/.docker` (ProtectHome=true systemd hardening)
- `sync_challenges_ctfd.py`: static challenges no longer get launch links appended

---

## v2.1.0 - 2026-04-07

### Changed
- Consolidated repository strategy to a single custom repo workflow.
- Cleaned Git remotes to keep only `origin` in the active custom repository setup.
- Updated core documentation to remove legacy template/upstream split guidance.
- Added an operations command cookbook to troubleshooting documentation.
- Corrected challenge template path references in workflow docs.
- Improved SSH command-card UX alignment and copy icon styling in orchestrator launch UI.

### Added
- Quota profile support in Ansible playbook via `orchestrator_quota_profile` with built-in profiles:
  - `small`
  - `medium`
  - `large`
- Validation for invalid quota profile values with explicit error messaging.
- Runtime summary output of applied quota values during provisioning.

### Removed
- Obsolete template-planning documents no longer relevant to the custom-only workflow:
  - `docs/TEMPLATE_BASELINE_PLAN.md`
  - `docs/TEMPLATE_SCOPE_MATRIX.md`
