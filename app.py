# app.py
import streamlit as st, json
st.set_page_config(page_title="Fatma Betül Arslan", page_icon="🤖", layout="centered")

from tools.rag_system import RAGSystem
from tools.tool_definitions import ToolDefinitions
import modern_chatbot
from common_css import LIGHT_CSS, DARK_CSS

st.session_state.setdefault("dark_mode", False)

# --- sol üst switch ---
dark = st.toggle("🌙 Karanlık Mod", value=st.session_state.dark_mode, key="dm_home")
st.session_state.dark_mode = dark       # state senkron

# --- Stil enjekte (en başta) ---
if dark:
    st.markdown(f"<style>{DARK_CSS}</style>", unsafe_allow_html=True)
    import streamlit.components.v1 as components
    components.html(
        """
        <script>
        // her 200 ms’de bir menü varsa koyulaştır
        const dark = setInterval(() => {
          const pop = document.querySelector('[data-baseweb="popover"]');
          if (pop){
             pop.style.background = "#23272f";
             pop.style.color      = "#f5f6fa";
             pop.querySelectorAll('[role="option"]').forEach(o=>{
                 o.style.background="#23272f";
                 o.style.color="#f5f6fa";
             });
          }
        }, 200);
        // sayfa kapandığında temizle
        window.addEventListener("beforeunload",()=>clearInterval(dark));
        </script>
        """,
        height=0,
    )
else:
    st.markdown(f"<style>{LIGHT_CSS}</style>", unsafe_allow_html=True)

# ---------- RAG & CV ----------
rag = RAGSystem("betül-cv.json")
with open("betül-cv.json", encoding="utf-8") as f:
    cv_json = json.load(f)

tools = ToolDefinitions()
tools.initialize_job_analyzer(
    client=None,
    cv_data=cv_json,
    rag_system=rag,
)

# ---------- Sayfa durumu ----------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

# ---------- Chat sayfası ----------
if st.session_state["page"] == "chat":
    modern_chatbot.run(tool_def=tools, rag=rag, cv_json=cv_json)
    st.stop()  # Chat çizildi, ana sayfa kodu çalışmasın

# ---------- Ana sayfa ----------
TEXT = {
    "tr": {
        "header": "👋 Merhaba! Ben Fatma Betül'ün AI Portföy Asistanıyım",
        "sub": "CV, projeler, sosyal medya içerikleri ve iş başvurularında size yardımcı olurum.",
        "cv": "📂 CV'yi Gör",
        "chat": "🤖 Sohbete Başla",
    },
    "en": {
        "header": "👋 Hi! I'm Fatma Betül's AI Portfolio Assistant",
        "sub": "I can help you with CV, projects, social media and job applications.",
        "cv": "📂 View CV",
        "chat": "🤖 Start Chat",
    },
}
lang = st.selectbox("🌐 Dil / Language", ["tr", "en"])
t = TEXT[lang]

st.markdown(f"## {t['header']}")
st.markdown(t["sub"])
st.markdown(
    "[LinkedIn](https://www.linkedin.com/in/fatma-bet%C3%BCl-arslan-9866291b1/) • "
    "[GitHub](https://github.com/betularsln) • "
    "[Medium](https://medium.com/@betularsln01)"
)

def show_cv_info():
    st.info("CV görüntüleme yakında!")

col_cv, col_chat = st.columns(2)
with col_cv:
    st.button(t["cv"], on_click=show_cv_info)
with col_chat:
    st.button(
        t["chat"],
        on_click=lambda: st.session_state.update(page="chat")
    )
