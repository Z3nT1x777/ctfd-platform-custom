# Challenge Family Templates

This directory stores templates grouped by family.

- web: docker-based web challenge
- osint: static challenge with no container runtime
- sandbox: docker-based sandbox challenge
- reverse: docker-based reverse challenge
- pwn: docker-based pwn challenge

Use helper scripts to generate new challenge folders:

- Windows: `./scripts/new-challenge.ps1 -Name <name> -Family <family>`
- Linux/macOS: `bash ./scripts/new-challenge.sh <name> --family <family>`
