from app.services.context_service import get_decision_context
from app.services.decision_service import evaluate_claim


def build_validated_evidence_package(claim_id: str):
    """
    Build the validated evidence package used by claim-level Mode C.

    The LLM receives this package only after deterministic
    claim evaluation has been completed.
    """

    context = get_decision_context(claim_id)
    decision = evaluate_claim(claim_id)

    if context is None or decision is None:
        return None

    claim = context.get("claim") or {}
    member = context.get("member") or {}
    provider = context.get("provider") or {}
    procedure = context.get("procedure") or {}
    diagnosis = context.get("diagnosis") or {}
    policy = context.get("policy") or {}
    requirement = context.get("requirement") or {}

    return {
        "claim_id": claim_id,

        "baseline_decision": {
            "decision": decision.get("decision"),
            "reason_code": decision.get("reason_code"),
            "evidence_complete": decision.get("evidence_complete"),
            "reasons": decision.get("reasons", []),
            "missing_evidence": decision.get("missing_evidence", []),
        },

        "verified_facts": {
            "member_id": member.get("member_id"),
            "member_eligibility": member.get("eligibility_status"),

            "provider_id": provider.get("provider_id"),
            "provider_name": provider.get("provider_name"),
            "provider_in_network": provider.get("in_network"),

            "procedure_code": procedure.get("code"),
            "diagnosis_code": diagnosis.get("code"),

            "claim_amount": claim.get("amount"),
            "prior_authorization": claim.get("prior_authorization"),
            "claim_status": claim.get("status"),
        },

        "policy_evidence": {
            "policy_id": policy.get("policy_id"),
            "policy_title": policy.get("title"),
            "requirement": requirement.get("name"),
            "policy_text": policy.get("text"),
        },

        "provenance": {
            "retrieval_source": context.get("retrieval_source"),
            "knowledge_graph": "projectm",
            "validation_method": "deterministic_baseline",
        },

        "generation_constraints": {
            "may_change_baseline_decision": False,
            "may_invent_missing_facts": False,
            "may_use_external_policy_knowledge": False,
            "must_cite_policy": True,
            "must_abstain_if_evidence_incomplete": True,
        },
    }


def validate_procedure_assertion(
    procedure_code: str,
    authority: str | None = None,
) -> dict:
    """
    Validate whether a requested procedure/policy assertion is
    supported by the structured knowledge graph.

    The validation layer distinguishes:
        - required authorization
        - conditional authorization
        - insufficient graph evidence
        - unsupported authority attribution

    The LLM is not used to infer missing relationships.
    """

    from app.graph.queries import get_procedure_graph_context

    graph_context = get_procedure_graph_context(procedure_code)

    if graph_context is None:
        return {
            "supported": False,
            "reason": "PROCEDURE_NOT_FOUND",
            "procedure_code": procedure_code,
            "authority": authority,
            "evidence_complete": False,
            "graph_context": None,
        }

    procedure = graph_context.get("procedure")
    policy = graph_context.get("policy")
    requirement = graph_context.get("requirement")
    authorization_rule = graph_context.get("authorization_rule")

    # Procedure may exist in the graph while having no validated
    # policy or requirement relationship.
    if (
        procedure is None
        or policy is None
        or requirement is None
        or authorization_rule is None
    ):
        return {
            "supported": False,
            "reason": "INSUFFICIENT_POLICY_EVIDENCE",
            "procedure_code": procedure_code,
            "authority": authority,
            "evidence_complete": False,
            "graph_context": graph_context,
        }

    # The current graph does not establish Medicare, Medicaid,
    # CMS, federal policy, or other external authorities.
    if authority:
        return {
            "supported": False,
            "reason": "AUTHORITY_RELATIONSHIP_NOT_VALIDATED",
            "procedure_code": procedure_code,
            "authority": authority,
            "evidence_complete": False,
            "graph_context": graph_context,
        }

    rule_type = authorization_rule.get("type")
    condition = authorization_rule.get("condition")

    if rule_type == "REQUIRED":
        validation_reason = "GRAPH_ASSERTION_REQUIRED"

    elif rule_type == "CONDITIONAL":
        validation_reason = "GRAPH_ASSERTION_CONDITIONAL"

    else:
        return {
            "supported": False,
            "reason": "AUTHORIZATION_RULE_NOT_VALIDATED",
            "procedure_code": procedure_code,
            "authority": None,
            "evidence_complete": False,
            "graph_context": graph_context,
        }

    return {
        "supported": True,
        "reason": validation_reason,
        "procedure_code": procedure_code,
        "authority": None,
        "evidence_complete": True,

        "policy": policy,
        "requirement": requirement,

        "authorization_rule": {
            "type": rule_type,
            "condition": condition,
        },

        "graph_context": graph_context,
    }
