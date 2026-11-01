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

GOOGLE_MODEL_CANDIDATES = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
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
        --bg0: #0b1117;
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
        background: linear-gradient(180deg, #0b1117 0%, #0f1720 100%);
        color: var(--text);
    }
    .stApp {
        background: linear-gradient(180deg, #0b1117 0%, #0f1720 100%);
    }
    .app-shell {
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 16px 18px 8px 18px;
    }
    .task-card {
        background: linear-gradient(180deg, rgba(23,36,48,0.9), rgba(18,28,38,0.96));
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 10px 18px rgba(0,0,0,0.18);
    }
    .task-card h3 {
        margin: 0 0 8px 0;
        color: var(--text);
        font-size: 1.2rem;
    }
    .muted {
        color: var(--muted);
        font-size: 0.78rem;
    }
    .task-summary {
        color: var(--text);
        line-height: 1.5;
        margin: 12px 0 10px 0;
    }
    .tag {
        display: inline-block;
        background: rgba(116,167,255,0.12);
        color: #dfeeff;
        border: 1px solid rgba(116,167,255,0.2);
        border-radius: 999px;
        padding: 6px 10px;
        margin: 4px 6px 0 0;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .detail-box {
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 14px;
        color: var(--text);
        line-height: 1.65;
        white-space: pre-wrap;
    }
    .status-pill {
        display: inline-block;
        background: rgba(50,213,131,0.12);
        border: 1px solid rgba(50,213,131,0.25);
        color: #b9f9dc;
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 8px 12px;
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--line);
    }
    .stButton > button {
        border-radius: 999px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.06);
        color: white;
    }
    .stFileUploader > div {
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--line);
        border-radius: 14px;
    }
    @media (max-width: 768px) {
        .app-shell { padding: 12px; }
        .task-card { padding: 14px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "agent_outputs" not in st.session_state:
    st.session_state.agent_outputs = {}
if "selected_task" not in st.session_state:
    st.session_state.selected_task = 0


def get_api_key():
    return st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))


def resolve_best_available_model():
    api_key = get_api_key()
    if not api_key:
        return GOOGLE_MODEL_CANDIDATES[0]

    try:
        genai.configure(api_key=api_key)
    except Exception:
        return GOOGLE_MODEL_CANDIDATES[0]

    for model_name in GOOGLE_MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            model.generate_content("Reply with OK")
            return model_name
        except Exception:
            continue
    return GOOGLE_MODEL_CANDIDATES[0]


def compatible_model_sequence(selected_model: str):
    ordered = []
    seen = set()
    for model_name in [selected_model] + GOOGLE_MODEL_CANDIDATES:
        value = (model_name or "").strip()
        if value and value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def call_gemini(prompt: str, selected_model: str) -> str:
    api_key = get_api_key()
    if not api_key:
        return (
            "Chưa có API key Google Gemini. Vui lòng thêm GEMINI_API_KEY vào Streamlit Secrets hoặc biến môi trường. "
            "Bạn vẫn có thể tiếp tục dùng text input để làm việc với hệ thống."
        )

    genai.configure(api_key=api_key)

    last_error = None
    debug_messages = []
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
            "Hãy chọn một model có sẵn trong Google AI Studio / Gemini API của bạn. "
            f"Lỗi cuối cùng: {str(last_error)}\n\n" + "\n".join(debug_messages)
        )

    return "No-Ron AI không thể kết nối đến Gemini sau khi thử nhiều model khác nhau."


def extract_text_from_uploaded_file(file_obj):
    name = (file_obj.name or "").lower()
    try:
        if name.endswith(".pdf"):
            if PdfReader is None:
                return "[PDF không thể đọc vì thư viện PyPDF chưa có trong môi trường.]"
            reader = PdfReader(file_obj)
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)
        raw = file_obj.read()
        return raw.decode("utf-8", errors="ignore")
    except Exception as e:
        return f"[Không thể đọc file: {e}]"


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


