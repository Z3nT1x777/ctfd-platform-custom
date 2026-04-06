# Changelog

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
