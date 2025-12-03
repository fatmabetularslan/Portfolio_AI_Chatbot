import streamlit as st
import streamlit.components.v1 as components
import base64

st.set_page_config(page_title="Fatma Betül Arslan", page_icon="🤖", layout="centered")

import json
from tools.tool_definitions import ToolDefinitions
try:
    from modern_chatbot import run as modern_chatbot_run
except ImportError:
    import modern_chatbot  # type: ignore
    modern_chatbot_run = getattr(modern_chatbot, "run", None)
from common_css import LIGHT_CSS, DARK_CSS
from rag_system import load_cv_index
from pathlib import Path
PDF_PATH = "assets/Fatma-Betül-ARSLAN-cv-2025.pdf"
PROFILE_IMG_PATH = Path("assets/vesika.jpg")

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
    width: 720px !important;
    min-width: 600px;
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
    font-size: 2.3em !important;
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

# RAG sistemini güvenli şekilde yükle
try:
    rag = load_cv_index(tag)
except Exception as e:
    st.error(f"❌ CV verileri yüklenirken hata oluştu: {str(e)}")
    st.info("Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.")
    st.stop()

# Chat artık ayrı sayfa değil, ana sayfanın altında bir bölüm
# Sayfa yönlendirmesi kaldırıldı

# --- Ana sayfa metinleri ---
TEXT = {
    "tr": {
        "header": "👋 Merhaba! Ben Fatma Betül'ün AI Portföy Asistanıyım",
        "sub"   : "Fatma Betül'ün özgeçmişi, projeleri ve deneyimlerine hızlıca göz atmak ister misin? İster CV'sini görüntüle, ister asistanıyla birebir sohbet etmeye başla.",
        "cv"    : "📂 CV'yi Gör",
        "chat"  : "Sohbete Başla",
    },
    "en": {
        "header": "👋 Hello!",
        "sub"   : "Would you like to quickly browse Fatma Betül's resume, projects and experiences? Either view her CV or start a one-on-one chat with her assistant.",
        "cv"    : "📂 View CV",
        "chat"  : "Start Chat",
    },
}
lang_text = TEXT[ st.session_state.lang ]

# --- Main content ---

# 1. Navigation Menu (Sabit, üstte)
st.markdown("""
<style>
.nav-menu {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    z-index: 1000;
    padding: 12px 0;
    border-bottom: 1px solid #e2e8f0;
}

.nav-menu-content {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 30px;
    flex-wrap: wrap;
}

.nav-link {
    color: #475569;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95em;
    transition: color 0.2s;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
}

.nav-link:hover {
    color: #667eea;
    background: rgba(102, 126, 234, 0.1);
}

.stApp[data-theme="dark"] .nav-menu {
    background: rgba(30, 41, 59, 0.95) !important;
    border-bottom-color: #475569 !important;
}

.stApp[data-theme="dark"] .nav-link {
    color: #cbd5e1 !important;
}

.stApp[data-theme="dark"] .nav-link:hover {
    color: #a5b4fc !important;
    background: rgba(102, 126, 234, 0.2) !important;
}

body {
    padding-top: 60px;
}

@media (max-width: 768px) {
    .nav-menu-content {
        gap: 15px;
        padding: 0 10px;
    }
    .nav-link {
        font-size: 0.85em;
        padding: 4px 8px;
    }
}
</style>
<script>
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
});
</script>
<div class="nav-menu">
    <div class="nav-menu-content">
        <a href="#about" class="nav-link">About</a>
        <a href="#experience" class="nav-link">Experience</a>
        <a href="#projects" class="nav-link">Projects</a>
        <a href="#skills" class="nav-link">Skills</a>
        <a href="#awards" class="nav-link">Awards</a>
        <a href="#references" class="nav-link">References</a>
        <a href="#chat-section" class="nav-link">Chat</a>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Toggle bar (dil/tema)
language_and_theme_toggle()

# 2. Modern arka plan şekilleri ve blob'lar
st.markdown("""
<style>
.background-shapes {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: -1;
    overflow: hidden;
}

.blob-1 {
    position: absolute;
    top: -10%;
    right: -10%;
    width: 400px;
    height: 400px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    filter: blur(60px);
    opacity: 0.15;
    animation: float 6s ease-in-out infinite;
}

.blob-2 {
    position: absolute;
    bottom: -15%;
    left: -15%;
    width: 350px;
    height: 350px;
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    border-radius: 50%;
    filter: blur(50px);
    opacity: 0.12;
    animation: float 8s ease-in-out infinite reverse;
}

.wave-shape {
    position: absolute;
    top: 20%;
    right: 5%;
    width: 200px;
    height: 200px;
    background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
    border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;
    filter: blur(40px);
    opacity: 0.1;
    animation: morph 10s ease-in-out infinite;
}

.bottom-wave {
    position: absolute;
    bottom: -5%;
    left: 0;
    width: 100%;
    height: 300px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    opacity: 0.08;
    clip-path: polygon(0 100%, 100% 100%, 100% 60%, 80% 40%, 60% 60%, 40% 40%, 20% 60%, 0 40%);
    animation: wave-float 12s ease-in-out infinite;
}

.bottom-blob {
    position: absolute;
    bottom: -10%;
    right: -5%;
    width: 500px;
    height: 500px;
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 50%, #4facfe 100%);
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.06;
    animation: blob-float 15s ease-in-out infinite;
}

@keyframes wave-float {
    0%, 100% { transform: translateY(0px) scale(1); }
    50% { transform: translateY(-15px) scale(1.02); }
}

@keyframes blob-float {
    0%, 100% { transform: translateY(0px) rotate(0deg) scale(1); }
    33% { transform: translateY(-10px) rotate(120deg) scale(1.05); }
    66% { transform: translateY(-5px) rotate(240deg) scale(0.95); }
}

@keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(180deg); }
}

