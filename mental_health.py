# mental_health.py
import streamlit as st
import requests
import base64
import os
from datetime import datetime
from auth import init_db, login_user, register_user

st.set_page_config(page_title="EmotionSense - AI Driven Virtual Therapist")

# --- INIT AUTH DB ---
init_db()

# --- USER AUTH ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("Login to EmotionSense")
    choice = st.selectbox("Login or Register", ["Login", "Register"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if choice == "Login":
        if st.button("Login"):
            if login_user(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.success(f"Welcome {username}")
            else:
                st.error("Incorrect username or password.")
    else:
        if st.button("Register"):
            if register_user(username, password):
                st.success("Registration successful. Please log in.")
            else:
                st.error("Username already exists.")
    st.stop()

# --- BACKGROUND IMAGE ---
def get_base64(background):
    with open(background, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_str = get_base64("background1.webp")
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/webp;base64,{bg_str}");
        background-size: cover;
        background-attachment: fixed;
    }}
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INIT ---
st.session_state.setdefault('conversation_history', [])
st.session_state.setdefault('mood_ratings', [])

# --- USER NAME INPUT ---
if 'user_name' not in st.session_state:
    name = st.text_input("👤 Enter your name to start:")
    if name:
        st.session_state['user_name'] = name
    else:
        st.stop()

# --- GREETING ---
st.title(f"EmotionSense - Welcome {st.session_state['user_name']}!")
st.markdown("_I'm your AI therapist. Let's talk about how you're feeling today._")

# --- TOGETHER AI ---
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]

def generate_response(user_input):
    st.session_state['conversation_history'].append({"role": "user", "content": user_input})

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": st.session_state['conversation_history'],
        "temperature": 0.7,
        "max_tokens": 512
    }

    res = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload)
    res.raise_for_status()
    ai_reply = res.json()["choices"][0]["message"]["content"]

    st.session_state['conversation_history'].append({"role": "assistant", "content": ai_reply})
    return ai_reply

def generate_affirmation():
    return generate_response("Provide a short positive affirmation for someone feeling overwhelmed.")

def generate_meditation_guide():
    return generate_response("Provide a 5-minute guided meditation to reduce stress.")

# --- MOOD CHECK-IN ---
st.markdown("### 🌡️ How do you feel today on a scale of 1 (low) to 10 (great)?")
mood = st.slider("Mood Rating", 1, 10, 5)
if st.button("Submit Mood"):
    st.session_state['mood_ratings'].append({"time": datetime.now(), "mood": mood})
    st.success("Thanks for sharing your mood!")

# --- CHAT ---
for msg in st.session_state['conversation_history']:
    role = "You" if msg['role'] == "user" else "AI"
    st.markdown(f"**{role}:** {msg['content']}")

user_message = st.text_input("💬 How can I help you today?")
if user_message:
    with st.spinner("Thinking..."):
        reply = generate_response(user_message)
        st.markdown(f"**AI:** {reply}")

# --- TOOLBOX ---
st.markdown("### 🧰 Tools for Your Wellbeing")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Positive Affirmation"):
        st.markdown(f"**Affirmation:** {generate_affirmation()}")

with col2:
    if st.button("Guided Meditation"):
        st.markdown(f"**Guided Meditation:** {generate_meditation_guide()}")

with col3:
    if st.button("Mental Health Checkup"):
        st.session_state['show_phq'] = True

# --- PHQ-9 Test ---
def phq9_test():
    st.subheader("🧠 PHQ-9 Depression Screening")
    st.markdown("Answer the following questions based on how you've felt **over the past two weeks**:")

    questions = [
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
        "Trouble falling or staying asleep, or sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself – or that you are a failure or have let yourself or your family down",
        "Trouble concentrating on things (e.g., reading the newspaper or watching TV)",
        "Moving or speaking slowly, or being fidgety or restless",
        "Thoughts that you would be better off dead or hurting yourself"
    ]

    options = {
        "Not at all": 0,
        "Several days": 1,
        "More than half the days": 2,
        "Nearly every day": 3
    }

    total_score = 0

    with st.form("phq9_form"):
        for i, q in enumerate(questions):
            ans = st.radio(f"{i+1}. {q}", options=list(options.keys()), key=f"q{i}")
            total_score += options[ans]
        submitted = st.form_submit_button("Submit Test")

    if submitted:
        st.success(f"Your PHQ-9 Score: {total_score}")
        if total_score <= 4:
            result = "Minimal or no depression"
        elif 5 <= total_score <= 9:
            result = "Mild depression"
        elif 10 <= total_score <= 14:
            result = "Moderate depression"
        elif 15 <= total_score <= 19:
            result = "Moderately severe depression"
        else:
            result = "Severe depression"
        st.markdown(f"### **Result: {result}**")

if st.session_state.get("show_phq"):
    phq9_test()
