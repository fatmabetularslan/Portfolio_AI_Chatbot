# rag_system.py

import json
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from google.generativeai.embedding import embed_content


class RAGSystem:
    def __init__(self, filepath: str, model="embedding-001"):
        self.filepath = filepath
        self.model = model
        self.chunks = []
        self.embeddings = []
        self._load_and_embed()

    def _load_and_embed(self):
        """CV içeriğini yükler, parçalara ayırır ve embed eder."""
        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for section_title, content in data.items():
            if isinstance(content, list):
                for entry in content:
                    text = f"{section_title}: {entry}"
                    self.chunks.append(text)
            elif isinstance(content, dict):
                for key, val in content.items():
                    self.chunks.append(f"{section_title} - {key}: {val}")
            else:
                self.chunks.append(f"{section_title}: {content}")

        embeddings = []
        for chunk in self.chunks:
            result = embed_content(
                model=self.model,
                content=chunk
            )
            embeddings.append(np.array(result["embedding"]))
        
        self.embeddings = embeddings

    def search_similar_chunks(self, query: str, top_k: int = 5) -> str:
        """Kullanıcının sorduğu soruya göre en ilgili CV parçalarını getirir."""
        query_result = embed_content(
            model=self.model,
            content=query
        )

        query_vector = np.array(query_result["embedding"])
        similarities = cosine_similarity([query_vector], self.embeddings)[0]

        top_indices = similarities.argsort()[-top_k:][::-1]
        top_chunks = [self.chunks[i] for i in top_indices]

        return "\n".join(top_chunks)