@keyframes morph {
    0%, 100% { border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%; }
    25% { border-radius: 58% 42% 75% 25% / 76% 46% 54% 24%; }
    50% { border-radius: 50% 50% 33% 67% / 55% 27% 73% 45%; }
    75% { border-radius: 33% 67% 58% 42% / 63% 68% 32% 37%; }
}

/* Ana içeriği arka plan şekillerinin üstünde tut */
.main-content {
    position: relative;
    z-index: 1;
}
</style>

<div class="background-shapes">
    <div class="blob-1"></div>
    <div class="blob-2"></div>
    <div class="wave-shape"></div>
    <div class="bottom-wave"></div>
    <div class="bottom-blob"></div>
</div>
""", unsafe_allow_html=True)

# 3. Header ve AI Avatar
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# AI Avatar CSS
st.markdown("""
<style>
.header-with-avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    margin-bottom: 20px;
    position: relative;
}

.ai-avatar {
    width: 155px;
    height: 155px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 58% 42% 60% 40% / 45% 55% 45% 55%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5em;
    box-shadow: 0 12px 30px rgba(86, 99, 255, 0.3);
    animation: pulse 2s ease-in-out infinite;
    position: relative;
    backdrop-filter: blur(8px);
    border: 2px solid rgba(255,255,255,0.4);
}

.ai-avatar::after {
    content: '';
    position: absolute;
    inset: -20px;
    border-radius: inherit;
    background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.45), transparent 60%);
    filter: blur(10px);
    opacity: 0.6;
    z-index: -2;
}

.ai-avatar::before {
    content: '';
    position: absolute;
    top: -14px;
    left: -14px;
    right: -14px;
    bottom: -14px;
    border-radius: inherit;
    background: linear-gradient(135deg, rgba(102,126,234,0.25), rgba(118,75,162,0.25));
    z-index: -1;
    opacity: 0.8;
    filter: blur(8px);
}

.ai-avatar img {
    width: 94%;
    height: 94%;
    border-radius: 55% 45% 50% 50% / 48% 52% 42% 58%;
    object-fit: cover;
    box-shadow: inset 0 0 12px rgba(0,0,0,0.15);
}