def planner_agent(task: str, context: str, language_name: str, model_name: str) -> str:
    if language_name == "Tiếng Việt":
        prompt = f"""
        Bạn là Planner Agent. Hãy phân tích nhiệm vụ sau và trả về kế hoạch rõ ràng:
        1. Mục tiêu
        2. Các bước triển khai
        3. Thời gian gợi ý
        4. Kết quả đầu ra

        Context:
        {context}

        Nhiệm vụ: {task}
        """
    else:
        prompt = f"""
        You are the Planner Agent. Analyze the task and plan execution.
        1. Goal
        2. Steps
        3. Timeline
        4. Outcome

        Context:
        {context}

        Task: {task}
        """
    return call_gemini(prompt, model_name)


def researcher_agent(task: str, context: str, language_name: str, model_name: str) -> str:
    if language_name == "Tiếng Việt":
        prompt = f"""
        Bạn là Research Agent. Hãy đưa ra góc nhìn chiến lược cho nhiệm vụ sau:
        - đối tượng mục tiêu
        - xu hướng thị trường
        - từ khóa và hướng đi
        - đối thủ và phân biệt hóa
        - rủi ro

        Context:
        {context}

        Nhiệm vụ: {task}
        """
    else:
        prompt = f"""
        You are the Research Agent. Provide strategic analysis for:
        - target audience
        - market trends
        - keywords
        - differentiated opportunities
        - risks

        Context:
        {context}

        Task: {task}
        """
    return call_gemini(prompt, model_name)


def script_agent(task: str, context: str, language_name: str, model_name: str) -> str:
    if language_name == "Tiếng Việt":
        prompt = f"""
        Bạn là Script Agent. Viết kịch bản quảng cáo/video cho nhiệm vụ sau.
        Yêu cầu:
        - hook mạnh
        - câu chuyện rõ
        - CTA rõ
        - ngắn gọn và có thể thực thi

        Context:
        {context}

        Nhiệm vụ: {task}
        """
    else:
        prompt = f"""
        You are the Script Agent. Write a short marketing or video script.
        Include hook, story, CTA, clarity, concise execution.

        Context:
        {context}

        Task: {task}
        """
    return call_gemini(prompt, model_name)


def email_agent(task: str, context: str, language_name: str, model_name: str) -> str:
    if language_name == "Tiếng Việt":
        prompt = f"""
        Bạn là Email Agent. Viết email ngắn, chuyên nghiệp, có tính hành động cho nhiệm vụ sau.
        Có: subject, greeting, body, CTA.

        Context:
        {context}

        Nhiệm vụ: {task}
        """
    else:
        prompt = f"""
        You are the Email Agent. Draft a concise professional email for this task.
        Include: subject, greeting, body, CTA.

        Context:
        {context}

        Task: {task}
        """
    return call_gemini(prompt, model_name)


def orchestrate_task(task: str, context: str, language_name: str, model_name: str) -> dict:
    return {
        "plan": planner_agent(task, context, language_name, model_name),
        "research": researcher_agent(task, context, language_name, model_name),
        "script": script_agent(task, context, language_name, model_name),
        "email": email_agent(task, context, language_name, model_name),
    }


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
    browser_voice = st.toggle("Mic web (Chrome)", value=False)

    model_options = ["Auto (best available)"] + GOOGLE_MODEL_CANDIDATES
    selected_model_option = st.selectbox("Model", model_options)
    model_name = resolve_best_available_model() if selected_model_option == "Auto (best available)" else selected_model_option
    st.caption(f"Using model: {model_name}")


