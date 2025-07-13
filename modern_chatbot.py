# modern_chatbot.py
import streamlit as st
import time
from datetime import datetime
from tools.gemini_tool import ask_gemini, generate_cover_letter
from common_css import LIGHT_CSS, DARK_CSS
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

# ------------------------------------------------------------------ #
def run(*, tool_def, rag, cv_json):
    # st.session_state.setdefault("dark_mode", False)  # KALDIRILDI

    # sağ üst anahtar
    # dark = st.toggle("🌙", value=st.session_state.dark_mode, key="dm_chat")
    # st.session_state.dark_mode = dark

    # Sadece ilgili CSS'i uygula
    if st.session_state.dark_mode:
        st.markdown(f"<style>{DARK_CSS}</style>", unsafe_allow_html=True)
    else:
        st.markdown(f"<style>{LIGHT_CSS}</style>", unsafe_allow_html=True)

    # Eğer özel bir CSS (CSS değişkeni) ekleniyorsa, onu da dark kontrolüne bağla
    # (Varsa, örnek olarak aşağıya ekliyorum)
    # if dark:
    #     st.markdown(f"<style>{DARK_CSS}</style>", unsafe_allow_html=True)
    # else:
    #     st.markdown(CSS, unsafe_allow_html=True)

    for k, v in {
        "lang": "tr",
        "dark_mode": False,
        "chat_history": [],
        "show_cover_form": False,
        "show_job_form": False,
    }.items():
        st.session_state.setdefault(k, v)

    # ---------- Stil ----------
    # Bu kısmı kaldırıyorum, çünkü yukarıda dark kontrolüyle CSS zaten eklendi
    # st.markdown(f"<style>{DARK_CSS}</style>", unsafe_allow_html=True)

    # ---------- Dil düğmesi ----------
    lang = st.session_state.lang
    LTXT = LANG_TEXTS[lang]
    col_tr, col_en = st.columns(2)
    with col_tr:
        if st.button("🇹🇷"): st.session_state.lang = "tr"; lang, LTXT = "tr", LANG_TEXTS["tr"]
    with col_en:
        if st.button("🇬🇧"): st.session_state.lang = "en"; lang, LTXT = "en", LANG_TEXTS["en"]

    # ---------- Profil kartı ----------
    prof = cv_json
    st.markdown(f"""<div class="profile-card"> … </div>""", unsafe_allow_html=True)
    
        # ---------- CV Bölüm Butonları ----------
   # ---------- CV BÖLÜM BUTONLARI ----------
    SECTION_MAP = {
        "🎓 Eğitim"      : ("education" ,  lambda i: f"<li>{i['institution']} – {i.get('degree','')} ({i.get('years','')})</li>"),
        "💼 Deneyim"     : ("experience" , lambda i: f"<li>{i['title']} – {i['company']} ({i['duration']})</li>"),
        "🚀 Projeler"    : ("projects"   , lambda i: f"<li>{i['name']} ({i['technology']}) – {i['description']}</li>"),
        "🏆 Ödüller"     : ("awards"     , lambda i: f"<li>{i['name']} – {i['organization']}</li>"),
        "📜 Sertifikalar": ("certificates", lambda i: f"<li>{i['name']} – {i['provider']} ({i['year']})</li>"),
        "🤝 Gönüllülük"  : ("volunteer"  , lambda i: f"<li>{i['role']} – {i['organization']} ({i['years']})</li>"),
        "📞 Referanslar" : ("references" , lambda i: f"<li>{i['name']} – {i['title']} ({i['organization']})</li>"),
    }

    FORMATTERS = {cv: fmt for _, (cv, fmt) in SECTION_MAP.items()}

    # ------ Butonlar ------
    # 1) CV’de mevcut bölümlerden liste oluştur
    btn_info = [(label, cv_key)                       # -> [('🎓 Eğitim','education'), ...]
                for label, (cv_key, _) in SECTION_MAP.items()
                if prof.get(cv_key)]

    # 2) Her buton için bir sütun (yan yana)
    cols = st.columns(len(btn_info), gap="small")

    # 3) Butonları çiz ve tıklandığında section seç
    for col, (label, cv_key) in zip(cols, btn_info):
        if col.button(label, key=f"btn_{cv_key}", use_container_width=True):
            st.session_state.selected_cv_section = cv_key
            st.rerun()



        

    # ---------- Chat geçmişi ----------
    for role, msg in st.session_state.chat_history:
        with st.chat_message("🧑‍💼" if role == "user" else "🤖"):
            st.markdown(msg, unsafe_allow_html=True)

    # --- CV bölümü seçildiyse bot cevabı oluştur ---
    if "selected_cv_section" in st.session_state:
        key        = st.session_state.pop("selected_cv_section")
        raw_items  = prof.get(key, [])
        fmt        = FORMATTERS[key]                  # doğrudan sözlükten
        items_html = "\n".join(fmt(i) for i in raw_items) or "<li>Bilgi bulunamadı.</li>"
        bot_reply  = f"<ul style='margin-left:0.8em;padding-left:0.8em'>{items_html}</ul>"

        st.session_state.chat_history.append(("bot", bot_reply))
        st.rerun()
            

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
        _job_compatibility_flow(tool_def, LTXT)
        st.stop()

    # ---------- Kullanıcı girişi ----------
    user_msg = st.chat_input(LTXT["input_placeholder"])
    if user_msg:
        st.session_state.chat_history.append(("user", user_msg))
        lowered = user_msg.lower()

        if "ön yazı" in lowered or "cover letter" in lowered:
            st.session_state.show_cover_form = True
            st.rerun()                               # formu göstermek için

        elif "iş uyum" in lowered or "compatibility" in lowered:
            st.session_state.show_job_form = True
            st.rerun()

        else:
            chunks  = rag.search_similar_chunks(user_msg)
            chunk_text = "\n".join(chunks)
            prompt = f"Fatma Betül'ün özgeçmiş bilgileri:\n{chunk_text}\n\nSoru: {user_msg}"
            answer  = ask_gemini(prompt)
            st.session_state.chat_history.append(("bot", answer))
            # burada rerun gerekmez; mesaj zaten görünüyor



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
        st.session_state.chat_history.append(("bot", letter_text))
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
        st.session_state.chat_history.append(("bot", f"❌ {res['message']}"))

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
    st.session_state.chat_history.append(("bot", reply))
