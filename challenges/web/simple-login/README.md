# Simple Login Challenge

## Overview

- Category: Web
- Difficulty: Easy (warmup)
- Points: 50

This challenge provides a basic authentication workflow for players to practice initial web exploitation and credential discovery logic.

## Objective

1. Reach the challenge instance.
2. Authenticate successfully.
3. Capture and submit the flag.

## Runtime

This challenge is orchestrated as a Docker Compose runtime.
Player access is normally launched through CTFd one-click button flow.

- Launch button path (generated): `/plugins/orchestrator/btn/<challenge_id>`
- Launch endpoint: `/plugins/orchestrator/launch?challenge_id=<id>&ttl_min=<minutes>`

## Local Test (inside VM)

```bash
cd /vagrant/challenges/web/simple-login
docker compose up -d --build
curl http://127.0.0.1:5000
```

## Files

- `app.py`: Flask app
- `Dockerfile`: image definition
- `docker-compose.yml`: local runtime mapping
- `requirements.txt`: dependencies
- `challenge.yml`: metadata used by CTF tooling
- `flag.txt`: local flag reference

## Metadata Notes

Current metadata is in `challenge.yml`.
For launch UI coherence, web challenges can declare:

```yaml
connection_mode: web
```

If omitted, access mode can still be inferred automatically.

## Troubleshooting

### Challenge does not start

```bash
docker compose logs -f
docker compose down
docker compose up -d --build
```

### Port conflict

Update host port in `docker-compose.yml`, then rebuild.
