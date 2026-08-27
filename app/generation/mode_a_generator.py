import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from app.retrieval.semantic_retriever import SemanticRetriever


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:7b-instruct"
TEMPERATURE = 0.0
TOP_K = 3

LOG_DIR = Path("experiment_logs")


SYSTEM_PROMPT = (
    "You are an exact factual responder. "
    "Answer the user's question using ONLY the provided context. "
    "If the context does not contain enough information to answer, state "
    "'I do not have enough information.' "
    "Do not use external knowledge."
)


def run_mode_a_experiment(
    query: str,
    experiment_id: str = "mode_a_run_001",
) -> dict:
    """
    Mode A: Conventional Semantic RAG baseline.

    Pipeline:
        Query
        -> MiniLM embeddings
        -> FAISS Top-K retrieval
        -> Local Ollama LLM generation

    Intentionally excluded:
        - Neo4j
        - deterministic decision service
        - evidence validation
        - graph traversal
        - reranking
    """

    retriever = SemanticRetriever()

    retrieved_chunks = retriever.retrieve(
        query=query,
        top_k=TOP_K,
    )

    context_parts = []

    for chunk in retrieved_chunks:
        context_parts.append(
            f"[{chunk['chunk_id']}]\n"
            f"Similarity Score: {chunk['similarity_score']}\n"
            f"{chunk['text']}"
        )

    context_str = "\n\n".join(context_parts)

    user_prompt = (
        f"Context:\n{context_str}\n\n"
        f"Question: {query}"
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
        "mode": "A_semantic_rag",

        "metadata": {
            "model": MODEL_NAME,
            "temperature": TEMPERATURE,
            "top_k": TOP_K,
            "latency_seconds": round(latency, 3),
            "ollama_created_at": response_data.get("created_at"),
            "done_reason": response_data.get("done_reason"),
        },

        "inputs": {
            "query": query,
            "system_prompt": SYSTEM_PROMPT,
            "retrieved_chunks": retrieved_chunks,
        },

        "usage": {
            "prompt_eval_count": response_data.get("prompt_eval_count"),
            "eval_count": response_data.get("eval_count"),
            "total_duration_ns": response_data.get("total_duration"),
            "load_duration_ns": response_data.get("load_duration"),
            "prompt_eval_duration_ns": response_data.get(
                "prompt_eval_duration"
            ),
            "eval_duration_ns": response_data.get("eval_duration"),
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
    print("\nGenerated answer:")
    print(answer)

    return artifact


if __name__ == "__main__":
    run_mode_a_experiment(
        query="Does procedure 70553 require prior authorization?",
        experiment_id="mode_a_run_001",
    )
