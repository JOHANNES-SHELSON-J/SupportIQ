import pandas as pd
import sqlite3
import joblib
from datetime import datetime, timedelta
import random
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load data and model
df = pd.read_csv("data.csv")
model = joblib.load("category_model.pkl")
vectorizer = joblib.load("category_vectorizer.pkl")
analyzer = SentimentIntensityAnalyzer()

# Take a sample so seeding is fast (2000 messages is plenty for a dashboard)
sample = df.sample(n=2000, random_state=42).reset_index(drop=True)

# Predict category + sentiment for each, and spread them over the last 90 days
conn = sqlite3.connect("tickets.db")

vecs = vectorizer.transform(sample["instruction"])
categories = model.predict(vecs)

rows = []
for i, msg in enumerate(sample["instruction"]):
    cat = categories[i]
    score = analyzer.polarity_scores(msg)["compound"]
    sent = "Negative" if score <= -0.3 else ("Positive" if score >= 0.3 else "Neutral")
    days_ago = random.randint(0, 90)
    when = (datetime.now() - timedelta(days=days_ago)).isoformat()
    rows.append((msg, cat, sent, when, "historical"))

conn.executemany(
    "INSERT INTO tickets (message, category, sentiment, created_at, source) VALUES (?, ?, ?, ?, ?)",
    rows
)
conn.commit()

count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
conn.close()
print(f"Seeded. Database now has {count} tickets.")
