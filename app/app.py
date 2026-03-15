import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import requests
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="AI Financial Research Agent",
   
    layout="wide"
)

# -------------------------
# API KEYS
# -------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY") or st.secrets.get("NEWS_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found")
    st.stop()

# -------------------------
# LLM SETUP
# -------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    groq_api_key=GROQ_API_KEY,
)

# -------------------------
# DATA FUNCTIONS
# -------------------------
@st.cache_data(ttl=600)
def get_stock_data(symbol):

    stock = yf.Ticker(symbol)
    data = stock.history(period="7d")

    if data.empty:
        return None

    return {
        "symbol": symbol,
        "current_price": round(data["Close"].iloc[-1], 2),
        "avg_price": round(data["Close"].mean(), 2),
        "volume": int(data["Volume"].iloc[-1])
    }


@st.cache_data(ttl=600)
def get_technical_indicators(symbol):

    stock = yf.Ticker(symbol)
    data = stock.history(period="1mo")

    if len(data) < 15:
        return None

    data["SMA_14"] = data["Close"].rolling(window=14).mean()

    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    return {
        "sma": round(data["SMA_14"].iloc[-1], 2),
        "rsi": round(data["RSI"].iloc[-1], 2)
    }


@st.cache_data(ttl=600)
def get_latest_news(symbol):

    if not NEWS_API_KEY:
        return "News API key missing"

    query = symbol.replace(".NS", "")

    url = f"https://newsapi.org/v2/everything?q={query}&pageSize=3&apiKey={NEWS_API_KEY}"

    try:
        res = requests.get(url).json()
        headlines = [a["title"] for a in res.get("articles", [])]

        if headlines:
            return "\n".join(headlines)
        else:
            return "No recent news found"

    except:
        return "News fetch error"


@st.cache_data(ttl=600)
def get_chart_data(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="30d")
    return data


# -------------------------
# AGENTS
# -------------------------
def stock_data_agent(stock_info):

    prompt = f"""
    Interpret this stock data:

    Price: ₹{stock_info['current_price']}
    Avg Price: ₹{stock_info['avg_price']}
    Volume: {stock_info['volume']}

    Provide a short insight.
    """

    return llm.invoke([HumanMessage(content=prompt)]).content


def technical_agent(symbol, tech):

    if not tech:
        return "Not enough data for indicators."

    prompt = f"""
    Analyze these indicators:

    SMA: {tech['sma']}
    RSI: {tech['rsi']}

    RSI>70 overbought
    RSI<30 oversold

    Provide a short technical insight.
    """

    return llm.invoke([HumanMessage(content=prompt)]).content


def news_agent(symbol, headlines):

    prompt = f"""
    Analyze the sentiment of these headlines for {symbol}:

    {headlines}

    Classify sentiment and briefly explain.
    """

    return llm.invoke([HumanMessage(content=prompt)]).content


def supervisor_agent(symbol, price, tech, news):

    prompt = f"""
    Combine these analyses for {symbol}

    Price:
    {price}

    Technical:
    {tech}

    News:
    {news}

    Produce a short executive investment summary.
    """

    return llm.invoke([HumanMessage(content=prompt)]).content


# -------------------------
# DEBATE AGENTS
# -------------------------
def bull_agent(symbol, summary):

    prompt = f"""
    Based on this analysis of {symbol}:

    {summary}

    Explain why the stock could be a good investment.
    """

    return llm.invoke([HumanMessage(content=prompt)]).content


def bear_agent(symbol, summary):

    prompt = f"""
    Based on this analysis of {symbol}:

    {summary}

    Explain the risks investors should consider.
    """

    return llm.invoke([HumanMessage(content=prompt)]).content


def judge_agent(symbol, bull, bear):

    prompt = f"""
    Bullish argument:
    {bull}

    Bearish argument:
    {bear}

    Provide a balanced investment verdict.
    """

    return llm.invoke([HumanMessage(content=prompt)]).content


# -------------------------
# UI
# -------------------------
st.title(" Multi-Agent Financial Research AI")
st.markdown("""
### AI Financial Intelligence Dashboard

Analyze stocks using **AI agents** that combine:
- Market data
- Technical indicators
- News sentiment
- Multi-agent reasoning

Enter a stock ticker below to begin analysis.
""")

col1, col2 = st.columns(2)

with col1:
    symbol_input1 = st.text_input("Stock 1 (example RELIANCE)")

with col2:
    symbol_input2 = st.text_input("Stock 2 (optional comparison)")


