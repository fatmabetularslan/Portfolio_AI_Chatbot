# rag_system.py

import json, numpy as np
import streamlit as st
import pickle
import os
from sklearn.metrics.pairwise import cosine_similarity
from google.generativeai.embedding import embed_content

@st.cache_resource(show_spinner=False)
def embed_cached(txt: str):
    """Query için embedding hesapla (sadece kullanıcı sorguları için)"""
    try:
        return np.asarray(embed_content(model="models/embedding-001", content=txt)["embedding"])
    except Exception as e:
        st.warning(f"Query embedding hatası: {str(e)}")
        return np.zeros(768)  # Fallback

@st.cache_resource(show_spinner=False)
def load_cv_index(cv_path):
    return RAGSystem(cv_path)

class RAGSystem:
    def __init__(self, cv_path: str):
        # Pre-computed embedding dosyasını kontrol et
        embedding_file = "embeddings_data.pkl"
        
        if os.path.exists(embedding_file):
            # Pre-computed embedding'leri yükle
            with open(embedding_file, 'rb') as f:
                data = pickle.load(f)
            
            self.cv_json = data['cv_json']
            self.chunks = data['chunks']
            self.index = data['embeddings']
            self.alias = data['alias']
            
        else:
            # Fallback: Eski yöntem (API kullanarak)
            self.cv_json = json.load(open(cv_path, encoding="utf-8"))
            self.chunks = self._build_chunks(self.cv_json)
            
            # Progress bar ile embedding'leri hesapla
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            embeddings = []
            for i, chunk in enumerate(self.chunks):
                status_text.text(f"Embedding hesaplanıyor... ({i+1}/{len(self.chunks)})")
                embeddings.append(embed_cached(chunk))
                progress_bar.progress((i + 1) / len(self.chunks))
            
            status_text.text("Embedding'ler hazır!")
            progress_bar.empty()
            status_text.empty()
            
            self.index = np.vstack(embeddings)
            self.alias = {
                "deneyim": "experience", "tecrübe": "experience",
                "eğitim": "education",  "projeler": "projects",
                "ödüller": "awards",    "yetenek": "skills",
            }
        
        self.full_text = json.dumps(self.cv_json, ensure_ascii=False, indent=2)

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
        """CV verilerini chunk'lara böler (generate_embeddings.py ile aynı mantık)"""
        chunks = []
        
        for section, content in cv_json.items():
            if section in ['name', 'title', 'location', 'email', 'phone']:
                # Kişisel bilgileri tek chunk'ta birleştir
                if section == 'name':
                    personal_info = f"Kişisel Bilgiler: {content}"
                    if 'title' in cv_json:
                        personal_info += f" - {cv_json['title']}"
                    if 'location' in cv_json:
                        personal_info += f" - {cv_json['location']}"
                    chunks.append(personal_info)
            elif section == 'profile':
                chunks.append(f"Profil: {content}")
            elif section == 'education':
                # Eğitim bilgilerini tek chunk'ta birleştir
                edu_text = "Eğitim: "
                for edu in content:
                    edu_text += f"{edu['institution']} - {edu['degree']} ({edu['years']}); "
                chunks.append(edu_text.strip())
            elif section == 'experience':
                # Her deneyimi ayrı chunk yap
                for exp in content:
                    exp_text = f"Deneyim: {exp['title']} at {exp['company']} ({exp['duration']}) - {exp['description']}"
                    chunks.append(exp_text)
            elif section == 'skills':
                # Yetenekleri kategorilere göre grupla
                for category, skills in content.items():
                    skills_text = f"Yetenekler - {category}: {', '.join(skills)}"
                    chunks.append(skills_text)
            elif section == 'projects':
                # Her projeyi ayrı chunk yap
                for project in content:
                    if isinstance(project, dict):
                        proj_text = f"Proje: {project.get('name', '')} - {project.get('description', '')}"
                        chunks.append(proj_text)
            elif section == 'links':
                # Linkleri tek chunk'ta birleştir
                links_text = "Linkler: " + " | ".join([f"{k}: {v}" for k, v in content.items()])
                chunks.append(links_text)
            else:
                # Diğer bölümler için genel yaklaşım
                if isinstance(content, (str, int, float)):
                    chunks.append(f"{section}: {content}")
        
        return chunks
