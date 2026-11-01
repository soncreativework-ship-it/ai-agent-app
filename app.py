import os
import base64
import io

import streamlit as st
from gtts import gTTS
import google.generativeai as genai

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

st.set_page_config(
    page_title="No-Ron Multi-Agent Studio",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --bg0: #0c141b;
        --bg1: #111b25;
        --bg2: #1a2430;
        --card: #172430;
        --line: rgba(255,255,255,0.08);
        --text: #edf3f8;
        --muted: #9cadbf;
        --green: #32d583;
        --blue: #4da3ff;
        --purple: #b088ff;
        --red: #ff6b6b;
    }
    html, body {
        background: #0b1117;
        color: var(--text);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .stApp {
        background: linear-gradient(180deg, #0b1117 0%, #0f1720 100%);
    }
    .mobile-shell {
        max-width: 460px;
        margin: 0 auto;
        background: #0d1a22;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 26px;
        overflow: hidden;
        min-height: calc(100vh - 12px);
    }
    .status-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 18px 8px 18px;
        color: #f0f5fb;
        font-size: 0.9rem;
        letter-spacing: 0.02em;
    }
    .status-icons {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.95rem;
        opacity: 0.9;
    }
    .url-bar {
        margin: 0 12px 8px 12px;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 999px;
        padding: 10px 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        color: var(--text);
    }
    .url-icon {
        width: 28px;
        height: 28px;
        border-radius: 10px;
        background: linear-gradient(135deg, #4f9dfd, #3ce0c2);
        font-weight: 700;
        color: #08131a;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
    }
    .url-text {
        flex: 1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: #dfeaf6;
        font-size: 0.95rem;
    }
    .toolbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 14px 8px 14px;
        color: #edf3f8;
        font-weight: 600;
    }
    .toolbar-left {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .toolbar-right {
        display: flex;
        align-items: center;
        gap: 18px;
        font-size: 1.2rem;
    }
    .chat-panel {
        padding: 14px 14px 0 14px;
        min-height: 420px;
    }
    .message {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 16px 14px;
        color: #edf3f8;
        line-height: 1.6;
        margin-bottom: 14px;
        white-space: pre-wrap;
        font-size: 0.96rem;
    }
    .message strong {
        color: #7ac3ff;
    }
    .message .model-line {
        color: #7bd5ff;
        font-weight: 600;
    }
    .composer {
        position: sticky;
        bottom: 0;
        padding: 12px 14px 16px 14px;
        background: rgba(13, 26, 34, 0.96);
        border-top: 1px solid rgba(255,255,255,0.04);
    }
    .composer-inner {
        display: flex;
        align-items: center;
        gap: 10px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.04);
        border-radius: 999px;
        padding: 8px 10px 8px 18px;
    }
    .composer input {
        flex: 1;
        border: none;
        background: transparent;
        color: var(--text);
        font-size: 1rem;
        outline: none;
    }
    .composer input::placeholder {
        color: rgba(255,255,255,0.55);
    }
    .send-btn {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7ac7ff, #4f9dfd);
        color: #07151b;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        font-weight: 700;
        border: none;
        cursor: pointer;
    }
    .bottom-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 18px 14px 18px;
        background: rgba(12,20,27,0.92);
        border-top: 1px solid rgba(255,255,255,0.04);
        color: #eaf3ff;
    }
    .nav-item {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 52px;
        height: 52px;
        border-radius: 50%;
        color: #edf3f8;
        font-size: 1.15rem;
        opacity: 0.9;
    }
    .nav-center {
        width: 58px;
        height: 58px;
        border-radius: 50%;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.08);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: 300;
    }
    .badge {
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: rgba(255,255,255,0.14);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.76rem;
        font-weight: 700;
    }
    .app-shell {
        display: none;
    }
    @media (max-width: 768px) {
        .app-shell { display: block; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = []


def get_api_key():
    return st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))


def get_available_models():
    api_key = get_api_key()
    if not api_key:
        return []

    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        available = []
        for model in models:
            name = getattr(model, "name", "")
            methods = getattr(model, "supported_generation_methods", [])
            if name and "generateContent" in methods:
                available.append(name.replace("models/", ""))
        return available
    except Exception:
        return []


def resolve_best_available_model():
    available = get_available_models()
    if available:
        for candidate in FALLBACK_MODELS:
            if candidate in available:
                return candidate
        return available[0]
    return "gemini-2.5-flash"


