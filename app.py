import base64
import io
import google.generativeai as genai
from gtts import gTTS
import streamlit as st

# 1. Cấu hình trang Streamlit
st.set_page_config(
    page_title="Voice AI Agent (No-Ron)", page_icon="🎙️", layout="wide"
)

st.title("🎙️ Voice AI Agent & Neural Execution (No-Ron)")

# 2. Cấu hình Gemini API
# Lấy API Key từ Secrets của Streamlit
if "GEMINI_API_KEY" in st.secrets:
  genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
  st.error("Chưa cấu hình GEMINI_API_KEY trong Secrets của Streamlit Cloud!")

# Khởi tạo model Gemini 3.8 Flash mới nhất
try:
  model = genai.GenerativeModel("gemini-3.8-flash")
except Exception as e:
  st.error(f"Lỗi kết nối Model Gemini: {e}")
  model = None

# 3. Quản lý trạng thái Session State
if "messages" not in st.session_state:
  st.session_state.messages = []
if "tasks" not in st.session_state:
  st.session_state.tasks = []

# 4. Giao diện Sidebar
with st.sidebar:
  st.header("⚙️ Cấu hình Voice Agent")
  language = st.selectbox("Ngôn ngữ giọng nói:", ["vi", "en"])
  st.markdown("---")
  st.subheader("📌 Bảng nhiệm vụ (Task Board)")
  if st.session_state.tasks:
    for idx, task in enumerate(st.session_state.tasks, 1):
      st.write(f"{idx}. {task}")
  else:
    st.info("Chưa có nhiệm vụ nào được tạo.")

# 5. Hiển thị lịch sử Chat
for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.write(msg["content"])

# 6. Xử lý đầu vào từ User
user_input = st.chat_input("Nhập câu lệnh cho No-Ron...")

if user_input and model:
  # Hiển thị câu hỏi của User
  st.session_state.messages.append({"role": "user", "content": user_input})
  with st.chat_message("user"):
    st.write(user_input)

  # Gọi Gemini 3.8 Flash xử lý
  with st.chat_message("assistant"):
    with st.spinner("No-Ron đang suy nghĩ..."):
      try:
        response = model.generate_content(user_input)
        reply_text = response.text
        st.write(reply_text)

        # Tạo file âm thanh đọc câu trả lời bằng gTTS
        tts = gTTS(text=reply_text, lang=language)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)

        # Phát âm thanh trực tiếp trên web
        st.audio(fp, format="audio/mp3")

        # Lưu câu trả lời vào lịch sử
        st.session_state.messages.append(
            {"role": "assistant", "content": reply_text}
        )

        # Cập nhật bảng công việc đơn giản nếu có từ khóa
        if "nhiệm vụ" in reply_text.lower() or "bước" in reply_text.lower():
          st.session_state.tasks.append(
              user_input[:30] + "..."
          )  # Lưu tóm tắt nhiệm vụ
          st.rerun()

      except Exception as err:
        st.error(f"Lỗi xử lý API: {err}")
