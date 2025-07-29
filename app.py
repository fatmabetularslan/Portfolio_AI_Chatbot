import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Fatma Betül Arslan", page_icon="🤖", layout="centered")

import json
from tools.tool_definitions import ToolDefinitions
import modern_chatbot
from common_css import LIGHT_CSS, DARK_CSS
from rag_system import load_cv_index
from pathlib import Path
PDF_PATH = "assets/Fatma-Betül-ARSLAN-cv.pdf"

# --- Modern Language Toggle Bar (flag icons, unified, no columns/buttons) ---
def language_and_theme_toggle():
    lang = st.session_state.get("lang", "tr")
    dark = st.session_state.get("dark_mode", False)
    page = st.session_state.get("page", "home")
    st.markdown("""
    <style>
    .top-right-toggles {
        position: fixed;
        top: 64px;
        right: 32px;
        display: flex;
        gap: 16px;
        z-index: 1000;
        background: rgba(255,255,255,0.85);
        box-shadow: 0 4px 24px 0 rgba(49,130,206,0.10), 0 0 16px 2px #fff2;
        border-radius: 32px;
        padding: 8px 18px;
        align-items: center;
    }
    .toggle-btn {
        width: 38px;
        height: 38px;
        font-size: 1.1em;
        border-radius: 18px;
        border: none;
        background: none;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: background 0.18s, color 0.18s;
        color: #222;
        margin: 0 2px;
    }
    .toggle-btn.selected {
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
        color: #fff;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f'''
    <div class="top-right-toggles">
      <form method="GET" style="display: flex; gap: 8px; align-items: center; margin:0;">
        <button class="toggle-btn{' selected' if lang == 'en' else ''}" name="setlang" value="en" type="submit">EN</button>
        <button class="toggle-btn{' selected' if lang == 'tr' else ''}" name="setlang" value="tr" type="submit">TR</button>
        <button class="toggle-btn{' selected' if not dark else ''}" name="settheme" value="light" type="submit">🌞</button>
        <button class="toggle-btn{' selected' if dark else ''}" name="settheme" value="dark" type="submit">🌙</button>
      </form>
    </div>
    ''', unsafe_allow_html=True)

    qp = st.query_params
    rerun_needed = False
    if qp.get("setlang"):
        st.session_state["lang"] = qp["setlang"]
        rerun_needed = True
    if qp.get("settheme"):
        st.session_state["dark_mode"] = qp["settheme"] == "dark"
        rerun_needed = True
    if rerun_needed:
        st.session_state["page"] = page  # Mevcut sayfada kal!
        qp.clear()
        st.rerun()

# --- State ve yardımcı fonksiyonlar ---
if "lang" not in st.session_state:
    st.session_state["lang"] = "tr"
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "home"

lang = st.session_state["lang"]

# Tema bazlı ek CSS
st.markdown(f"<style>{DARK_CSS if st.session_state.dark_mode else LIGHT_CSS}</style>", unsafe_allow_html=True)

# Modern butonlar için CSS
st.markdown("""
<style>
div.stButton > button {
    width: 420px !important;
    min-width: 320px;
    font-size: 1.45em;
    padding: 22px 0;
    border-radius: 18px;
    margin-bottom: 0px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    background: linear-gradient(90deg, #1D3557, #457B9D);
    color: #fff !important;
    border: none;
    box-shadow: 0 4px 16px #2563eb33;
    transition: all 0.2s;
}
div.stButton > button:last-child {
    background: linear-gradient(90deg, #3A86FF, #219EBC);
}
</style>
""", unsafe_allow_html=True)

# Header ve subheader için CSS
st.markdown("""
<style>
.big-header {
    font-size: 2.7em !important;
    font-weight: 800 !important;
    text-align: center !important;
    margin-bottom: 0.2em !important;
}
.big-subheader {
    font-size: 1.35em !important;
    font-weight: 500 !important;
    text-align: center !important;
    margin-bottom: 1.2em !important;
}
</style>
""", unsafe_allow_html=True)

# --- Sayfa yönlendirme ---
tag = 'betül-cv.json'
rag = load_cv_index(tag)

if st.session_state.page == "chat":
    tool_def_obj = ToolDefinitions()
    tool_def_obj.initialize_job_analyzer(
        client=None,
        cv_data=json.load(open(tag, encoding="utf-8")),
        rag_system=rag
    )
    modern_chatbot.run(
        tool_def = tool_def_obj,
        rag     = rag,
        cv_json = json.load(open(tag, encoding="utf-8"))
    )
    st.stop()

# --- Ana sayfa metinleri ---
TEXT = {
    "tr": {
        "header": "👋 Merhaba! Ben Fatma Betül'ün AI Portföy Asistanıyım",
        "sub"   : "CV, projeler, sosyal medya içerikleri ve iş başvurularında size yardımcı olurum.",
        "cv"    : "📂 CV'yi Gör",
        "chat"  : "Sohbete Başla",
    },
    "en": {
        "header": "👋 Hi! I'm Fatma Betül's AI Portfolio Assistant",
        "sub"   : "I can help you with CV, projects, social media and job applications.",
        "cv"    : "📂 View CV",
        "chat"  : "Start Chat",
    },
}
lang_text = TEXT[ st.session_state.lang ]

# --- Main content ---

# 1. Toggle bar (dil/tema)
language_and_theme_toggle()

# 2. Header
st.markdown(f'<div class="big-header">{lang_text["header"]}</div>', unsafe_allow_html=True)

# 3. Subheader
st.markdown(f'<div class="big-subheader">{lang_text["sub"]}</div>', unsafe_allow_html=True)

# 4. Sosyal medya linkleri
st.markdown("""
<div class="social-links" style="display: flex; justify-content: center; gap: 32px; margin: 18px 0 8px 0; flex-wrap: wrap;">
  <a href="https://www.linkedin.com/in/fatma-betül-arslan" target="_blank" style="text-decoration: none; font-size: 1.15em; display: flex; align-items: center; gap: 6px;">
    <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg" alt="LinkedIn" style="width:22px; height:22px; vertical-align:middle;"> LinkedIn
  </a>
  <a href="https://github.com/fatmabetularslan" target="_blank" style="text-decoration: none; font-size: 1.15em; display: flex; align-items: center; gap: 6px;">
    <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg" alt="GitHub" style="width:22px; height:22px; vertical-align:middle;"> GitHub
  </a>
  <a href="https://medium.com/@betularsln01" target="_blank" style="text-decoration: none; font-size: 1.15em; display: flex; align-items: center; gap: 6px;">
    <img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/medium.svg" alt="Medium" style="width:22px; height:22px; vertical-align:middle;"> Medium
  </a>
</div>
""", unsafe_allow_html=True)

# 5. Modern butonlar (sadece bir yerde, ortalanmış) ---
# Üstteki butonları kaldır, sadece alttaki kalsın
# (Yalnızca bir kez, ana başlık ve sosyal medya linklerinden sonra göster)

# --- Animasyonlu butonlar için özel CSS ---
st.markdown("""
<style>
.animated-btns-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  margin-top: 18px;
}
div.stButton > button {
  background: linear-gradient(90deg, #1D3557, #2563eb) !important;
  color: white !important;
  padding: 22px 48px;
  font-weight: bold;
  border: none;
  border-radius: 16px;
  font-size: 1.5em;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
  min-width: 340px;
  max-width: 440px;
  justify-content: center;
  box-shadow: 0 4px 16px #1d355733;
}
div.stButton > button:hover {
  cursor: pointer;
  filter: brightness(1.08);
  background: linear-gradient(90deg, #274472, #2563eb) !important;
}
@media (max-width: 600px) {
  .animated-btns-wrap {
    gap: 18px;
    margin-top: 8px;
  }
  div.stButton > button {
    font-size: 1.05em !important;
    padding: 14px 8px !important;
    min-width: 90vw !important;
    max-width: 98vw !important;
    border-radius: 12px !important;
    gap: 8px !important;
  }
  .big-header { font-size: 1.5em !important; }
  .big-subheader { font-size: 1em !important; }
  .social-links {
    flex-direction: column !important;
    gap: 10px !important;
    align-items: center !important;
  }
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="animated-btns-wrap">', unsafe_allow_html=True)
if st.session_state.get('page') != 'chat':
    left, center, right = st.columns([1, 2, 1])
    with center:
        if st.button("📁  CV'yi Gör", key="cv_btn_home", use_container_width=True):
            with open(PDF_PATH, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 PDF'i İndir",
                data=pdf_bytes,
                file_name="Fatma_Betul_Arslan_CV.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="cv_download_btn_direct"
            )
        if st.button("🤖  Sohbete Başla", key="chat_btn_home", use_container_width=True):
            st.session_state['page'] = 'chat'
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- CV ile ilgili butonlar için özel CSS ---
st.markdown("""
<style>
button[data-testid="cv_preview_btn"], button[data-testid="cv_download_btn"] {
    background: #fff !important;
    color: #1D3557 !important;
    border: 2px solid #e3e8f0 !important;
    border-radius: 16px !important;
    font-size: 1.25em !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 12px #1d355722;
    margin-bottom: 18px !important;
    padding: 20px 0 !important;
    transition: all 0.18s;
}
button[data-testid="cv_preview_btn"]:hover, button[data-testid="cv_download_btn"]:hover {
    background: #f1f5fa !important;
    color: #274472 !important;
    border-color: #457B9D !important;
}
</style>
""", unsafe_allow_html=True)

# --- PDF İndir butonu için özel CSS ---
st.markdown("""
<style>
div.stButton > button[data-baseweb="button"][id*="cv_download_btn"] {
    background: #fff !important;
    color: #1D3557 !important;
    border: 1.5px solid #e3e8f0 !important;
    box-shadow: 0 2px 8px #1d355722;
    font-weight: 600;
    font-size: 1.1em;
    margin-bottom: 12px;
}
div.stButton > button[data-baseweb="button"][id*="cv_download_btn"]:hover {
    background: #f1f5fa !important;
    color: #274472 !important;
}
</style>
""", unsafe_allow_html=True)


