# modern_chatbot.py
import streamlit as st
import time
from datetime import datetime
from tools.gemini_tool import ask_gemini, generate_cover_letter
from common_css import LIGHT_CSS, DARK_CSS
import ast
import re
# ------------------------------------------------------------------ #
# (İstersen bu uzun CSS'i ayrı bir dosyaya da taşıyabilirsin)
CSS = """
<style>
/* —— KISA NOT —— 
   Aşağıya önceki dosyandaki tüm .profile-card, .chat-container,
   .msg-user, .msg-bot, dark-mode ve media-query kurallarını 
   eksiksiz yerleştir.  
*/
body
div[data-baseweb="input"] > div {
{ background: #f5f6fa !important;
border: 2px solid #c6c9d4 !important;  
border-radius: 10px !important;
box-shadow: 0 2px 6px rgba(0,0,0,0.08) !important;

div[data-baseweb="input"]:focus-within > div {
border: 2px solid #6C63FF !important;  /* marka moru */
box-shadow: 0 0 0 3px rgba(108,99,255,0.25) !important;
    }
    /* Placeholder metni daha koyu gri */
    div[data-baseweb="input"] input::placeholder {
        color: #8a8f9c !important; }
...
</style>
"""
# ------------------------------------------------------------------ #

LANG_TEXTS = {
    "tr": {
        "input_placeholder": "Mesajınızı yazın...",
        "send": "Gönder",
        "spinner": "Yanıt oluşturuluyor...",
        "download_cv": "⬇️ CV'yi İndir",
        "dark_mode": "🌙 Karanlık Mod Aktif",
    },
    "en": {
        "input_placeholder": "Type your message...",
        "send": "Send",
        "spinner": "Generating response...",
        "download_cv": "⬇️ Download CV",
        "dark_mode": "🌙 Dark Mode Active",
    },
}

# --- Modern Language Toggle Bar (flag icons, unified, no columns/buttons) ---
def language_and_theme_toggle():
    lang = st.session_state.get("lang", "tr")
    dark = st.session_state.get("dark_mode", False)
    page = st.session_state.get("page", "home")
    st.markdown("""
<style>
.toggle-bar-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 48px 0 48px 0;
    gap: 48px;
}
.lang-toggle, .theme-toggle {
    display: flex;
    align-items: center;
    background: #f3f4f8;
    border-radius: 40px;
    box-shadow: 0 4px 24px 0 rgba(49,130,206,0.10), 0 0 16px 2px #fff2;
    padding: 8px 18px;
    gap: 0;
    position: relative;
}
.lang-flag-btn, .theme-btn {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.1em;
    background: none;
    border: none;
    margin: 0 6px;
    transition: filter 0.18s, background 0.18s, box-shadow 0.18s;
    cursor: pointer;
    outline: none;
    box-shadow: none;
}
.lang-flag-btn.selected, .theme-btn.selected {
    background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
    box-shadow: 0 4px 16px #2563eb33;
    filter: none;
    color: #fff;
}
.lang-flag-btn.unselected, .theme-btn.unselected {
    filter: grayscale(0.7) opacity(0.5);
    background: none;
    color: #222;
}
</style>
""", unsafe_allow_html=True)

    st.markdown(f'''
    <div class="toggle-bar-wrap">
      <form method="GET" style="display: flex; gap: 32px; align-items: center;">
        <div class="lang-toggle">
          <button class="lang-flag-btn{' selected' if lang == 'en' else ' unselected'}" name="setlang" value="en" type="submit">🇬🇧</button>
          <button class="lang-flag-btn{' selected' if lang == 'tr' else ' unselected'}" name="setlang" value="tr" type="submit">🇹🇷</button>
        </div>
        <div class="theme-toggle">
          <button class="theme-btn{' selected' if not dark else ' unselected'}" name="settheme" value="light" type="submit">☀️</button>
          <button class="theme-btn{' selected' if dark else ' unselected'}" name="settheme" value="dark" type="submit">🌙</button>
        </div>
      </form>
    </div>
    ''', unsafe_allow_html=True)

    # Query param ile state güncelle
    qp = st.query_params
    rerun_needed = False
    if qp.get("setlang"):
        st.session_state["lang"] = qp["setlang"]
        rerun_needed = True
    if qp.get("settheme"):
        st.session_state["dark_mode"] = qp["settheme"] == "dark"
        rerun_needed = True
    if rerun_needed:
        if page == "chat":
            st.session_state["page"] = "chat"
        qp.clear()
        st.rerun()

