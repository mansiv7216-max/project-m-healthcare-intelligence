import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

CLAIMS_FILE = DATA_DIR / "claims.csv"
MEMBERS_FILE = DATA_DIR / "members.csv"
PROVIDERS_FILE = DATA_DIR / "providers.csv"
POLICY_FILE = DATA_DIR / "policies" / "imaging_policy.txt"


def get_decision_context(claim_id: str):
    claims = pd.read_csv(CLAIMS_FILE)
    members = pd.read_csv(MEMBERS_FILE)
    providers = pd.read_csv(PROVIDERS_FILE)

    claim_rows = claims[
        claims["claim_id"].str.upper() == claim_id.upper()
    ]

    if claim_rows.empty:
        return None

    claim = claim_rows.iloc[0]

    member_rows = members[
        members["member_id"] == claim["member_id"]
    ]

    provider_rows = providers[
        providers["provider_id"] == claim["provider_id"]
    ]

    member = (
        member_rows.iloc[0].to_dict()
        if not member_rows.empty
        else None
    )

    provider = (
        provider_rows.iloc[0].to_dict()
        if not provider_rows.empty
        else None
    )

    policy_text = POLICY_FILE.read_text()

    return {
        "claim": claim.to_dict(),
        "member": member,
        "provider": provider,
        "policy": {
            "policy_id": "POL-IMG-001",
            "title": "Advanced Imaging Coverage Policy",
            "text": policy_text
        }
    }
