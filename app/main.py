from fastapi import FastAPI, HTTPException
from app.services.claims_service import get_claim
from app.services.context_service import get_decision_context
from app.graph.queries import get_claim_graph_context
app = FastAPI(
    title="Project M",
    description="Enterprise Knowledge Graph for Healthcare Decision Intelligence",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "project": "Project M",
        "description": "Enterprise Knowledge Graph for Healthcare Decision Intelligence",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
@app.get("/claims/{claim_id}")
def read_claim(claim_id: str):
    claim = get_claim(claim_id)

    if claim is None:
        raise HTTPException(
            status_code=404,
            detail=f"Claim {claim_id} not found"
        )

    return claim
@app.get("/claims/{claim_id}/context")
def read_claim_context(claim_id: str):
    context = get_decision_context(claim_id)

    if context is None:
        raise HTTPException(
            status_code=404,
            detail=f"Claim {claim_id} not found"
        )

    return context
