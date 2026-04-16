from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from src.config import load_settings
from src.engine import STEPS, ConversationEngine

load_dotenv()

st.set_page_config(
    page_title="TalentScout Hiring Assistant",
    page_icon="TS",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&display=swap');
    :root {
      --bg-primary: #191b20;
      --bg-secondary: #20232b;
      --bg-tertiary: #272b34;
      --border: rgba(255, 255, 255, 0.12);
      --text: #f3f4f6;
      --muted: #a9afbb;
      --assistant: #232730;
      --user: #1f3a2f;
      --accent: #77d2ff;
      --shadow: 0 6px 24px rgba(0, 0, 0, 0.28);
    }
    html, body, [class*="css"] {
      font-family: 'Manrope', sans-serif;
      color: var(--text);
    }
    .stApp {
      background:
        radial-gradient(circle at 20% 0%, rgba(78, 92, 128, 0.26), transparent 34%),
        radial-gradient(circle at 95% 0%, rgba(45, 58, 84, 0.24), transparent 38%),
        linear-gradient(180deg, #15171c 0%, var(--bg-primary) 100%);
      color: var(--text);
    }
    [data-testid="stAppViewContainer"] .main .block-container {
      max-width: 880px;
      padding-top: 1.25rem;
      padding-bottom: 8rem;
    }
    header[data-testid="stHeader"] {
      background: transparent;
    }
    #MainMenu, footer {
      visibility: hidden;
    }
    [data-testid="stSidebar"] {
      display: none;
    }
    .hero {
      border: 1px solid var(--border);
      border-radius: 16px;
      background: linear-gradient(135deg, #1f2430 0%, #272b34 100%);
      box-shadow: var(--shadow);
      padding: 16px 18px;
      margin-bottom: 12px;
    }
    .hero-title {
      margin: 0;
      font-size: 1.28rem;
      font-weight: 700;
      color: var(--text);
      letter-spacing: 0.01em;
    }
    .hero-subtitle {
      margin: 6px 0 0 0;
      color: var(--muted);
      font-size: 0.94rem;
    }
    .state-pill {
      display: inline-block;
      margin-top: 10px;
      border-radius: 999px;
      padding: 5px 10px;
      background: rgba(119, 210, 255, 0.14);
      border: 1px solid rgba(119, 210, 255, 0.35);
      color: #c6ebff;
      font-size: 0.79rem;
      font-weight: 700;
    }
    div[data-testid="stExpander"] details {
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--bg-secondary);
      box-shadow: var(--shadow);
    }
    div[data-testid="stExpander"] summary {
      color: var(--text) !important;
      font-weight: 600;
    }
    .snapshot-row {
      border: 1px solid var(--border);
      border-radius: 10px;
      background: var(--bg-tertiary);
      padding: 9px 11px;
      margin-bottom: 7px;
    }
    .snapshot-label {
      margin: 0;
      font-size: 0.76rem;
      color: var(--muted);
    }
    .snapshot-value {
      margin: 2px 0 0 0;
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--text);
    }
    [data-testid="stChatMessage"] {
      border: 1px solid var(--border);
      border-radius: 14px;
      margin-bottom: 11px;
      box-shadow: var(--shadow);
      padding: 10px 12px;
      background: var(--assistant);
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
      background: var(--user);
      border-color: rgba(134, 239, 172, 0.28);
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
      background: var(--assistant);
      border-color: rgba(148, 163, 184, 0.32);
    }
    [data-testid="stChatMessageContent"],
    [data-testid="stChatMessageContent"] * {
      color: var(--text) !important;
      font-size: 1rem;
      line-height: 1.58;
    }
    [data-testid="stChatInput"] > div {
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(39, 43, 52, 0.95);
      box-shadow: var(--shadow);
      padding-left: 10px;
      padding-right: 10px;
    }
    [data-testid="stChatInput"] textarea {
      color: var(--text) !important;
      background: transparent !important;
      font-size: 1.02rem !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
      color: var(--muted) !important;
      opacity: 1;
    }
    [data-testid="stNotificationContentInfo"],
    [data-testid="stNotificationContentSuccess"] {
      color: var(--text) !important;
      background: var(--bg-secondary) !important;
      border: 1px solid var(--border) !important;
    }
    .separator {
      height: 1px;
      background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.16) 18%, rgba(255, 255, 255, 0.16) 82%, transparent 100%);
      margin: 14px 0 12px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize() -> None:
    if "engine" not in st.session_state:
        settings = load_settings()
        st.session_state.engine = ConversationEngine(settings=settings)
        st.session_state.messages = []
        st.session_state.ended = False
        for message in st.session_state.engine.start_messages():
            st.session_state.messages.append({"role": "assistant", "content": message})


def _display_value(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "Pending"
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value)
    if value is None:
        return "Pending"
    text = str(value).strip()
    return text if text else "Pending"


def _profile_completion(engine: ConversationEngine) -> tuple[int, int]:
    completed = 0
    for step in STEPS:
        value = getattr(engine.profile, step.field_name)
        if isinstance(value, list):
            completed += int(bool(value))
        elif isinstance(value, float):
            completed += int(value > 0)
        else:
            completed += int(bool(str(value).strip()))
    return completed, len(STEPS)


def _render_header(engine: ConversationEngine) -> None:
    state_text = (
        "Conversation completed"
        if st.session_state.ended
        else (
            "Technical round in progress"
            if engine.phase == "technical_round"
            else "Collecting candidate profile"
        )
    )
    st.markdown(
        f"""
        <div class="hero">
          <p class="hero-title">TalentScout Hiring Assistant</p>
          <p class="hero-subtitle">AI screening chatbot for candidate intake and technical evaluation.</p>
          <span class="state-pill">{state_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_snapshot(engine: ConversationEngine) -> None:
    completed, total = _profile_completion(engine)
    with st.expander("Candidate Snapshot", expanded=True):
        st.progress(completed / total, text=f"Profile completion: {completed}/{total}")
        rows = [
            ("Full Name", engine.profile.full_name),
            ("Email", engine.profile.email),
            ("Phone Number", engine.profile.phone_number),
            ("Years of Experience", engine.profile.years_of_experience),
            ("Desired Role(s)", engine.profile.desired_positions),
            ("Location", engine.profile.current_location),
            ("Tech Stack", engine.profile.tech_stack),
        ]
        for label, value in rows:
            st.markdown(
                (
                    "<div class='snapshot-row'>"
                    f"<p class='snapshot-label'>{label}</p>"
                    f"<p class='snapshot-value'>{_display_value(value)}</p>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

        asked = len(engine.technical_responses)
        total_questions = len(engine.technical_questions)
        if total_questions:
            st.progress(
                asked / total_questions,
                text=f"Technical progress: {asked}/{total_questions}",
            )
        else:
            st.caption("Technical questions start after profile capture.")


initialize()
engine = st.session_state.engine

_render_header(engine)
_render_snapshot(engine)
st.markdown("<div class='separator'></div>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if not st.session_state.ended:
    user_input = st.chat_input("Ask anything")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        result = engine.handle_user_message(user_input)
        for message in result["messages"]:
            st.session_state.messages.append({"role": "assistant", "content": message})
        st.session_state.ended = bool(result["ended"])
        st.rerun()
else:
    st.info("Chat closed. Start a new conversation to evaluate another candidate.")
    if st.button("Start New Conversation", type="primary"):
        engine.reset()
        st.session_state.messages = []
        st.session_state.ended = False
        for message in engine.start_messages():
            st.session_state.messages.append({"role": "assistant", "content": message})
        st.rerun()
