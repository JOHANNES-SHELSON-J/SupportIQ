# SupportIQ

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=flat&logo=google&logoColor=white)

**An AI-powered customer support platform with built-in analytics.**

SupportIQ does more than answer customer questions. Every customer message is automatically classified by topic, scored for sentiment, and logged — turning a support chat into a live stream of business intelligence. Customers get conversational AI replies; support staff get a dashboard showing what customers are contacting them about, how they feel, and which issues are trending.

---

## What it does

**For customers** — a clean chat interface backed by a large language model. Customers sign up with an email, log in, and receive warm, context-aware support replies.

**Behind every message** — the system silently runs its own machine-learning pipeline:
- A trained classifier tags the message by category (Account, Order, Refund, Payment, Delivery, etc.)
- A sentiment analyser scores it Positive / Neutral / Negative
- A confidence score is recorded; low-confidence classifications can be flagged for human review

**For support staff** — a role-protected analytics dashboard:
- Headline metrics (total tickets, % negative sentiment, top category)
- Interactive charts (category, sentiment, volume over time, negative by category)
- A date-range filter that drives the whole dashboard
- A per-customer conversation drill-down
- Excel export of the filtered data

---

## Why it's interesting

A typical "support chatbot" project stops at wrapping an LLM. SupportIQ is a **hybrid system**: the LLM handles the open-ended human reply, while a separate, classical ML model does the structured classification that powers the analytics. Each tool does what it's best at — the LLM for natural language, the trained classifier for fast, controllable, measurable categorisation. The result is a product that both *talks* to customers and *learns* from them.

---

## Tech stack

- **App framework:** Streamlit (multi-page, role-based)
- **Classification:** scikit-learn (TF-IDF + Logistic Regression)
- **Sentiment:** VADER
- **Conversational AI:** Google Gemini (REST API)
- **Storage:** SQLite
- **Auth:** email + bcrypt-hashed passwords, role-based access (customer vs. staff)
- **Visualisation:** Plotly (interactive charts)

---

## Machine learning notes

The classifier was trained on the public Bitext customer-support dataset (~27,000 messages, 11 categories), reaching ~99.6% accuracy on the held-out test set.

**That number is honest but misleading, and understanding why matters.** The dataset is *synthetically generated* from templates, so messages within a category are highly patterned and easy to separate — the model partly memorises template shapes rather than learning the full variability of human language. This shows up in the confidence scores: on real, free-form messages the model's confidence drops sharply, because they're out-of-distribution relative to the clean templates. The system surfaces this rather than hiding it — uncertain predictions can be flagged for human review instead of trusted blindly.

**Takeaway:** a model can post excellent benchmark numbers while generalising poorly to real input. Measuring and acting on prediction confidence is what makes the difference.

---

## Running locally

1. Clone the repository and enter the folder
2. Create a virtual environment and activate it
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file containing: `GEMINI_API_KEY=your_key_here`
5. Run `python setup_users.py` to create staff accounts
6. Launch with `streamlit run app.py`

**Demo staff login:** `admin@supportiq.com` / `Admin@123`
Customers can register their own accounts from the Sign Up tab.

---

## Limitations & future work

- **Synthetic training data** limits real-world generalisation (see ML notes). Production would train on real, anonymised tickets.
- **Auth** demonstrates hashed credentials and role gating; production would add email verification, password reset, and session tokens.
- **Database** uses SQLite for simplicity; production would use PostgreSQL.
- **Next steps:** sentence-embedding models for better generalisation, a human-review queue for low-confidence tickets, and live deployment.

---

## Author

**Johannes Johnson**
[LinkedIn](http://www.linkedin.com/in/johannes-johnson-882636257) · [GitHub](https://github.com/JOHANNES-SHELSON-J) · [Portfolio](https://johannes-johnson-portfolio.vercel.app/)