.ai-avatar::before {
    content: '';
    position: absolute;
    top: -5px;
    left: -5px;
    right: -5px;
    bottom: -5px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    z-index: -1;
    opacity: 0.3;
    animation: pulse-ring 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

@keyframes pulse-ring {
    0% { transform: scale(1); opacity: 0.3; }
    50% { transform: scale(1.1); opacity: 0.1; }
    100% { transform: scale(1); opacity: 0.3; }
}

@media (max-width: 768px) {
    .header-with-avatar {
        flex-direction: column;
        gap: 15px;
    }
    .ai-avatar {
        width: 115px;
        height: 115px;
        font-size: 2em;
    }
}
</style>
""", unsafe_allow_html=True)

# Header ve AI Avatar birlikte
avatar_html = "🤖"
if PROFILE_IMG_PATH.exists():
    avatar_bytes = PROFILE_IMG_PATH.read_bytes()
    avatar_b64 = base64.b64encode(avatar_bytes).decode("utf-8")
    avatar_html = f'<img src="data:image/jpeg;base64,{avatar_b64}" alt="Fatma Betül Arslan" />'

st.markdown(f"""
<div class="header-with-avatar">
    <div class="ai-avatar">{avatar_html}</div>
    <div class="big-header">{lang_text["header"]}</div>
</div>
""", unsafe_allow_html=True)

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
  justify-content: center;
  gap: 24px;
  margin-top: 24px;
  width: 100%;
  text-align: center;
}

.animated-btns-wrap div.stButton {
  display: flex !important;
  justify-content: center !important;
  width: 100% !important;
}
div.stButton > button {
  background: linear-gradient(90deg, #1D3557, #2563eb) !important;
  color: white !important;
  padding: 24px 44px;
  font-weight: 600;
  border: none;
  border-radius: 16px;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 600px;
  max-width: 800px;
  justify-content: center;
  box-shadow: 0 8px 25px rgba(37, 99, 235, 0.25);
  position: relative;
  overflow: hidden;
  min-height: 60px;
  margin: 0 auto !important;
  float: none !important;
}
div.stButton > button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}
div.stButton > button:hover::before {
  left: 100%;
}
div.stButton > button:hover {
  cursor: pointer;
  transform: scale(1.02) translateY(-2px);
  box-shadow: 0 12px 35px rgba(37, 99, 235, 0.35);
  background: linear-gradient(90deg, #274472, #2563eb) !important;
}
div.stButton > button:active {
  transform: scale(0.98) translateY(0px);
  box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
}
div.stButton > button:focus {
  outline: 2px solid rgba(37, 99, 235, 0.5);
  outline-offset: 2px;
}
div.stButton > button:last-child {
  background: linear-gradient(90deg, #3A86FF, #219EBC) !important;
  box-shadow: 0 8px 25px rgba(58, 134, 255, 0.25);
}
div.stButton > button:last-child:hover {
  background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
  box-shadow: 0 12px 35px rgba(58, 134, 255, 0.35);
}
@media (max-width: 600px) {
  .animated-btns-wrap {
    gap: 18px;
    margin-top: 8px;
  }
  div.stButton > button {
    font-size: 1.1rem !important;
    padding: 20px 16px !important;
    min-width: 90vw !important;
    max-width: 98vw !important;
    border-radius: 12px !important;
    gap: 8px !important;
    min-height: 56px !important;
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
if st.button("📁  CV'yi Gör", key="cv_btn_home_main", use_container_width=False):
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label="📥 PDF'i İndir",
        data=pdf_bytes,
        file_name="Fatma_Betul_Arslan_CV.pdf",
        mime="application/pdf",
        use_container_width=False,
        key="cv_download_btn_direct"
    )

if st.button("🤖  Sohbete Başla", key="chat_btn_home_main", use_container_width=False):
    # JavaScript ile smooth scroll yap
    st.markdown("""
    <script>
    (function() {
        setTimeout(function() {
            const chatSection = document.getElementById('chat-section');
            if (chatSection) {
                chatSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 100);
    })();
    </script>
    """, unsafe_allow_html=True)
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

# Ana içeriği kapat
st.markdown('</div>', unsafe_allow_html=True)

# --- Portfolio Bölümleri (Scrollable) ---
cv_data = json.load(open(tag, encoding="utf-8"))
current_lang = st.session_state.get("lang", "tr")

# Portfolio bölümleri için CSS
st.markdown("""
<style>
.portfolio-section {
    margin: 60px 0;
    padding: 40px 20px;
    max-width: 1000px;
    margin-left: auto;
    margin-right: auto;
}

.section-title {
    font-size: 2em;
    font-weight: 700;
    margin-bottom: 30px;
    text-align: center;
    color: #1e293b;
    position: relative;
    padding-bottom: 15px;
}

.section-title::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 60px;
    height: 3px;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    border-radius: 2px;
}

.about-content {
    font-size: 1.1em;
    line-height: 1.8;
    color: #475569;
    text-align: center;
    max-width: 800px;
    margin: 0 auto;
}

.experience-card, .education-card, .project-card, .award-card, .reference-card {
    background: #fff;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    transition: transform 0.2s, box-shadow 0.2s;
    border-left: 4px solid #667eea;
}

.experience-card:hover, .education-card:hover, .project-card:hover, .award-card:hover, .reference-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
}

.experience-title, .education-title {
    font-size: 1.3em;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 8px;
}

.experience-company, .education-institution {
    font-size: 1.1em;
    color: #667eea;
    font-weight: 500;
    margin-bottom: 8px;
}

.experience-duration, .education-years {
    font-size: 0.9em;
    color: #64748b;
    margin-bottom: 12px;
}

.experience-description, .education-degree {
    color: #475569;
    line-height: 1.6;
}

.skills-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-top: 30px;
}

