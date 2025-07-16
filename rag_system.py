# rag_system.py

import json, numpy as np
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity
from google.generativeai.embedding import embed_content

@st.cache_resource(show_spinner=False)
def embed_cached(txt: str):
    return np.asarray(embed_content(model="models/embedding-001", content=txt)["embedding"])

@st.cache_resource(show_spinner=False)
def load_cv_index(cv_path):
    return RAGSystem(cv_path)

class RAGSystem:
    def __init__(self, cv_path: str):
        self.cv_json   = json.load(open(cv_path, encoding="utf-8"))
        self.chunks    = self._build_chunks(self.cv_json)
        # tüm embedding’leri **bir kez** hesapla ve RAM’de tut
        self.index     = np.vstack([embed_cached(c) for c in self.chunks])
        self.full_text = json.dumps(self.cv_json, ensure_ascii=False, indent=2)
        self.alias = {  # TR-EN eşleştirme
            "deneyim": "experience", "tecrübe": "experience",
            "eğitim": "education",  "projeler": "projects",
            "ödüller": "awards",    "yetenek": "skills",
        }

    # — Kullanıcı sorgusu
    def search_similar_chunks(self, query: str, top_k: int = 5):
        key = query.lower().strip()
        q_vec = embed_cached(key)
        sims = cosine_similarity([q_vec], self.index)[0]
        top_idx = sims.argsort()[-top_k:][::-1]
        top_chunks = [self.chunks[i] for i in top_idx]
        return top_chunks or [json.dumps(self.cv_json, ensure_ascii=False, indent=2)]  # fall-back

    # —— yardımcılar (_build_chunks & _build_embed_index) aynı kalır


    def _build_chunks(self, cv_json):
        # Example: flatten all text fields into a list of strings
        chunks = []
        for section, content in cv_json.items():
            if isinstance(content, list):
                for item in content:
                    chunks.append(f"{section}: {item}")
            elif isinstance(content, dict):
                for k, v in content.items():
                    chunks.append(f"{section} - {k}: {v}")
            else:
                chunks.append(f"{section}: {content}")
        return chunks
