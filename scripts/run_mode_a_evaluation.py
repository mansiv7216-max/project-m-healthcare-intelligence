import json
from pathlib import Path

from app.generation.mode_a_generator import run_mode_a_experiment


EVALUATION_FILE = Path("data/evaluation/rag_evaluation_cases.json")


def main():
    cases = json.loads(
        EVALUATION_FILE.read_text(encoding="utf-8")
    )

    print(f"Running {len(cases)} Mode A evaluation cases...\n")

    for case in cases:
        case_id = case["case_id"]
        question = case["question"]

        print("=" * 70)
        print(f"{case_id}: {question}")
        print("=" * 70)

        artifact = run_mode_a_experiment(
            query=question,
            experiment_id=f"mode_a_{case_id.lower()}",
        )

        print("\nExpected behavior:", case["expected_behavior"])
        print("Expected fact:", case["expected_fact"])
        print("Actual answer:", artifact["output"]["text"])
        print()

    print("Mode A evaluation complete.")


if __name__ == "__main__":
    main()
