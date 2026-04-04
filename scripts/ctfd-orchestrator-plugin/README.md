# CTFd Orchestrator Plugin

CTFd plugin that provides one-click challenge launch for players, backed by the orchestrator API.

## What It Does

- Player launch buttons: `/plugins/orchestrator/btn/<challenge_id>`
- One-click launch endpoint: `/plugins/orchestrator/launch`
- Team-scoped start/stop/list endpoints under `/plugins/orchestrator/*`
- Real-time activity leaderboard
- Team quotas and TTL enforcement
- Access-aware launch page output:
  - Web URL button for web challenges
  - Copy-ready SSH commands for terminal-based challenges
  - Instruction block when challenge is not web/ssh direct

## Access Model

The plugin only orchestrates challenges that are spawnable (runtime includes `docker-compose.yml`).
Static challenges are intentionally excluded from orchestration launch flow.

This avoids showing invalid web links for non-web challenge types.

## Configuration

Environment variables used by the plugin:

- `ORCHESTRATOR_API_URL` (recommended from CTFd container: `http://host.docker.internal:8181`)
- `ORCHESTRATOR_API_TOKEN`
- `ORCHESTRATOR_SIGNING_SECRET`
- `ORCHESTRATOR_WEBHOOK_TOKEN`
- `ORCHESTRATOR_TEAM_MAX_ACTIVE`

TTL range is enforced server-side: 5 to 240 minutes.

## Deployment Notes

The repository already mounts this plugin in CTFd via Compose template and Ansible provisioning.
In normal usage, you only need to reprovision/restart CTFd after plugin updates.

Example:

```bash
vagrant provision
vagrant ssh -c "docker restart ctfd"
```

## Security Notes

- Player launch endpoints require authenticated users in a team.
- Admin/dev UI route (`/plugins/orchestrator/ui`) is restricted to admins.
- Launch uses signed calls to orchestrator API through `webhook_handler.py`.

## Sync Helper Endpoint

- `POST /plugins/orchestrator/sync`
- Auth header: `X-Orchestrator-Secret: <ORCHESTRATOR_SIGNING_SECRET>`
- Purpose: updates CTFd challenge `connection_info` for orchestrated challenges with button links.

## Troubleshooting

### `connection_error` from CTFd

Verify CTFd container can reach host orchestrator API:

- `ORCHESTRATOR_API_URL` should target `host.docker.internal` from inside container.
- Compose service should include host-gateway mapping.

### Launch works but URL missing

Expected for non-web access modes. The launch card should provide SSH commands or instructions instead of forcing a browser link.

### Team shown as numeric id

Recent plugin updates resolve and render team name when available.
