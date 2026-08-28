import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from app.services.decision_service import evaluate_claim
from app.services.evidence_service import (
    build_validated_evidence_package,
    validate_procedure_assertion,
)


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:7b-instruct"
TEMPERATURE = 0.0

LOG_DIR = Path("experiment_logs")


SYSTEM_PROMPT = (
    "You are a bounded factual responder. "
    "Use ONLY the validated evidence provided. "
    "Do not invent missing facts. "
    "Do not use external policy knowledge. "
    "Do not strengthen or weaken the meaning of the validated evidence. "
    "If evidence is incomplete, abstain. "
    "If a requirement is marked CONDITIONAL, preserve that conditionality "
    "and do not describe it as always, automatically, universally, or "
    "unconditionally required."
)


def run_mode_c_experiment(
    claim_id: str,
    question: str,
    experiment_id: str = "mode_c_run_001",
) -> dict:
    """
    Claim-level Mode C.

    Pipeline:
        Neo4j
        -> deterministic claim validation
        -> validated evidence package
        -> bounded local LLM generation
    """

    baseline = evaluate_claim(claim_id)
    evidence_package = build_validated_evidence_package(claim_id)

    if baseline is None or evidence_package is None:
        answer = (
            "I do not have enough validated evidence "
            f"to evaluate claim {claim_id}."
        )

        artifact = {
            "experiment_id": experiment_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "C_bounded_rag",
            "metadata": {
                "model": MODEL_NAME,
                "temperature": TEMPERATURE,
                "generation_invoked": False,
            },
            "inputs": {
                "claim_id": claim_id,
                "question": question,
            },
            "output": {
                "decision": "ABSTAIN",
                "text": answer,
            },
        }

        _save_artifact(artifact, experiment_id)

        print(f"\nExperiment saved: {LOG_DIR / f'{experiment_id}.json'}")
        print("\nGenerated answer:")
        print(answer)

        return artifact

    if not baseline.get("evidence_complete", False):
        answer = (
            "The available evidence is incomplete. "
            f"Claim {claim_id} must be abstained."
        )

        artifact = {
            "experiment_id": experiment_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "C_bounded_rag",
            "metadata": {
                "model": MODEL_NAME,
                "temperature": TEMPERATURE,
                "generation_invoked": False,
            },
            "inputs": {
                "claim_id": claim_id,
                "question": question,
                "baseline_decision": baseline,
                "validated_evidence_package": evidence_package,
            },
            "output": {
                "decision": "ABSTAIN",
                "text": answer,
            },
        }

        _save_artifact(artifact, experiment_id)

        print(f"\nExperiment saved: {LOG_DIR / f'{experiment_id}.json'}")
        print("\nGenerated answer:")
        print(answer)

        return artifact

    user_prompt = (
        "VALIDATED EVIDENCE PACKAGE:\n"
        f"{json.dumps(evidence_package, indent=2)}\n\n"
        "BASELINE DECISION:\n"
        f"{json.dumps(baseline, indent=2)}\n\n"
        f"QUESTION:\n{question}\n\n"
        "The baseline decision is authoritative. "
        "Explain it without changing it."
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
            "generation_invoked": True,
        },

        "inputs": {
            "claim_id": claim_id,
            "question": question,
            "system_prompt": SYSTEM_PROMPT,
            "baseline_decision": baseline,
            "validated_evidence_package": evidence_package,
        },

        "usage": {
            "prompt_eval_count": response_data.get("prompt_eval_count"),
            "eval_count": response_data.get("eval_count"),
            "total_duration_ns": response_data.get("total_duration"),
        },

        "output": {
            "decision": baseline.get("decision"),
            "text": answer,
        },
    }

    _save_artifact(artifact, experiment_id)

    print(f"\nExperiment saved: {LOG_DIR / f'{experiment_id}.json'}")
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
    Assertion-level Mode C.

    The deterministic evidence layer decides whether the requested
    relationship is supported before the LLM is allowed to respond.
    """

    validation = validate_procedure_assertion(
        procedure_code=procedure_code,
        authority=authority,
    )

    if not validation["supported"]:
        if authority:
            answer = (
                "I do not have enough validated evidence to determine "
                f"{authority}'s requirement for procedure {procedure_code}."
            )
        else:
            answer = (
                "I do not have enough validated evidence to determine "
                f"the requirement for procedure {procedure_code}."
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

        _save_artifact(artifact, experiment_id)

        print(f"\nExperiment saved: {LOG_DIR / f'{experiment_id}.json'}")
        print(f"Validation: {validation['reason']}")
        print("Generation invoked: False")
        print(f"\nGenerated answer:\n{answer}")

        return artifact

    authorization_rule = validation.get("authorization_rule") or {}
    rule_type = authorization_rule.get("type")
    condition = authorization_rule.get("condition")

    if rule_type == "CONDITIONAL":
        semantic_instruction = (
            "The validated authorization rule is CONDITIONAL. "
            "You must preserve that wording. "
            "Do not say that authorization is always required, "
            "automatically required, universally required, mandatory "
            "in every case, or unconditional. "
            f"The validated condition is: {condition}"
        )

    elif rule_type == "REQUIRED":
        semantic_instruction = (
            "The validated authorization rule is REQUIRED. "
            "You may state that prior authorization is required."
        )

    else:
        answer = (
            "I do not have enough validated evidence to determine "
            f"the requirement for procedure {procedure_code}."
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

        _save_artifact(artifact, experiment_id)

        return artifact

    user_prompt = (
        "VALIDATED EVIDENCE:\n"
        f"{json.dumps(validation, indent=2)}\n\n"
        "SEMANTIC CONSTRAINT:\n"
        f"{semantic_instruction}\n\n"
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
        "mode": "C_bounded_assertion",

        "metadata": {
            "model": MODEL_NAME,
            "temperature": TEMPERATURE,
            "generation_invoked": True,
            "latency_seconds": round(latency, 3),
            "done_reason": response_data.get("done_reason"),
        },

        "inputs": {
            "question": question,
            "procedure_code": procedure_code,
            "authority": authority,
            "semantic_instruction": semantic_instruction,
        },

        "validation": validation,

        "usage": {
            "prompt_eval_count": response_data.get("prompt_eval_count"),
            "eval_count": response_data.get("eval_count"),
            "total_duration_ns": response_data.get("total_duration"),
        },

        "output": {
            "decision": "ANSWER",
            "text": answer,
        },
    }

    _save_artifact(artifact, experiment_id)

    print(f"\nExperiment saved: {LOG_DIR / f'{experiment_id}.json'}")
    print(f"Validation: {validation['reason']}")
    print("Generation invoked: True")
    print(f"\nGenerated answer:\n{answer}")

    return artifact


def _save_artifact(
    artifact: dict,
    experiment_id: str,
) -> None:
    LOG_DIR.mkdir(exist_ok=True)

    log_path = LOG_DIR / f"{experiment_id}.json"

    with log_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            artifact,
            file,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    run_mode_c_experiment(
        claim_id="CLM1001",
        question="Should claim CLM1001 be approved?",
        experiment_id="mode_c_run_001",
    )
