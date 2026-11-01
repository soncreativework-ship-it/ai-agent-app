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
