from app.services.context_service import get_decision_context


REQUIRED_FIELDS = [
    "member",
    "provider",
    "procedure",
    "policy",
]


def evaluate_claim(claim_id: str):
    context = get_decision_context(claim_id)

    if context is None:
        return None

    # -----------------------------
    # 1. EVIDENCE COMPLETENESS CHECK
    # -----------------------------
    missing_evidence = []

    for field in REQUIRED_FIELDS:
        if not context.get(field):
            missing_evidence.append(field)

    claim = context.get("claim")
    member = context.get("member")
    provider = context.get("provider")
    procedure = context.get("procedure")
    policy = context.get("policy")
    requirement = context.get("requirement")

    if not claim:
        missing_evidence.append("claim")

    if missing_evidence:
        return {
            "claim_id": claim_id,
            "decision": "ABSTAIN",
            "reason_code": "INSUFFICIENT_EVIDENCE",
            "missing_evidence": missing_evidence,
            "evidence_complete": False,
        }

    # -----------------------------
    # 2. EXTRACT VERIFIED FACTS
    # -----------------------------
    member_active = (
        member.get("eligibility_status") == "ACTIVE"
    )

    provider_in_network = (
        provider.get("in_network") is True
    )

    prior_auth_present = (
        claim.get("prior_authorization") is True
    )

    requires_prior_auth = (
        requirement is not None
        and requirement.get("name") == "Prior Authorization"
    )

    # -----------------------------
    # 3. DETERMINISTIC RULES
    # -----------------------------
    reasons = []

    if not member_active:
        reasons.append("Member eligibility is not active.")

        return {
            "claim_id": claim_id,
            "decision": "DENY",
            "reason_code": "MEMBER_INELIGIBLE",
            "reasons": reasons,
            "evidence_complete": True,
            "evidence": build_evidence_package(context),
        }

    reasons.append("Member eligibility is active.")

    if not provider_in_network:
        reasons.append("Provider is not in network.")

        return {
            "claim_id": claim_id,
            "decision": "ABSTAIN",
            "reason_code": "NETWORK_REVIEW_REQUIRED",
            "reasons": reasons,
            "evidence_complete": True,
            "evidence": build_evidence_package(context),
        }

    reasons.append("Provider is in network.")

    if requires_prior_auth:
        if not prior_auth_present:
            reasons.append(
                f"Procedure {procedure.get('code')} requires prior "
                "authorization, but authorization is not present."
            )

            return {
                "claim_id": claim_id,
                "decision": "DENY",
                "reason_code": "PRIOR_AUTH_MISSING",
                "reasons": reasons,
                "evidence_complete": True,
                "evidence": build_evidence_package(context),
            }

        reasons.append(
            f"Procedure {procedure.get('code')} requires prior "
            "authorization, and authorization is present."
        )

    # -----------------------------
    # 4. BASELINE APPROVAL
    # -----------------------------
    return {
        "claim_id": claim_id,
        "decision": "APPROVE",
        "reason_code": "BASELINE_RULES_SATISFIED",
        "reasons": reasons,
        "evidence_complete": True,
        "evidence": build_evidence_package(context),
    }


def build_evidence_package(context):
    claim = context.get("claim") or {}
    member = context.get("member") or {}
    provider = context.get("provider") or {}
    procedure = context.get("procedure") or {}
    diagnosis = context.get("diagnosis") or {}
    policy = context.get("policy") or {}
    requirement = context.get("requirement") or {}

    return {
        "claim_id": claim.get("claim_id"),
        "member_id": member.get("member_id"),
        "member_eligibility": member.get("eligibility_status"),
        "provider_id": provider.get("provider_id"),
        "provider_name": provider.get("provider_name"),
        "provider_in_network": provider.get("in_network"),
        "procedure_code": procedure.get("code"),
        "diagnosis_code": diagnosis.get("code"),
        "prior_authorization": claim.get("prior_authorization"),
        "policy_id": policy.get("policy_id"),
        "policy_title": policy.get("title"),
        "requirement": requirement.get("name"),
        "retrieval_source": context.get("retrieval_source"),
    }
