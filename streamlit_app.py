import sys
import openai
import streamlit as st
from pinecone import Pinecone
from pinecone_plugins.assistant.models.chat import Message
import re

# Ensure the default encoding is UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Initialize Pinecone
pinecone_api_key = "d81b5f77-4498-4206-9bb6-93465e872257"
pc = Pinecone(api_key=pinecone_api_key)

assistant = pc.assistant.describe_assistant(
    assistant_name="global-market-analysis",
)

# Set OpenAI API key
openai.api_key = "sk-SdsESq8lplaDr2sO4sEvjxJFNIMgQtkaKm11dBdJ19BxbzrE"
openai.api_base = "https://api.fe8.cn/v1"

# Initialize conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Function to check if ChatGPT should generate a reply
def needs_gpt_reply(assistant_reply):
    gpt_trigger_phrases = [
        "无法提供", "无法回答", "对不起", "没有具体信息", "具体信息", "sorry",
        "no reply", "cannot answer", "no specific information", 
        "根据提供的搜索结果，没有具体信息", "具体数据", "没有具体数据", 
        "I do not have the necessary information to answer your question",
        "here is no information available"
    ]
    return any(phrase in assistant_reply for phrase in gpt_trigger_phrases)

# Function to convert document names into clickable links
def convert_to_clickable_links(text):
    pattern = r'\("([^"]+)"\)\(([^)]+)\)'
    replacement = r'[\1](\2)'
    return re.sub(pattern, replacement, text)

# Process user input and return result
def process_input(user_input):
    chat_context = st.session_state.conversation_history + [Message(content=user_input)]
    
    # Get assistant's response
    response = assistant.chat_completions(messages=chat_context)
    assistant_reply = response.choices[0]['message']['content']

    # Check if ChatGPT should provide an answer
    if needs_gpt_reply(assistant_reply):
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_input}]
        )
        final_reply = f"Sorry, there's no relevant content in the company's database. Here's a response from ChatGPT:\n\n{gpt_response.choices[0].message['content']}"
    else:
        # Convert document names to clickable links
        final_reply = convert_to_clickable_links(assistant_reply)

    st.session_state.conversation_history.append(Message(role="user", content=user_input))
    st.session_state.conversation_history.append(Message(role="assistant", content=final_reply))
    
    return final_reply

# Streamlit page layout
st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center;'>Intelligent Analysis of Global Market</h1>", unsafe_allow_html=True)

page_width = st.container()
with page_width:
    col1, col2 = st.columns([1, 1.75], gap="large")

    # Left input box and buttons
    def clear_text():
        st.session_state["input_text"] = ""

    with col1:
        st.markdown("<div style='margin-bottom: 10px;'>Here enter your questions</div>", unsafe_allow_html=True)
        input_container = st.container()
        with input_container:
            # Use session state to manage the text input
            if "input_text" not in st.session_state:
                st.session_state.input_text = ""
            user_input = st.text_area("Input your query here", value=st.session_state.input_text, height=320, key="input_text", label_visibility="collapsed")
        
        clear_submit_cols = st.columns([1, 1])
        with clear_submit_cols[0]:
            if st.button("Clear", on_click=clear_text):
                pass
        with clear_submit_cols[1]:
            if st.button("Submit") and user_input:
                response = process_input(user_input)

    # Right output box with scrollbar
    with col2:
        st.markdown("<div style='margin-bottom: 10px;'>Here check your conversations.</div>", unsafe_allow_html=True)
        output_container = st.container()
        with output_container:
            if st.session_state.conversation_history:
                history = "\n\n".join(
                    [f"**{msg.role.capitalize()}:** {msg.content}" for msg in st.session_state.conversation_history]
                )
                st.markdown(
                    f"""
                    <div style="height: 320px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;">
                    {history}
                    </div>
                    """, unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div style="height: 320px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;">
                    
                    </div>
                    """, unsafe_allow_html=True
                )

        # Clear Conversation button centered below the output container with padding
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)  # Add some padding
        if st.button("Clear Conversation"):
            st.session_state.conversation_history = []
            st.rerun()

# Style settings
st.markdown(
    """
    <style>
    .reportview-container .main .block-container {
        max-width: 80%;
        padding: 1rem;
    }
    textarea {
        border: none !important;  /* Hide the border for the textarea */
        box-shadow: none !important; /* Remove shadow to hide border completely */
    }
    .stTextArea div[role='textbox'] a {
        color: #0366d6;
        text-decoration: none;
    }
    .stTextArea div[role='textbox'] a:hover {
        text-decoration: underline;
    }
    .stTextArea div[role='textbox'] {
        border: none !important;  /* Hide border of the textbox */
        padding: 10px; /* Adjust padding to match overall look */
    }
    .stContainer {
        border: 1px solid #ccc;  /* Border for containers */
        padding: 10px;  /* Padding inside the container */
    }
    button {
        border: 1px solid #ccc;
        background-color: #f0f0f0;
        cursor: pointer;
    }
    button:hover {
        background-color: #e0e0e0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
