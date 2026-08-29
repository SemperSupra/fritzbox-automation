"""Pure desired-state planning primitives for FRITZ!Box automation.

This module contains no network I/O and no secret access. Device adapters must
normalize raw FRITZ!OS state before calling this planner.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

JSON = Any
PLAN_SCHEMA_VERSION = 1
SNAPSHOT_SCHEMA_VERSION = 1
DESIRED_SCHEMA_VERSION = 1
WRITE_VERIFIED = "live-write-verified"


def canonical_json(value: JSON) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_digest(value: JSON) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _compatibility_identity(snapshot: Mapping[str, JSON]) -> dict[str, JSON]:
    target = snapshot.get("target") or {}
    return {
        "id": target.get("id"),
        "model": target.get("model"),
        "fritzOS": target.get("fritzOS"),
        "firmwareEvidenceId": target.get("firmwareEvidenceId"),
    }


def state_fingerprint(snapshot: Mapping[str, JSON]) -> str:
    return content_digest({
        "target": _compatibility_identity(snapshot),
        "resources": snapshot.get("resources") or {},
    })


def desired_digest(desired: Mapping[str, JSON]) -> str:
    return content_digest({
        "targetId": desired.get("targetId"),
        "resources": desired.get("resources") or {},
    })


def build_plan(
    snapshot: Mapping[str, JSON],
    desired: Mapping[str, JSON],
    bindings: Mapping[str, Mapping[str, JSON]],
) -> dict[str, JSON]:
    """Build a deterministic minimal plan from normalized state."""
    if snapshot.get("schemaVersion") != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError("unsupported snapshot schemaVersion")
    if desired.get("schemaVersion") != DESIRED_SCHEMA_VERSION:
        raise ValueError("unsupported desired-state schemaVersion")

    target = snapshot.get("target") or {}
    if desired.get("targetId") != target.get("id"):
        raise ValueError("desired targetId does not match snapshot target id")

    current_resources: Mapping[str, JSON] = snapshot.get("resources") or {}
    desired_resources: Mapping[str, JSON] = desired.get("resources") or {}
    operations: list[dict[str, JSON]] = []
    blockers: list[dict[str, str]] = []

    for resource_id in sorted(desired_resources):
        before = current_resources.get(resource_id, None)
        after = desired_resources[resource_id]
        if canonical_json(before) == canonical_json(after):
            continue

        binding = bindings.get(resource_id)
        if not binding:
            blockers.append({
                "resource": resource_id,
                "code": "binding-missing",
                "message": "No binding exists for this canonical resource.",
            })
            operations.append({
                "resource": resource_id,
                "before": before,
                "after": after,
                "bindingId": None,
                "bindingConfidence": "missing",
                "risk": "unknown",
                "reversibility": "unknown",
                "requiresConfirmation": True,
                "blocked": True,
            })
            continue

        confidence = str(binding.get("confidence") or "unverified")
        blocked = bool(binding.get("blocked", False))
        if confidence != WRITE_VERIFIED:
            blockers.append({
                "resource": resource_id,
                "code": "binding-not-write-verified",
                "message": f"Binding confidence is {confidence!r}, not live-write-verified.",
            })
        if blocked:
            blockers.append({
                "resource": resource_id,
                "code": "binding-blocked",
                "message": "Binding is explicitly blocked by policy/evidence.",
            })

        operations.append({
            "resource": resource_id,
            "before": before,
            "after": after,
            "bindingId": binding.get("bindingId"),
            "bindingConfidence": confidence,
            "evidenceId": binding.get("evidenceId"),
            "risk": binding.get("risk", "normal"),
            "sideEffects": list(binding.get("sideEffects") or []),
            "reversibility": binding.get("reversibility", "manual_recovery"),
            "requiresConfirmation": bool(binding.get("requiresConfirmation", False)),
            "blocked": blocked,
        })

    no_op = not operations
    plan_without_digest: dict[str, JSON] = {
        "schemaVersion": PLAN_SCHEMA_VERSION,
        "target": _compatibility_identity(snapshot),
        "preconditionStateFingerprint": state_fingerprint(snapshot),
        "desiredStateDigest": desired_digest(desired),
        "operations": operations,
        "blockers": blockers,
        "noOp": no_op,
        "requiresConfirmation": any(op["requiresConfirmation"] for op in operations),
        "applyAuthorized": bool(operations) and not blockers,
    }
    if no_op:
        plan_without_digest["applyAuthorized"] = False

    plan = dict(plan_without_digest)
    plan["planDigest"] = content_digest(plan_without_digest)
    return plan


def build_rollback_plan(plan: Mapping[str, JSON]) -> dict[str, JSON]:
    reverse_ops: list[dict[str, JSON]] = []
    for operation in reversed(list(plan.get("operations") or [])):
        op = dict(operation)
        op["before"], op["after"] = op.get("after"), op.get("before")
        reverse_ops.append(op)

    payload = {
        "schemaVersion": PLAN_SCHEMA_VERSION,
        "rollbackOf": plan.get("planDigest"),
        "target": plan.get("target"),
        "operations": reverse_ops,
        "blocked": any(
            op.get("reversibility") not in ("reversible", "reversible_with_connectivity_risk")
            or op.get("blocked")
            for op in reverse_ops
        ),
    }
    result = dict(payload)
    result["planDigest"] = content_digest(payload)
    return result


def assert_plan_precondition(snapshot: Mapping[str, JSON], plan: Mapping[str, JSON]) -> None:
    actual = state_fingerprint(snapshot)
    expected = plan.get("preconditionStateFingerprint")
    if actual != expected:
        raise RuntimeError(
            "planned state precondition no longer matches target; inspect and re-plan required"
        )
