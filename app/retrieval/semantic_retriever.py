from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


POLICY_FILE = Path("data/policies/imaging_policy.txt")
MODEL_NAME = "all-MiniLM-L6-v2"


class SemanticRetriever:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.chunks = self._load_policy_chunks()
        self.embeddings = self._embed_chunks()

        dimension = self.embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings)

    def _load_policy_chunks(self):
        text = POLICY_FILE.read_text()

        paragraphs = [
            paragraph.strip()
            for paragraph in text.split("\n\n")
            if paragraph.strip()
        ]

        chunks = []

        for index, paragraph in enumerate(paragraphs):
            chunks.append(
                {
                    "chunk_id": f"POL-IMG-001-{index + 1}",
                    "source_id": "POL-IMG-001",
                    "source_type": "policy",
                    "text": paragraph,
                }
            )

        return chunks

    def _embed_chunks(self):
        texts = [chunk["text"] for chunk in self.chunks]

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        return np.asarray(
            embeddings,
            dtype="float32",
        )

    def retrieve(self, query: str, top_k: int = 3):
        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32",
        )

        scores, indices = self.index.search(
            query_embedding,
            top_k,
        )

        results = []

        for rank, (index, score) in enumerate(
            zip(indices[0], scores[0]),
            start=1,
        ):
            if index < 0:
                continue

            chunk = self.chunks[index]

            results.append(
                {
                    "rank": rank,
                    "similarity_score": round(float(score), 4),
                    "chunk_id": chunk["chunk_id"],
                    "source_id": chunk["source_id"],
                    "source_type": chunk["source_type"],
                    "text": chunk["text"],
                }
            )

        return results
