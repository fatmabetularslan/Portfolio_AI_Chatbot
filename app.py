import streamlit as st
import base64
import json
from pathlib import Path

from tools.tool_definitions import ToolDefinitions
from rag_system import load_cv_index
from common_css import LIGHT_CSS, DARK_CSS

try:
    from modern_chatbot import run as modern_chatbot_run
except ImportError:
    import modern_chatbot  # type: ignore
    modern_chatbot_run = getattr(modern_chatbot, "run", None)

# ---------------------------------------------------------
# Genel ayarlar
# ---------------------------------------------------------
st.set_page_config(
    page_title="Fatma Betül Arslan",
    page_icon="🤖",
    layout="wide",
)

PDF_PATH = "assets/Fatma-Betül-ARSLAN-cv.pdf"
PROFILE_IMG_PATH = Path("assets/vesika.jpg")
CV_JSON_PATH = "betül-cv.json"


# ---------------------------------------------------------
# Dil & Tema toggle
# ---------------------------------------------------------
def language_and_theme_toggle():
    lang = st.session_state.get("lang", "tr")
    dark = st.session_state.get("dark_mode", False)
    page = st.session_state.get("page", "home")

    # Toggle bar CSS
    st.markdown(
        """
    <style>
    .top-right-toggles {
        position: fixed;
        top: 64px;
        right: 32px;
        display: flex;
        gap: 16px;
        z-index: 1100;
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
    .stApp[data-theme="dark"] .top-right-toggles {
        background: rgba(15,23,42,0.9);
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
    <div class="top-right-toggles">
      <form method="GET" style="display: flex; gap: 8px; align-items: center; margin:0;">
        <button class="toggle-btn{' selected' if lang == 'en' else ''}" name="setlang" value="en" type="submit">EN</button>
        <button class="toggle-btn{' selected' if lang == 'tr' else ''}" name="setlang" value="tr" type="submit">TR</button>
        <button class="toggle-btn{' selected' if not dark else ''}" name="settheme" value="light" type="submit">🌞</button>
        <button class="toggle-btn{' selected' if dark else ''}" name="settheme" value="dark" type="submit">🌙</button>
      </form>
    </div>
    """,
        unsafe_allow_html=True,
    )

    qp = st.query_params
    rerun_needed = False

    if qp.get("setlang"):
        st.session_state["lang"] = qp["setlang"]
        rerun_needed = True

    if qp.get("settheme"):
        st.session_state["dark_mode"] = qp["settheme"] == "dark"
        rerun_needed = True

    if rerun_needed:
        st.session_state["page"] = page
        qp.clear()
        st.rerun()


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state["lang"] = "tr"
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "home"

current_lang = st.session_state["lang"]

