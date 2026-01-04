import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# -----------------------------
# Constants
# -----------------------------
MONTHLY_COST = 26.00
FULL_TICKET_PRICE = 15.99

SHEET_ID = "1tx1soNTPFvJP9LFuk-aB4g3SvMogoamBUryrMW_hMfY"
SHEET_NAME = "Sheet1"

# -----------------------------
# Load Data from Google Sheets
# -----------------------------
st.title("🎬 Regal Unlimited Movie Pass Dashboard")

@st.cache_data(ttl=60)  # refresh every 60 seconds
def load_data():
    url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    )
    df = pd.read_csv(url)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M")
    return df

df = load_data()

# -----------------------------
# Metrics Calulation
# -----------------------------
visits_per_month = df.groupby("month").size()
total_visits = len(df)
avg_visits = visits_per_month.mean()

months_active = visits_per_month.count()
total_spent = months_active * MONTHLY_COST
full_price_cost = total_visits * FULL_TICKET_PRICE
savings = full_price_cost - total_spent

# -----------------------------
# Dashboard Metrics
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("🎥 Total Movies Watched", total_visits)
col2.metric("📆 Avg Visits / Month", f"{avg_visits:.1f}")
col3.metric("💳 Total Spent", f"${total_spent:.2f}")
col4.metric("💰 Savings vs Full Price", f"${savings:.2f}")

# -----------------------------
# Visits Per Month Chart
# -----------------------------
st.subheader("📊 Movies Watched Per Month")

fig, ax = plt.subplots()
visits_per_month.plot(kind="bar", ax=ax)
ax.set_xlabel("Month")
ax.set_ylabel("Number of Movies")
ax.set_title("Monthly Regal Unlimited Usage")

st.pyplot(fig)

# -----------------------------
# Cost Comparison Chart
# -----------------------------
st.subheader("Cost Comparison")

cost_df = pd.DataFrame({
    "Cost Type": ["Regal Unlimited", "Full Price Tickets"],
    "Amount": [total_spent, full_price_cost]
})

fig2, ax2 = plt.subplots()
ax2.bar(cost_df["Cost Type"], cost_df["Amount"])
ax2.set_ylabel("Dollars ($)")
ax2.set_title("Unlimited vs Full Price")

st.pyplot(fig2)

# -----------------------------
# Webpage Footer
# -----------------------------
st.caption("- Data auto-syncs from Google Sheets every 60 seconds")
