import pandas as pd
from pathlib import Path

CLAIMS_FILE = Path("data/claims.csv")


def get_claim(claim_id: str):
    claims = pd.read_csv(CLAIMS_FILE)

    claim = claims[
        claims["claim_id"].str.upper() == claim_id.upper()
    ]

    if claim.empty:
        return None

    return claim.iloc[0].to_dict()
