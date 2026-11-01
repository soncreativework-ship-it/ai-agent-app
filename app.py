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

DEFAULT_MODEL_CANDIDATES = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash-lite",
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
        --card-2: #1f2d3a;
        --line: rgba(255,255,255,0.08);
        --text: #edf3f8;
        --muted: #9cadbf;
        --green: #32d583;
        --blue: #4da3ff;
        --purple: #b088ff;
        --yellow: #f5c76b;
        --orange: #ff8c5a;
        --red: #ff6b6b;
    }

    html, body {
        background: linear-gradient(180deg, #0b1117 0%, #0f1720 100%);
        color: var(--text);
    }
    .stApp {
        background: linear-gradient(180deg, #0b1117 0%, #0f1720 100%);
    }
    .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 12px 18px;
        margin-bottom: 14px;
    }
    .brand-wrap {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .brand-icon {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: linear-gradient(135deg, #3b82f6, #22c55e);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        font-size: 14px;
    }
    .brand-text {
        font-size: 28px;
        font-weight: 700;
        letter-spacing: -0.04em;
        color: #f4f8fb;
    }
    .toolbar {
        display: flex;
        gap: 10px;
        align-items: center;
    }
    .toolbar-btn {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background: rgba(255,255,255,0.06);
        border: 1px solid var(--line);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
    }
    .top-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 10px 12px;
        margin-bottom: 12px;
    }
    .search-wrap {
        display: flex;
        gap: 10px;
        align-items: center;
        width: 100%;
    }
    .search-box {
        flex: 1;
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 14px 16px;
        color: var(--text);
        font-size: 16px;
        min-height: 52px;
    }
    .pill-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 14px;
    }
    .pill {
        background: rgba(255,255,255,0.03);
        border: 1px solid var(--line);
        color: var(--text);
        border-radius: 999px;
        padding: 10px 14px;
        font-size: 14px;
        font-weight: 600;
    }
    .feed-card {
        background: linear-gradient(180deg, rgba(23,36,48,0.85), rgba(18,28,38,0.92));
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 16px 16px 14px 16px;
        margin-bottom: 16px;
        box-shadow: 0 10px 18px rgba(0,0,0,0.18);
    }
    .feed-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
    }
    .left-head {
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 0;
    }
    .avatar {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: white;
        background: linear-gradient(135deg, #5d9dff, #7c6cff);
        flex-shrink: 0;
    }
    .repo-label {
        color: var(--muted);
        font-size: 13px;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .card-title {
        font-size: 18px;
        font-weight: 700;
        line-height: 1.3;
        color: var(--text);
    }
    .follow-btn {
        background: rgba(255,255,255,0.06);
        border: 1px solid var(--line);
        border-radius: 999px;
        color: var(--text);
        padding: 8px 14px;
        font-weight: 600;
        font-size: 13px;
        white-space: nowrap;
    }
    .summary {
        margin-top: 14px;
        color: #f5f8fb;
        font-size: 17px;
        line-height: 1.45;
    }
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
    }
    .chip {
        background: rgba(116, 167, 255, 0.11);
        color: #dfeeff;
        border: 1px solid rgba(116,167,255,0.2);
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 13px;
        font-weight: 600;
    }
    .meta-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 16px;
        color: var(--muted);
        font-size: 14px;
    }
    .meta-left {
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
    }
    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    .detail-panel {
        margin-top: 16px;
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 18px;
    }
    .detail-title {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 12px;
    }
    .detail-box {
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 12px 14px;
        color: var(--text);
        line-height: 1.6;
        white-space: pre-wrap;
    }
    .bottom-nav {
        display: flex;
        justify-content: center;
        gap: 18px;
        align-items: center;
        margin-top: 16px;
        padding-bottom: 6px;
    }
    .nav-btn {
        width: 58px;
        height: 58px;
        border-radius: 18px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.04);
        color: white;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    .nav-btn.primary {
        background: linear-gradient(135deg, #2dd4bf, #22c55e);
        border: none;
        color: #03150b;
    }
    .nav-btn.alert {
        background: linear-gradient(135deg, #f59e0b, #f97316);
        border: none;
        color: white;
    }
    .glass {
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 16px;
    }
    @media (max-width: 900px) {
        .brand-text { font-size: 24px; }
        .card-title { font-size: 17px; }
        .summary { font-size: 15px; }
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


def compatible_model_sequence(selected_model: str):
    ordered = []
    seen = set()
    for m in [selected_model] + DEFAULT_MODEL_CANDIDATES:
        label = (m or "").strip()
        if label and label not in seen:
            ordered.append(label)
            seen.add(label)
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
    for model_name in compatible_model_sequence(selected_model):
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if not getattr(response, "text", None):
                raise ValueError("empty response")
            return response.text.strip()
        except Exception as e:
            last_error = e
            msg = str(e).lower()
            if "404" in msg or "not found" in msg or "unsupported" in msg or "does not exist" in msg:
                continue
            return f"No-Ron AI gặp lỗi khi gọi Gemini: {str(e)}"

    if last_error is not None:
        return (
            "No-Ron AI không tìm thấy model Gemini phù hợp trong tài khoản của bạn. "
            "Hãy đổi sang một model đang được hỗ trợ trong tài khoản Google AI Studio của bạn. "
            f"Lỗi cuối cùng: {str(last_error)}"
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
        2. Các bư���c triển khai
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
    plan = planner_agent(task, context, language_name, model_name)
    research = researcher_agent(task, context, language_name, model_name)
    script = script_agent(task, context, language_name, model_name)
    email = email_agent(task, context, language_name, model_name)
    return {
        "plan": plan,
        "research": research,
        "script": script,
        "email": email,
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
    model_name = st.selectbox("Model", DEFAULT_MODEL_CANDIDATES)


# Optional mic UI only when enabled
if browser_voice:
    st.markdown(
        """
        <div style="margin: 0 0 14px 0; display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
            <button id="voice-button" style="background:#1f8fff;color:#fff;border:none;padding:10px 16px;border-radius:12px;font-weight:700;cursor:pointer;">🎙️ Nói lệnh</button>
            <span id="voice-status" style="color:#b7c6d6;font-size:14px;">Mic ready</span>
        </div>
        <script>
        const button = document.getElementById('voice-button');
        const status = document.getElementById('voice-status');
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            status.textContent = 'Mic không được hỗ trợ';
            button.disabled = true;
        } else {
            const recognition = new SpeechRecognition();
            recognition.lang = '""" + speech_lang_code + """';
            recognition.interimResults = false;
            recognition.continuous = false;
            button.addEventListener('click', () => {
                status.textContent = 'Đang nghe...';
                button.textContent = '🔴 Đang nghe';
                navigator.mediaDevices.getUserMedia({ audio: true })
                    .then(() => recognition.start())
                    .catch(() => {
                        status.textContent = 'Mic bị từ chối';
                        button.textContent = '🎙️ Nói lệnh';
                    });
            });
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                status.textContent = 'Đã nghe: ' + transcript;
                const textareas = document.querySelectorAll('textarea');
                const target = textareas[textareas.length - 1];
                if (target) {
                    target.value = transcript;
                    target.dispatchEvent(new Event('input', { bubbles: true }));
                    target.focus();
                }
                button.textContent = '🎙️ Nói lệnh';
            };
            recognition.onerror = (event) => {
                status.textContent = 'Lỗi mic: ' + event.error;
                button.textContent = '🎙️ Nói lệnh';
            };
            recognition.onend = () => {
                button.textContent = '🎙️ Nói lệnh';
            };
        }
        </script>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="topbar">
        <div class="brand-wrap">
            <div class="brand-icon">N</div>
            <div class="brand-text">No-Ron</div>
        </div>
        <div class="toolbar">
            <div class="toolbar-btn">↻</div>
            <div class="toolbar-btn">◫</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="top-actions">
        <div class="search-wrap">
            <div class="pill">Lọc</div>
            <div class="search-box">Khi bạn upload file hoặc nhập lệnh, task sẽ hiện ở đây</div>
        </div>
        <div class="toolbar-btn">⋯</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="pill-row"><div class="pill">Tất cả</div><div class="pill">Đang hoạt động</div><div class="pill">Pending</div><div class="pill">Nổi bật</div></div>', unsafe_allow_html=True)


uploaded_files = st.file_uploader("📎 Upload file (PDF, TXT, MD, CSV)", accept_multiple_files=True, type=["txt", "md", "csv", "pdf"])
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
    sample_task = {
        "title": "Expensify / Ứng dụng",
        "summary": "Chào mừng đến với Expensify mới: một sự tái định hình hoàn toàn về hợp tác tài chính, tập trung vào trải nghiệm người dùng. Hãy giúp xây dựng hệ thống tiếp theo...",
        "tags": ["TypeScript", "5.1k", "AI"],
        "status": "Nổi bật",
        "repo": "Expensify",
        "type": "ứng dụng",
        "detail": "Task mẫu để mô phỏng feed. Bạn có thể nhập lệnh mới để tạo task thực tế.",
    }
    st.session_state.tasks = [sample_task]

for idx, task in enumerate(st.session_state.tasks):
    with st.container():
        st.markdown(
            f"""
            <div class="feed-card">
                <div class="feed-head">
                    <div class="left-head">
                        <div class="avatar">{task['repo'][0].upper()}</div>
                        <div>
                            <div class="repo-label">{task['repo']}</div>
                            <div class="card-title">{task['title']}</div>
                        </div>
                    </div>
                    <button class="follow-btn">{task['status']}</button>
                </div>
                <div class="summary">{task['summary']}</div>
                <div class="chip-row">
                    {''.join(f'<div class="chip">{tag}</div>' for tag in task['tags'])}
                </div>
                <div class="meta-row">
                    <div class="meta-left">
                        <span><span class="dot" style="background: #2ed573;"></span> {task['type']}</span>
                        <span>•</span>
                        <span>{task['status']}</span>
                    </div>
                    <div>
                        <button class="follow-btn" style="background: rgba(50,213,131,0.12); border-color: rgba(50,213,131,0.25);">Xem chi tiết</button>
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
            st.markdown(
                """
                <div class="detail-panel">
                    <div class="detail-title">Chi tiết task</div>
                    <div class="detail-box">""" + detail + """</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown(
    """
    <div class="bottom-nav">
        <div class="nav-btn">←</div>
        <div class="nav-btn primary">＋</div>
        <div class="nav-btn alert">4</div>
        <div class="nav-btn">⋯</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Append chat transcript for visibility
st.markdown("<br>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_prompt or uploaded_files:
    st.caption("Note: Mic hỗ trợ trên Chrome nhưng app vẫn hoạt động bình thường bằng text + file upload.")
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
