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

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="No-Ron Multi-Agent Studio",
    page_icon="🚀",
    layout="wide",
)

st.title("🚀 No-Ron Multi-Agent Studio")
st.caption("AI đa tác nhân: Planner • Research • Script • Email • File Context")

# Khởi tạo Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "agent_outputs" not in st.session_state:
    st.session_state.agent_outputs = {}

# --- Sidebar config ---
with st.sidebar:
    st.header("⚙️ Cấu hình hệ thống")

    language_option = st.selectbox(
        "🌐 Chọn ngôn ngữ phản hồi:",
        options=[
            ("Tiếng Việt", "vi", "vi-VN"),
            ("English (US)", "en", "en-US"),
            ("日本語 (Japanese)", "ja", "ja-JP"),
            ("한국어 (Korean)", "ko", "ko-KR"),
            ("Français (French)", "fr", "fr-FR"),
        ],
        format_func=lambda x: x[0],
    )

    selected_lang_name, gtts_lang_code, _ = language_option
    voice_enabled = st.toggle("🔊 Bật phát giọng (TTS)", value=True)
    model_name = st.selectbox("🤖 Chọn model Gemini", ["gemini-1.5-flash", "gemini-1.5-pro"])

    st.divider()
    st.markdown("**Trạng thái:** 🟢 Sẵn sàng")


# --- Utility functions ---
def get_api_key():
    return st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))


def call_gemini(prompt: str, model_name: str) -> str:
    api_key = get_api_key()
    if not api_key:
        return (
            "Chưa có API key Google Gemini. Vui lòng thêm GEMINI_API_KEY vào Streamlit Secrets hoặc biến môi trường. "
            "Bạn vẫn có thể tiếp tục dùng text input để làm việc với hệ thống."
        )

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"No-Ron AI gặp lỗi khi gọi Gemini: {str(e)}"


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
        audio_bytes = fp.read()
        b64 = base64.b64encode(audio_bytes).decode()
        md = f"""
            <audio autoplay style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
        """
        return md
    except Exception as e:
        return f"<!-- Audio error: {str(e)} -->"


# --- Agent logic ---
def planner_agent(task: str, context: str, language_name: str) -> str:
    if language_name == "Tiếng Việt":
        prompt = f"""
        Bạn là Planner Agent. Hãy phân tích nhiệm vụ sau và trả về kế hoạch triển khai rõ ràng dưới dạng:
        1. Mục tiêu
        2. Các bước thực hiện
        3. Thời gian gợi ý
        4. Kết quả đầu ra

        Tài liệu context:
        {context}

        Nhiệm vụ: {task}
        """
    else:
        prompt = f"""
        You are the Planner Agent. Analyze the task and return a clear plan with:
        1. Goal
        2. Execution steps
        3. Recommended timeline
        4. Expected output

        Context:
        {context}

        Task: {task}
        """
    return call_gemini(prompt, model_name)


def researcher_agent(task: str, context: str, language_name: str) -> str:
    if language_name == "Tiếng Việt":
        prompt = f"""
        Bạn là Research Agent. Hãy nghiên cứu và đưa ra ý tưởng chiến lược cho nhiệm vụ sau:
        - đối tượng mục tiêu
        - xu hướng thị trường
        - từ khóa gợi ý
        - đối thủ và cách khác biệt hóa
        - rủi ro / thách thức

        Tài liệu context:
        {context}

        Nhiệm vụ: {task}
        """
    else:
        prompt = f"""
        You are the Research Agent. Analyze the task and provide strategic insight for:
        - target audience
        - market trends
        - suggested keywords
        - competitors and differentiation
        - risks and challenges

        Context:
        {context}

        Task: {task}
        """
    return call_gemini(prompt, model_name)


def script_agent(task: str, context: str, language_name: str) -> str:
    if language_name == "Tiếng Việt":
        prompt = f"""
        Bạn là Script Agent. Hãy viết kịch bản marketing/video cho nhiệm vụ sau.
        Yêu cầu:
        - hook mở đầu mạnh
        - câu chuyện rõ ràng
        - CTA rõ ràng
        - ngắn gọn, dễ thực thi
        - phù hợp với quảng cáo / video ngắn / landing page

        Tài liệu context:
        {context}

        Nhiệm vụ: {task}
        """
    else:
        prompt = f"""
        You are the Script Agent. Write a strong marketing or video script for this task.
        Requirements:
        - strong hook
        - clear story arc
        - clear CTA
        - concise and practical
        - suitable for ad, short video, or landing page

        Context:
        {context}

        Task: {task}
        """
    return call_gemini(prompt, model_name)


