import csv
import json
from pathlib import Path

from app.generation.mode_a_generator import run_mode_a_experiment
from app.generation.mode_b_generator import run_mode_b_experiment
from app.generation.mode_c_generator import run_mode_c_assertion_experiment


DATASET_FILE = Path("data/evaluation/rag_evaluation_cases.json")
RESULT_DIR = Path("experiment_logs/comparison")

ABSTENTION_MARKERS = [
    "do not have enough",
    "not enough information",
    "not enough validated evidence",
    "cannot determine",
    "unable to determine",
    "insufficient evidence",
    "insufficient information",
]


def is_abstention(text: str) -> bool:
    text = text.lower()

    return any(
        marker in text
        for marker in ABSTENTION_MARKERS
    )


def score_output(case: dict, text: str) -> dict:
    """
    Deterministic evaluation.

    We deliberately avoid using another LLM as the evaluator.
    """

    expected_behavior = case["expected_behavior"]

    if expected_behavior == "ABSTAIN":
        passed = is_abstention(text)

        return {
            "passed": passed,
            "observed_behavior": (
                "ABSTAIN"
                if passed
                else "ANSWER"
            ),
            "required_terms_present": None,
        }

    required_terms = case.get("required_terms", [])

    text_lower = text.lower()

    required_terms_present = all(
        term.lower() in text_lower
        for term in required_terms
    )

    passed = (
        not is_abstention(text)
        and required_terms_present
    )

    return {
        "passed": passed,
        "observed_behavior": (
            "ABSTAIN"
            if is_abstention(text)
            else "ANSWER"
        ),
        "required_terms_present": required_terms_present,
    }


def run_case(case: dict) -> dict:
    case_id = case["case_id"]
    question = case["question"]

    print("\n" + "=" * 80)
    print(
        f"{case_id} | "
        f"{case['category']} | "
        f"{case['expected_behavior']}"
    )
    print(question)
    print("=" * 80)

    mode_a = run_mode_a_experiment(
        query=question,
        experiment_id=f"benchmark_{case_id.lower()}_mode_a",
    )

    mode_b = run_mode_b_experiment(
        query=question,
        experiment_id=f"benchmark_{case_id.lower()}_mode_b",
    )

    mode_c = run_mode_c_assertion_experiment(
        procedure_code=case["procedure_code"],
        question=question,
        authority=case.get("authority"),
        experiment_id=f"benchmark_{case_id.lower()}_mode_c",
    )

    outputs = {
        "A": mode_a["output"]["text"],
        "B": mode_b["output"]["text"],
        "C": mode_c["output"]["text"],
    }

    scores = {
        mode: score_output(case, text)
        for mode, text in outputs.items()
    }

    return {
        "case": case,
        "outputs": outputs,
        "scores": scores,
    }


def calculate_metrics(results: list[dict]) -> dict:
    metrics = {}

    for mode in ["A", "B", "C"]:
        total = len(results)

        passed = sum(
            1
            for result in results
            if result["scores"][mode]["passed"]
        )

        abstention_cases = [
            result
            for result in results
            if result["case"]["expected_behavior"] == "ABSTAIN"
        ]

        correct_abstentions = sum(
            1
            for result in abstention_cases
            if result["scores"][mode]["observed_behavior"] == "ABSTAIN"
        )

        answer_cases = [
            result
            for result in results
            if result["case"]["expected_behavior"] == "ANSWER"
        ]

        correct_answers = sum(
            1
            for result in answer_cases
            if result["scores"][mode]["passed"]
        )

        unsupported_answers = sum(
            1
            for result in abstention_cases
            if result["scores"][mode]["observed_behavior"] == "ANSWER"
        )

        metrics[mode] = {
            "total_cases": total,

            "overall_pass_count": passed,

            "overall_accuracy": round(
                passed / total,
                4,
            ),

            "answer_accuracy": round(
                correct_answers / len(answer_cases),
                4,
            ) if answer_cases else None,

            "abstention_accuracy": round(
                correct_abstentions / len(abstention_cases),
                4,
            ) if abstention_cases else None,

            "unsupported_answer_count": unsupported_answers,

            "unsupported_claim_rate": round(
                unsupported_answers / len(abstention_cases),
                4,
            ) if abstention_cases else None,
        }

    return metrics


def save_results(
    results: list[dict],
    metrics: dict,
):
    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = RESULT_DIR / "benchmark_results.json"

    json_path.write_text(
        json.dumps(
            {
                "results": results,
                "metrics": metrics,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    csv_path = RESULT_DIR / "benchmark_summary.csv"

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            [
                "case_id",
                "category",
                "expected_behavior",
                "mode_a_pass",
                "mode_b_pass",
                "mode_c_pass",
                "mode_a_behavior",
                "mode_b_behavior",
                "mode_c_behavior",
            ]
        )

        for result in results:
            case = result["case"]

            writer.writerow(
                [
                    case["case_id"],
                    case["category"],
                    case["expected_behavior"],

                    result["scores"]["A"]["passed"],
                    result["scores"]["B"]["passed"],
                    result["scores"]["C"]["passed"],

                    result["scores"]["A"]["observed_behavior"],
                    result["scores"]["B"]["observed_behavior"],
                    result["scores"]["C"]["observed_behavior"],
                ]
            )

    print(f"\nJSON results: {json_path}")
    print(f"CSV summary: {csv_path}")


def print_metrics(metrics: dict):
    print("\n")
    print("=" * 80)
    print("FINAL BENCHMARK METRICS")
    print("=" * 80)

    for mode in ["A", "B", "C"]:
        data = metrics[mode]

        print(f"\nMODE {mode}")
        print(
            f"Overall accuracy: "
            f"{data['overall_accuracy']:.1%}"
        )
        print(
            f"Answer accuracy: "
            f"{data['answer_accuracy']:.1%}"
        )
        print(
            f"Abstention accuracy: "
            f"{data['abstention_accuracy']:.1%}"
        )
        print(
            f"Unsupported claim rate: "
            f"{data['unsupported_claim_rate']:.1%}"
        )
        print(
            f"Unsupported answers: "
            f"{data['unsupported_answer_count']}"
        )


def main():
    cases = json.loads(
        DATASET_FILE.read_text(
            encoding="utf-8"
        )
    )

    print(
        f"\nRunning {len(cases)} cases "
        "across Modes A, B and C..."
    )

    results = [
        run_case(case)
        for case in cases
    ]

    metrics = calculate_metrics(results)

    save_results(
        results,
        metrics,
    )

    print_metrics(metrics)


if __name__ == "__main__":
    main()
