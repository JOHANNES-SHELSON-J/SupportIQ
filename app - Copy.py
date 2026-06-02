import streamlit as st
import joblib
import sqlite3
import os
import requests
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv
import auth

st.set_page_config(page_title="SupportIQ", initial_sidebar_state="collapsed")

# ---------- Global CSS ----------
st.markdown("""
<style>
    .main .block-container { max-width: 760px; padding-top: 3rem; }
    .brand-title {
        color: #1f3a5f;
        font-size: 2.6rem;
        font-weight: 800;
        margin-bottom: 0;
        letter-spacing: -0.02em;
    }
    .brand-sub {
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .stButton > button {
        background: #1f3a5f;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.4rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background: #2d4f7c;
        color: #ffffff;
    }
    .chat-header {
        color: #1f3a5f;
        font-size: 1.8rem;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Session state for login ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

# ---------- Helpers ----------
def reset_session():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.history = []

def logout():
    reset_session()
    st.rerun()

# ---------- Login / Signup screen ----------
def show_login():
    st.markdown('<div class="brand-title">SupportIQ</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">AI-powered customer support with built-in analytics</div>', unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

    with tab_login:
        st.subheader("Log in to your account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In"):
            success, result = auth.authenticate(email, password)
            if success:
                st.session_state.history = []
                st.session_state.logged_in = True
                st.session_state.username = email
                st.session_state.role = result
                st.rerun()
            else:
                st.error(result)

    with tab_signup:
        st.subheader("Create a customer account")
        new_email = st.text_input("Email", key="signup_email")
        new_pass = st.text_input("Password", type="password", key="signup_pass")
        st.caption("Password must be at least 8 characters and include an uppercase letter, a lowercase letter, a number, and a special character.")
        if st.button("Sign Up"):
            success, message = auth.create_customer(new_email, new_pass)
            if success:
                st.success(message)
            else:
                st.error(message)

# ---------- Loaders ----------
@st.cache_resource
def load_model():
    model = joblib.load("category_model.pkl")
    vectorizer = joblib.load("category_vectorizer.pkl")
    return model, vectorizer

@st.cache_resource
def load_sentiment():
    return SentimentIntensityAnalyzer()

# ---------- Gemini ----------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# ---------- Database ----------
def log_ticket(message, category, sentiment, username, confidence=None, source="live_chat"):
    conn = sqlite3.connect("tickets.db")
    conn.execute(
        "INSERT INTO tickets (message, category, sentiment, created_at, source, username, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (message, category, sentiment, datetime.now().isoformat(), source, username, confidence)
    )
    conn.commit()
    conn.close()

def predict_category(message, model, vectorizer):
    vec = vectorizer.transform([message])
    category = model.predict(vec)[0]
    probabilities = model.predict_proba(vec)[0]
    confidence = float(max(probabilities))
    return category, confidence

def detect_sentiment(message, analyzer):
    score = analyzer.polarity_scores(message)["compound"]
    if score <= -0.3:
        return "Negative"
    elif score >= 0.3:
        return "Positive"
    else:
        return "Neutral"

def generate_reply(message, category, sentiment):
    prompt = f"""You are a helpful, professional customer support agent for an e-commerce company.
A customer has sent the following message: "{message}"

Our system has classified this as a {category} issue with {sentiment} sentiment.

Write a warm, concise, helpful reply (2-4 sentences). Acknowledge their concern,
show you understand the issue, and explain the next step. Do not make up specific
order numbers or account details. Be empathetic if the sentiment is negative."""
    try:
        r = requests.post(
            GEMINI_URL,
            headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return f"(The AI assistant is temporarily unavailable. This looks like a {category.title()} issue and our team will follow up.)"

# ---------- Chat page (customers) ----------
def show_chat():
    model, vectorizer = load_model()
    analyzer = load_sentiment()

    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<div class="chat-header">SupportIQ</div>', unsafe_allow_html=True)
        st.caption(f"Logged in as {st.session_state.username}")
    with col2:
        if st.button("Log Out"):
            logout()

    st.divider()

    if "history" not in st.session_state:
        st.session_state.history = []

    if st.session_state.history:
        if st.button("Clear conversation"):
            st.session_state.history = []
            st.rerun()

    if not st.session_state.history:
        st.info("Hi! How can we help you today? Type your question below.")

    for turn in st.session_state.history:
        with st.chat_message("user"):
            st.write(turn["message"])
        with st.chat_message("assistant"):
            st.write(turn["reply"])

    user_message = st.chat_input("Type your support message...")
    if user_message:
        if len(user_message) > 1000:
            st.warning("Please keep your message under 1000 characters.")
            return

        with st.chat_message("user"):
            st.write(user_message)

        with st.chat_message("assistant"):
            with st.spinner("Typing..."):
                category, confidence = predict_category(user_message, model, vectorizer)
                sentiment = detect_sentiment(user_message, analyzer)
                reply = generate_reply(user_message, category, sentiment)
            st.write(reply)

        log_ticket(user_message, category, sentiment, st.session_state.username, confidence=confidence)
        st.session_state.history.append({
            "message": user_message,
            "category": category,
            "sentiment": sentiment,
            "reply": reply,
            "confidence": confidence,
        })
        st.rerun()

# ---------- Staff landing page ----------
def show_staff_landing():
    st.markdown('<div class="brand-title">Welcome back</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="brand-sub">Logged in as {st.session_state.username} (staff)</div>', unsafe_allow_html=True)
    st.write("Access your support analytics and customer chat history below.")
    st.write("")
    st.page_link("pages/1_Dashboard.py", label="Open Analytics Dashboard", icon=":material/dashboard:")
    st.write("")
    if st.button("Log Out"):
        logout()

# ---------- Main routing ----------
if not st.session_state.logged_in:
    show_login()
else:
    if st.session_state.role == "staff":
        show_staff_landing()
    else:
        show_chat()