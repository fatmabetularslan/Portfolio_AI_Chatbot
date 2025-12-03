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
PDF_PATH = "assets/Fatma-Betül-ARSLAN-cv.pdf"
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

# Streamlit header'ını gizle ve navigasyon menüsünü görünür yap
st.markdown("""
<style>
/* Streamlit header'ını tamamen gizle */
header[data-testid="stHeader"],
.stApp > header,
header {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Main container padding'ini ayarla */
.main .block-container {
    padding-top: 0 !important;
    max-width: 1200px;
}

/* Body padding'ini ayarla - navigasyon menüsü için yer aç */
body {
    padding-top: 70px !important;
}

/* Main content'i menünün altından başlat */
.main {
    padding-top: 0 !important;
}

.stApp > div:first-child {
    padding-top: 0 !important;
}
</style>
""", unsafe_allow_html=True)

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
current_lang = st.session_state.get("lang", "tr")

# --- Main content ---

# 1. Navigation Menu (Sabit, üstte)
st.markdown("""
<style>
/* Streamlit header'ını gizle */
header[data-testid="stHeader"] {
    display: none !important;
}

/* Streamlit'in default padding'ini kaldır */
.stApp > header {
    display: none !important;
}

/* Main container'ı üstten başlat */
.main .block-container {
    padding-top: 0 !important;
}

/* Navigation Menu */
.nav-menu {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    background: rgba(255, 255, 255, 0.98) !important;
    backdrop-filter: blur(10px) !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08) !important;
    z-index: 9999 !important;
    padding: 16px 0 !important;
    border-bottom: 1px solid #e2e8f0 !important;
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}

.nav-menu-content {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    padding: 0 40px;
    flex-wrap: wrap;
}

.nav-menu-links {
    display: flex;
    align-items: center;
    gap: 24px;
    flex-wrap: wrap;
}

.nav-menu-toggles {
    display: flex;
    align-items: center;
    gap: 16px;
}

.nav-link {
    color: #1e293b;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.98em;
    transition: color 0.2s, background 0.2s;
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
    white-space: nowrap;
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
    padding-top: 70px !important;
    scroll-behavior: smooth;
}

/* Main content'i menünün altından başlat */
.main {
    padding-top: 70px !important;
}

.stApp > div:first-child {
    padding-top: 0 !important;
}

/* Scroll offset için portfolio bölümleri */
.portfolio-section {
    scroll-margin-top: 80px;
}

#chat-section {
    scroll-margin-top: 80px;
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
                const offset = 70; // Navigation menu yüksekliği için offset
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - offset;
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
});
</script>
""", unsafe_allow_html=True)

# Navigasyon menüsü linkleri (Python'da oluşturuluyor - dil desteği ile)
nav_menu_texts = {
    "tr": {
        "about": "Hakkımda",
        "experience": "Deneyim",
        "projects": "Projeler",
        "skills": "Yetenekler",
        "awards": "Ödüller",
        "articles": "Yazılar",
        "references": "Referanslar",
        "contact": "İletişim",
        "chat": "Chat"
    },
    "en": {
        "about": "About",
        "experience": "Experience",
        "projects": "Projects",
        "skills": "Skills",
        "awards": "Awards",
        "articles": "Articles",
        "references": "References",
        "contact": "Contact",
        "chat": "Chat"
    }
}

nav_texts = nav_menu_texts[current_lang]
home_text = "Ana Sayfa" if current_lang == "tr" else "Home"

# Toggle'ları navigasyon menüsüne entegre et
lang = st.session_state.get("lang", "tr")
dark = st.session_state.get("dark_mode", False)

# Navigasyon menüsü HTML'i
en_selected = 'selected' if lang == 'en' else ''
tr_selected = 'selected' if lang == 'tr' else ''
light_selected = 'selected' if not dark else ''
dark_selected = 'selected' if dark else ''

