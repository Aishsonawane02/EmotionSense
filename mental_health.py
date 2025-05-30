import streamlit as st
import openai 
import base64
from datetime import datetime
from auth import init_db, login_user, register_user

# Initialize client using project-scoped key from secrets
from openai import OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])  # ✅ Correct way to initialize

st.set_page_config(page_title="EmotionSense - AI Driven Virtual Therapist")

    def get_base64(background):
        with open(background, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()

    bin_str = get_base64("background1.png")

    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
        }}
        .stTextInput > div > div > input {{
            background-color: #ffffffcc;
            color: #000;
        }}
        .stButton button {{
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
            padding: 0.5em 1em;
            font-weight: bold;
        }}
        </style>
    """, unsafe_allow_html=True)
init_db()

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
else:
    st.success(f"Logged in as {st.session_state['username']}")

    st.session_state.setdefault('conversation_history', [])
    st.session_state.setdefault('mood_ratings', [])

    if 'user_name' not in st.session_state:
        st.session_state['user_name'] = st.text_input("👤 Enter your name to start:", key="user_name_input")
        if not st.session_state['user_name']:
            st.stop()

    st.title(f"EmotionSense - AI Driven Virtual Therapist {st.session_state['user_name']}!")
    st.markdown("_I'm your AI therapist. Let's talk about how you're feeling today._")

    st.markdown("### 🌡️ How do you feel today on a scale of 1 (low) to 10 (great)?")
    mood = st.slider("Mood Rating", 1, 10, 5)
    if st.button("Submit Mood"):
        st.session_state['mood_ratings'].append({"time": datetime.now(), "mood": mood})
        if mood <= 2:
            st.warning("Sounds like you're really down. Would you like a calming meditation or a listening ear?")
        elif mood <= 4:
            st.info("Sorry to hear you're not feeling well. I'm here to help you through it.")
        elif mood <= 6:
            st.info("Seems like you're doing okay. Let’s keep the momentum!")
        elif mood <= 8:
            st.success("That’s good! Let’s keep the positivity going.")
        else:
            st.balloons()
            st.success("Awesome! Glad to hear you're feeling great!")

    def generate_response(user_input):
        st.session_state['conversation_history'].append({"role": "user", "content": user_input})
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state['conversation_history']
        )
        ai_response = response['choices'][0]['message']['content']
        st.session_state['conversation_history'].append({"role": "assistant", "content": ai_response})
        return ai_response

    def generate_affirmation():
        prompt = "Provide a short positive affirmation for someone feeling overwhelmed."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']

    def generate_meditation_guide():
        prompt = "Provide a 5-minute guided meditation to reduce stress."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']

    for msg in st.session_state['conversation_history']:
        role = "You" if msg['role'] == "user" else "AI"
        st.markdown(f"**{role}:** {msg['content']}")

    user_message = st.text_input("💬 How can I help you today?")
    if user_message:
        with st.spinner("Thinking..."):
            ai_response = generate_response(user_message)
            st.markdown(f"**AI:** {ai_response}")

    st.markdown("### 🧰 Tools for Your Wellbeing")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(" Positive Affirmation"):
            affirmation = generate_affirmation()
            st.markdown(f"**Affirmation:** {affirmation}")

    with col2:
        if st.button(" Guided Meditation"):
            meditation_guide = generate_meditation_guide()
            st.markdown(f"**Guided Meditation:** {meditation_guide}")

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
            "Moving or speaking so slowly that others noticed? Or the opposite – being fidgety or restless?",
            "Thoughts that you would be better off dead or hurting yourself in some way"
        ]

        options = {
            "Not at all": 0,
            "Several days": 1,
            "More than half the days": 2,
            "Nearly every day": 3
        }
        

        total_score = 0

        with st.form("phq9_form"):
            for i, question in enumerate(questions):
                response = st.radio(f"{i + 1}. {question}", list(options.keys()), key=f"q{i}")
                score = options[response]
                total_score += score

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

    with col3:
        if st.button("Mental Health Checkup"):
            st.session_state['show_phq'] = True

    if st.session_state.get('show_phq'):
        phq9_test()