symbol1 = symbol_input1.strip().upper()
symbol2 = symbol_input2.strip().upper()

if symbol1 and not symbol1.endswith(".NS"):
    symbol1 += ".NS"

if symbol2 and not symbol2.endswith(".NS"):
    symbol2 += ".NS"


# -------------------------
# ANALYSIS
# -------------------------
if st.button("Analyze") and symbol1:

    with st.spinner("Running AI financial agents..."):

        stock1 = get_stock_data(symbol1)
        tech1 = get_technical_indicators(symbol1)
        news1 = get_latest_news(symbol1)

        price_insight = stock_data_agent(stock1)
        tech_insight = technical_agent(symbol1, tech1)
        news_insight = news_agent(symbol1, news1)

        final_summary = supervisor_agent(
            symbol1,
            price_insight,
            tech_insight,
            news_insight
        )

        bull_view = bull_agent(symbol1, final_summary)
        bear_view = bear_agent(symbol1, final_summary)
        judge_view = judge_agent(symbol1, bull_view, bear_view)

        st.success("Analysis Complete")

        # -------------------------
        # DASHBOARD TABS
        # -------------------------
        tab1, tab2, tab3, tab4 = st.tabs([
               "Market Dashboard",
               "AI Research Summary",
               "Investment Debate",
               "Stock Comparison"])
    

        # -------------------------
        # TAB 1
        # -------------------------
        with tab1:
            st.markdown("### Key Market Metrics")

            colA, colB, colC = st.columns(3)

            with colA:
                st.divider()
                st.subheader("Technical Indicators")
                st.subheader("Price")
                st.metric(
                label="Current Price",
                value=f"₹{stock1['current_price']}",
                delta=f"{round(stock1['current_price'] - stock1['avg_price'],2)} vs avg")

                st.metric("Volume", stock1["volume"])
                st.info(price_insight)

            with colB:
                st.divider()
                st.subheader("Technical Indicators")
                if tech1:
                    st.metric("SMA", tech1["sma"])
                    st.metric("RSI", tech1["rsi"])
                st.info(tech_insight)

            with colC:
                st.divider()
                st.subheader("News Sentiment")
                st.caption(news1)
                st.info(news_insight)

            data = get_chart_data(symbol1)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data["Close"],
                mode="lines",
                name=symbol1
            ))

            st.plotly_chart(fig, use_container_width=True)

        # -------------------------
        # TAB 2
        # -------------------------
        with tab2:
            st.divider()

            st.subheader("AI Executive Summary")

            st.success(final_summary)

        # -------------------------
        # TAB 3
        # -------------------------
        with tab3:
            st.divider()

            st.subheader("AI Investment Debate")

            col1, col2 = st.columns(2)

            with col1:
                st.divider()
                st.markdown("### Bull Perspective")
                st.write(bull_view)

            with col2:
                st.divider()
                st.markdown("### Bear Perspective")
                st.write(bear_view)

            st.markdown("---")

            st.markdown("### Final AI Verdict")

            st.success(judge_view)

        # -------------------------
        # TAB 4
        # -------------------------
        with tab4:
            st.divider()

            if symbol2:

                stock2 = get_stock_data(symbol2)
                tech2 = get_technical_indicators(symbol2)

                colX, colY = st.columns(2)

                with colX:
                    st.divider()
                    st.markdown(f"### {symbol1}")
                    st.metric("Price", f"₹{stock1['current_price']}")
                    if tech1:
                        st.metric("RSI", tech1["rsi"])

                with colY:
                    st.divider()
                    st.markdown(f"### {symbol2}")
                    st.metric("Price", f"₹{stock2['current_price']}")
                    if tech2:
                        st.metric("RSI", tech2["rsi"])

                data1 = get_chart_data(symbol1)
                data2 = get_chart_data(symbol2)

                fig2 = go.Figure()

                fig2.add_trace(go.Scatter(
                    x=data1.index,
                    y=data1["Close"],
                    mode="lines",
                    name=symbol1
                ))

                fig2.add_trace(go.Scatter(
                    x=data2.index,
                    y=data2["Close"],
                    mode="lines",
                    name=symbol2
                ))

                fig2.update_layout(
                    title="Stock Price Comparison",
                    xaxis_title="Date",
                    yaxis_title="Price"
                )

                st.plotly_chart(fig2, use_container_width=True)

            else:
                st.info("Enter a second stock to enable comparison.")

st.markdown("---")
st.caption(
    "AI Financial Research Assistant • Built with Streamlit, LangChain, Groq LLM, and Financial Data APIs"
)
