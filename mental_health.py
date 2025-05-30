# emotion_sense_app.py (Streamlit App using Together AI)
import streamlit as st
from chatbot import TogetherAIChatbot
from utils import show_emergency_resources, display_session_notes

st.set_page_config(page_title="EmotionSense - AI Therapist", layout="wide")
st.title("🧠 EmotionSense: Your AI Mental Health Companion")

# Initialize chatbot and session state
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = TogetherAIChatbot()

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Mood rating input
mood_score = st.slider("How are you feeling today? (0 = Terrible, 10 = Great)", 0, 10, 5)
if mood_score <= 3:
    st.warning("It looks like you're feeling low today. Remember, it's okay to ask for help.")

# User input
user_input = st.text_area("Talk to the AI Therapist", placeholder="Share your thoughts here...", height=150)
if st.button("Send") and user_input:
    st.session_state.conversation_history.append({"role": "user", "content": user_input})

    with st.spinner("AI is thinking..."):
        try:
            ai_response = st.session_state.chatbot.generate_response(st.session_state.conversation_history)
            st.session_state.conversation_history.append({"role": "assistant", "content": ai_response})
            st.success("AI responded!")
        except Exception as e:
            st.error(f"Something went wrong: {str(e)}")
            st.stop()

    if any(keyword in user_input.lower() for keyword in ["suicide", "harm", "kill myself", "end my life"]):
        show_emergency_resources()

# Display chat history
st.markdown("---")
st.subheader("🗨️ Chat History")
for message in st.session_state.conversation_history:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Session notes display
display_session_notes(st.session_state.chatbot)