# Tema CSS
st.markdown(
    f"<style>{DARK_CSS if st.session_state.dark_mode else LIGHT_CSS}</style>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# CV JSON & RAG yükleme
# ---------------------------------------------------------
try:
    with open(CV_JSON_PATH, encoding="utf-8") as f:
        cv_data = json.load(f)
except Exception as e:
    st.error(f"❌ CV JSON yüklenemedi: {e}")
    st.stop()

try:
    rag = load_cv_index(CV_JSON_PATH)
except Exception as e:
    st.error(f"❌ CV verileri (RAG) yüklenirken hata oluştu: {str(e)}")
    st.info("Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.")
    st.stop()


# ---------------------------------------------------------
# Navigation bar (fixed, scrollable anchor’lar)
# ---------------------------------------------------------
NAV_LABELS = {
    "tr": {
        "about": "Hakkımda",
        "experience": "Deneyim",
        "projects": "Projeler",
        "skills": "Yetenekler",
        "awards": "Ödüller",
        "articles": "Yazılar",
        "references": "Referanslar",
        "contact": "İletişim",
        "chat": "Asistan",
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
        "chat": "Chat",
    },
}
nav = NAV_LABELS[current_lang]

st.markdown(
    f"""
<style>
.nav-menu {{
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
}}

.nav-menu-content {{
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 30px;
    flex-wrap: wrap;
}}

.nav-link {{
    color: #475569;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95em;
    transition: color 0.2s;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
}}

.nav-link:hover {{
    color: #667eea;
    background: rgba(102, 126, 234, 0.1);
}}

.stApp[data-theme="dark"] .nav-menu {{
    background: rgba(30, 41, 59, 0.95) !important;
    border-bottom-color: #475569 !important;
}}

.stApp[data-theme="dark"] .nav-link {{
    color: #cbd5e1 !important;
}}

.stApp[data-theme="dark"] .nav-link:hover {{
    color: #a5b4fc !important;
    background: rgba(102, 126, 234, 0.2) !important;
}}

body {{
    padding-top: 60px;
    scroll-behavior: smooth;
}}

.portfolio-section {{
    scroll-margin-top: 80px;
}}

#chat-section {{
    scroll-margin-top: 80px;
}}

@media (max-width: 768px) {{
    .nav-menu-content {{
        gap: 15px;
        padding: 0 10px;
    }}
    .nav-link {{
        font-size: 0.85em;
        padding: 4px 8px;
    }}
}}
</style>

<script>
document.addEventListener('DOMContentLoaded', function() {{
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {{
        link.addEventListener('click', function(e) {{
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {{
                const offset = 70;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - offset;
                window.scrollTo({{
                    top: offsetPosition,
                    behavior: 'smooth'
                }});
            }}
        }});
    }});
}});
</script>

<div class="nav-menu">
    <div class="nav-menu-content">
        <a href="#about" class="nav-link">{nav['about']}</a>
        <a href="#experience" class="nav-link">{nav['experience']}</a>
        <a href="#projects" class="nav-link">{nav['projects']}</a>
        <a href="#skills" class="nav-link">{nav['skills']}</a>
        <a href="#awards" class="nav-link">{nav['awards']}</a>
        <a href="#articles" class="nav-link">{nav['articles']}</a>
        <a href="#references" class="nav-link">{nav['references']}</a>
        <a href="#contact" class="nav-link">{nav['contact']}</a>
        <a href="#chat-section" class="nav-link">{nav['chat']}</a>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Dil & tema toggle
language_and_theme_toggle()

# ---------------------------------------------------------
# Background blob’lar
# ---------------------------------------------------------
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# ---------------------------------------------------------
# HERO SECTION
# ---------------------------------------------------------
st.markdown(
    """
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
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
    margin: 20px 0 10px 0;
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

.chat-cta-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 12px 26px;
    border-radius: 8px;
    border: 2px solid #667eea;
    font-weight: 600;
    font-size: 1.05em;
    color: #667eea;
    background: #ffffff;
    text-decoration: none;
    transition: all 0.2s;
    min-width: 200px;
}

.chat-cta-btn:hover {
    background: rgba(102, 126, 234, 0.08);
    transform: translateY(-2px);
}

.social-links {
    display: flex;
    justify-content: center;
    gap: 24px;
    flex-wrap: wrap;
    margin-top: 25px;
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

.stApp[data-theme="dark"] .chat-cta-btn {
    background: #020617;
    border-color: #818cf8;
    color: #e5e7eb;
}

.stApp[data-theme="dark"] .chat-cta-btn:hover {
    background: rgba(129, 140, 248, 0.16);
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
""",
    unsafe_allow_html=True,
)

name = cv_data.get("name", "Fatma Betül Arslan")
title = cv_data.get("title", "Data Scientist")
location = cv_data.get("location", "İstanbul, Turkey")

specialization_tr = "Machine Learning, Data Science ve Veri Analizi"
specialization_en = "Machine Learning, Data Science and Data Analysis"
specialization = specialization_tr if current_lang == "tr" else specialization_en

# Profil foto
if PROFILE_IMG_PATH.exists():
    profile_bytes = PROFILE_IMG_PATH.read_bytes()
    profile_b64 = base64.b64encode(profile_bytes).decode("utf-8")
    profile_img_html = (
        f'<img src="data:image/jpeg;base64,{profile_b64}" '
        f'alt="{name}" class="hero-profile-img" />'
    )
else:
    profile_img_html = (
        f'<div class="hero-profile-img" '
        f'style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
        f'display: flex; align-items: center; justify-content: center; '
        f'color: white; font-size: 4em; font-weight: 700;">{name[0]}</div>'
    )

st.markdown(
    f"""
<div class="hero-section">
    {profile_img_html}
    <h1 class="hero-name">{name}</h1>
    <h2 class="hero-title">{title}</h2>
    <p class="hero-specialization">{specialization}</p>
    <p class="hero-location">📍 {location}</p>
    <div class="hero-actions">
""",
    unsafe_allow_html=True,
)

# CV download butonu
try:
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()
    st.markdown('<div class="download-cv-btn-wrapper">', unsafe_allow_html=True)
    st.download_button(
        label="📥 CV'yi İndir" if current_lang == "tr" else "📥 Download CV",
        data=pdf_bytes,
        file_name="Fatma_Betul_Arslan_CV.pdf",
        mime="application/pdf",
        use_container_width=False,
        key="hero_cv_download_btn",
    )
    st.markdown("</div>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error(f"CV dosyası bulunamadı: {PDF_PATH}")

chat_label = "💬 Sohbete Başla" if current_lang == "tr" else "💬 Start Chat"
st.markdown(
    f'<a href="#chat-section" class="chat-cta-btn">{chat_label}</a>',
    unsafe_allow_html=True,
)

# Sosyal linkler
st.markdown(
    """
    </div>  <!-- hero-actions -->
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
</div>  <!-- hero-section -->
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# PORTFOLIO BÖLÜMLERİ
# ---------------------------------------------------------
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# --- About ---
st.markdown('<div class="portfolio-section" id="about">', unsafe_allow_html=True)
st.markdown(
    '<h2 class="section-title">📖 About Me / Hakkımda</h2>',
    unsafe_allow_html=True,
)

education_info = ""
if cv_data.get("education"):
    edu0 = cv_data["education"][0]
    institution = edu0.get("institution", "")
    if institution:
        education_info = (
            '<p style="text-align: center; color: #667eea; '
            f'font-weight: 500; margin-top: 20px;">🎓 {institution}</p>'
        )

profile_text = cv_data.get("profile", "")
if profile_text:
    st.markdown(
        f'<div class="about-content">{profile_text}</div>',
        unsafe_allow_html=True,
    )
    if education_info:
        st.markdown(education_info, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --- Experience & Education ---
st.markdown(
    '<div class="portfolio-section" id="experience">',
    unsafe_allow_html=True,
)
st.markdown(
    '<h2 class="section-title">💼 Experience & Education / Deneyim & Eğitim</h2>',
    unsafe_allow_html=True,
)

for exp in cv_data.get("experience", []):
    e_title = exp.get("title", "")
    company = exp.get("company", "")
    duration = exp.get("duration", "")
    description = exp.get("description", "")
    st.markdown(
        f"""
    <div class="experience-card">
        <div class="experience-title">{e_title}</div>
        <div class="experience-company">{company}</div>
        <div class="experience-duration">{duration}</div>
        <div class="experience-description">{description}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

for edu in cv_data.get("education", []):
    institution = edu.get("institution", "")
    degree = edu.get("degree", "")
    years = edu.get("years", "")
    st.markdown(
        f"""
    <div class="education-card">
        <div class="education-title">{degree}</div>
        <div class="education-institution">{institution}</div>
        <div class="education-years">{years}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# --- Projects ---
st.markdown(
    '<div class="portfolio-section" id="projects">',
    unsafe_allow_html=True,
)
st.markdown(
    '<h2 class="section-title">🚀 Featured Projects / Öne Çıkan Projeler</h2>',
    unsafe_allow_html=True,
)

for proj in cv_data.get("projects", []):
    p_name = proj.get("name", "")
    tech = proj.get("technology", "")
    desc = proj.get("description", "")
    features = proj.get("features", [])
    github = proj.get("github", "")

    if isinstance(desc, dict):
        description = desc.get(current_lang, desc.get("en", desc.get("tr", "")))
    else:
        description = desc

    if isinstance(features, dict):
        features_list = features.get(
            current_lang, features.get("en", features.get("tr", []))
        )
    elif isinstance(features, list):
        features_list = features
    else:
        features_list = []

    features_html = ""
    if features_list:
        features_html = '<div class="project-features">'
        for ft in features_list:
            features_html += f'<div class="project-feature">{ft}</div>'
        features_html += "</div>"

    github_link = ""
    if github:
        github_link = (
            f'<a href="{github}" target="_blank" class="project-link">'
            "🔗 View on GitHub</a>"
        )

    st.markdown(
        f"""
    <div class="project-card">
        <div class="project-name">{p_name}</div>
        <div class="project-tech">{tech}</div>
        <div class="project-description">{description}</div>
        {features_html}
        {github_link}
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# --- Skills ---
st.markdown(
    '<div class="portfolio-section" id="skills">',
    unsafe_allow_html=True,
)
st.markdown(
    '<h2 class="section-title">🛠️ Skills / Yetenekler</h2>',
    unsafe_allow_html=True,
)

skills = cv_data.get("skills", {})
st.markdown('<div class="skills-container">', unsafe_allow_html=True)
for category, skill_list in skills.items():
    skills_html = "".join(
        f'<span class="skill-tag">{sk}</span>' for sk in skill_list
    )
    st.markdown(
        f"""
    <div class="skill-category">
        <div class="skill-category-title">{category}</div>
        <div>{skills_html}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- Awards ---
st.markdown(
    '<div class="portfolio-section" id="awards">',
    unsafe_allow_html=True,
)
st.markdown(
    '<h2 class="section-title">🏆 Awards & Achievements / Ödüller</h2>',
    unsafe_allow_html=True,
)

for award in cv_data.get("awards", []):
    a_name = award.get("name", "")
    org = award.get("organization", "")
    desc = award.get("description", "")
    st.markdown(
        f"""
    <div class="award-card">
        <div class="award-name">{a_name}</div>
        <div class="award-org">{org}</div>
        <div class="award-description">{desc}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# --- References ---
st.markdown(
    '<div class="portfolio-section" id="references">',
    unsafe_allow_html=True,
)
st.markdown(
    '<h2 class="section-title">📞 References / Referanslar</h2>',
    unsafe_allow_html=True,
)

for ref in cv_data.get("references", []):
    r_name = ref.get("name", "")
    r_title = ref.get("title", "")
    org = ref.get("organization", "")
    st.markdown(
        f"""
    <div class="reference-card">
        <div class="reference-name">{r_name}</div>
        <div class="reference-title">{r_title}</div>
        <div class="reference-org">{org}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# --- Articles (Medium) ---
st.markdown(
    '<div class="portfolio-section" id="articles">',
    unsafe_allow_html=True,
)
st.markdown(
    '<h2 class="section-title">📝 Latest Articles / Son Yazılar</h2>',
    unsafe_allow_html=True,
)

medium_articles = cv_data.get("medium_articles", [])
if medium_articles:
    for article in medium_articles[:5]:
        t = article.get("title", "")
        url = article.get("url", "")
        summary_tr = article.get("summary_tr", "")
        summary_en = article.get("summary_en", "")
        summary = summary_tr if current_lang == "tr" else summary_en or summary_tr

        st.markdown(
            f"""
        <div class="project-card">
            <div class="project-name">{t}</div>
            <div class="project-description">{summary}</div>
            <a href="{url}" target="_blank" class="project-link">📖 Read on Medium</a>
        </div>
        """,
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        '<p style="text-align: center; color: #64748b;">No articles available.</p>',
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# --- Contact ---
st.markdown(
    '<div class="portfolio-section" id="contact">',
    unsafe_allow_html=True,
)
st.markdown(
    '<h2 class="section-title">📧 Get In Touch / İletişim</h2>',
    unsafe_allow_html=True,
)

contact_text_tr = (
    "Yeni fırsatlar ve işbirlikleri hakkında konuşmak için benimle iletişime "
    "geçebilirsiniz. Ayrıca sayfanın altındaki AI Asistanı üzerinden de bana ulaşabilirsiniz."
)
contact_text_en = (
    "I'm always interested in hearing about new opportunities and collaborations. "
    "You can also reach me via the AI Assistant at the bottom of this page."
)
contact_text = contact_text_tr if current_lang == "tr" else contact_text_en

email = cv_data.get("email", "")
links = cv_data.get("links", {})

st.markdown(
    f"""
<div style="text-align: center; max-width: 600px; margin: 0 auto;">
    <p style="font-size: 1.1em; line-height: 1.8; color: #475569; margin-bottom: 30px;">
        {contact_text}
    </p>
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
""",
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# CHAT BÖLÜMÜ
# ---------------------------------------------------------
st.markdown(
    """
<style>
#chat-section {
    margin-top: 80px;
    padding-top: 40px;
    border-top: 2px solid #e2e8f0;
}
.stApp[data-theme="dark"] #chat-section {
    border-top-color: #475569;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div id="chat-section"></div>', unsafe_allow_html=True)

if modern_chatbot_run is not None:
    tool_def_obj = ToolDefinitions()
    tool_def_obj.initialize_job_analyzer(
        client=None,
        cv_data=cv_data,
        rag_system=rag,
    )
    modern_chatbot_run(
        tool_def=tool_def_obj,
        rag=rag,
        cv_json=cv_data,
    )
else:
    st.error("Chat modülünü yüklerken sorun oluştu (modern_chatbot.run bulunamadı).")

# main-content wrapper'ını kapat
st.markdown("</div>", unsafe_allow_html=True)
