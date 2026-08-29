"""Public FRITZ!Box automation package."""

from .core import (
    assert_plan_precondition,
    build_plan,
    build_rollback_plan,
    canonical_json,
    content_digest,
    desired_digest,
    state_fingerprint,
)

__all__ = [
    "assert_plan_precondition",
    "build_plan",
    "build_rollback_plan",
    "canonical_json",
    "content_digest",
    "desired_digest",
    "state_fingerprint",
]
