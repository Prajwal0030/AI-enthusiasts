import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
import os

# -------------------------
# LOAD API KEY FROM SECRETS
# -------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# -------------------------
# STOCK TOOL
# -------------------------
@tool
def get_stock_data(symbol: str) -> str:
    stock = yf.Ticker(symbol)
    data = stock.history(period="7d")

    if data.empty:
        return "No data found."

    current_price = data["Close"].iloc[-1]
    avg_price = data["Close"].mean()
    volume = data["Volume"].iloc[-1]

    return (
        f"Stock: {symbol}\n"
        f"Current Price: ₹{round(current_price,2)}\n"
        f"7-Day Average Price: ₹{round(avg_price,2)}\n"
        f"Latest Volume: {int(volume)}"
    )

# -------------------------
# LLM SETUP
# -------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a financial research assistant for Indian markets. Call tools only once."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ]
)

tools = [get_stock_data]

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# -------------------------
# STREAMLIT UI
# -------------------------
st.title("📈 Multi-Agent Financial Research AI")

symbol = st.text_input("Enter Indian Stock Symbol (e.g., RELIANCE.NS)")

if st.button("Analyze") and symbol:
    response = agent_executor.invoke({"input": f"What is the price of {symbol}?"})
    st.write(response["output"])

    stock = yf.Ticker(symbol)
    data = stock.history(period="30d")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode="lines"))
    fig.update_layout(title=f"{symbol} - Last 30 Days")

    st.plotly_chart(fig)
