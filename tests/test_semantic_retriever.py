from app.retrieval.semantic_retriever import SemanticRetriever


def test_semantic_retriever_returns_ranked_policy_chunks():
    retriever = SemanticRetriever()

    results = retriever.retrieve(
        "Does procedure 70553 require prior authorization?",
        top_k=3,
    )

    assert len(results) == 3

    assert results[0]["rank"] == 1
    assert results[1]["rank"] == 2
    assert results[2]["rank"] == 3

    for result in results:
        assert "similarity_score" in result
        assert "chunk_id" in result
        assert "source_id" in result
        assert "text" in result


def test_semantic_retrieval_can_return_related_but_not_exact_evidence():
    retriever = SemanticRetriever()

    results = retriever.retrieve(
        "Does procedure 70553 require prior authorization?",
        top_k=3,
    )

    retrieved_text = " ".join(
        result["text"] for result in results
    )

    # Exact evidence should be present somewhere in retrieved context.
    assert "70553" in retrieved_text

    # Semantically related evidence may also be retrieved.
    # This intentionally documents the limitation of semantic-only retrieval.
    assert "70551" in retrieved_text
