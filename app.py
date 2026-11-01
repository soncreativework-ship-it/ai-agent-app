import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

st.set_page_config(
    page_title="AI Multi-Agent Control",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Khởi tạo Gemini API từ Secrets
gemini_key = st.secrets.get("GEMINI_API_KEY", "")
if gemini_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    st.error("⚠️ Chưa tìm thấy GEMINI_API_KEY trong phần Secrets của Streamlit Cloud!")

st.title("🤖 AI Multi-Agent Neural Control Center")
st.markdown("<p style='text-align: center; color: #888;'>Hệ thống Quản lý và Tương tác Đa Tác Nhân (Multi-Agent System)</p>", unsafe_allow_html=True)

st.markdown("---")
st.subheader("💬 Tương Tác & Phân Việc AI Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập câu lệnh hoặc nội dung cần phân việc..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if gemini_key:
            try:
                with st.spinner("Agent đang xử lý..."):
                    response = model.generate_content(prompt)
                    ai_reply = response.text
                    st.markdown(ai_reply)
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            except Exception as e:
                st.error(f"Lỗi kết nối AI: {e}")
        else:
            st.error("Vui lòng cấu hình GEMINI_API_KEY trong Secrets.")

st.markdown("---")
st.markdown("### 🌐 Sơ đồ Mạng lưới Tác nhân (Neural Topology)")

vis_html = """
<div id="mynetwork" style="width: 100%; height: 300px; background-color: #111; border-radius: 10px;"></div>
<script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<script type="text/javascript">
  var nodes = new vis.DataSet([
    {id: 1, label: 'Master Agent', color: '#ff4b4b'},
    {id: 2, label: 'Analyzer Agent', color: '#4b79ff'},
    {id: 3, label: 'Executor Agent', color: '#4bffb3'}
  ]);
  var edges = new vis.DataSet([
    {from: 1, to: 2},
    {from: 1, to: 3}
  ]);
  var container = document.getElementById('mynetwork');
  var data = { nodes: nodes, edges: edges };
  var options = { physics: true };
  var network = new vis.Network(container, data, options);
</script>
"""
components.html(vis_html, height=320)
import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai

st.set_page_config(
    page_title="AI Multi-Agent Control",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Khởi tạo Gemini API từ Secrets
gemini_key = st.secrets.get("GEMINI_API_KEY", "")
if gemini_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    st.error("⚠️ Chưa tìm thấy GEMINI_API_KEY trong phần Secrets của Streamlit Cloud!")

st.title("🤖 AI Multi-Agent Neural Control Center")
st.markdown("<p style='text-align: center; color: #888;'>Hệ thống Quản lý và Tương tác Đa Tác Nhân (Voice-Controlled)</p>", unsafe_allow_html=True)

# Tích hợp bộ nhận diện giọng nói trực tiếp qua Web Speech API của trình duyệt
voice_html = """
<div style="background: #1e1e1e; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; border: 1px solid #333;">
    <h3 style="color: #fff; margin-top: 0; font-size: 16px;">🎙️ Điều Khiển Giọng Nói Trực Tiếp</h3>
    <button id="micBtn" onclick="toggleMic()" style="background-color: #ff4b4b; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 30px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 12px rgba(255,75,75,0.4);">
        🔴 Bật Micro (Off)
    </button>
    <p id="transcript" style="color: #00ffcc; margin-top: 10px; font-style: italic; min-height: 24px;"></p>
</div>

<script>
    let recognition;
    let isListening = false;
    const micBtn = document.getElementById('micBtn');
    const transcriptDisplay = document.getElementById('transcript');

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'vi-VN'; // Nhận diện tiếng Việt
        recognition.continuous = false;
        recognition.interimResults = true;

        recognition.onstart = function() {
            isListening = true;
            micBtn.style.backgroundColor = '#00cc66';
            micBtn.innerText = '🟢 Đang nghe... (Bấm để tắt)';
            transcriptDisplay.innerText = "Đang lắng nghe mệnh lệnh của bạn...";
        };

        recognition.onresult = function(event) {
            let interimTranscript = '';
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            if (finalTranscript) {
                transcriptDisplay.innerText = "Đã nhận: " + finalTranscript;
                // Tự động tìm khung nhập chat của Streamlit và điền vào
                setTimeout(() => {
                    const chatInputs = window.parent.document.querySelectorAll('input[type="text"], textarea');
                    for (let input of chatInputs) {
                        if (input.placeholder && input.placeholder.includes("Nhập câu lệnh")) {
                            input.value = finalTranscript;
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            // Tự động nhấn phím Enter để gửi lệnh cho Agent
                            input.dispatchEvent(new KeyboardEvent('keydown', {
                                key: 'Enter',
                                code: 'Enter',
                                keyCode: 13,
                                which: 13,
                                bubbles: true
                            }));
                            break;
                        }
                    }
                }, 500);
            } else if (interimTranscript) {
                transcriptDisplay.innerText = "Đang nghe: " + interimTranscript;
            }
        };

        recognition.onerror = function(event) {
            transcriptDisplay.innerText = "Lỗi micro: " + event.error;
            stopMic();
        };

        recognition.onend = function() {
            stopMic();
        };
    } else {
        micBtn.innerText = "⚠️ Trình duyệt không hỗ trợ Voice";
        micBtn.disabled = true;
    }

    function toggleMic() {
        if (!isListening) {
            try {
                recognition.start();
            } catch(e) {
                console.log(e);
            }
        } else {
            recognition.stop();
            stopMic();
        }
    }

    function stopMic() {
        isListening = false;
        micBtn.style.backgroundColor = '#ff4b4b';
        micBtn.innerText = '🔴 Bật Micro (Off)';
    }
</script>
"""
components.html(voice_html, height=140)

st.markdown("---")
st.subheader("💬 Tương Tác & Phân Việc AI Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập câu lệnh hoặc nội dung cần phân việc..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if gemini_key:
            try:
                with st.spinner("Agent đang xử lý..."):
                    response = model.generate_content(prompt)
                    ai_reply = response.text
                    st.markdown(ai_reply)
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            except Exception as e:
                st.error(f"Lỗi kết nối AI: {e}")
        else:
            st.error("Vui lòng cấu hình GEMINI_API_KEY trong Secrets.")

st.markdown("---")
st.markdown("### 🌐 Sơ đồ Mạng lưới Tác nhân (Neural Topology)")

vis_html = """
<div id="mynetwork" style="width: 100%; height: 250px; background-color: #111; border-radius: 10px;"></div>
<script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<script type="text/javascript">
  var nodes = new vis.DataSet([
    {id: 1, label: 'Master Agent', color: '#ff4b4b'},
    {id: 2, label: 'Analyzer Agent', color: '#4b79ff'},
    {id: 3, label: 'Executor Agent', color: '#4bffb3'}
  ]);
  var edges = new vis.DataSet([
    {from: 1, to: 2},
    {from: 1, to: 3}
  ]);
  var container = document.getElementById('mynetwork');
  var data = { nodes: nodes, edges: edges };
  var options = { physics: true };
  var network = new vis.Network(container, data, options);
</script>
"""
components.html(vis_html, height=270)
