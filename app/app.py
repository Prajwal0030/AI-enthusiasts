import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os

# -------------------------
# API KEY
# -------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY not found in Streamlit Secrets.")
    st.stop()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    groq_api_key=GROQ_API_KEY,
)

# -------------------------
# STOCK FUNCTION
# -------------------------
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="7d")

    if data.empty:
        return None

    current_price = data["Close"].iloc[-1]
    avg_price = data["Close"].mean()
    volume = data["Volume"].iloc[-1]

    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "avg_price": round(avg_price, 2),
        "volume": int(volume)
    }

# -------------------------
# UI
# -------------------------
st.title("📈 Multi-Agent Financial Research AI")

symbol_input = st.text_input("Enter Indian Stock Symbol (e.g., RELIANCE, TCS, INFY)")

symbol = symbol_input.strip().upper()

if symbol and not symbol.endswith(".NS"):
    symbol = symbol + ".NS"

if st.button("Analyze") and symbol:

    stock_info = get_stock_data(symbol)

    if not stock_info:
        st.error("No data found for this symbol.")
    else:
        # Display raw data
        st.write(f"### Current Price: ₹{stock_info['current_price']}")
        st.write(f"7-Day Average: ₹{stock_info['avg_price']}")
        st.write(f"Latest Volume: {stock_info['volume']}")

        # Ask LLM to explain
        prompt = f"""
        Analyze this Indian stock briefly:
        Symbol: {stock_info['symbol']}
        Current Price: {stock_info['current_price']}
        7-Day Average: {stock_info['avg_price']}
        Volume: {stock_info['volume']}
        Give a short professional summary.
        """

        response = llm.invoke([HumanMessage(content=prompt)])
        st.write("### AI Insight")
        st.write(response.content)

        # Chart
        stock = yf.Ticker(symbol)
        data = stock.history(period="30d")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode="lines"))
        fig.update_layout(title=f"{symbol} - Last 30 Days")

        st.plotly_chart(fig)