def email_agent(task: str, context: str, language_name: str) -> str:
    if language_name == "Tiếng Việt":
        prompt = f"""
        Bạn là Email Agent. Viết 1 email ngắn, chuyên nghiệp, có tính hành động cho công việc sau.
        Email nên có:
        - subject line
        - greeting
        - nội dung chính
        - CTA

        Tài liệu context:
        {context}

        Nhiệm vụ: {task}
        """
    else:
        prompt = f"""
        You are the Email Agent. Write a concise, professional, action-oriented email for the following task.
        Include:
        - subject line
        - greeting
        - main content
        - CTA

        Context:
        {context}

        Task: {task}
        """
    return call_gemini(prompt, model_name)


def orchestrate_task(task: str, context: str, language_name: str) -> dict:
    plan = planner_agent(task, context, language_name)
    research = researcher_agent(task, context, language_name)
    script = script_agent(task, context, language_name)
    email = email_agent(task, context, language_name)

    return {
        "plan": plan,
        "research": research,
        "script": script,
        "email": email,
    }


# --- Main app area ---
col1, col2 = st.columns([1.7, 1])

with col1:
    st.subheader("💬 Trò chuyện & Giao việc")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    uploaded_files = st.file_uploader(
        "📎 Tải lên file đính kèm (PDF, TXT, MD, CSV)",
        accept_multiple_files=True,
        type=["txt", "md", "csv", "pdf"],
    )

    user_prompt = st.chat_input("Nhập yêu cầu cho hệ thống AI đa tác nhân...")

    if user_prompt or uploaded_files:
        context_chunks = []
        if uploaded_files:
            for file_obj in uploaded_files:
                context_chunks.append(f"### File: {file_obj.name}\n{extract_text_from_uploaded_file(file_obj)}")

        combined_context = "\n\n".join(context_chunks) if context_chunks else "Không có file đính kèm."

        st.session_state.messages.append({"role": "user", "content": user_prompt or "[File upload only]"})
        if user_prompt:
            with st.chat_message("user"):
                st.markdown(user_prompt)
        else:
            with st.chat_message("user"):
                st.markdown("[Người dùng upload file để cung cấp context]")

        with st.spinner("No-Ron đang điều phối Planner, Research, Script và Email Agent..."):
            result = orchestrate_task(user_prompt or "Tổng hợp file đính kèm và đưa ra kế hoạch xử lý.", combined_context, selected_lang_name)

        st.session_state.agent_outputs[user_prompt or "uploaded_files"] = result

        tabs = st.tabs(["Kế hoạch", "Nghiên cứu", "Kịch bản", "Email"])

        with tabs[0]:
            st.markdown(result["plan"])

        with tabs[1]:
            st.markdown(result["research"])

        with tabs[2]:
            st.markdown(result["script"])

        with tabs[3]:
            st.markdown(result["email"])

        final_text = (
            "### Kế hoạch\n"
            f"{result['plan']}\n\n"
            "### Nghiên cứu\n"
            f"{result['research']}\n\n"
            "### Kịch bản\n"
            f"{result['script']}\n\n"
            "### Email\n"
            f"{result['email']}"
        )

        with st.chat_message("assistant"):
            st.markdown(final_text)
            if voice_enabled:
                audio_html = text_to_audio_html(final_text, gtts_lang_code)
                st.components.v1.html(audio_html, height=0, width=0)

        st.session_state.messages.append({"role": "assistant", "content": final_text})

        st.session_state.tasks.append({
            "task": user_prompt or "[Task từ file upload]",
            "status": "Đã phân phối ⚡",
            "lang": selected_lang_name,
        })

with col2:
    st.subheader("⚡ Bảng công việc No-Ron")
    if not st.session_state.tasks:
        st.info("Chưa có nhiệm vụ nào. Hãy nhập yêu cầu hoặc upload file để AI phân phối task cho các agent.")
    else:
        for idx, item in enumerate(reversed(st.session_state.tasks)):
            with st.container(border=True):
                st.markdown(f"**Nhiệm vụ #{len(st.session_state.tasks) - idx}:** {item['task']}")
                st.caption(f"Ngôn ngữ: {item['lang']} | Trạng thái: {item['status']}")

# --- Additional info panel ---
with st.expander("🧠 Cấu trúc Agentic multi-agent", expanded=False):
    st.markdown(
        "- Planner Agent: phân tích task và chia kế hoạch\n"
        "- Research Agent: nghiên cứu thị trường, từ khóa, đối tác\n"
        "- Script Agent: viết kịch bản marketing / ads / video\n"
        "- Email Agent: viết email cập nhật và follow-up\n"
        "- File Context: đọc file upload để bổ sung input\n"
        "- TTS: đọc phản hồi nếu trình duyệt hỗ trợ"
    )

    st.markdown(
        "Ví dụ yêu cầu: 'Tạo 1 video ads 15s cho sản phẩm X, nghiên cứu đối tượng, keyword, script, và viết email báo cáo kết quả làm việc.'"
    )
