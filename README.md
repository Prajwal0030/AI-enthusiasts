# AI Financial Research Assistant

## Project Vision

This project aims to build a **multi-agent financial intelligence platform** that assists users in analyzing stocks using real-time market data, technical indicators, and AI-driven insights.

The system follows a modular **agent-based architecture**, where multiple specialized AI agents collaborate to generate comprehensive financial analysis and investment recommendations.

---

# Current Features (Week 4)

### Multi-Agent Financial Analysis

The system includes multiple AI agents:

- Stock Analysis Agent – interprets price and volume data  
- Technical Analysis Agent – analyzes SMA, EMA, RSI  
- News Sentiment Agent – evaluates recent market news  
- Supervisor Agent – combines all insights into a structured summary  

---

### AI Investment Decision System

- Generates **Buy / Hold / Sell recommendations**
- Provides **confidence level**
- Includes **reasoning based on technical + sentiment analysis**

---

### Multi-Agent Debate System

- **Bull Agent** – highlights growth opportunities  
- **Bear Agent** – identifies risks  
- **Judge Agent** – gives final balanced decision  

---

### Portfolio AI Analyzer

Users can input multiple stocks to get:

- Diversification analysis  
- Risk evaluation  
- Strengths and weaknesses  
- Investment suggestions  

---

### Advanced Technical Indicators

Includes:

- SMA (Trend analysis)  
- EMA (Short-term trend sensitivity)  
- RSI (Momentum indicator)  

Also provides **AI-based interpretation** for better decision-making.

---

### Stock Comparison System

- Compare two stocks simultaneously  
- Visualize performance with interactive charts  

---

### Economic Context Agent

Provides macro-level insights:

- Inflation trends  
- Interest rates  
- Market sentiment  
- Investment outlook  

---

### UI & Performance

- Tab-based dashboard for structured insights  
- Interactive Plotly charts  
- Streamlit caching for performance optimization  

---

# Architecture (Simplified)

User Input  
↓  
Stock Data (Yahoo Finance API)  
↓  
Technical Indicators + News Data  
↓  
Multi-Agent Analysis  
↓  
Supervisor + Debate Agents  
↓  
Recommendation System  
↓  
Streamlit Dashboard  

---

# Tech Stack

- Python  
- Streamlit  
- Plotly  
- yfinance  
- News API  
- LangChain  
- Groq LLM  
- Pandas  

---

# Week 1 Implementation

- Stock data retrieval  
- Basic LLM insights  
- Streamlit dashboard  

---

# Week 2 Implementation

- Multi-agent architecture  
- Technical + sentiment analysis  
- Supervisor agent  

---

# Week 3 Implementation

- Multi-agent debate system  
- Stock comparison  
- UI upgrade  
- Performance optimization  

---

# Week 4 Implementation

- Investment recommendation system (Buy/Hold/Sell)  
- Portfolio AI analyzer  
- Advanced indicators (SMA, EMA, RSI)  
- Economic context agent  
- Improved structured AI outputs
  

---

# Week 5 Implementation

In Week 5, the project was transformed into a domain-specific Indian stock analysis platform with enhanced financial intelligence features.

Key improvements include:

### Indian Market Integration
- Integrated NSE stock data using Yahoo Finance (.NS symbols)
- Enabled real-time Indian stock analysis

### Watchlist System
- Users can save and manage stocks for future tracking
- Persistent session-based watchlist implementation

### Fundamental Analysis
- Implemented core financial metrics:
  - P/E Ratio
  - Return on Equity (ROE)
  - Debt-to-Equity Ratio
  - Revenue/Earnings Growth

### Sector Comparison
- Compared major Indian IT stocks (TCS, Infosys, Wipro)
- Displayed key financial metrics for peer analysis

### Technical Indicators Enhancement
- SMA, EMA, RSI displayed with real-time values
- Added interpretation (overbought / oversold / neutral)

### Market Context Module
- Displays Indian market open/close status
- Provides macro-level insights for better decision-making
  

---

# Week 6 Implementation

In Week 6, the project was enhanced with advanced financial intelligence features to make the system more practical and decision-driven.

### Portfolio Intelligence

- Introduced portfolio scoring system (0–100)
- Evaluates diversification and risk using technical indicators

### Risk Analysis Engine

- Classifies stocks into Low, Moderate, and High risk
- Helps users understand investment safety

### Real-Time Alerts

- Added Buy/Sell signals based on RSI levels
- Provides actionable insights for trading decisions

### Multi-Asset Support

- Extended analysis beyond stocks:
  - Gold (Commodities)
  - USD/INR (Currency)
  - Bitcoin (Crypto)

These upgrades transformed the system into a more production-ready financial assistant with deeper analytical capabilities.

---

Week 7 Implementation

In Week 7, the project was refined with a strong focus on UI enhancement, usability, and production-level improvements.

Key improvements include:

UI & Visualization Enhancements

- Improved dashboard charts with SMA and EMA overlays
- Cleaner layout with better spacing and structured sections
- Enhanced user experience for smoother navigation

Sentiment Analysis Integration

- Implemented news-based sentiment detection
- Displays bullish or bearish outlook based on recent headlines

Export Functionality

- Added report download feature
- Users can export AI-generated analysis along with news insights

Portfolio Cards

- Introduced card-based portfolio visualization
- Each asset shows RSI and corresponding risk level
- Enables quick comparison of multiple stocks

Validation & Error Handling

- Added input validation for stock symbols
- Improved error messages for invalid or missing data
- Ensured stable behavior across all tabs

System Refinement

- Fixed tab-level inconsistencies
- Improved comparison and watchlist interaction
- Optimized overall performance

This week focused on transforming the platform into a more polished, user-friendly, and production-ready financial intelligence system.

---

---

# Deployment

Deployed on **Streamlit Cloud**

Users can analyze stocks like:

RELIANCE  
TCS  
INFY  

---

# Goal

To build a **real-world financial intelligence system powered by AI agents** that helps users make smarter investment decisions.
