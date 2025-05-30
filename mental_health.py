import streamlit as st
import openai
import base64
from datetime import datetime
from auth import init_db, login_user, register_user

# Set your Together.ai API key and endpoint
openai.api_key = "tgp_v1_hc26vYRxpnf-p8e516kP67AD2VXwxVKtj-ZyWSSCxrw"
openai.api_base = "https://api.together.xyz/v1"

st.set_page_config(page_title="EmotionSense - AI Driven Virtual Therapist")

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


def get_base64(background):
    with open(background, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

bin_str = get_base64("background1.png")

st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:background1.png;base64,{bin_str}");
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

# --- SESSION STATE INIT ---
st.session_state.setdefault('conversation_history', [])
st.session_state.setdefault('mood_ratings', [])

# --- USER NAME INPUT ---
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = st.text_input("\U0001F464 Enter your name to start:", key="user_name_input")
    if not st.session_state['user_name']:
        st.stop()

# --- GREETING ---
st.title(f"EmotionSense - AI Driven Virtual Therapist {st.session_state['user_name']}!")
st.markdown("_I'm your AI therapist. Let's talk about how you're feeling today._")

# --- MOOD CHECK-IN ---
st.markdown("### \U0001F321\ufe0f How do you feel today on a scale of 1 (low) to 10 (great)?")
mood = st.slider("Mood Rating", 1, 10, 5)
if st.button("Submit Mood"):
    st.session_state['mood_ratings'].append({"time": datetime.now(), "mood": mood})
    st.success("Thanks for sharing your mood!")

# --- TOGETHER.AI CHAT FUNCTIONS ---
def generate_response(user_input):
    st.session_state['conversation_history'].append({"role": "user", "content": user_input})
    response = openai.ChatCompletion.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=st.session_state['conversation_history'],
        temperature=0.7
    )
    ai_response = response['choices'][0]['message']['content']
    st.session_state['conversation_history'].append({"role": "assistant", "content": ai_response})
    return ai_response

def generate_affirmation():
    prompt = "Provide a short positive affirmation for someone feeling overwhelmed."
    response = openai.ChatCompletion.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

def generate_meditation_guide():
    prompt = "Provide a 5-minute guided meditation to reduce stress."
    response = openai.ChatCompletion.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# --- DISPLAY CHAT ---
for msg in st.session_state['conversation_history']:
    role = "You" if msg['role'] == "user" else "AI"
    st.markdown(f"**{role}:** {msg['content']}")

user_message = st.text_input("\U0001F4AC How can I help you today?")
if user_message:
    with st.spinner("Thinking..."):
        ai_response = generate_response(user_message)
        st.markdown(f"**AI:** {ai_response}")

# --- TOOLBOX ---
st.markdown("### \U0001FA9A Tools for Your Wellbeing")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button(" Positive Affirmation"):
        affirmation = generate_affirmation()
        st.markdown(f"**Affirmation:** {affirmation}")

with col2:
    if st.button(" Guided Meditation"):
        meditation_guide = generate_meditation_guide()
        st.markdown(f"**Guided Meditation:** {meditation_guide}")

with col3:
    if st.button("Mental Health Checkup"):
        st.session_state['show_phq'] = True

def phq9_test():
    st.subheader("\U0001F9E0 PHQ-9 Depression Screening")
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
            total_score += options[response]

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

if st.session_state.get('show_phq'):
    phq9_test()
