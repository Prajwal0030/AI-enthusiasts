import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="AI Financial Research", layout="wide")

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or st.secrets.get("NEWS_API_KEY")

if not GROQ_API_KEY:
    st.error("Missing GROQ API Key")
    st.stop()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

# -------------------------
# DATA FUNCTIONS
# -------------------------
@st.cache_data(ttl=600)
def get_stock_data(symbol):
    data = yf.Ticker(symbol).history(period="7d")
    if data.empty:
        return None

    return {
        "price": round(data["Close"].iloc[-1], 2),
        "avg": round(data["Close"].mean(), 2),
        "volume": int(data["Volume"].iloc[-1])
    }

@st.cache_data(ttl=600)
def get_technical_indicators(symbol):
    data = yf.Ticker(symbol).history(period="1mo")

    if len(data) < 20:
        return None

    data["SMA"] = data["Close"].rolling(14).mean()
    data["EMA"] = data["Close"].ewm(span=14).mean()

    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    data["RSI"] = 100 - (100 / (1 + rs))

    return {
        "sma": round(data["SMA"].iloc[-1], 2),
        "ema": round(data["EMA"].iloc[-1], 2),
        "rsi": round(data["RSI"].iloc[-1], 2)
    }

@st.cache_data(ttl=600)
def get_news(symbol):
    if not NEWS_API_KEY:
        return "News unavailable"

    query = symbol.replace(".NS", "")
    url = f"https://newsapi.org/v2/everything?q={query}&pageSize=3&apiKey={NEWS_API_KEY}"

    try:
        res = requests.get(url).json()
        headlines = [a["title"] for a in res.get("articles", [])]
        return "\n".join(headlines[:3]) if headlines else "No recent news"
    except:
        return "Error fetching news"

@st.cache_data(ttl=600)
def get_chart(symbol):
    return yf.Ticker(symbol).history(period="30d")

# -------------------------
# AGENTS (SHORT + CLEAN)
# -------------------------
def llm_call(prompt):
    return llm.invoke([HumanMessage(content=prompt)]).content

def summary_agent(symbol, stock, tech, news):
    return llm_call(f"""
    Give a concise financial summary (max 3 lines):

    Price: {stock}
    Indicators: {tech}
    News: {news}
    """)

def bull_agent(symbol, summary):
    return llm_call(f"Give 2-line bullish view for {symbol}: {summary}")

def bear_agent(symbol, summary):
    return llm_call(f"Give 2-line risks for {symbol}: {summary}")

def judge_agent(bull, bear):
    return llm_call(f"Give final decision in 2 lines:\nBull: {bull}\nBear: {bear}")

def portfolio_agent(data):
    return llm_call(f"Analyze portfolio in 3 short lines: {data}")

def macro_agent():
    return llm_call("Give current market outlook in 3 short lines")

def indicator_agent(tech):
    return llm_call(f"""
    Explain briefly what these indicators suggest (max 3 lines):

    SMA: {tech['sma']}
    EMA: {tech['ema']}
    RSI: {tech['rsi']}
    """)

# -------------------------
# UI
# -------------------------
st.title("📈 AI Financial Research Platform")

col1, col2 = st.columns(2)

symbol1 = col1.text_input("Stock 1 (e.g., RELIANCE)")
symbol2 = col2.text_input("Stock 2 (optional)")

portfolio_input = st.text_input("Portfolio (comma separated stocks)")

# -------------------------
# MAIN
# -------------------------
if st.button("Analyze") and symbol1:

    symbol1 = symbol1.strip().upper()
    symbol2 = symbol2.strip().upper()

    if not symbol1.endswith(".NS"):
        symbol1 += ".NS"

    if symbol2 and not symbol2.endswith(".NS"):
        symbol2 += ".NS"

    stock = get_stock_data(symbol1)
    tech = get_technical_indicators(symbol1)
    news = get_news(symbol1)

    if not stock:
        st.error("Invalid stock symbol")
        st.stop()

    summary = summary_agent(symbol1, stock, tech, news)
    bull = bull_agent(symbol1, summary)
    bear = bear_agent(symbol1, summary)
    verdict = judge_agent(bull, bear)

    # -------------------------
    # TABS
    # -------------------------
    tabs = st.tabs([
        "Dashboard",
        "AI Summary",
        "Debate",
        "Comparison",
        "Portfolio AI",
        "Advanced Indicators",
        "Economic Context"
    ])

    # -------------------------
    # DASHBOARD
    # -------------------------
    with tabs[0]:
        colA, colB = st.columns(2)

        colA.metric("Price", stock["price"])
        colB.metric("Volume", stock["volume"])

        chart = get_chart(symbol1)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chart.index, y=chart["Close"], name="Price"))
        st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # SUMMARY
    # -------------------------
    with tabs[1]:
        st.write(summary)

    # -------------------------
    # DEBATE
    # -------------------------
    with tabs[2]:
        st.write("Bull:", bull)
        st.write("Bear:", bear)
        st.success("Final Verdict: " + verdict)

    # -------------------------
    # COMPARISON
    # -------------------------
    with tabs[3]:
        if symbol2:
            data1 = get_chart(symbol1)
            data2 = get_chart(symbol2)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data1.index, y=data1["Close"], name=symbol1))
            fig.add_trace(go.Scatter(x=data2.index, y=data2["Close"], name=symbol2))

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Enter second stock for comparison")

    # -------------------------
    # PORTFOLIO AI
    # -------------------------
    with tabs[4]:
        if portfolio_input:
            symbols = [s.strip().upper() + ".NS" for s in portfolio_input.split(",")]
            pdata = []

            for s in symbols:
                d = get_stock_data(s)
                if d:
                    pdata.append(d)

            st.write(portfolio_agent(pdata))
        else:
            st.info("Enter portfolio stocks")

    # -------------------------
    # ADVANCED INDICATORS
    # -------------------------
    with tabs[5]:
        st.subheader("Technical Indicators Overview")

        col1, col2, col3 = st.columns(3)

        col1.metric("SMA (14)", tech['sma'])
        col2.metric("EMA (14)", tech['ema'])
        col3.metric("RSI (14)", tech['rsi'])

        st.markdown("---")

        st.write("Interpretation:")
        st.write(indicator_agent(tech))

        if tech['rsi'] > 70:
            st.warning("Stock may be overbought")
        elif tech['rsi'] < 30:
            st.success("Stock may be oversold")

    # -------------------------
    # ECONOMIC CONTEXT
    # -------------------------
    with tabs[6]:
        st.write(macro_agent())
