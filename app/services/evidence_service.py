from app.services.context_service import get_decision_context
from app.services.decision_service import evaluate_claim


def build_validated_evidence_package(claim_id: str):
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
    Validate whether the requested procedure/policy assertion
    is supported by the structured knowledge graph.

    This does not ask the LLM to infer missing relationships.
    """

    from app.graph.queries import get_procedure_graph_context

    graph_context = get_procedure_graph_context(procedure_code)

    if graph_context is None:
        return {
            "supported": False,
            "reason": "PROCEDURE_NOT_FOUND",
            "procedure_code": procedure_code,
            "authority": authority,
            "graph_context": None,
        }

    policy = graph_context.get("policy")
    requirement = graph_context.get("requirement")

    # Current graph contains procedure -> policy -> requirement,
    # but no validated authority relationship such as Medicare.
    if authority:
        return {
            "supported": False,
            "reason": "AUTHORITY_RELATIONSHIP_NOT_VALIDATED",
            "procedure_code": procedure_code,
            "authority": authority,
            "graph_context": graph_context,
        }

    return {
        "supported": True,
        "reason": "GRAPH_ASSERTION_VALIDATED",
        "procedure_code": procedure_code,
        "authority": None,
        "policy": policy,
        "requirement": requirement,
        "graph_context": graph_context,
    }
