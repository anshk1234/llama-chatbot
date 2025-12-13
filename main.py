import streamlit as st
import ollama
import datetime
import json
import os
import time
from streamlit_lottie import st_lottie
import pandas as pd

st.set_page_config(page_title="💬 Chatbot", layout="centered")

# Splash animation
def load_lottiefile(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

if "show_intro" not in st.session_state:
    st.session_state.show_intro = True

if st.session_state.show_intro:
    lottie_intro = load_lottiefile("neural.json")
    splash = st.empty()
    with splash.container():
        st.markdown("<h1 style='text-align:center;'>WELCOME to Ollama chat 💬</h1>", unsafe_allow_html=True)
        st_lottie(lottie_intro, height=350, speed=1.0, loop=True)
        time.sleep(3)
    splash.empty()
    st.session_state.show_intro = False

st.title("💬 Ollama Chat")
st.caption("🚀 Powered by Ollama — multiple chat sessions with persistence")

# File to store chats locally
CHAT_FILE = "saved_chats.json"

def load_chats():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"Chat 1": [{"role": "assistant", "content": "How can I help you?"}]}

def save_chats():
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.chats, f, indent=2)

# Initialize chats
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()
if "current_chat" not in st.session_state:
    st.session_state.current_chat = list(st.session_state.chats.keys())[0]

# Sidebar controls
with st.sidebar:
    st.markdown("### 🛠️ Settings")
    model_name = st.selectbox("Choose model", [
        "qwen2.5:0.5b",
        "gemma3:1b",
        "llama3.2:1b",
        "deepseek-r1:1.5b",
        "qwen2.5:1.5b",
        "phi3:mini",
        "minimax-m2:cloud",
        "deepseek-v3.1:671b-cloud",
        "gpt-oss:20b-cloud",
        "gpt-oss:120b-cloud",
        "qwen3-coder:480b-cloud"
    ])
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    max_tokens = st.slider("Max Tokens", 64, 4000, 1000, 64)

    with st.expander("💬 Manage Chats"):
        chat_names = list(st.session_state.chats.keys())
        selected_chat = st.selectbox("Select chat", chat_names, index=chat_names.index(st.session_state.current_chat))
        st.session_state.current_chat = selected_chat

        if st.button("➕ New Chat"):
            new_chat_name = f"Chat {len(st.session_state.chats) + 1}"
            st.session_state.chats[new_chat_name] = [{"role": "assistant", "content": "New chat started. How can I help you?"}]
            st.session_state.current_chat = new_chat_name
            save_chats()

        if st.button("🗑️ Delete Current Chat"):
            if st.session_state.current_chat in st.session_state.chats:
                del st.session_state.chats[st.session_state.current_chat]
                if st.session_state.chats:
                    st.session_state.current_chat = list(st.session_state.chats.keys())[0]
                else:
                    st.session_state.chats = {"Chat 1": [{"role": "assistant", "content": "How can I help you?"}]}
                    st.session_state.current_chat = "Chat 1"
                save_chats()

        new_name = st.text_input("✏️ Rename Current Chat", value=st.session_state.current_chat)
        if st.button("✅ Apply Rename"):
            if new_name and new_name != st.session_state.current_chat:
                st.session_state.chats[new_name] = st.session_state.chats.pop(st.session_state.current_chat)
                st.session_state.current_chat = new_name
                save_chats()

        if st.button("💾 Export Current Chat"):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            chat_text = "\n\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chats[st.session_state.current_chat]])
            st.download_button("Download .txt", chat_text, file_name=f"{st.session_state.current_chat}_{timestamp}.txt")

# Ensure current_chat is valid
if st.session_state.current_chat not in st.session_state.chats:
    if not st.session_state.chats:
        st.session_state.chats = {"Chat 1": [{"role": "assistant", "content": "How can I help you?"}]}
    st.session_state.current_chat = list(st.session_state.chats.keys())[0]

# Display chat history
for msg in st.session_state.chats[st.session_state.current_chat]:
    st.chat_message(msg["role"]).markdown(msg["content"])

# Input bar with mic + file upload
prompt = st.chat_input(
    "Say something, record audio (speech-to-text), or attach a file",
    accept_audio=True,
    accept_file=True,
    file_type=["txt", "pdf", "json", "py", "csv"]
)

# Handle input
if prompt:
    # Text input (typed or speech-to-text)
    if prompt.text:
        st.session_state.chats[st.session_state.current_chat].append({"role": "user", "content": prompt.text})
        st.chat_message("user").markdown(prompt.text)

        stream_area = st.chat_message("assistant").markdown("")
        reply = ""
        for chunk in ollama.chat(
            model=model_name,
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.chats[st.session_state.current_chat]],
            options={"temperature": temperature, "num_predict": max_tokens},
            stream=True
        ):
            token = chunk["message"]["content"]
            reply += token
            stream_area.markdown(reply)

        st.session_state.chats[st.session_state.current_chat].append({"role": "assistant", "content": reply})
        save_chats()

    # File input
    if prompt.files:
        uploaded_file = prompt.files[0]
        st.chat_message("user").markdown(f"📎 Uploaded file: {uploaded_file.name}")

        # Read file contents depending on type
        ext = uploaded_file.name.split(".")[-1].lower()
        file_text = ""
        if ext == "txt":
            file_text = uploaded_file.read().decode("utf-8")
        elif ext == "json":
            file_text = json.dumps(json.load(uploaded_file), indent=2)
        elif ext == "csv":
            df = pd.read_csv(uploaded_file)
            file_text = df.to_string()
        elif ext == "py":
            file_text = uploaded_file.read().decode("utf-8")
        elif ext == "pdf":
            import PyPDF2
            reader = PyPDF2.PdfReader(uploaded_file)
            file_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

        # Add file contents into chat context
        if file_text:
            st.session_state.chats[st.session_state.current_chat].append({"role": "user", "content": f"[File {uploaded_file.name} uploaded]\n\n{file_text}"})
            save_chats()