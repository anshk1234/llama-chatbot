import streamlit as st
import ollama
import datetime

st.set_page_config(page_title="💬 Chatbot", layout="centered")
st.title("💬 Chatbot")
st.caption("🚀 Powered by Ollama — choose any installed model")

# Sidebar controls
with st.sidebar:
    st.markdown("### 🛠️ Settings")
    model_name = st.selectbox("Choose model", [
        "gemma3:1b",
        "llama3.2:1b",
        "deepseek-r1:1.5b",
        "phi3:mini",
        "minimax-m2:cloud",
        "deepseek-v3.1:671b-cloud",
        "gpt-oss:20b-cloud"
    ])
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    max_tokens = st.slider("Max Tokens", 64, 1024, 256, 64)

    if st.button("💾 Export Chat History"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        chat_text = "\n\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.messages])
        st.download_button("Download .txt", chat_text, file_name=f"chat_history_{timestamp}.txt")

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help you?"}]

# Display chat history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).markdown(msg["content"])

# Input bar
prompt = st.chat_input("Type your message...")

# Handle new input
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    response = ollama.chat(
        model=model_name,
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        options={
            "temperature": temperature,
            "num_predict": max_tokens
        }
    )

    reply = response["message"]["content"]
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.chat_message("assistant").markdown(reply)