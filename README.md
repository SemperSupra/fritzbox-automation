# fritzbox-automation

Public, sanitized deployment/release repository for reusable FRITZ!Box automation.

The implementation model is `inspect -> plan -> apply -> verify`. Undocumented bindings must carry model/FRITZ!OS provenance and fail closed on unknown firmware drift.

## Repository boundary

- Private development/source of truth: `SemperSupra/fritzbox-automation-private`.
- Public deploy/release surface: this repository.
- Disposable public firmware/static-analysis execution: `SupraShellScripts/github-ops-lab`.
- Infrastructure integration/consumption: `SupraCraft/minecraft-infra`.

This repository must not contain router-specific desired state, credentials, session material, real topology/device identifiers, authenticated captures, or private rollback state. Promotion from private development requires sanitization, license review, and test evidence.

See issue #1 for the initial public contract and scope.