.skill-category {
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.skill-category-title {
    font-size: 1.2em;
    font-weight: 600;
    color: #667eea;
    margin-bottom: 12px;
}

.skill-tag {
    display: inline-block;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    color: #475569;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.9em;
    margin: 4px 4px 4px 0;
    border: 1px solid #e2e8f0;
}

.project-card {
    border-left-color: #764ba2;
}

.project-name {
    font-size: 1.3em;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 12px;
}

.project-tech {
    color: #667eea;
    font-size: 0.95em;
    margin-bottom: 12px;
    font-weight: 500;
}

.project-description {
    color: #475569;
    line-height: 1.6;
    margin-bottom: 12px;
}

.project-features {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #e2e8f0;
}

.project-feature {
    color: #64748b;
    font-size: 0.9em;
    margin: 4px 0;
}

.project-feature::before {
    content: '• ';
    color: #667eea;
    font-weight: bold;
}

.project-link {
    display: inline-block;
    margin-top: 12px;
    color: #667eea;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
}

.project-link:hover {
    color: #764ba2;
}

.award-name {
    font-size: 1.2em;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 6px;
}

.award-org {
    color: #667eea;
    font-weight: 500;
    margin-bottom: 8px;
}

.award-description {
    color: #475569;
    line-height: 1.6;
}

.reference-name {
    font-size: 1.2em;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 6px;
}

.reference-title {
    color: #667eea;
    font-weight: 500;
    margin-bottom: 4px;
}

.reference-org {
    color: #64748b;
    font-size: 0.9em;
}

/* Dark mode */
.stApp[data-theme="dark"] .section-title {
    color: #f1f5f9 !important;
}

.stApp[data-theme="dark"] .about-content,
.stApp[data-theme="dark"] .experience-description,
.stApp[data-theme="dark"] .education-degree,
.stApp[data-theme="dark"] .project-description,
.stApp[data-theme="dark"] .award-description {
    color: #cbd5e1 !important;
}

.stApp[data-theme="dark"] .experience-card,
.stApp[data-theme="dark"] .education-card,
.stApp[data-theme="dark"] .project-card,
.stApp[data-theme="dark"] .award-card,
.stApp[data-theme="dark"] .reference-card,
.stApp[data-theme="dark"] .skill-category {
    background: #1e293b !important;
    border-color: #475569 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
}

.stApp[data-theme="dark"] .experience-title,
.stApp[data-theme="dark"] .education-title,
.stApp[data-theme="dark"] .project-name,
.stApp[data-theme="dark"] .award-name,
.stApp[data-theme="dark"] .reference-name {
    color: #f1f5f9 !important;
}

.stApp[data-theme="dark"] .skill-tag {
    background: #334155 !important;
    color: #cbd5e1 !important;
    border-color: #475569 !important;
}

@media (max-width: 768px) {
    .portfolio-section {
        padding: 30px 15px;
        margin: 40px 0;
    }
    .section-title {
        font-size: 1.6em;
    }
    .skills-container {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# About Me / Hakkımda
st.markdown('<div class="portfolio-section" id="about">', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">📖 About Me / Hakkımda</h2>', unsafe_allow_html=True)
profile_text = cv_data.get("profile", "")
if profile_text:
    st.markdown(f'<div class="about-content">{profile_text}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Experience & Education
st.markdown('<div class="portfolio-section" id="experience">', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">💼 Experience & Education / Deneyim & Eğitim</h2>', unsafe_allow_html=True)

# Experience
for exp in cv_data.get("experience", []):
    title = exp.get("title", "")
    company = exp.get("company", "")
    duration = exp.get("duration", "")
    description = exp.get("description", "")
    st.markdown(f"""
    <div class="experience-card">
        <div class="experience-title">{title}</div>
        <div class="experience-company">{company}</div>
        <div class="experience-duration">{duration}</div>
        <div class="experience-description">{description}</div>
    </div>
    """, unsafe_allow_html=True)

# Education
for edu in cv_data.get("education", []):
    institution = edu.get("institution", "")
    degree = edu.get("degree", "")
    years = edu.get("years", "")
    st.markdown(f"""
    <div class="education-card">
        <div class="education-title">{degree}</div>
        <div class="education-institution">{institution}</div>
        <div class="education-years">{years}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Projects
st.markdown('<div class="portfolio-section" id="projects">', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">🚀 Projects / Projeler</h2>', unsafe_allow_html=True)

for proj in cv_data.get("projects", []):
    name = proj.get("name", "")
    tech = proj.get("technology", "")
    desc = proj.get("description", "")
    features = proj.get("features", [])
    github = proj.get("github", "")
    
    # Dil desteği için description
    if isinstance(desc, dict):
        description = desc.get(current_lang, desc.get("en", desc.get("tr", "")))
    else:
        description = desc
    
    # Dil desteği için features
    if isinstance(features, dict):
        features_list = features.get(current_lang, features.get("en", features.get("tr", [])))
    elif isinstance(features, list):
        features_list = features
    else:
        features_list = []
    
    features_html = ""
    if features_list:
        features_html = '<div class="project-features">'
        for feature in features_list:
            features_html += f'<div class="project-feature">{feature}</div>'
        features_html += '</div>'
    
    github_link = ""
    if github:
        github_link = f'<a href="{github}" target="_blank" class="project-link">🔗 View on GitHub</a>'
    
    st.markdown(f"""
    <div class="project-card">
        <div class="project-name">{name}</div>
        <div class="project-tech">{tech}</div>
        <div class="project-description">{description}</div>
        {features_html}
        {github_link}
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Skills
st.markdown('<div class="portfolio-section" id="skills">', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">🛠️ Skills / Yetenekler</h2>', unsafe_allow_html=True)

skills = cv_data.get("skills", {})
st.markdown('<div class="skills-container">', unsafe_allow_html=True)
for category, skill_list in skills.items():
    skills_html = ""
    for skill in skill_list:
        skills_html += f'<span class="skill-tag">{skill}</span>'
    st.markdown(f"""
    <div class="skill-category">
        <div class="skill-category-title">{category}</div>
        <div>{skills_html}</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Awards
st.markdown('<div class="portfolio-section" id="awards">', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">🏆 Awards & Achievements / Ödüller</h2>', unsafe_allow_html=True)

for award in cv_data.get("awards", []):
    name = award.get("name", "")
    org = award.get("organization", "")
    desc = award.get("description", "")
    st.markdown(f"""
    <div class="award-card">
        <div class="award-name">{name}</div>
        <div class="award-org">{org}</div>
        <div class="award-description">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# References
st.markdown('<div class="portfolio-section" id="references">', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">📞 References / Referanslar</h2>', unsafe_allow_html=True)

for ref in cv_data.get("references", []):
    name = ref.get("name", "")
    title = ref.get("title", "")
    org = ref.get("organization", "")
    st.markdown(f"""
    <div class="reference-card">
        <div class="reference-name">{name}</div>
        <div class="reference-title">{title}</div>
        <div class="reference-org">{org}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- Chat Bölümü (Ana sayfanın altında) ---
st.markdown("""
<style>
#chat-section {
    margin-top: 80px;
    padding-top: 40px;
    border-top: 2px solid #e2e8f0;
    scroll-margin-top: 20px;
}
.stApp[data-theme="dark"] #chat-section {
    border-top-color: #475569;
}
</style>
""", unsafe_allow_html=True)
st.markdown('<div id="chat-section"></div>', unsafe_allow_html=True)

# Chat modülünü yükle ve çalıştır
if modern_chatbot_run is not None:
    tool_def_obj = ToolDefinitions()
    tool_def_obj.initialize_job_analyzer(
        client=None,
        cv_data=json.load(open(tag, encoding="utf-8")),
        rag_system=rag
    )
    modern_chatbot_run(
        tool_def = tool_def_obj,
        rag     = rag,
        cv_json = json.load(open(tag, encoding="utf-8"))
    )
else:
    st.error("Chat modülünü yüklerken sorun oluştu (modern_chatbot.run bulunamadı).")
