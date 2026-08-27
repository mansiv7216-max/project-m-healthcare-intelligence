from app.graph.connection import Neo4jConnection

db = Neo4jConnection()


def get_claim_graph_context(claim_id: str):
    query = """
    MATCH (c:Claim {claim_id: $claim_id})
    OPTIONAL MATCH (m:Member)-[:FILED]->(c)
    OPTIONAL MATCH (c)-[:PERFORMED_BY]->(p:Provider)
    OPTIONAL MATCH (c)-[:USES_PROCEDURE]->(proc:Procedure)
    OPTIONAL MATCH (c)-[:HAS_DIAGNOSIS]->(d:Diagnosis)
    OPTIONAL MATCH (proc)-[:GOVERNED_BY]->(policy:Policy)
    OPTIONAL MATCH (policy)-[:REQUIRES]->(req:Requirement)

    RETURN
        c,
        m,
        p,
        proc,
        d,
        policy,
        req
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(query, claim_id=claim_id)
        record = result.single()

        if record is None:
            return None

        return {
            "claim": dict(record["c"]) if record["c"] else None,
            "member": dict(record["m"]) if record["m"] else None,
            "provider": dict(record["p"]) if record["p"] else None,
            "procedure": dict(record["proc"]) if record["proc"] else None,
            "diagnosis": dict(record["d"]) if record["d"] else None,
            "policy": dict(record["policy"]) if record["policy"] else None,
            "requirement": dict(record["req"]) if record["req"] else None,
        }
def get_procedure_graph_context(procedure_code: str):
    """
    Retrieve structured policy relationships for a procedure code.

    Used by Mode B graph-grounded RAG.
    This performs graph retrieval only and does not apply
    deterministic validation or decision rules.
    """

    query = """
    MATCH (proc:Procedure {code: $procedure_code})
    OPTIONAL MATCH (proc)-[:GOVERNED_BY]->(policy:Policy)
    OPTIONAL MATCH (policy)-[:REQUIRES]->(req:Requirement)

    RETURN
        proc,
        policy,
        req
    """

    with db.driver.session(database=db.database) as session:
        result = session.run(
            query,
            procedure_code=procedure_code,
        )

        record = result.single()

        if record is None:
            return None

        return {
            "procedure": (
                dict(record["proc"])
                if record["proc"]
                else None
            ),
            "policy": (
                dict(record["policy"])
                if record["policy"]
                else None
            ),
            "requirement": (
                dict(record["req"])
                if record["req"]
                else None
            ),
        }
