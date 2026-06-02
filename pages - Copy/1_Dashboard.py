import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="collapsed")

# ---------- Access control: staff only ----------
if not st.session_state.get("logged_in") or st.session_state.get("role") != "staff":
    st.title("Staff Access Only")
    st.warning("You must be logged in as a staff member to view this page.")
    st.page_link("app.py", label="Return to login", icon=":material/arrow_back:")
    st.stop()

# ---------- Custom CSS ----------
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; max-width: 1200px; }
    .stat-card {
        background: #ffffff;
        border: 1px solid #e3e6ea;
        border-left: 4px solid #1f3a5f;
        border-radius: 10px;
        padding: 20px 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .stat-label {
        color: #6b7280;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .stat-value {
        color: #1f3a5f;
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1;
    }
    .section-title {
        color: #1f3a5f;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 28px 0 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Theme colors ----------
NAVY = "#1f3a5f"
RED = "#c0392b"
GREY = "#95a5a6"
GREEN = "#27ae60"

def apply_layout(fig, height=350):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#1a1a2e", size=12),
        xaxis=dict(gridcolor="#eef0f3"),
        yaxis=dict(gridcolor="#eef0f3"),
        showlegend=False,
    )
    return fig

# ---------- Header ----------
col1, col2 = st.columns([4, 1])
with col1:
    st.title("Analytics Dashboard")
    st.caption(f"Logged in as {st.session_state.username} (staff)")
with col2:
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.switch_page("app.py")

@st.cache_data(ttl=10)
def load_tickets():
    conn = sqlite3.connect("tickets.db")
    df = pd.read_sql_query("SELECT * FROM tickets", conn)
    conn.close()
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["date"] = df["created_at"].dt.date
    return df

df_all = load_tickets()

if df_all.empty:
    st.warning("No tickets yet.")
    st.stop()

# ---------- Date range filter ----------
st.markdown('<div class="section-title">Date Range</div>', unsafe_allow_html=True)
preset = st.radio(
    "Quick range",
    ["All time", "Last 7 days", "Last 30 days", "Last 90 days", "Custom"],
    horizontal=True,
    label_visibility="collapsed",
)

max_date = df_all["created_at"].max().date()
min_date = df_all["created_at"].min().date()

if preset == "All time":
    start_date, end_date = min_date, max_date
elif preset == "Last 7 days":
    start_date, end_date = max_date - timedelta(days=7), max_date
elif preset == "Last 30 days":
    start_date, end_date = max_date - timedelta(days=30), max_date
elif preset == "Last 90 days":
    start_date, end_date = max_date - timedelta(days=90), max_date
else:
    c1, c2 = st.columns(2)
    start_date = c1.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
    end_date = c2.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

df = df_all[(df_all["date"] >= start_date) & (df_all["date"] <= end_date)].copy()
st.caption(f"Showing data from {start_date} to {end_date}  ({len(df):,} tickets)")

st.divider()

view = st.radio("View", ["Analytics", "Chat History"], horizontal=True)
st.divider()

if df.empty:
    st.info("No tickets in this date range. Try a wider range.")
    st.stop()

if view == "Analytics":
    total = len(df)
    neg_pct = round((df["sentiment"] == "Negative").mean() * 100, 1)
    top_cat = df["category"].value_counts().idxmax().title()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Total Tickets</div><div class="stat-value">{total:,}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Negative Sentiment</div><div class="stat-value">{neg_pct}%</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Top Category</div><div class="stat-value">{top_cat}</div></div>', unsafe_allow_html=True)

    # ----- Export button -----
    buffer = io.BytesIO()
    export_df = df[["created_at", "username", "message", "category", "sentiment", "source"]].copy()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Tickets")
    st.write("")
    st.download_button(
        label="Download report (Excel)",
        data=buffer.getvalue(),
        file_name=f"support_tickets_{start_date}_to_{end_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    left, right = st.columns(2)

    with left:
        st.markdown('<div class="section-title">Tickets by Category</div>', unsafe_allow_html=True)
        cat_counts = df["category"].value_counts()
        fig1 = go.Figure(go.Bar(
            x=cat_counts.index, y=cat_counts.values,
            marker_color=NAVY,
            hovertemplate="%{x}: %{y} tickets<extra></extra>",
        ))
        apply_layout(fig1)
        st.plotly_chart(fig1, use_container_width=True)

    with right:
        st.markdown('<div class="section-title">Sentiment Breakdown</div>', unsafe_allow_html=True)
        sent_counts = df["sentiment"].value_counts()
        color_map = {"Negative": RED, "Neutral": GREY, "Positive": GREEN}
        fig2 = go.Figure(go.Pie(
            labels=sent_counts.index, values=sent_counts.values,
            marker_colors=[color_map.get(s, GREY) for s in sent_counts.index],
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        ))
        fig2.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10),
                           paper_bgcolor="white", font=dict(color="#1a1a2e"))
        st.plotly_chart(fig2, use_container_width=True)

    left2, right2 = st.columns(2)

    with left2:
        st.markdown('<div class="section-title">Ticket Volume Over Time</div>', unsafe_allow_html=True)
        daily = df.groupby("date").size().reset_index(name="count")
        fig3 = go.Figure(go.Scatter(
            x=daily["date"], y=daily["count"],
            mode="lines+markers", line=dict(color=NAVY, width=2),
            marker=dict(size=5),
            hovertemplate="%{x}: %{y} tickets<extra></extra>",
        ))
        apply_layout(fig3)
        st.plotly_chart(fig3, use_container_width=True)

    with right2:
        st.markdown('<div class="section-title">Negative Tickets by Category</div>', unsafe_allow_html=True)
        neg_by_cat = df[df["sentiment"] == "Negative"]["category"].value_counts()
        if not neg_by_cat.empty:
            fig4 = go.Figure(go.Bar(
                x=neg_by_cat.index, y=neg_by_cat.values,
                marker_color=RED,
                hovertemplate="%{x}: %{y} negative<extra></extra>",
            ))
            apply_layout(fig4)
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No negative tickets in this range.")

