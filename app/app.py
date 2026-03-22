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

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

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
        return "\n".join(headlines[:3])
    except:
        return "Error fetching news"

@st.cache_data(ttl=600)
def get_chart(symbol):
    return yf.Ticker(symbol).history(period="30d")



# -------------------------
# AGENTS (DETAILED OUTPUT)
# -------------------------
def llm_call(prompt):
    return llm.invoke([HumanMessage(content=prompt)]).content

def summary_agent(symbol, stock, tech, news):
    return llm_call(f"""
    Perform a detailed financial analysis for {symbol}.

    Include:
    1. Market Position
    2. Technical Trend Analysis
    3. Volume Interpretation
    4. News Impact
    5. Final Recommendation (Buy/Hold/Sell)

    Data:
    Price: {stock}
    Indicators: {tech}
    News: {news}
    """)

def bull_agent(symbol, summary):
    return llm_call(f"""
    Provide a strong bullish case for {symbol}.
    Include growth potential, strengths, and upside.
    Keep it structured.
    """)

def bear_agent(symbol, summary):
    return llm_call(f"""
    Provide a bearish analysis for {symbol}.
    Include risks, weaknesses, and downside.
    Keep it structured.
    """)

def judge_agent(bull, bear):
    return llm_call(f"""
    Compare the bullish and bearish views.

    Give:
    - Final balanced conclusion
    - Clear investment stance (Buy/Hold/Sell)
    """)

def portfolio_agent(data):
    return llm_call(f"""
    Analyze this portfolio:

    {data}

    Include:
    - Diversification
    - Risk level
    - Strengths
    - Weaknesses
    - Suggestions
    """)

def macro_agent():
    return llm_call("""
    Explain current market conditions:

    - Inflation
    - Interest rates
    - Market sentiment
    - Investment outlook
    """)

def indicator_agent(tech):
    return llm_call(f"""
    Explain these indicators:

    SMA: {tech['sma']}
    EMA: {tech['ema']}
    RSI: {tech['rsi']}

    Include what they imply for trading decisions.
    """)

def recommendation_agent(symbol, summary, tech):
    return llm_call(f"""
    Based on this analysis of {symbol}:

    {summary}

    Indicators:
    RSI: {tech['rsi']}
    SMA: {tech['sma']}
    EMA: {tech['ema']}

    Give:
    1. Final Recommendation (BUY / HOLD / SELL)
    2. Confidence Level (Low / Medium / High)
    3. One-line justification

    Keep it short and clear.
    """)

def calculate_risk_score(tech):
    rsi = tech['rsi']

    if rsi > 70:
        return "High Risk (Overbought)"
    elif rsi < 30:
        return "Low Risk (Oversold Opportunity)"
    else:
        return "Moderate Risk"
        

# -------------------------
# UI
# -------------------------
st.title("📈 AI Financial Research Platform")

col1, col2 = st.columns(2)

symbol1 = col1.text_input("Stock 1")
symbol2 = col2.text_input("Stock 2 (optional)")
portfolio_input = st.text_input("Portfolio (comma separated)")

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

    summary = summary_agent(symbol1, stock, tech, news)
    recommendation = recommendation_agent(symbol1, summary, tech)
    risk = calculate_risk_score(tech)
    bull = bull_agent(symbol1, summary)
    bear = bear_agent(symbol1, summary)
    verdict = judge_agent(bull, bear)

    tabs = st.tabs([
        "Dashboard",
        "AI Summary",
        "Debate",
        "Comparison",
        "Portfolio AI",
        "Advanced Indicators",
        "Economic Context"
    ])

    # Dashboard
    with tabs[0]:
        st.metric("Price", stock["price"])
        st.metric("Volume", stock["volume"])

        chart = get_chart(symbol1)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chart.index, y=chart["Close"]))
        st.plotly_chart(fig)

    # Summary
    with tabs[1]:
        st.write(summary)

    # Debate
    with tabs[2]:
        st.subheader("Bullish View")
        st.write(bull)

        st.subheader("Bearish View")
        st.write(bear)

        st.subheader("Final Decision")
        st.success(verdict)

        

    # Comparison
    with tabs[3]:
        if symbol2:
            d1 = get_chart(symbol1)
            d2 = get_chart(symbol2)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=d1.index, y=d1["Close"], name=symbol1))
            fig.add_trace(go.Scatter(x=d2.index, y=d2["Close"], name=symbol2))
            st.plotly_chart(fig)

    # Portfolio
    with tabs[4]:
        if portfolio_input:
            symbols = [s.strip().upper()+".NS" for s in portfolio_input.split(",")]
            pdata = [get_stock_data(s) for s in symbols if get_stock_data(s)]
            st.write(portfolio_agent(pdata))

    # Indicators
    with tabs[5]:
        st.metric("SMA", tech['sma'])
        st.metric("EMA", tech['ema'])
        st.metric("RSI", tech['rsi'])

        st.write(indicator_agent(tech))

    # Macro
    with tabs[6]:
        st.write(macro_agent())

    st.subheader("📌 Investment Signal")

    col1, col2 = st.columns(2)

    with col1:
         st.info(recommendation)

    with col2:
      st.write("**Risk Level:**")
      st.write(risk)

      st.markdown("---")
