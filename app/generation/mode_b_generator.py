import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from app.graph.queries import get_procedure_graph_context
from app.retrieval.semantic_retriever import SemanticRetriever


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:7b-instruct"
TEMPERATURE = 0.0
TOP_K = 3

LOG_DIR = Path("experiment_logs")


SYSTEM_PROMPT = (
    "You are an exact factual responder. "
    "Answer the user's question using ONLY the provided context. "
    "The context may contain semantic document evidence and structured "
    "knowledge graph evidence. "
    "If the context does not contain enough information to answer, state "
    "'I do not have enough information.' "
    "Do not use external knowledge."
)


def extract_procedure_codes(query: str) -> list[str]:
    """
    Extract five-digit procedure codes appearing in the question.
    """
    return re.findall(r"\b\d{5}\b", query)


def run_mode_b_experiment(
    query: str,
    experiment_id: str = "mode_b_run_001",
) -> dict:
    """
    Mode B: Semantic RAG + Knowledge Graph grounding.

    Includes:
        - MiniLM semantic retrieval
        - FAISS Top-K retrieval
        - Neo4j procedure/policy relationships
        - Local Qwen generation

    Intentionally excludes:
        - deterministic decision service
        - validated evidence package
        - evidence filtering
        - bounded decision enforcement
    """

    # Semantic retrieval: identical to Mode A
    retriever = SemanticRetriever()

    retrieved_chunks = retriever.retrieve(
        query=query,
        top_k=TOP_K,
    )

    semantic_parts = []

    for chunk in retrieved_chunks:
        semantic_parts.append(
            f"[{chunk['chunk_id']}]\n"
            f"Similarity Score: {chunk['similarity_score']}\n"
            f"{chunk['text']}"
        )

    semantic_context = "\n\n".join(semantic_parts)

    # Graph retrieval
    procedure_codes = extract_procedure_codes(query)

    graph_results = {}

    for code in procedure_codes:
        graph_results[code] = get_procedure_graph_context(code)

    graph_context = json.dumps(
        graph_results,
        indent=2,
        ensure_ascii=False,
    )

    user_prompt = (
        "SEMANTIC DOCUMENT CONTEXT:\n"
        f"{semantic_context}\n\n"
        "STRUCTURED KNOWLEDGE GRAPH CONTEXT:\n"
        f"{graph_context}\n\n"
        f"QUESTION:\n{query}"
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
        "mode": "B_graph_grounded_rag",

        "metadata": {
            "model": MODEL_NAME,
            "temperature": TEMPERATURE,
            "top_k": TOP_K,
            "latency_seconds": round(latency, 3),
            "done_reason": response_data.get("done_reason"),
        },

        "inputs": {
            "query": query,
            "system_prompt": SYSTEM_PROMPT,
            "procedure_codes": procedure_codes,
            "retrieved_chunks": retrieved_chunks,
            "graph_context": graph_results,
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
    print("\nGraph context:")
    print(graph_context)
    print("\nGenerated answer:")
    print(answer)

    return artifact


if __name__ == "__main__":
    run_mode_b_experiment(
        query="Does procedure 70553 require prior authorization?",
        experiment_id="mode_b_run_001",
    )
