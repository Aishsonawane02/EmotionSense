import streamlit as st
import ollama
import base64
from datetime import datetime
from auth import init_db, login_user, register_user
from secure_store import init_data_db, save_mood, save_chat, get_mood_history, get_chat_history
init_data_db()


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
    #  Show the chatbot here (move your chatbot code below this block)

#add logout button 
    if st.button("Logout"):
          # Clear session state and rerun
        st.session_state['authenticated'] = False
        st.session_state['username'] = ""
        st.session_state['conversation_history'] = []
        st.session_state['mood_ratings'] = []
        st.rerun()

def get_base64(background):
    with open(background,"rb") as f:
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
    st.session_state['user_name'] = st.text_input("👤 Enter your name to start:", key="user_name_input")
    if not st.session_state['user_name']:
        st.stop()

# --- GREETING ---
st.title(f"EmotionSense - AI Driven Virtual Therapist {st.session_state['user_name']}!")
st.markdown("_I'm your AI therapist. Let's talk about how you're feeling today._")

# --- MOOD CHECK-IN ---
st.markdown("### 🌡️ How do you feel today on a scale of 1 (low) to 10 (great)?")
mood = st.slider("Mood Rating", 1, 10, 5)
if st.button("Submit Mood"):
    save_mood(st.session_state['username'], mood)


    if mood <= 2:
        st.warning("😔 It sounds like you're really struggling. I'm here for you — feel free to talk.")
    elif 3 <= mood <= 4:
        st.info("😟 You’re not feeling your best today. Let’s talk about it, maybe it’ll help.")
    elif 5 <= mood <= 6:
        st.info("😐 You're feeling neutral. Let’s explore what might lift your spirits.")
    elif 7 <= mood <= 9:
        st.success("😊 That’s good to hear! Let’s keep up the positive vibes.")
    else:
        st.balloons()
        st.success("😄 You’re feeling great! That’s wonderful to see!")

# --- CONVERSATION ---
def generate_response(user_input):
    st.session_state['conversation_history'].append({"role": "user", "content": user_input})
    response = ollama.chat(model="llama3.1:8b", messages=st.session_state['conversation_history'])
    ai_response = response['message']['content']
    save_chat(st.session_state['username'], "user", user_input)
    save_chat(st.session_state['username'], "AI", ai_response)

    st.session_state['conversation_history'].append({"role": "assistant", "content": ai_response})
    return ai_response

@st.cache_data
def generate_affirmation():
    prompt = "Provide a short positive affirmation for someone feeling overwhelmed."
    response = ollama.chat(model="llama3.1:8b", messages=[{"role": "user", "content": prompt}])
    return response['message']['content']
@st.cache_data
def generate_meditation_guide():
    prompt = "Provide a 5-minute guided meditation to reduce stress."
    response = ollama.chat(model="llama3.1:8b", messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

# --- DISPLAY CHAT ---
for msg in st.session_state['conversation_history']:
    role = "You" if msg['role'] == "user" else "AI"
    st.markdown(f"**{role}:** {msg['content']}")

user_message = st.text_input("💬 How can I help you today?")
if user_message:
    with st.spinner("Thinking..."):
        ai_response = generate_response(user_message)
        st.markdown(f"**AI:** {ai_response}")

# --- TOOLBOX ---
st.markdown("### 🧰 Tools for Your Wellbeing")
col1, col2 , col3 = st.columns(3)

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

# Show the test if triggered
if st.session_state.get('show_phq'):
    phq9_test()
