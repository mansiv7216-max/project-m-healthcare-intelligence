import pandas as pd
from app.graph.connection import Neo4jConnection


# Load synthetic Project M healthcare data
claims = pd.read_csv("data/claims.csv")
members = pd.read_csv("data/members.csv")
providers = pd.read_csv("data/providers.csv")

db = Neo4jConnection()


def seed_graph():
    with db.driver.session(database=db.database) as session:

        # -------------------------
        # MEMBER NODES
        # -------------------------
        for _, member in members.iterrows():
            session.run(
                """
                MERGE (m:Member {member_id: $member_id})
                SET m.plan_type = $plan_type,
                    m.state = $state,
                    m.eligibility_status = $eligibility_status
                """,
                member_id=member["member_id"],
                plan_type=member["plan_type"],
                state=member["state"],
                eligibility_status=member["eligibility_status"],
            )

        # -------------------------
        # PROVIDER NODES
        # -------------------------
        for _, provider in providers.iterrows():
            session.run(
                """
                MERGE (p:Provider {provider_id: $provider_id})
                SET p.provider_name = $provider_name,
                    p.provider_type = $provider_type,
                    p.state = $state,
                    p.in_network = $in_network
                """,
                provider_id=provider["provider_id"],
                provider_name=provider["provider_name"],
                provider_type=provider["provider_type"],
                state=provider["state"],
                in_network=bool(provider["in_network"]),
            )

        # -------------------------
        # CLAIM + RELATIONSHIPS
        # -------------------------
        for _, claim in claims.iterrows():
            session.run(
                """
                MERGE (c:Claim {claim_id: $claim_id})
                SET c.amount = $amount,
                    c.status = $status,
                    c.prior_authorization = $prior_authorization

                WITH c

                MATCH (m:Member {member_id: $member_id})
                MATCH (p:Provider {provider_id: $provider_id})

                MERGE (m)-[:FILED]->(c)
                MERGE (c)-[:PERFORMED_BY]->(p)

                MERGE (proc:Procedure {code: $procedure_code})
                MERGE (c)-[:USES_PROCEDURE]->(proc)

                MERGE (diag:Diagnosis {code: $diagnosis_code})
                MERGE (c)-[:HAS_DIAGNOSIS]->(diag)
                """,
                claim_id=claim["claim_id"],
                member_id=claim["member_id"],
                provider_id=claim["provider_id"],
                procedure_code=str(claim["procedure_code"]),
                diagnosis_code=claim["diagnosis_code"],
                amount=float(claim["amount"]),
                prior_authorization=bool(claim["prior_authorization"]),
                status=claim["status"],
            )

        # -------------------------
        # POLICY KNOWLEDGE
        # -------------------------
        session.run(
            """
            MERGE (policy:Policy {policy_id: 'POL-IMG-001'})
            SET policy.title = 'Advanced Imaging Coverage Policy'

            MERGE (req:Requirement {name: 'Prior Authorization'})

            MERGE (policy)-[:REQUIRES]->(req)

            WITH policy

            MATCH (proc:Procedure)
            WHERE proc.code IN ['70553', '70551']

            MERGE (proc)-[:GOVERNED_BY]->(policy)
            """
        )


if __name__ == "__main__":
    db.verify()

    seed_graph()

    print("Neo4j graph seeded successfully.")

    db.close()
