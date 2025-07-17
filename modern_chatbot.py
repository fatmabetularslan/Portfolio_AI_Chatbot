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
        position: fixed;
        left: 32px;
        top: 64px;
        z-index: 1001;
    }
    @media (max-width: 600px) {
        .back-btn-fixed { left: 8px; top: 32px; }
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

    # --- Modern, ikonlu, dikey butonlar ---
    icon_map = {
        "eğitim": "🎓",
        "deneyim": "💼",
        "projeler": "🚀",
        "ödüller": "🏆",
        "referanslar": "📞"
    }
    cv_sections = ["eğitim", "deneyim", "projeler", "ödüller", "referanslar"]
    st.markdown('<div style="display: flex; flex-direction: column; align-items: flex-start; gap: 8px;">', unsafe_allow_html=True)
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
                for proj in cv_json.get("projects", []):
                    name = proj.get("name", "")
                    tech = proj.get("technology", "")
                    desc = proj.get("description", "")
                    lines.append(
                        f"<b>🚀 {name}</b> <br><i>{tech}</i><br>{desc}"
                    )
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
    for msg in st.session_state.chat_history:
        if isinstance(msg, dict):
            role = msg.get("role", "bot")
            content = msg.get("content", "")
        else:
            role, content = msg
        with st.chat_message("🧑‍💼" if role == "user" else "🤖"):
            st.markdown(content, unsafe_allow_html=True)

    # ---------- Önce PDF butonu (varsa) ----------
    if "cover_pdf_bytes" in st.session_state:
        st.download_button(
            "💾 Ön Yazıyı PDF Olarak İndir",
            data      = st.session_state.cover_pdf_bytes,
            file_name = st.session_state.cover_pdf_name,
            mime      = "application/pdf",
            key       = "cover_pdf_dl"
        )

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

    if user_msg and (not st.session_state.get("last_user_msg") or st.session_state.last_user_msg != user_msg):
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        st.session_state.last_user_msg = user_msg
        history_text = "\n".join([
                f"{m['role']}: {m['content']}" for m in st.session_state.chat_history if isinstance(m, dict)
            ])
        assistant_reply = ask_gemini(history_text)
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
        st.session_state.chat_history.append({"role": "bot", "content": letter_text})
        with st.chat_message("🤖"):
            st.markdown(letter_text)
            # PDF’i oturumda sakla  🔸
        st.session_state.cover_pdf_bytes = res["data"]["pdf_bytes"]
        st.session_state.cover_pdf_name  = res["data"]["filename"]
        # 💾 2) PDF indir butonu
        st.download_button(
            "💾 Ön Yazıyı PDF Olarak İndir",
            data      = res["data"]["pdf_bytes"],
            file_name = res["data"]["filename"],
            mime      = "application/pdf"
        )
    else:
        st.session_state.chat_history.append({"role": "bot", "content": f"❌ {res['message']}"})

    st.session_state.show_cover_form = False
    #st.rerun()



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
    width: 420px !important;
    min-width: 320px;
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
