# Custom Repository Workflow (EN)

This workflow keeps a clean baseline template while allowing fast custom development.

## Repository Model

- Template repository: stable baseline (`ctfd-platform-template`)
- Custom repository: team-specific product (`ctfd-platform-custom`)

## Local Git Remote Setup

Inside your custom local clone:

```bash
git remote -v
# origin   -> custom repo
# upstream -> template repo
```

If `upstream` is missing:

```bash
git remote add upstream https://github.com/<owner>/ctfd-platform-template.git
git fetch upstream --prune
```

## Pull Template Updates Into Custom

```bash
git checkout main
git fetch upstream --prune
git merge upstream/main
# or: git rebase upstream/main
```

Then push to your custom repo:

```bash
git push origin main
```

## Recommended Change Routing

- Generic, reusable improvements: open PR to template repository.
- Team branding, operations shortcuts, or risky experiments: keep in custom repository.

## Release Rhythm

- Template: slower, quality-gated releases.
- Custom: faster iteration with selective upstream sync.