st.markdown(f"""
<div class="nav-menu">
    <div class="nav-menu-content">
        <div class="nav-menu-links">
            <a href="#" class="nav-link" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}}); return false;">{home_text}</a>
            <a href="#about" class="nav-link">{nav_texts['about']}</a>
            <a href="#experience" class="nav-link">{nav_texts['experience']}</a>
            <a href="#projects" class="nav-link">{nav_texts['projects']}</a>
            <a href="#skills" class="nav-link">{nav_texts['skills']}</a>
            <a href="#awards" class="nav-link">{nav_texts['awards']}</a>
            <a href="#references" class="nav-link">{nav_texts['references']}</a>
            <a href="#articles" class="nav-link">{nav_texts['articles']}</a>
            <a href="#contact" class="nav-link">{nav_texts['contact']}</a>
        </div>
        <div class="nav-menu-toggles">
            <form method="GET" style="display: flex; gap: 6px; align-items: center; margin:0;">
                <button class="nav-toggle-btn {en_selected}" name="setlang" value="en" type="submit" title="English">🇬🇧</button>
                <button class="nav-toggle-btn {tr_selected}" name="setlang" value="tr" type="submit" title="Türkçe">🇹🇷</button>
                <button class="nav-toggle-btn {light_selected}" name="settheme" value="light" type="submit" title="Light Mode">☀️</button>
                <button class="nav-toggle-btn {dark_selected}" name="settheme" value="dark" type="submit" title="Dark Mode">🌙</button>
            </form>
        </div>
    </div>
</div>
<style>
.nav-menu-toggles {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.nav-toggle-btn {{
    width: 40px;
    height: 40px;
    font-size: 1.2em;
    border-radius: 20px;
    border: 1px solid #e2e8f0;
    background: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
    color: #475569;
    margin: 0;
    padding: 0;
}}
.nav-toggle-btn:hover {{
    background: #f1f5f9;
    border-color: #cbd5e1;
    transform: scale(1.05);
}}
.nav-toggle-btn.selected {{
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
    border-color: #2563eb;
    color: #ffffff;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}}
.stApp[data-theme="dark"] .nav-menu-toggles .nav-toggle-btn {{
    background: #1e293b;
    border-color: #475569;
    color: #cbd5e1;
}}
.stApp[data-theme="dark"] .nav-menu-toggles .nav-toggle-btn:hover {{
    background: #334155;
    border-color: #64748b;
}}
.stApp[data-theme="dark"] .nav-menu-toggles .nav-toggle-btn.selected {{
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    border-color: #3b82f6;
    color: #ffffff;
}}
</style>
""", unsafe_allow_html=True)

# Query param ile state güncelle (toggle'lar için)
qp = st.query_params
rerun_needed = False
if qp.get("setlang"):
    st.session_state["lang"] = qp["setlang"]
    rerun_needed = True
if qp.get("settheme"):
    st.session_state["dark_mode"] = qp["settheme"] == "dark"
    rerun_needed = True
if rerun_needed:
    qp.clear()
    st.rerun()

# Eski toggle bar'ı kaldır - artık menü içinde

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