def compatible_model_sequence(selected_model: str):
    ordered = []
    seen = set()
    for model_name in [selected_model] + FALLBACK_MODELS:
        value = (model_name or "").strip()
        if value and value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def call_gemini(prompt: str, selected_model: str) -> str:
    api_key = get_api_key()
    if not api_key:
        return (
            "Chưa có API key Google Gemini. Vui lòng thêm GEMINI_API_KEY vào Streamlit Secrets hoặc biến môi trường."
        )

    genai.configure(api_key=api_key)
    debug_messages = []
    last_error = None

    for model_name in compatible_model_sequence(selected_model):
        debug_messages.append(f"Trying model: {model_name}")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = getattr(response, "text", None)
            if not text:
                raise ValueError("empty response")
            return text.strip()
        except Exception as e:
            last_error = e
            msg = str(e).lower()
            debug_messages.append(f"Failed model {model_name}: {str(e)}")
            if "404" in msg or "not found" in msg or "unsupported" in msg or "does not exist" in msg:
                continue
            return (
                f"No-Ron AI gặp lỗi khi gọi Gemini: {str(e)}\n\n"
                + "\n".join(debug_messages)
            )

    if last_error is not None:
        return (
            "No-Ron AI không tìm thấy model Gemini phù hợp trong tài khoản của bạn. "
            "Hãy chọn một model có sẵn trong Google AI Studio / Gemini API của bạn.\n\n"
            + "\n".join(debug_messages)
        )

    return "No-Ron AI không thể kết nối đến Gemini sau khi thử nhiều model khác nhau."


def text_to_audio_html(text: str, lang_code: str):
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        b64 = base64.b64encode(fp.read()).decode()
        return f"<audio autoplay><source src='data:audio/mp3;base64,{b64}' type='audio/mp3'></audio>"
    except Exception:
        return ""


with st.sidebar:
    st.header("⚙️ Settings")
    language_option = st.selectbox(
        "Language",
        [
            ("Tiếng Việt", "vi", "vi-VN"),
            ("English (US)", "en", "en-US"),
            ("日本語", "ja", "ja-JP"),
            ("한국어", "ko", "ko-KR"),
        ],
        format_func=lambda x: x[0],
    )
    selected_lang_name, gtts_lang_code, speech_lang_code = language_option
    voice_enabled = st.toggle("TTS", value=True)

    selected_model_option = st.selectbox(
        "Model",
        ["Auto (best available)"] + FALLBACK_MODELS,
    )
    model_name = resolve_best_available_model() if selected_model_option == "Auto (best available)" else selected_model_option
    st.caption(f"Using model: {model_name}")


mobile_container = st.container()

with mobile_container:
    st.markdown('<div class="mobile-shell">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="status-bar">
            <div>02:11</div>
            <div class="status-icons">◔◷◍</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="url-bar">
            <div class="url-icon">G</div>
            <div class="url-text">...j5yfabpfgjw7ecg7zc4ti.streamlit.app</div>
            <div>⤴</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="toolbar">
            <div class="toolbar-left">»</div>
            <div class="toolbar-right">
                <span>Share</span>
                <span>☆</span>
                <span>✎</span>
                <span>⋮</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="chat-panel">', unsafe_allow_html=True)
    if st.session_state.messages:
        for msg in st.session_state.messages:
            st.markdown(f"<div class='message'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div class='message'>
            <strong>No-Ron AI</strong> đang sẵn sàng.<br><br>
            Nếu bạn tiếp tục nhập lệnh, tôi sẽ phân tích nhiệm vụ, nghiên cứu, viết kịch bản và email cho bạn.
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    prompt = st.text_input("", key="prompt_input_mobile", label_visibility="collapsed", placeholder="Nhập yêu cầu hoặc nói lệnh...")

    if st.button("Gửi", key="send_mobile", help="Gửi nhiệm vụ", use_container_width=False):
        if prompt and prompt.strip():
            st.session_state.prompt_history.append(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            result = call_gemini(
                f"Bạn là Trợ lý AI trong ứng dụng No-Ron. Hãy xử lý yêu cầu sau: {prompt}",
                model_name,
            )
            st.session_state.messages.append({"role": "assistant", "content": result})
            st.rerun()

    st.markdown(
        """
        <div class="bottom-nav">
            <div class="nav-item">←</div>
            <div class="nav-item">→</div>
            <div class="nav-center">＋</div>
            <div class="nav-item"><span class="badge">6</span></div>
            <div class="nav-item">⋯</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('</div>', unsafe_allow_html=True)

st.caption("Debug: model đang dùng = " + model_name)
