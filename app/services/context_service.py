from pathlib import Path

from app.graph.queries import get_claim_graph_context


POLICY_FILE = Path("data/policies/imaging_policy.txt")


def get_decision_context(claim_id: str):
    """
    Build decision context for a healthcare claim using
    Neo4j relationship-aware retrieval plus source policy text.
    """

    graph_context = get_claim_graph_context(claim_id)

    if graph_context is None:
        return None

    policy_text = POLICY_FILE.read_text()

    return {
        "claim": graph_context["claim"],
        "member": graph_context["member"],
        "provider": graph_context["provider"],
        "procedure": graph_context["procedure"],
        "diagnosis": graph_context["diagnosis"],
        "policy": {
            **(graph_context["policy"] or {}),
            "text": policy_text,
        },
        "requirement": graph_context["requirement"],
        "retrieval_source": "neo4j_knowledge_graph",
    }
