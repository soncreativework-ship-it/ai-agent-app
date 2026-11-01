import os
import base64
import io

import streamlit as st
from gtts import gTTS
import google.generativeai as genai

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Voice AI Agent - No-Ron Core",
    page_icon="🎙️",
    layout="wide"
)

# Tiêu đề ứng dụng
st.title("🎙️ Voice AI Agent & Neural Execution (No-Ron)")
st.caption("Hệ thống điều khiển AI Agent đa tác nhân bằng text, với hỗ trợ giọng nói nếu trình duyệt cho phép")

# Khởi tạo Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# --- THANH CẤU HÌNH BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Cấu hình AI & Giọng nói")

    language_option = st.selectbox(
        "🌐 Chọn ngôn ngữ phản hồi:",
        options=[
            ("Tiếng Việt", "vi", "vi-VN"),
            ("English (US)", "en", "en-US"),
            ("日本語 (Japanese)", "ja", "ja-JP"),
            ("한국어 (Korean)", "ko", "ko-KR"),
            ("Français (French)", "fr", "fr-FR")
        ],
        format_func=lambda x: x[0]
    )

    selected_lang_name, gtts_lang_code, _ = language_option
    voice_enabled = st.toggle("🔊 Bật giọng nói phản hồi (TTS)", value=True)
    model_name = st.selectbox("🤖 Chọn model Gemini", ["gemini-1.5-flash", "gemini-1.5-pro"]) 

    st.divider()
    st.markdown("**Trạng thái No-Ron Agent:** 🟢 Sẵn sàng")


# --- HÀM CHUNG ---
def get_api_key():
    key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
    return key


# --- HÀM GỌI GEMINI ---
def call_gemini(prompt: str, model_name: str) -> str:
    api_key = get_api_key()
    if not api_key:
        return (
            "Chưa có API key Google Gemini. Vui lòng thêm GEMINI_API_KEY vào Streamlit Secrets hoặc biến môi trường. "
            "Bạn vẫn có thể gõ tay câu lệnh và tiếp tục dùng app."
        )

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"No-Ron AI gặp lỗi khi gọi Gemini: {str(e)}"


# --- HÀM MULTI-AGENT ---
def orchestrate_multi_agent(user_prompt: str, language_name: str) -> str:
    """Mô phỏng multi-agent pipeline: Planner -> Researcher -> Executor."""
    if language_name == "Tiếng Việt":
        planner_prompt = f"""
        Bạn là Planner Agent. Phân tích nhiệm vụ sau và trả về một kế hoạch ngắn gọn gồm:
        1. Mục tiêu
        2. Bước thực hiện
        3. Kết quả mong muốn

        Nhiệm vụ: {user_prompt}
        """
        researcher_prompt = f"""
        Bạn là Researcher Agent. Dựa trên mục tiêu sau, đưa ra ý tưởng, gợi ý hoặc thông tin cần thiết để thực hiện khiêm tốn, rõ ràng.

        Nhiệm vụ: {user_prompt}
        """
        executor_prompt = f"""
        Bạn là Executor Agent. Hãy tạo ra câu trả lời cuối cùng cho người dùng theo ngôn ngữ tiếng Việt, ngắn gọn nhưng hữu ích, phù hợp với nhiệm vụ sau:

        Nhiệm vụ: {user_prompt}
        """
    else:
        planner_prompt = f"""
        You are the Planner Agent. Analyze the task and return a short plan with:
        1. Goal
        2. Steps
        3. Desired result

        Task: {user_prompt}
        """
        researcher_prompt = f"""
        You are the Researcher Agent. Based on the task, provide concise but useful guidance and ideas.

        Task: {user_prompt}
        """
        executor_prompt = f"""
        You are the Executor Agent. Produce the final answer in English, concise and useful, for this task:

        Task: {user_prompt}
        """

    planner_text = call_gemini(planner_prompt, model_name)
    researcher_text = call_gemini(researcher_prompt, model_name)

    final_prompt = f"""
    Hãy tổng hợp 3 đầu vào sau thành câu trả lời cuối cùng cho người dùng.

    [Planner Agent]
    {planner_text}

    [Researcher Agent]
    {researcher_text}

    [User Request]
    {user_prompt}

    Yêu cầu:
    - Trả lời theo ngôn ngữ: {language_name}
    - Giữ cấu trúc rõ ràng
    - Không dài quá 10-12 câu
    - Nếu tính chất yêu cầu cần làm nội dung cụ thể, hãy đáp án trực tiếp
    """

    return call_gemini(final_prompt, model_name)


# --- HÀM TẠO ÂM THANH CHUẨN ĐẸP VỚI gTTS ---
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


# --- KHU VỰC THÔNG BÁO VỀ MICRO ---
st.subheader("🗣️ Điều khiển bằng Giọng nói")
st.info("Microphone trong trình duyệt không luôn hoạt động trên iPhone/Safari. Vì vậy app ưu tiên nhập text và vẫn hỗ trợ TTS nếu trình duyệt cho phép.")

# --- KHU VỰC HIỂN THỊ CHAT & XỬ LÝ NHỆM VỤ ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💬 Trò chuyện & Giao việc")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Nhập câu lệnh hoặc yêu cầu cho No-Ron...")

    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.spinner("No-Ron đang phân tích và điều phối tác nhân..."):
            agent_response = orchestrate_multi_agent(user_prompt, selected_lang_name)

        with st.chat_message("assistant"):
            st.markdown(agent_response)
            if voice_enabled:
                audio_html = text_to_audio_html(agent_response, gtts_lang_code)
                st.components.v1.html(audio_html, height=0, width=0)

        st.session_state.messages.append({"role": "assistant", "content": agent_response})

        st.session_state.tasks.append({
            "task": user_prompt,
            "status": "Đang thực thi ⚡",
            "lang": selected_lang_name
        })

with col2:
    st.subheader("⚡ Bảng công việc No-Ron thực thi")
    if not st.session_state.tasks:
        st.info("Chưa có nhiệm vụ nào. Hãy nhập yêu cầu để bắt đầu!")
    else:
        for idx, item in enumerate(reversed(st.session_state.tasks)):
            with st.container(border=True):
                st.markdown(f"**Nhiệm vụ #{len(st.session_state.tasks) - idx}:** {item['task']}")
                st.caption(f"Ngôn ngữ: {item['lang']} | Trạng thái: {item['status']}")

# --- THANH DỰ PHÒNG CHO MICRO (KHÔNG BẮT BUỘC) ---
with st.expander("🔧 Trợ giúp Micro / nhập tay", expanded=False):
    st.markdown(
        "- Nếu micro không hoạt động trên Safari/iPhone, hãy gõ tay câu lệnh ở ô chat dưới cùng.\n"
        "- App luôn ưu tiên text input để đảm bảo hoạt động ổn định.\n"
        "- TTS chỉ là chức năng phụ, dùng khi trình duyệt hỗ trợ phát âm thanh."
    )
