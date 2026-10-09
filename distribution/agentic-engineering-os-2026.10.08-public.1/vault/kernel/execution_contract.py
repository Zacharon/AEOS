"""Shared constants and lifecycle rules for Execution Kernel v0.1.

This module is the smallest reusable code surface extracted from the two proven
dry-run verticals. It contains no runner, provider, filesystem, network, or
approval side effects. Project adapters may import it without inheriting
project-specific behavior.
"""

from __future__ import annotations

from types import MappingProxyType


ARTIFACT_RUN_STATE = "RunState"
ARTIFACT_EXECUTION_CONTRACT = "ExecutionContract"
ARTIFACT_MEMORY_CHECKPOINT = "MemoryCheckpoint"
ARTIFACT_STATE_TRANSITION = "StateTransition"
ARTIFACT_TOOL_GATEWAY_CALL = "ToolGatewayCall"
ARTIFACT_REVIEW_DECISION = "ReviewDecision"
ARTIFACT_EVAL_RESULT = "EvalResult"
ARTIFACT_REVIEW_PACKET = "ReviewPacket"
ARTIFACT_EVIDENCE_LINK = "EvidenceLink"
ARTIFACT_UNCERTAINTY_ASSESSMENT = "UncertaintyAssessment"
ARTIFACT_EXECUTION_PLAN = "ExecutionPlan"
ARTIFACT_KNOWLEDGE_SOURCE_INGESTED = "KnowledgeSourceIngested"
ARTIFACT_KNOWLEDGE_PROPOSAL_CREATED = "KnowledgeProposalCreated"
ARTIFACT_KNOWLEDGE_PROPOSAL_VERIFIED = "KnowledgeProposalVerified"
ARTIFACT_KNOWLEDGE_OWNER_DECISION = "KnowledgeOwnerDecision"
ARTIFACT_KNOWLEDGE_PROPOSAL_APPLIED = "KnowledgeProposalApplied"
ARTIFACT_KNOWLEDGE_PROPOSAL_REJECTED = "KnowledgeProposalRejected"
ARTIFACT_KNOWLEDGE_CONTRADICTION_RESOLVED = "KnowledgeContradictionResolved"
ARTIFACT_KNOWLEDGE_ROLLBACK = "KnowledgeRollback"

VALID_ARTIFACT_TYPES = frozenset(
    {
        ARTIFACT_RUN_STATE,
        ARTIFACT_EXECUTION_CONTRACT,
        ARTIFACT_MEMORY_CHECKPOINT,
        ARTIFACT_STATE_TRANSITION,
        ARTIFACT_TOOL_GATEWAY_CALL,
        ARTIFACT_REVIEW_DECISION,
        ARTIFACT_EVAL_RESULT,
        ARTIFACT_REVIEW_PACKET,
        ARTIFACT_EVIDENCE_LINK,
        ARTIFACT_UNCERTAINTY_ASSESSMENT,
        ARTIFACT_EXECUTION_PLAN,
        ARTIFACT_KNOWLEDGE_SOURCE_INGESTED,
        ARTIFACT_KNOWLEDGE_PROPOSAL_CREATED,
        ARTIFACT_KNOWLEDGE_PROPOSAL_VERIFIED,
        ARTIFACT_KNOWLEDGE_OWNER_DECISION,
        ARTIFACT_KNOWLEDGE_PROPOSAL_APPLIED,
        ARTIFACT_KNOWLEDGE_PROPOSAL_REJECTED,
        ARTIFACT_KNOWLEDGE_CONTRADICTION_RESOLVED,
        ARTIFACT_KNOWLEDGE_ROLLBACK,
    }
)

REQUIRED_DRY_RUN_ARTIFACT_TYPES = (
    ARTIFACT_RUN_STATE,
    ARTIFACT_MEMORY_CHECKPOINT,
    ARTIFACT_REVIEW_PACKET,
    ARTIFACT_EVAL_RESULT,
)

CANONICAL_LIFECYCLE_STATES = frozenset(
    {"needs_review", "approved", "rejected", "changes_requested"}
)

LIFECYCLE_ALIASES = MappingProxyType(
    {
        "needs_human_approval": "needs_review",
        "owner_approved": "approved",
        "owner_rejected": "rejected",
        "execution_plan_created": "approved",
    }
)

TERMINAL_LIFECYCLE_STATES = frozenset({"approved", "rejected"})


class InvalidLifecycleStateError(ValueError):
    """Raised when a state is outside the shared lifecycle contract."""


def normalize_lifecycle_state(state: str) -> str:
    """Return the canonical lifecycle state for a canonical name or known alias."""

    if not isinstance(state, str) or not state.strip():
        raise InvalidLifecycleStateError("lifecycle state must be a non-empty string")
    if state != state.strip():
        raise InvalidLifecycleStateError(
            "lifecycle state must not have leading or trailing whitespace"
        )

    canonical = LIFECYCLE_ALIASES.get(state, state)
    if canonical not in CANONICAL_LIFECYCLE_STATES:
        allowed = sorted(CANONICAL_LIFECYCLE_STATES | set(LIFECYCLE_ALIASES))
        raise InvalidLifecycleStateError(
            f"unsupported lifecycle state {state!r}; expected one of: {', '.join(allowed)}"
        )
    return canonical


def is_terminal_lifecycle_state(state: str) -> bool:
    """Return whether a canonical state or known alias closes the current run."""

    return normalize_lifecycle_state(state) in TERMINAL_LIFECYCLE_STATES
