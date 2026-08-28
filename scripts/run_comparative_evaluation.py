from app.generation.mode_a_generator import run_mode_a_experiment
from app.generation.mode_b_generator import run_mode_b_experiment
from app.generation.mode_c_generator import run_mode_c_assertion_experiment


EVALUATION_CASES = [
    {
        "id": "exact_70553",
        "procedure_code": "70553",
        "authority": None,
        "question": "Does procedure 70553 require prior authorization?",
    },
    {
        "id": "authority_70553",
        "procedure_code": "70553",
        "authority": "Medicare",
        "question": "What does Medicare require for procedure 70553?",
    },
]


def main():
    results = []

    for case in EVALUATION_CASES:
        print("\n" + "=" * 70)
        print(f"CASE: {case['id']}")
        print(f"QUESTION: {case['question']}")
        print("=" * 70)

        mode_a = run_mode_a_experiment(
            query=case["question"],
            experiment_id=f"comparison_{case['id']}_mode_a",
        )

        mode_b = run_mode_b_experiment(
            query=case["question"],
            experiment_id=f"comparison_{case['id']}_mode_b",
        )

        mode_c = run_mode_c_assertion_experiment(
            procedure_code=case["procedure_code"],
            question=case["question"],
            authority=case["authority"],
            experiment_id=f"comparison_{case['id']}_mode_c",
        )

        results.append(
            {
                "case": case,
                "mode_a": mode_a,
                "mode_b": mode_b,
                "mode_c": mode_c,
            }
        )

    print("\n" + "=" * 70)
    print("A / B / C COMPARATIVE EVALUATION COMPLETE")
    print("=" * 70)

    for result in results:
        print(f"\nCASE: {result['case']['id']}")

        print("\nMode A:")
        print(result["mode_a"]["output"]["text"])

        print("\nMode B:")
        print(result["mode_b"]["output"]["text"])

        print("\nMode C:")
        print(result["mode_c"]["output"]["text"])


if __name__ == "__main__":
    main()
