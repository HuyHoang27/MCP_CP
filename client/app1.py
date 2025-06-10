import streamlit as st

st.set_page_config(page_title="Chatbot Đơn Giản", page_icon="💬")

st.title("💬 Chatbot Đơn Giản với Streamlit")

# ────────────────────────────
# SIDEBAR + DIALOG
# ────────────────────────────

@st.dialog("📂 Prompt Explorer")
def show_dialog():
    st.markdown("### 🔍 Khám phá dữ liệu CSV")
    csv_path = st.text_input("📁 CSV Path", value="", placeholder="Nhập đường dẫn tới file CSV")
    topic = st.text_input("📝 Chủ đề", value="", placeholder="Nhập chủ đề cần khám phá")
    if st.button("✅ Xác nhận"):
        st.session_state.prompt = f"Khám phá chủ đề **{topic}** trong dữ liệu: `{csv_path}`"
        st.rerun()

def create_mcp_prompts_widget():
    with st.sidebar:
        st.header("⚙️ Tùy chọn")
        st.subheader("📜 Các Prompt sẵn có")
        if st.button("📊 explore-data"):
            show_dialog()

create_mcp_prompts_widget()

# ────────────────────────────
# SESSION STATE INIT
# ────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "prompt" not in st.session_state:
    st.session_state.prompt = []

# ────────────────────────────
# HIỂN THỊ LỊCH SỬ CHAT
# ────────────────────────────

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ────────────────────────────
# NHẬN INPUT
# ────────────────────────────

user_input = st.chat_input("Nhập tin nhắn của bạn...")

# Nếu người dùng nhập hoặc có prompt được tạo từ dialog
if user_input or st.session_state.prompt:
    content = user_input if user_input else st.session_state.prompt
    st.session_state.messages.append({"role": "user", "content": content})
    with st.chat_message("user"):
        st.markdown(content)

    # Tạo phản hồi từ bot
    bot_response = f"🤖 Bot: Tôi vừa nhận được: **{content}**"
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    with st.chat_message("assistant"):
        st.markdown(bot_response)

    # Reset prompt sau khi sử dụng
    st.session_state.prompt = ""