else:  # Chat History
    st.markdown('<div class="section-title">Customer Conversations</div>', unsafe_allow_html=True)

    live = df[df["source"] == "live_chat"].copy()

    if live.empty:
        st.info("No live customer chats in this date range.")
    else:
        summary = (
            live.groupby("username")
            .agg(
                messages=("message", "count"),
                last_active=("created_at", "max"),
                negative=("sentiment", lambda s: (s == "Negative").sum()),
            )
            .reset_index()
            .sort_values("last_active", ascending=False)
        )

        st.caption(f"{len(summary)} customer(s) with live conversations")

        customer_list = summary["username"].tolist()
        selected = st.selectbox("Select a customer to view their conversation", customer_list)

        row = summary[summary["username"] == selected].iloc[0]
        s1, s2, s3 = st.columns(3)
        with s1:
            st.markdown(f'<div class="stat-card"><div class="stat-label">Messages</div><div class="stat-value">{int(row["messages"])}</div></div>', unsafe_allow_html=True)
        with s2:
            st.markdown(f'<div class="stat-card"><div class="stat-label">Negative Msgs</div><div class="stat-value">{int(row["negative"])}</div></div>', unsafe_allow_html=True)
        with s3:
            st.markdown(f'<div class="stat-card"><div class="stat-label">Last Active</div><div class="stat-value" style="font-size:1.1rem;">{row["last_active"].strftime("%b %d, %H:%M")}</div></div>', unsafe_allow_html=True)

        st.write("")
        st.markdown(f'<div class="section-title">Conversation with {selected}</div>', unsafe_allow_html=True)

        convo = live[live["username"] == selected].sort_values("created_at")
        for _, msg in convo.iterrows():
            with st.chat_message("user"):
                st.write(msg["message"])
                st.caption(f"{msg['created_at'].strftime('%b %d, %Y %H:%M')}  •  {msg['category']}  •  {msg['sentiment']}")