# 3. Main Content Container
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Hero Section (Selman'ın sitesine benzer)
cv_data = json.load(open(tag, encoding="utf-8"))
current_lang = st.session_state.get("lang", "tr")
name = cv_data.get("name", "Fatma Betül Arslan")
title = cv_data.get("title", "Data Scientist")
location = cv_data.get("location", "İstanbul, Turkey")

# Hero section için özel CSS (Profil fotoğrafı, butonlar ve ikonlar dahil)
st.markdown("""
<style>
.hero-section {
    text-align: center;
    padding: 80px 20px 50px;
    max-width: 900px;
    margin: 0 auto 60px auto;
}

.hero-profile-img {
    width: 180px;
    height: 180px;
    border-radius: 50%;
    object-fit: cover;
    margin: 0 auto 30px auto;
    display: block;
    border: 4px solid #667eea;
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
    transition: transform 0.3s ease;
}

.hero-profile-img:hover {
    transform: scale(1.05);
}

.hero-name {
    font-size: 4em;
    font-weight: 800;
    margin-bottom: 15px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
}

.hero-title {
    font-size: 2em;
    font-weight: 600;
    color: #475569;
    margin-bottom: 15px;
}

.hero-specialization {
    font-size: 1.3em;
    color: #64748b;
    margin-bottom: 20px;
    font-style: italic;
    font-weight: 400;
}

.hero-location {
    font-size: 1em;
    color: #64748b;
    margin-bottom: 30px;
}

.hero-actions {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
    margin: 30px 0;
}

.download-cv-btn-wrapper {
    display: flex;
    justify-content: center;
}

.download-cv-btn-wrapper button,
.download-cv-btn-wrapper div[data-baseweb="button"],
.download-cv-btn-wrapper .stDownloadButton button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    padding: 14px 32px !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 1.05em !important;
    cursor: pointer !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    min-width: 200px !important;
}

.download-cv-btn-wrapper button:hover,
.download-cv-btn-wrapper div[data-baseweb="button"]:hover,
.download-cv-btn-wrapper .stDownloadButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4) !important;
    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
}

.social-links {
    display: flex;
    justify-content: center;
    gap: 24px;
    flex-wrap: wrap;
    margin-top: 10px;
}

.social-links a {
    text-decoration: none;
    font-size: 1.1em;
    display: flex;
    align-items: center;
    gap: 8px;
    color: #667eea;
    transition: color 0.2s, transform 0.2s;
    padding: 8px 12px;
    border-radius: 8px;
}

.social-links a:hover {
    color: #764ba2;
    transform: translateY(-2px);
    background: rgba(102, 126, 234, 0.1);
}

.social-links img {
    width: 24px;
    height: 24px;
    vertical-align: middle;
}

.stApp[data-theme="dark"] .hero-title {
    color: #cbd5e1 !important;
}

.stApp[data-theme="dark"] .hero-specialization,
.stApp[data-theme="dark"] .hero-location {
    color: #94a3b8 !important;
}

.stApp[data-theme="dark"] .hero-profile-img {
    border-color: #8b5cf6;
    box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4);
}

.stApp[data-theme="dark"] .social-links a {
    color: #a5b4fc !important;
}

.stApp[data-theme="dark"] .social-links a:hover {
    color: #c4b5fd !important;
    background: rgba(102, 126, 234, 0.2) !important;
}

@media (max-width: 768px) {
    .hero-profile-img {
        width: 140px;
        height: 140px;
    }
    .hero-name {
        font-size: 2.5em;
    }
    .hero-title {
        font-size: 1.4em;
    }
    .hero-specialization {
        font-size: 1em;
    }
    .social-links {
        gap: 16px;
    }
    .social-links a {
        font-size: 0.95em;
    }
}
</style>
""", unsafe_allow_html=True)

# Profil fotoğrafını yükle
profile_img_html = ""
if PROFILE_IMG_PATH.exists():
    profile_bytes = PROFILE_IMG_PATH.read_bytes()
    profile_b64 = base64.b64encode(profile_bytes).decode("utf-8")
    profile_img_html = f'<img src="data:image/jpeg;base64,{profile_b64}" alt="{name}" class="hero-profile-img" />'
else:
    # Fallback: İlk harf avatar
    profile_img_html = f'<div class="hero-profile-img" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 4em; font-weight: 700;">{name[0]}</div>'

# Hero content
specialization_tr = "Machine Learning, Data Science ve Veri Analizi"
specialization_en = "Machine Learning, Data Science and Data Analysis"
specialization = specialization_tr if current_lang == "tr" else specialization_en

# Hero section - Profil fotoğrafı, isim, başlık, uzmanlık, lokasyon
st.markdown(f"""
<div class="hero-section">
    {profile_img_html}
    <h1 class="hero-name">{name}</h1>
    <h2 class="hero-title">{title}</h2>
    <p class="hero-specialization">{specialization}</p>
    <p class="hero-location">📍 {location}</p>
    <div class="hero-actions">
""", unsafe_allow_html=True)

# Download CV butonu (Streamlit bileşeni - HTML dışında)
try:
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()
    st.markdown('<div class="download-cv-btn-wrapper">', unsafe_allow_html=True)
    st.download_button(
        label="📥 Download CV",
        data=pdf_bytes,
        file_name="Fatma_Betul_Arslan_CV.pdf",
        mime="application/pdf",
        use_container_width=False,
        key="hero_cv_download_btn"
    )
    st.markdown('</div>', unsafe_allow_html=True)
except FileNotFoundError:
    st.error(f"CV dosyası bulunamadı: {PDF_PATH}")

# Sosyal medya linkleri
st.markdown("""
        <div class="social-links">
          <a href="https://www.linkedin.com/in/fatma-betül-arslan" target="_blank">
            <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg" alt="LinkedIn"> LinkedIn
          </a>
          <a href="https://github.com/fatmabetularslan" target="_blank">
            <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg" alt="GitHub"> GitHub
          </a>
          <a href="https://medium.com/@betularsln01" target="_blank">
            <img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/medium.svg" alt="Medium"> Medium
          </a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Gereksiz CSS ve buton kodları temizlendi - hero section'da Download CV butonu var

# Ana içeriği kapat
st.markdown('</div>', unsafe_allow_html=True)

# --- Portfolio Bölümleri (Scrollable) ---
# cv_data ve current_lang zaten yukarıda tanımlı

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

# Education bilgisini About Me'de göster
education_info = ""
if cv_data.get("education"):
    edu = cv_data["education"][0]
    institution = edu.get("institution", "")
    education_info = f'<p style="text-align: center; color: #667eea; font-weight: 500; margin-top: 20px;">🎓 {institution}</p>'

profile_text = cv_data.get("profile", "")
if profile_text:
    st.markdown(f'<div class="about-content">{profile_text}</div>', unsafe_allow_html=True)
    if education_info:
        st.markdown(education_info, unsafe_allow_html=True)

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
st.markdown('<h2 class="section-title">🚀 Featured Projects / Öne Çıkan Projeler</h2>', unsafe_allow_html=True)

# Sadece belirtilen projeleri göster
allowed_projects = [
    "AI-Powered Portfolio Chatbot",
    "FinTurk Finansal Asistan",
    "Customer Churn Prediction",
    "Energy Consumption Prediction API"
]

for proj in cv_data.get("projects", []):
    name = proj.get("name", "")
    # Sadece izin verilen projeleri göster
    if name not in allowed_projects:
        continue
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

# Latest Articles / Son Yazılar (Medium)
st.markdown('<div class="portfolio-section" id="articles">', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">📝 Latest Articles / Son Yazılar</h2>', unsafe_allow_html=True)

medium_articles = cv_data.get("medium_articles", [])
if medium_articles:
    for article in medium_articles[:5]:  # İlk 5 yazıyı göster
        title = article.get("title", "")
        url = article.get("url", "")
        summary_tr = article.get("summary_tr", "")
        summary_en = article.get("summary_en", "")
        summary = summary_tr if current_lang == "tr" else summary_en
        
        st.markdown(f"""
        <div class="project-card">
            <div class="project-name">{title}</div>
            <div class="project-description">{summary}</div>
            <a href="{url}" target="_blank" class="project-link">📖 Read on Medium</a>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown('<p style="text-align: center; color: #64748b;">No articles available.</p>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Get In Touch / İletişim
st.markdown('<div class="portfolio-section" id="contact">', unsafe_allow_html=True)
st.markdown('<h2 class="section-title">📧 Get In Touch / İletişim</h2>', unsafe_allow_html=True)

contact_text_tr = "Yeni fırsatlar ve işbirlikleri hakkında konuşmak için benimle iletişime geçebilirsiniz. Ayrıca sayfanın altındaki AI Asistanı üzerinden de bana ulaşabilirsiniz."
contact_text_en = "I'm always interested in hearing about new opportunities and collaborations. You can also reach me via the AI Assistant at the bottom of this page."

contact_text = contact_text_tr if current_lang == "tr" else contact_text_en

email = cv_data.get("email", "")
links = cv_data.get("links", {})

st.markdown(f"""
<div style="text-align: center; max-width: 600px; margin: 0 auto;">
    <p style="font-size: 1.1em; line-height: 1.8; color: #475569; margin-bottom: 30px;">{contact_text}</p>
    <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
        <a href="mailto:{email}" style="display: inline-flex; align-items: center; gap: 8px; color: #667eea; text-decoration: none; font-weight: 500; padding: 10px 20px; border: 2px solid #667eea; border-radius: 8px; transition: all 0.2s;">
            📧 Mail Me
        </a>
        <a href="{links.get('linkedin', '#')}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; color: #667eea; text-decoration: none; font-weight: 500; padding: 10px 20px; border: 2px solid #667eea; border-radius: 8px; transition: all 0.2s;">
            💼 LinkedIn
        </a>
        <a href="{links.get('github', '#')}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; color: #667eea; text-decoration: none; font-weight: 500; padding: 10px 20px; border: 2px solid #667eea; border-radius: 8px; transition: all 0.2s;">
            🔗 GitHub
        </a>
        <a href="{links.get('medium', '#')}" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; color: #667eea; text-decoration: none; font-weight: 500; padding: 10px 20px; border: 2px solid #667eea; border-radius: 8px; transition: all 0.2s;">
            ✍️ Medium
        </a>
    </div>
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