def run(*, tool_def, rag, cv_json):
    # Accordion boşluklarını kaldıran CSS
    st.markdown("""
    <style>
    /* Accordion boşluklarını tamamen kaldır */
    .streamlit-expanderHeader {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    .streamlit-expanderContent {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* Accordion'lar arası boşluk */
    div[data-testid="stExpander"] {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
        padding-bottom: 0 !important;
        padding-top: 0 !important;
    }
    /* Son accordion'da alt boşluk olmasın */
    div[data-testid="stExpander"]:last-child {
        margin-bottom: 0 !important;
    }
    /* Tüm accordion container'ları için */
    div[data-testid="stExpander"] > div {
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Accordion header ve content arasındaki boşluk */
    div[data-testid="stExpander"] .streamlit-expanderHeader {
        margin: 0 !important;
        padding: 8px 16px !important;
    }
    div[data-testid="stExpander"] .streamlit-expanderContent {
        margin: 0 !important;
        padding: 8px 16px !important;
    }
    
    /* Daha güçlü accordion boşluk kaldırma */
    div[data-testid="stExpander"] {
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
    }
    
    /* Her accordion arasındaki boşluğu kaldır */
    div[data-testid="stExpander"] + div[data-testid="stExpander"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Streamlit'in kendi CSS'ini geçersiz kıl */
    .stExpander {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Accordion wrapper'ı için */
    div[data-testid="stExpander"] {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
        padding-bottom: 0 !important;
        padding-top: 0 !important;
        border-spacing: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Tema bazlı CSS
    if st.session_state.dark_mode:
        st.markdown(f"<style>{DARK_CSS}</style>", unsafe_allow_html=True)
    else:
        st.markdown(f"<style>{LIGHT_CSS}</style>", unsafe_allow_html=True)

    for k, v in {
        "lang": "tr",
        "dark_mode": False,
        "chat_history": [],
        "show_cover_form": False,
        "show_job_form": False,
        "welcome_message_shown": False,
        "typing_animation": False,
        "show_projects": False,
    }.items():
        st.session_state.setdefault(k, v)

    # --- Modern Language Toggle Bar (sağ üstte, sabit) ---
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
    .back-btn-fixed {
        position: fixed;
        left: 32px;
        top: 64px;
        z-index: 1001;
    }
    @media (max-width: 600px) {
        .top-right-toggles { right: 8px; top: 32px; }
        .back-btn-fixed { left: 8px; top: 32px; }
    }
    </style>
    """, unsafe_allow_html=True)

    lang = st.session_state.get("lang", "tr")
    dark = st.session_state.get("dark_mode", False)
    page = st.session_state.get("page", "chat")
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

    # Query param ile state güncelle
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

    # --- Geri butonu (sol üstte, sabit) ---
    st.markdown('''
    <style>
    .back-btn-fixed {
        position: fixed !important;
        left: 32px !important;
        top: 64px !important;
        z-index: 1001 !important;
        display: flex !important;
        align-items: center !important;
        height: 54px !important;
    }
    @media (max-width: 600px) {
        .back-btn-fixed { left: 8px !important; top: 32px !important; }
    }
    </style>
    ''', unsafe_allow_html=True)
    back_btn_placeholder = st.empty()
    with back_btn_placeholder.container():
        st.markdown('<div class="back-btn-fixed">', unsafe_allow_html=True)
        if st.button('⬅️ Geri', key='back_to_home_btn', help='Ana sayfaya dön'):
            st.session_state['page'] = 'home'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- AI Asistan Hazır Mesajı ---
    st.markdown("""
    <style>
    .ai-assistant-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        position: relative;
    }

    .ai-assistant-content {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .ai-brain-icon {
        font-size: 1.5em;
        color: #ec4899;
    }
    .ai-message {
        flex: 1;
    }
    .ai-message-title {
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 4px;
        font-size: 1.1em;
    }
    .ai-message-subtitle {
        color: #64748b;
        font-size: 0.95em;
        line-height: 1.4;
    }
    
    /* Dark mode için */
    [data-testid="stAppViewContainer"] [data-testid="stSidebar"] .ai-assistant-card,
    .stApp[data-theme="dark"] .ai-assistant-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
        border: 1px solid #475569 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }
    .stApp[data-theme="dark"] .ai-assistant-title,
    .stApp[data-theme="dark"] .ai-action-btn {
        color: #94a3b8 !important;
    }
    .stApp[data-theme="dark"] .ai-message-title {
        color: #f1f5f9 !important;
    }
    .stApp[data-theme="dark"] .ai-message-subtitle {
        color: #cbd5e1 !important;
    }
    .stApp[data-theme="dark"] .ai-action-btn:hover {
        background: rgba(102, 126, 234, 0.2) !important;
        color: #a5b4fc !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="ai-assistant-card">
        <div class="ai-assistant-content">
            <div class="ai-brain-icon">🧠</div>
            <div class="ai-message">
                <div class="ai-message-title">AI Asistan Hazır!</div>
                <div class="ai-message-subtitle">Hakkımda merak ettiklerini bir tıkla öğrenebilirsin.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Animasyonlu Chat Başlangıcı ---
    if not st.session_state.get("welcome_message_shown", False):
        st.markdown("""
        <style>
        .typing-animation {
            display: inline-block;
            animation: blink 1.4s infinite;
        }
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        .welcome-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 24px;
            border-radius: 18px;
            margin: 20px 0;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.25);
            position: relative;
            overflow: hidden;
        }
        .welcome-message::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: shimmer 2s infinite;
        }
        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        .welcome-message-content {
            position: relative;
            z-index: 1;
        }
        .welcome-message-title {
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .welcome-message-text {
            font-size: 1em;
            line-height: 1.5;
            margin-bottom: 12px;
        }
        .welcome-message-question {
            font-size: 1.1em;
            font-weight: 500;
            color: rgba(255,255,255,0.9);
        }
        .typing-indicator {
            display: inline-block;
            margin-left: 8px;
        }
        .typing-dots {
            display: inline-block;
            animation: typing 1.4s infinite;
        }
        .typing-dots::after {
            content: '...';
            animation: dots 1.4s infinite;
        }
        @keyframes typing {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        
        /* Dark mode için */
        .stApp[data-theme="dark"] .welcome-message {
            background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%) !important;
            box-shadow: 0 8px 25px rgba(124, 58, 237, 0.3) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Önce typing animasyonu göster
        if not st.session_state.get("typing_animation", False):
            with st.chat_message("🤖"):
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.1em;">typing</span>
                    <div class="typing-dots"></div>
                </div>
                """, unsafe_allow_html=True)
            
            # 2 saniye beklet
            import time
            time.sleep(2)
            st.session_state["typing_animation"] = True
            st.rerun()
        else:
            # Karşılama mesajını göster
            welcome_text = {
                "tr": {
                    "title": "👋 Merhaba!",
                    "message": "Ben Fatma Betül'ün AI destekli portföy asistanıyım. CV'sini, projelerini, deneyimlerini ve sosyal medya içeriklerini seninle paylaşabilirim.",
                    "question": "Ne hakkında bilgi almak istersin?"
                },
                "en": {
                    "title": "👋 Hello!",
                    "message": "I'm Fatma Betül’s AI-powered portfolio assistant. I can share her CV, projects, experiences, and social media content with you.",
                    "question": "What would you like to learn more about"
                }
            }
            
            current_lang = st.session_state.get("lang", "tr")
            text = welcome_text[current_lang]
            
            with st.chat_message("🤖"):
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 20px; border-radius: 16px; margin: 8px 0;">
                    <div style="font-size: 1.2em; font-weight: 600; margin-bottom: 8px;">{text['title']}</div>
                    <div style="font-size: 1em; line-height: 1.5; margin-bottom: 12px;">{text['message']}</div>
                    <div style="font-size: 1.1em; font-weight: 500; color: rgba(255,255,255,0.9);">{text['question']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Mesajı chat history'e ekleme - duplicate olmaması için
            # st.session_state.chat_history.append({
            #     "role": "assistant", 
            #     "content": f"{text['title']}<br><br>{text['message']}<br><br><strong>{text['question']}</strong>"
            # })
            
            st.session_state["welcome_message_shown"] = True

    # --- Modern, ikonlu, dikey butonlar ---
    st.markdown("""
    <style>
    /* CV Butonları için Hover Efektleri */
    .cv-button-container {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
        margin: 20px 0;
    }
    
    /* Streamlit butonlarını hedefle */
    .cv-button-container div.stButton > button {
        background: linear-gradient(90deg, #1D3557, #2563eb) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 24px 44px !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.25) !important;
        position: relative !important;
        overflow: hidden !important;
        min-width: 600px !important;
        max-width: 800px !important;
        min-height: 60px !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        justify-content: center !important;
    }
    
    /* Hover efektleri */
    .cv-button-container div.stButton > button:hover {
        cursor: pointer !important;
        transform: scale(1.02) translateY(-2px) !important;
        box-shadow: 0 12px 35px rgba(37, 99, 235, 0.35) !important;
        background: linear-gradient(90deg, #274472, #2563eb) !important;
        color: white !important;
    }
    
    /* Active (tıklama) efekti */
    .cv-button-container div.stButton > button:active {
        transform: scale(0.98) translateY(0px) !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3) !important;
    }
    
    /* Focus efekti */
    .cv-button-container div.stButton > button:focus {
        outline: 2px solid rgba(102, 126, 234, 0.5) !important;
        outline-offset: 2px !important;
    }
    
    /* Shimmer efekti */
    .cv-button-container div.stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .cv-button-container div.stButton > button:hover::before {
        left: 100%;
    }
    
    /* Dark mode için */
    .stApp[data-theme="dark"] .cv-button-container div.stButton > button {
        background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%) !important;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3) !important;
    }
    
    .stApp[data-theme="dark"] .cv-button-container div.stButton > button:hover {
        background: linear-gradient(135deg, #5b21b6 0%, #8b5cf6 100%) !important;
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4) !important;
    }
    
    /* Mobil responsive */
    @media (max-width: 600px) {
        .cv-button-container div.stButton > button {
            font-size: 1.1rem !important;
            padding: 20px 16px !important;
            min-width: 90vw !important;
            max-width: 98vw !important;
            border-radius: 12px !important;
            gap: 8px !important;
            min-height: 56px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    icon_map = {
        "eğitim": "🎓",
        "deneyim": "💼",
        "projeler": "🚀",
        "ödüller": "🏆",
        "referanslar": "📞"
    }
    cv_sections = ["eğitim", "deneyim", "projeler", "ödüller", "referanslar"]
    st.markdown('<div class="cv-button-container">', unsafe_allow_html=True)
    for section in cv_sections:
        if st.button(f"{icon_map[section]} {section.capitalize()}", key=f"cv_section_{section}_modern"):
            lines = []
            if section == "eğitim":
                for edu in cv_json.get("education", []):
                    inst = edu.get("institution", "")
                    degree = edu.get("degree", "")
                    years = edu.get("years", "")
                    lines.append(
                        f"<b>🎓 {inst}</b> <br><i>{degree}</i> <span style='color:#888'>({years})</span>"
                    )
            elif section == "deneyim":
                for exp in cv_json.get("experience", []):
                    title = exp.get("title", "")
                    company = exp.get("company", "")
                    duration = exp.get("duration", "")
                    desc = exp.get("description", "")
                    lines.append(
                        f"<b>💼 {title}</b> <br><i>{company}</i> <span style='color:#888'>({duration})</span><br>{desc}"
                    )
            elif section == "projeler":
                st.session_state.show_projects = True
                # Chat geçmişine ekleme - sadece projeleri göster
                st.rerun()
            elif section == "ödüller":
                for award in cv_json.get("awards", []):
                    name = award.get("name", "")
                    org = award.get("organization", "")
                    lines.append(f"<b>🏆 {name}</b> <br><i>{org}</i>")
            elif section == "referanslar":
                for ref in cv_json.get("references", []):
                    name = ref.get("name", "")
                    title = ref.get("title", "")
                    org = ref.get("organization", "")
                    lines.append(f"<b>📞 {name}</b> <br><i>{title}</i> <span style='color:#888'>({org})</span>")
            if not lines:
                lines.append("Bilgi bulunamadı.")
            st.markdown("""
            <style>
            .chat-block {
              margin: 12px 0;
              padding: 12px 16px;
              border-radius: 14px;
              background: #f3f4f8;
              color: #333;
              box-shadow: 0 1px 4px rgba(0,0,0,0.05);
            }
            </style>
            """, unsafe_allow_html=True)
            response = "".join(f"<div class='chat-block'>{line}</div>" for line in lines)
            st.session_state.chat_history.append({"role": "user", "content": section.capitalize()})
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.session_state.page = "chat"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
        
    # --- Eski, büyük, yatay butonlar ve ilgili kodlar tamamen kaldırıldı ---

    # ---------- Chat geçmişi ----------
    # --- 2) Ekrana mevcut geçmişi bas ---
    for m in st.session_state.chat_history:
        if isinstance(m, dict):
            role = m.get("role", "assistant")
            content = m.get("content", "")
        elif isinstance(m, tuple) and len(m) == 2:
            role, content = m
        else:
            continue  # Beklenmeyen tipte veri varsa atla
        with st.chat_message("🧑‍💼" if role == "user" else "🤖"):
            st.markdown(content, unsafe_allow_html=True)

    # ---------- Projeler Accordion ----------
    if st.session_state.get("show_projects", False):
        st.markdown("""
        <style>
        .project-accordion {
            margin: 16px 0;
        }
        .project-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 600;
            font-size: 1.1em;
        }
        .project-header:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .project-content {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 8px;
            margin-left: 20px;
        }
        .project-section {
            margin-bottom: 16px;
            padding: 12px;
            background: #f8fafc;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .section-title {
            color: #667eea;
            font-weight: 600;
            font-size: 1.1em;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .section-content {
            color: #374151;
            line-height: 1.6;
            padding-left: 8px;
        }
        .project-links {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #e5e7eb;
        }
        .project-link {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.9em;
            margin-right: 8px;
            margin-bottom: 4px;
            transition: all 0.2s ease;
        }
        .project-link:hover {
            background: #5a67d8;
            transform: translateY(-1px);
        }
        
        /* Accordion başlık özeti için */
        .expander-header small {
            display: block;
            margin-top: 4px;
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        /* Proje özeti kutusu */
        .project-summary {
            background: #f0f2f6;
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 12px;
            border-left: 3px solid #667eea;
        }
        
        /* Dark mode için accordion başlık özeti */
        .stApp[data-theme="dark"] .expander-header small {
            color: #cbd5e1 !important;
        }
        
        /* Dark mode için proje özeti */
        .stApp[data-theme="dark"] .project-summary {
            background: #334155 !important;
            border-left-color: #8b5cf6 !important;
        }
        .stApp[data-theme="dark"] .project-summary small {
            color: #e2e8f0 !important;
        }
        
        /* Dark mode için */
        .stApp[data-theme="dark"] .project-content {
            background: #1e293b !important;
            border-color: #475569 !important;
        }
        .stApp[data-theme="dark"] .project-section {
            background: #334155 !important;
            border-left-color: #8b5cf6 !important;
        }
        .stApp[data-theme="dark"] .section-title {
            color: #8b5cf6 !important;
        }
        .stApp[data-theme="dark"] .section-content {
            color: #e2e8f0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🚀 Projeler")
        
        # Projeleri accordion olarak göster
        for i, proj in enumerate(cv_json.get("projects", [])):
            name = proj.get("name", "")
            tech = proj.get("technology", "")
            desc = proj.get("description", "")
            links = proj.get("links", [])
            
            # Sabit proje ikonları (görsel tutarlılık için)
            project_icons = {
                "AI-Powered Portfolio Chatbot": "🚀",
                "Mobile App User Behavior Analysis": "📊", 
                "Customer Churn Prediction": "🎯",
                "Movie Recommendation System": "🎬",
                "Natural Language to SQL Query Tool": "💬",
                "Smart Home Energy Management Application": "🏠",
                "Credit Score Prediction": "💰",
                "Energy Consumption Prediction API": "⚡",
                "AdventureWorks Sales Dashboard": "📈",
                "Real-Time Face Recognition App": "👤",
                "Safe Area Detection": "🛡️",
                "Market Prices Automation": "🛒",
                "Simple E-Commerce System with Python": "🛍️"
            }
            
            icon = project_icons.get(name, "🚀")  # Sabit ikonlar
            
            # Kısa özet oluştur (dil desteği ile)
            current_lang = st.session_state.get("lang", "tr")
            short_summary = ""
            
            if "AI-Powered Portfolio Chatbot" in name:
                short_summary = "💬 AI destekli CV tabanlı asistan, job-fit & cover letter üretir" if current_lang == "tr" else "💬 AI-powered CV-based assistant, generates job-fit & cover letters"
            elif "Mobile App User Behavior Analysis" in name:
                short_summary = "📱 Kullanıcı davranış analizi ve segmentasyon" if current_lang == "tr" else "📱 User behavior analysis and segmentation"
            elif "Customer Churn Prediction" in name:
                short_summary = "📉 Müşteri kaybı tahmin modeli" if current_lang == "tr" else "📉 Customer churn prediction model"
            elif "Movie Recommendation System" in name:
                short_summary = "🎭 150M+ kayıt ile kişiselleştirilmiş film önerileri" if current_lang == "tr" else "🎭 Personalized movie recommendations with 150M+ records"
            elif "Natural Language to SQL Query Tool" in name:
                short_summary = "🗣️ Doğal dil ile SQL sorguları" if current_lang == "tr" else "🗣️ Natural language to SQL queries"
            elif "Smart Home Energy Management" in name:
                short_summary = "🏠 Akıllı ev enerji yönetimi" if current_lang == "tr" else "🏠 Smart home energy management"
            elif "Credit Score Prediction" in name:
                short_summary = "💳 Kredi skoru tahmin sistemi" if current_lang == "tr" else "💳 Credit score prediction system"
            elif "Energy Consumption Prediction API" in name:
                short_summary = "⚡ Enerji tüketimi tahmin API'si" if current_lang == "tr" else "⚡ Energy consumption prediction API"
            elif "AdventureWorks Sales Dashboard" in name:
                short_summary = "📊 Satış optimizasyonu dashboard'u" if current_lang == "tr" else "📊 Sales optimization dashboard"
            elif "Real-Time Face Recognition App" in name:
                short_summary = "👤 Gerçek zamanlı yüz tanıma uygulaması" if current_lang == "tr" else "👤 Real-time face recognition app"
            elif "Safe Area Detection" in name:
                short_summary = "🛡️ Güvenli alan tespit sistemi" if current_lang == "tr" else "🛡️ Safe area detection system"
            elif "Market Prices Automation" in name:
                short_summary = "🛒 Pazar fiyatları otomasyonu" if current_lang == "tr" else "🛒 Market prices automation"
            elif "Simple E-Commerce System" in name:
                short_summary = "🛍️ Basit e-ticaret sistemi" if current_lang == "tr" else "🛍️ Simple e-commerce system"
            
            # GitHub linki varsa özete ekle (artık eklemiyoruz)
            # github_url = proj.get("github", "")
            # if github_url:
            #     short_summary += " [GitHub]"
            
            # Accordion başlığı
            expander_title = f"{icon} {name}"
            
            # Accordion başlığına tooltip ekle
            if short_summary:
                tooltip_css = f"""
                <style>
                .accordion-tooltip-{i} {{
                    position: relative;
                    margin-bottom: 0 !important;
                }}
                .accordion-tooltip-{i} .streamlit-expanderHeader {{
                    margin-bottom: 0 !important;
                    padding-bottom: 8px !important;
                }}
                .accordion-tooltip-{i}:hover::after {{
                    content: "{short_summary}";
                    position: absolute;
                    bottom: 130%;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #333;
                    color: white;
                    padding: 10px 15px;
                    border-radius: 8px;
                    font-size: 14px;
                    z-index: 1000;
                    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                    max-width: 300px;
                    word-wrap: break-word;
                    white-space: normal;
                }}
                .accordion-tooltip-{i}:hover::before {{
                    content: "";
                    position: absolute;
                    bottom: 125%;
                    left: 50%;
                    transform: translateX(-50%);
                    border: 6px solid transparent;
                    border-top-color: #333;
                    z-index: 1000;
                }}
                </style>
                """
                st.markdown(tooltip_css, unsafe_allow_html=True)
                
                # Accordion'u tooltip ile sar
                st.markdown(f'<div class="accordion-tooltip-{i}">', unsafe_allow_html=True)
                with st.expander(expander_title, expanded=False):
                    # Teknolojiler bölümü
                    st.markdown("**🛠️ Teknolojiler:**")
                    st.markdown(tech)
                    
                    # Açıklama bölümü
                    st.markdown("**📝 Açıklama:**")
                    # Dil desteği için açıklamayı kontrol et
                    if isinstance(desc, dict):
                        # Çoklu dil desteği varsa
                        current_lang = st.session_state.get("lang", "tr")
                        description = desc.get(current_lang, desc.get("en", desc.get("tr", str(desc))))
                    else:
                        # Tek dil (string) ise
                        description = desc
                    st.markdown(description)
                    
                    # Özellikler bölümü
                    features = proj.get("features", "")
                    features_list = []

                    # Dil desteği için özellikleri kontrol et
                    if isinstance(features, dict):
                        # Çoklu dil desteği varsa
                        current_lang = st.session_state.get("lang", "tr")
                        features = features.get(current_lang, features.get("en", features.get("tr", [])))

                    if isinstance(features, list):
                        features_list = features
                    elif isinstance(features, str):
                        features_clean = features.replace("<br>", "\n").replace("•", "")
                        features_list = [f.strip() for f in features_clean.split("\n") if f.strip()]

                    if features_list:
                        features_html = """
                        <div class="project-section">
                            <div class="section-title">✨ <strong>Özellikler</strong></div>
                            <div class="section-content">
                        """
                        for feature in features_list:
                            features_html += f"<div>• {feature}</div>"

                        features_html += """
                            </div>
                        </div>
                        """  # 🔐 Kapanışlar burada net

                        st.markdown(features_html, unsafe_allow_html=True)
                    
                    # GitHub linki
                    github_url = proj.get("github", "")
                    if github_url:
                        st.markdown("**🔗 GitHub:**")
                        st.markdown(f"[📂 Projeyi İncele]({github_url})")
                    
                    # Diğer linkler
                    if links:
                        st.markdown("**🔗 Diğer Linkler:**")
                        for link in links:
                            if isinstance(link, dict):
                                url = link.get("url", "")
                                text = link.get("text", "Link")
                            else:
                                url = link
                                text = "Proje Linki"
                            st.markdown(f"[{text}]({url})")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                with st.expander(expander_title, expanded=False):
                    # Teknolojiler bölümü
                    st.markdown("**🛠️ Teknolojiler:**")
                    st.markdown(tech)
                    
                    # Açıklama bölümü
                    st.markdown("**📝 Açıklama:**")
                    # Dil desteği için açıklamayı kontrol et
                    if isinstance(desc, dict):
                        # Çoklu dil desteği varsa
                        current_lang = st.session_state.get("lang", "tr")
                        description = desc.get(current_lang, desc.get("en", desc.get("tr", str(desc))))
                    else:
                        # Tek dil (string) ise
                        description = desc
                    st.markdown(description)
                    
                    # Özellikler bölümü
                    features = proj.get("features", "")
                    features_list = []

                    # Dil desteği için özellikleri kontrol et
                    if isinstance(features, dict):
                        # Çoklu dil desteği varsa
                        current_lang = st.session_state.get("lang", "tr")
                        features = features.get(current_lang, features.get("en", features.get("tr", [])))

                    if isinstance(features, list):
                        features_list = features
                    elif isinstance(features, str):
                        features_clean = features.replace("<br>", "\n").replace("•", "")
                        features_list = [f.strip() for f in features_clean.split("\n") if f.strip()]

                    if features_list:
                        features_html = """
                        <div class="project-section">
                            <div class="section-title">✨ <strong>Özellikler</strong></div>
                            <div class="section-content">
                        """
                        for feature in features_list:
                            features_html += f"<div>• {feature}</div>"

                        features_html += """
                            </div>
                        </div>
                        """  # 🔐 Kapanışlar burada net

                        st.markdown(features_html, unsafe_allow_html=True)
                    
                    # GitHub linki
                    github_url = proj.get("github", "")
                    if github_url:
                        st.markdown("**🔗 GitHub:**")
                        st.markdown(f"[📂 Projeyi İncele]({github_url})")
                    
                    # Diğer linkler
                    if links:
                        st.markdown("**🔗 Diğer Linkler:**")
                        for link in links:
                            if isinstance(link, dict):
                                url = link.get("url", "")
                                text = link.get("text", "Link")
                            else:
                                url = link
                                text = "Proje Linki"
                            st.markdown(f"[{text}]({url})")

    # --- Cover letter PDF indir butonu ---
    if "cover_pdf_bytes" in st.session_state:
        st.download_button(
            "💾 Ön Yazıyı PDF Olarak İndir",
            data      = st.session_state.cover_pdf_bytes,
            file_name = st.session_state.cover_pdf_name,
            mime      = "application/pdf",
            key       = "cover_pdf_dl"
        )

    # --- Cover letter formu ---
    if st.session_state.get("show_cover_form"):
        _cover_letter_form(tool_def, rag)
        st.stop()

    # ---------- Aktif formlar ----------
    if st.session_state.show_cover_form:
        _cover_letter_form(tool_def, rag)
        st.stop()
    if st.session_state.show_job_form:
        _job_compatibility_flow(tool_def, LANG_TEXTS[st.session_state.lang])
        st.stop()

    # --- Chat geçmişi state kontrolü ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # --- 1) Girdiyi anında yakala ---
    user_msg = st.chat_input(LANG_TEXTS[st.session_state.lang]["input_placeholder"])

    # Kullanıcı 'cover letter yaz', 'ön yazı', 'cover letter', veya 'ön yazı yaz' derse formu aç
    trigger_phrases = ["cover letter yaz", "ön yazı", "cover letter", "ön yazı yaz"]
    if user_msg and any(p in user_msg.lower() for p in trigger_phrases):
        st.session_state.show_cover_form = True
        st.rerun()

    if user_msg and (not st.session_state.get("last_user_msg") or st.session_state.last_user_msg != user_msg):
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        st.session_state.last_user_msg = user_msg
        
        # Son 3 mesajı al (çok uzun geçmiş olmasın)
        recent_history = st.session_state.chat_history[-6:] if len(st.session_state.chat_history) > 6 else st.session_state.chat_history
        history_text = "\n".join([
                f"{m['role']}: {m['content']}" for m in recent_history if isinstance(m, dict)
            ])
        
        # Dil seçimine göre prompt oluştur
        current_lang = st.session_state.get("lang", "tr")
        if current_lang == "tr":
            language_prompt = "Sen Fatma Betül'ün AI portföy asistanısın. Sadece Türkçe cevap ver. İngilizce çeviri yapma. Kullanıcının mesajına odaklan, önceki konulardan bağımsız olarak yanıtla."
        else:
            language_prompt = "You are Fatma Betül's AI portfolio assistant. Answer only in English. Do not provide Turkish translations. Focus on the user's message, respond independently of previous topics."
        
        full_prompt = f"{language_prompt}\n\n{history_text}"
        assistant_reply = ask_gemini(full_prompt)
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
        st.rerun()



# ------------------------------------------------------------------ #
def _cover_letter_form(tool_def, rag):
    with st.form("cover_letter"):
        st.info("📄 Ön yazıyı oluşturun:")
        job_desc = st.text_area("💼 İş Tanımı")
        company  = st.text_input("🏢 Şirket")
        lang     = st.selectbox("🌐 Dil", ["tr", "en"])
        submitted = st.form_submit_button("✍️ Oluştur")

    if not submitted:
        return

    cv_text = "\n".join(rag.search_similar_chunks("özgeçmiş"))
    res = tool_def.execute_tool("generate_cover_letter", {
        "job_description": job_desc,
        "cv_text": cv_text,
        "language": lang,
        "company_name": company,
    })

    if res["success"]:
        letter_text = res["data"]["text"]
        st.session_state.chat_history.append({"role": "assistant", "content": letter_text})
        st.session_state.cover_pdf_bytes = res["data"]["pdf_bytes"]
        st.session_state.cover_pdf_name  = res["data"]["filename"]
        st.session_state.show_cover_form = False
        st.rerun()
    else:
        st.session_state.chat_history.append({"role": "assistant", "content": f"❌ {res['message']}"})
        st.session_state.show_cover_form = False
        st.rerun()



def _job_compatibility_flow(tool_def, LTXT):
    with st.form("job_form"):
        st.info("📊 İş uyum analizi için iş ilanını girin.")
        job_desc = st.text_area("💼 İş Tanımı")
        company = st.text_input("🏢 Şirket Adı")
        lang = st.selectbox("🌐 Dil", ["tr", "en"])
        submitted = st.form_submit_button("🚀 Analizi Başlat")
    if not submitted:
        return

    result = tool_def.execute_tool(
        "analyze_job_compatibility",
        {
            "job_description": job_desc,
            "report_language": lang,
            "company_name": company,
        },
    )
    reply = (
        result["data"]["report_text"]
        if result.get("success")
        else "Analiz oluşturulamadı 😕"
    )
    st.session_state.chat_history.append({"role": "bot", "content": reply})

st.markdown("""
<style>
.big-action-btn {
    width: 720px !important;
    min-width: 600px;
    font-size: 1.45em;
    padding: 22px 0;
    border-radius: 18px;
    margin-bottom: 32px;
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
.big-action-btn.chat {
    background: linear-gradient(90deg, #3A86FF, #219EBC);
}
.big-action-btn span {
    display: inline-block;
}
</style>
""", unsafe_allow_html=True)

# --- Remove main page buttons at the end ---
