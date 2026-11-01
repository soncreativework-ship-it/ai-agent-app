import streamlit as st
import base64
from gtts import gTTS
import io

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
    
    # Cho phép chọn ngôn ngữ phát âm & nhận diện
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

# --- HÀM TẠO ÂM THANH CHUẨN ĐẸP VỚI gTTS (KHÔNG BỊ RUNG/MÉO) ---
def text_to_audio_html(text: str, lang_code: str):
    """Tạo audio player ẩn tự động phát bằng giọng chuẩn gTTS"""
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_bytes = fp.read()
        b64 = base64.b64encode(audio_bytes).decode()
        # Tạo HTML5 audio tự động phát (Autoplay)
        md = f"""
            <audio autoplay style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        return md
    except Exception as e:
        return f"<!-- Audio error: {str(e)} -->"

# --- KHU VỰC ĐIỀU KHIỂN GIỌNG NÓI (WEB SPEECH RECOGNITION) ---
st.subheader("🗣️ Điều khiển bằng Giọng nói")

# Web Component tích hợp Micro trực tiếp trong trình duyệt
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
    statusText.innerText = "Trình duyệt của bạn không hỗ trợ nhận diện giọng nói (Hãy dùng Chrome/Safari).";
}} else {{
    const recognition = new SpeechRecognition();
    recognition.lang = '{speech_rec_code}';
    recognition.interimResults = false;

    let isListening = false;

    micBtn.addEventListener('click', () => {{
        if (!isListening) {{
            recognition.start();
            micBtn.style.backgroundColor = '#00c853';
            micBtn.innerText = '🔴 Đang nghe... Hãy nói ngay';
            statusText.innerText = 'Đang lắng nghe câu lệnh của bạn...';
            isListening = true;
        }} else {{
            recognition.stop();
        }}
    }});

    recognition.onresult = (event) => {{
        const transcript = event.results[0][0].transcript;
        statusText.innerText = 'Đã nghe: "' + transcript + '"';
        
        // Tự động điền vào khung chat của Streamlit nếu tìm thấy
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
        statusText.innerText = 'Lỗi nhận diện: ' + event.error;
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
    
    # Hiển thị lịch sử chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Nhận câu lệnh từ Chat Input hoặc từ Micro điền vào
    user_prompt = st.chat_input("Nhập câu lệnh hoặc bấm nút Micro phía trên để nói...")

    if user_prompt:
        # 1. Hiển thị câu lệnh của user
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # 2. No-Ron Agent xử lý & phản hồi
        agent_response = f"Đã nhận lệnh: '{user_prompt}'. No-Ron đang tiến hành phân tích và thực thi ngay!"
        
        with st.chat_message("assistant"):
            st.markdown(agent_response)
            
            # Nếu bật voice, phát giọng nói chuẩn gTTS rõ ràng
            if voice_enabled:
                audio_html = text_to_audio_html(agent_response, gtts_lang_code)
                st.components.v1.html(audio_html, height=0, width=0)

        st.session_state.messages.append({"role": "assistant", "content": agent_response})
        
        # 3. Thêm công việc vào Task Board của No-Ron
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
