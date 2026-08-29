# Private-to-public promotion boundary

`SemperSupra/fritzbox-automation-private` is the development/source-of-truth repository. This public repository receives only reusable material that is safe to publish independently of any real deployment.

## Allowed in public

- reusable `inspect -> plan -> apply -> verify` engine code;
- generic resource schemas and normalized state models;
- public-safe model/FRITZ!OS compatibility metadata;
- generic bindings derived from documented/publicly observable behavior;
- synthetic/public fixtures, tests, documentation, and release artifacts;
- sanitized firmware-analysis findings containing paths, hashes, endpoint/schema identifiers, and compatibility evidence.

## Never promote

- credentials, private keys, cookies, SIDs, tokens, or secret values;
- telephone numbers, internal addresses, MAC/device identifiers, or real topology;
- router-specific desired state;
- authenticated captures from a real router;
- private rollback snapshots or environment-specific failure evidence;
- raw AVM firmware images, extracted proprietary binaries, or proprietary Web UI source trees;
- material whose licensing does not permit redistribution.

## Promotion gate

A candidate moves from private to public only when:

1. private/environment-specific data has been removed;
2. dependencies and copied material have passed license review;
3. fixtures/tests exercise the public behavior without private data;
4. model/FRITZ!OS applicability and evidence provenance are explicit;
5. every enabled mutation has inspect, deterministic plan, rollback/pre-state, apply, and verify semantics;
6. undocumented bindings fail closed after unknown firmware drift.

Raw firmware and extracted binary evidence may be retained privately for provenance and reproducibility, but only derived public-safe findings may cross this boundary.