st.markdown('<div class="app-shell">', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    st.title("No-Ron")
with col2:
    st.write("")
    st.write("")
    if browser_voice:
        st.info("Mic đang bật — chỉ hoạt động trên trình duyệt hỗ trợ Web Speech API")
    else:
        st.caption("Mic đang tắt. Bạn vẫn có thể dùng text + file upload.")

st.markdown("### Tạo task")

uploaded_files = st.file_uploader(
    "📎 Upload file (PDF, TXT, MD, CSV)",
    accept_multiple_files=True,
    type=["txt", "md", "csv", "pdf"],
)
user_prompt = st.chat_input("Nhập yêu cầu hoặc nói lệnh...")

if user_prompt or uploaded_files:
    context_chunks = []
    if uploaded_files:
        for f in uploaded_files:
            context_chunks.append(f"### File: {f.name}\n{extract_text_from_uploaded_file(f)}")
    combined_context = "\n\n".join(context_chunks) if context_chunks else "Không có file đính kèm."
    task_text = user_prompt or "Tổng hợp file đính kèm và đưa ra kế hoạch xử lý."

    with st.spinner("No-Ron đang điều phối task cho Planner / Research / Script / Email..."):
        result = orchestrate_task(task_text, combined_context, selected_lang_name, model_name)

    st.session_state.messages.append({"role": "user", "content": task_text})
    st.session_state.agent_outputs[task_text] = result
    task_summary = (result["plan"][:180] + "...") if len(result["plan"]) > 180 else result["plan"]
    new_task = {
        "title": task_text[:70] + ("..." if len(task_text) > 70 else ""),
        "summary": task_summary,
        "tags": ["Research", "Script", "Email", "Task"],
        "status": "Đã phân phối",
        "repo": "No-Ron Studio",
        "type": "AI Workflow",
        "detail": (
            "### Kế hoạch\n"
            f"{result['plan']}\n\n"
            "### Nghiên cứu\n"
            f"{result['research']}\n\n"
            "### Kịch bản\n"
            f"{result['script']}\n\n"
            "### Email\n"
            f"{result['email']}"
        ),
    }
    st.session_state.tasks.insert(0, new_task)
    st.session_state.selected_task = 0

if not st.session_state.tasks:
    st.session_state.tasks = [{
        "title": "Expensify / Ứng dụng",
        "summary": "Chào mừng đến với Expensify mới: một sự tái định hình hoàn toàn về hợp tác tài chính, tập trung vào trải nghiệm người dùng. Hãy giúp xây dựng hệ thống tiếp theo...",
        "tags": ["TypeScript", "5.1k", "AI"],
        "status": "Nổi bật",
        "repo": "Expensify",
        "type": "ứng dụng",
        "detail": "Task mẫu để mô phỏng feed. Bạn có thể nhập lệnh mới để tạo task thực tế.",
    }]

for idx, task in enumerate(st.session_state.tasks):
    with st.container():
        st.markdown(
            f"""
            <div class="task-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px;">
                    <div>
                        <div class="muted">{task['repo']}</div>
                        <h3>{task['title']}</h3>
                    </div>
                    <span class="status-pill">{task['status']}</span>
                </div>
                <div class="task-summary">{task['summary']}</div>
                <div>
                    {''.join(f'<span class="tag">{tag}</span>' for tag in task['tags'])}
                </div>
                <div style="margin-top:12px; display:flex; justify-content:space-between; align-items:center;">
                    <div class="muted">{task['type']}</div>
                    <div>
                        <button type="button">Xem chi tiết</button>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(f"Mở task #{idx + 1}", key=f"open_{idx}"):
            st.session_state.selected_task = idx

        if idx == st.session_state.selected_task:
            detail = st.session_state.tasks[idx].get("detail", "Chưa có nội dung chi tiết.")
            st.markdown(f"### Chi tiết task\n\n<div class='detail-box'>{detail}</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_prompt or uploaded_files:
    if voice_enabled:
        final_text = (
            "### Kế hoạch\n"
            f"{st.session_state.agent_outputs.get(user_prompt or 'uploaded_files', {}).get('plan', '')}\n\n"
            "### Nghiên cứu\n"
            f"{st.session_state.agent_outputs.get(user_prompt or 'uploaded_files', {}).get('research', '')}\n\n"
            "### Kịch bản\n"
            f"{st.session_state.agent_outputs.get(user_prompt or 'uploaded_files', {}).get('script', '')}\n\n"
            "### Email\n"
            f"{st.session_state.agent_outputs.get(user_prompt or 'uploaded_files', {}).get('email', '')}"
        )
        audio_html = text_to_audio_html(final_text, gtts_lang_code)
        if audio_html:
            st.components.v1.html(audio_html, height=0, width=0)
