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
st.caption("Hệ thống điều khiển AI Agent bằng giọng nói rõ ràng, hỗ trợ đa ngôn ngữ")

# Khởi tạo Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# --- THANH CẤU HÌNH BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Cấu hình Giọng nói & Agent")

    language_option = st.selectbox(
        "🌐 Chọn ngôn ngữ phản hồi (Language):",
        options=[
            ("Tiếng Việt", "vi", "vi-VN"),
            ("English (US)", "en", "en-US"),
            ("日本語 (Japanese)", "ja", "ja-JP"),
            ("한국어 (Korean)", "ko", "ko-KR"),
            ("Français (French)", "fr", "fr-FR")
        ],
        format_func=lambda x: x[0]
    )

    selected_lang_name, gtts_lang_code, speech_rec_code = language_option
    voice_enabled = st.toggle("🔊 Bật giọng nói phản hồi (Voice Output)", value=True)
    st.divider()
    st.markdown("**Trạng thái No-Ron Agent:** 🟢 Ready")


# --- HÀM GỌI GOOGLE GEMINI ---
def get_gemini_response(prompt: str, language: str) -> str:
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

    if not api_key:
        return (
            "Chưa có API key Google Gemini. Vui lòng thêm GEMINI_API_KEY vào Streamlit Secrets hoặc biến môi trường. "
            "Nếu mic đang lỗi, bạn vẫn có thể gõ tay câu lệnh để tiếp tục."
        )

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        language_instruction = {
            "Tiếng Việt": "Bạn là No-Ron AI, trả lời tiếng Việt tự nhiên, ngắn gọn nhưng rõ ràng.",
            "English (US)": "You are No-Ron AI, respond in English naturally and clearly.",
            "日本語 (Japanese)": "あなたはNo-Ron AIです。自然で明確な日本語で返答してください。",
            "한국어 (Korean)": "당신은 No-Ron AI입니다. 자연스럽고 명확한 한국어로 답변하세요.",
            "Français (French)": "Tu es No-Ron AI, réponds en français de manière naturelle et claire."
        }.get(language, "Bạn là No-Ron AI, trả lời rõ ràng và ngắn gọn.")

        full_prompt = f"{language_instruction}\n\nNgười dùng yêu cầu: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        return f"No-Ron AI gặp lỗi khi gọi Gemini: {str(e)}"


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


# --- KHU VỰC ĐIỀU KHIỂN GIỌNG NÓI ---
st.subheader("🗣️ Điều khiển bằng Giọng nói")

warning_msg = """
<div style="margin-bottom: 12px; color: #ffd166; font-size: 14px;">
  Nếu Micro không hoạt động trên Safari/iPhone, hãy gõ tay ở ô chat phía dưới. Đây là giới hạn của trình duyệt.
</div>
"""

st.markdown(warning_msg, unsafe_allow_html=True)

components_code = f"""
<div style="background-color: #1e1e2e; padding: 15px; border-radius: 10px; color: white; text-align: center;">
    <button id="mic-btn" style="background-color: #ff4b4b; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 20px; cursor: pointer;">
        🎤 Bắt đầu nói ({selected_lang_name})
    </button>
    <p id="status-text" style="margin-top: 10px; font-style: italic; color: #aaa;">Bấm nút để nói câu lệnh...</p>
</div>

<script>
const micBtn = document.getElementById('mic-btn');
const statusText = document.getElementById('status-text');
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {{
    statusText.innerText = 'Trình duyệt không hỗ trợ nhận diện giọng nói. Hãy gõ tay ở ô chat bên dưới.';
}} else if (!window.isSecureContext && location.hostname !== 'localhost') {{
    statusText.innerText = 'Cần HTTPS để dùng Microphone. Nếu đang trên iPhone/Safari, hãy gõ tay hoặc mở trên máy tính.';
}} else {{
    const recognition = new SpeechRecognition();
    recognition.lang = '{speech_rec_code}';
    recognition.interimResults = false;
    recognition.continuous = false;

    let isListening = false;

    const tryStart = () => {{
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
            statusText.innerText = 'Microphone không khả dụng trong trình duyệt này. Hãy gõ tay.';
            return;
        }}

        navigator.mediaDevices.getUserMedia({{ audio: true }})
            .then(() => {{
                recognition.start();
                micBtn.style.backgroundColor = '#00c853';
                micBtn.innerText = '🔴 Đang nghe... Hãy nói ngay';
                statusText.innerText = 'Đang lắng nghe câu lệnh của bạn...';
                isListening = true;
            }})
            .catch((err) => {{
                console.error(err);
                statusText.innerText = 'Microphone bị từ chối hoặc không hỗ trợ trên thiết bị này. Hãy gõ tay.';
                micBtn.style.backgroundColor = '#ff4b4b';
                micBtn.innerText = '🎤 Bắt đầu nói ({selected_lang_name})';
                isListening = false;
            }});
    };

    micBtn.addEventListener('click', () => {{
        if (!isListening) {{
            tryStart();
        }} else {{
            recognition.stop();
        }}
    }});

    recognition.onresult = (event) => {{
        const transcript = event.results[0][0].transcript;
        statusText.innerText = 'Đã nghe: "' + transcript + '"';

        const chatInput = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
        if (chatInput) {{
            chatInput.value = transcript;
            chatInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
        }}

        micBtn.style.backgroundColor = '#ff4b4b';
        micBtn.innerText = '🎤 Bắt đầu nói ({selected_lang_name})';
        isListening = false;
    }};

    recognition.onerror = (event) => {{
        let msg = 'Lỗi nhận diện: ' + event.error;

        if (event.error === 'service-not-allowed' || event.error === 'not-allowed') {{
            msg = 'Microphone bị chặn bởi trình duyệt hoặc iPhone. Vui lòng cho phép quyền Microphone hoặc gõ tay.';
        }} else if (event.error === 'no-speech') {{
            msg = 'Không nghe thấy giọng nói. Hãy nói rõ hơn hoặc gõ tay.';
        }}

        statusText.innerText = msg;
        micBtn.style.backgroundColor = '#ff4b4b';
        micBtn.innerText = '🎤 Bắt đầu nói ({selected_lang_name})';
        isListening = false;
    }};

    recognition.onend = () => {{
        micBtn.style.backgroundColor = '#ff4b4b';
        micBtn.innerText = '🎤 Bắt đầu nói ({selected_lang_name})';
        isListening = false;
    }};
}}
</script>
"""

st.components.v1.html(components_code, height=120)

# --- KHU VỰC HIỂN THỊ CHAT & XỬ LÝ NHỆM VỤ ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💬 Trò chuyện & Giao việc")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Nhập câu lệnh hoặc bấm nút Micro phía trên để nói...")

    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        agent_response = get_gemini_response(user_prompt, selected_lang_name)

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
        st.info("Chưa có nhiệm vụ nào được giao. Hãy nói hoặc gõ câu lệnh!")
    else:
        for idx, item in enumerate(reversed(st.session_state.tasks)):
            with st.container(border=True):
                st.markdown(f"**Nhiệm vụ #{len(st.session_state.tasks) - idx}:** {item['task']}")
                st.caption(f"Ngôn ngữ: {item['lang']} | Trạng thái: {item['status']}")
