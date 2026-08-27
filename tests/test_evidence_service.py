from unittest.mock import patch

from app.services.evidence_service import build_validated_evidence_package


MOCK_CONTEXT = {
    "claim": {
        "claim_id": "TEST001",
        "amount": 1450.0,
        "prior_authorization": True,
        "status": "PENDING",
    },
    "member": {
        "member_id": "M001",
        "eligibility_status": "ACTIVE",
    },
    "provider": {
        "provider_id": "P001",
        "provider_name": "Test Provider",
        "in_network": True,
    },
    "procedure": {"code": "70553"},
    "diagnosis": {"code": "G43.909"},
    "policy": {
        "policy_id": "POL-IMG-001",
        "title": "Advanced Imaging Coverage Policy",
        "text": "Prior authorization is required.",
    },
    "requirement": {"name": "Prior Authorization"},
    "retrieval_source": "neo4j_knowledge_graph",
}


MOCK_DECISION = {
    "decision": "APPROVE",
    "reason_code": "BASELINE_RULES_SATISFIED",
    "evidence_complete": True,
    "reasons": ["Required evidence satisfied."],
    "missing_evidence": [],
}


@patch("app.services.evidence_service.evaluate_claim")
@patch("app.services.evidence_service.get_decision_context")
def test_build_validated_evidence_package(mock_context, mock_decision):
    mock_context.return_value = MOCK_CONTEXT
    mock_decision.return_value = MOCK_DECISION

    package = build_validated_evidence_package("TEST001")

    assert package is not None

    assert package["claim_id"] == "TEST001"

    assert package["baseline_decision"]["decision"] == "APPROVE"
    assert package["baseline_decision"]["evidence_complete"] is True

    assert package["verified_facts"]["claim_amount"] == 1450.0
    assert package["verified_facts"]["procedure_code"] == "70553"
    assert package["verified_facts"]["prior_authorization"] is True

    assert package["policy_evidence"]["policy_id"] == "POL-IMG-001"

    assert (
        package["provenance"]["validation_method"]
        == "deterministic_baseline"
    )

    constraints = package["generation_constraints"]

    assert constraints["may_change_baseline_decision"] is False
    assert constraints["may_invent_missing_facts"] is False
    assert constraints["may_use_external_policy_knowledge"] is False
    assert constraints["must_cite_policy"] is True
    assert constraints["must_abstain_if_evidence_incomplete"] is True
