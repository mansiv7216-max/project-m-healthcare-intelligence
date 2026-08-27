from unittest.mock import patch

from app.services.decision_service import evaluate_claim


BASE_CONTEXT = {
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
    "procedure": {
        "code": "70553",
    },
    "diagnosis": {
        "code": "G43.909",
    },
    "policy": {
        "policy_id": "POL-IMG-001",
        "title": "Advanced Imaging Coverage Policy",
    },
    "requirement": {
        "name": "Prior Authorization",
    },
    "retrieval_source": "controlled_test_data",
}


@patch("app.services.decision_service.get_decision_context")
def test_approve_when_all_evidence_satisfied(mock_context):
    mock_context.return_value = BASE_CONTEXT

    result = evaluate_claim("TEST001")

    assert result["decision"] == "APPROVE"
    assert result["reason_code"] == "BASELINE_RULES_SATISFIED"
    assert result["evidence_complete"] is True


@patch("app.services.decision_service.get_decision_context")
def test_deny_when_prior_authorization_missing(mock_context):
    context = {
        **BASE_CONTEXT,
        "claim": {
            **BASE_CONTEXT["claim"],
            "claim_id": "TEST002",
            "prior_authorization": False,
        },
    }

    mock_context.return_value = context

    result = evaluate_claim("TEST002")

    assert result["decision"] == "DENY"
    assert result["reason_code"] == "PRIOR_AUTH_MISSING"
    assert result["evidence_complete"] is True


@patch("app.services.decision_service.get_decision_context")
def test_abstain_when_required_evidence_missing(mock_context):
    context = {
        **BASE_CONTEXT,
        "claim": {
            **BASE_CONTEXT["claim"],
            "claim_id": "TEST003",
        },
        "policy": None,
    }

    mock_context.return_value = context

    result = evaluate_claim("TEST003")

    assert result["decision"] == "ABSTAIN"
    assert result["reason_code"] == "INSUFFICIENT_EVIDENCE"
    assert result["evidence_complete"] is False
    assert "policy" in result["missing_evidence"]
