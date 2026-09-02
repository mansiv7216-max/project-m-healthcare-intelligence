import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from app.services.decision_service import evaluate_claim
from app.services.evidence_service import build_validated_evidence_package


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:7b-instruct"
TEMPERATURE = 0.0

LOG_DIR = Path("experiment_logs")


SYSTEM_PROMPT = (
    "You are a bounded factual responder. "
    "Use ONLY the validated evidence package provided. "
    "You may not change the baseline decision. "
    "You may not invent missing facts. "
    "You may not use external policy knowledge. "
    "If evidence is incomplete, state that the case must be abstained. "
    "Explain the result using only the supplied validated evidence."
)


def run_mode_c_experiment(
    claim_id: str,
    question: str,
    experiment_id: str = "mode_c_run_001",
) -> dict:
    """
    Mode C:
        Neo4j
        -> deterministic claim validation
        -> validated evidence package
        -> bounded local LLM generation
    """

    baseline = evaluate_claim(claim_id)

    evidence_package = build_validated_evidence_package(claim_id)

    user_prompt = (
        "VALIDATED EVIDENCE PACKAGE:\n"
        f"{json.dumps(evidence_package, indent=2)}\n\n"
        "BASELINE DECISION:\n"
        f"{json.dumps(baseline, indent=2)}\n\n"
        f"QUESTION:\n{question}"
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
            "num_predict": 400,
        },
    }

    start_time = time.time()

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120,
    )

    latency = time.time() - start_time

    response.raise_for_status()

    response_data = response.json()
    answer = response_data["message"]["content"]

    artifact = {
        "experiment_id": experiment_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "C_bounded_rag",

        "metadata": {
            "model": MODEL_NAME,
            "temperature": TEMPERATURE,
            "latency_seconds": round(latency, 3),
            "done_reason": response_data.get("done_reason"),
        },

        "inputs": {
            "claim_id": claim_id,
            "question": question,
            "system_prompt": SYSTEM_PROMPT,
            "baseline_decision": baseline,
            "validated_evidence_package": evidence_package,
        },

        "usage": {
            "prompt_eval_count": response_data.get(
                "prompt_eval_count"
            ),
            "eval_count": response_data.get("eval_count"),
            "total_duration_ns": response_data.get(
                "total_duration"
            ),
        },

        "output": {
            "text": answer,
        },
    }

    LOG_DIR.mkdir(exist_ok=True)

    log_path = LOG_DIR / f"{experiment_id}.json"

    with log_path.open("w", encoding="utf-8") as file:
        json.dump(
            artifact,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nExperiment saved: {log_path}")
    print("\nBaseline decision:")
    print(baseline["decision"])
    print("\nGenerated answer:")
    print(answer)

    return artifact
def run_mode_c_assertion_experiment(
    procedure_code: str,
    question: str,
    authority: str | None = None,
    experiment_id: str = "mode_c_assertion_001",
) -> dict:
    """
    Mode C assertion-validation path.

    The deterministic evidence layer decides whether the requested
    relationship is supported before the LLM is allowed to respond.
    """

    from app.services.evidence_service import validate_procedure_assertion

    validation = validate_procedure_assertion(
        procedure_code=procedure_code,
        authority=authority,
    )

    # Hard evidence boundary: unsupported assertions never reach
    # unconstrained generation.
    if not validation["supported"]:
        answer = (
            "I do not have enough validated evidence to determine "
            f"{authority}'s requirement for procedure {procedure_code}."
        )

        artifact = {
            "experiment_id": experiment_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "C_bounded_assertion",
            "metadata": {
                "model": MODEL_NAME,
                "temperature": TEMPERATURE,
                "generation_invoked": False,
            },
            "inputs": {
                "question": question,
                "procedure_code": procedure_code,
                "authority": authority,
            },
            "validation": validation,
            "output": {
                "decision": "ABSTAIN",
                "text": answer,
            },
        }

    else:
        user_prompt = (
            "VALIDATED EVIDENCE:\n"
            f"{json.dumps(validation, indent=2)}\n\n"
            f"QUESTION:\n{question}"
        )

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "stream": False,
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": 400,
            },
        }

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120,
        )

        response.raise_for_status()

        response_data = response.json()
        answer = response_data["message"]["content"]

        artifact = {
            "experiment_id": experiment_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "C_bounded_assertion",
            "metadata": {
                "model": MODEL_NAME,
                "temperature": TEMPERATURE,
                "generation_invoked": True,
            },
            "inputs": {
                "question": question,
                "procedure_code": procedure_code,
                "authority": authority,
            },
            "validation": validation,
            "output": {
                "decision": "ANSWER",
                "text": answer,
            },
        }

    LOG_DIR.mkdir(exist_ok=True)

    log_path = LOG_DIR / f"{experiment_id}.json"

    with log_path.open("w", encoding="utf-8") as file:
        json.dump(artifact, file, indent=2, ensure_ascii=False)

    print(f"\nExperiment saved: {log_path}")
    print(f"Validation: {validation['reason']}")
    print(f"Generation invoked: {artifact['metadata']['generation_invoked']}")
    print(f"\nGenerated answer:\n{artifact['output']['text']}")

    return artifact

if __name__ == "__main__":
    run_mode_c_experiment(
        claim_id="CLM1001",
        question="Should claim CLM1001 be approved?",
        experiment_id="mode_c_run_001",
    )
