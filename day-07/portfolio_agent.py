"""
Day 7: Portfolio Tracker Agent for FinTech Research
Adds portfolio management to multi-agent system
"""

import requests
import os
import json
import re
from typing import TypedDict, Annotated, List, Dict
from dotenv import load_dotenv
import operator
from datetime import datetime

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    print("❌ Error: MISTRAL_API_KEY not found")
    exit(1)

print("✅ API key loaded")

# ============================================
# STEP 1: Define State (Updated for Portfolio)
# ============================================

class PortfolioHolding:
    def __init__(self, symbol: str, shares: float, buy_price: float):
        self.symbol = symbol.upper()
        self.shares = shares
        self.buy_price = buy_price
        self.current_price = 0
        self.current_value = 0
        self.pnl = 0
        self.pnl_percent = 0

class FinTechAgentState(TypedDict):
    messages: Annotated[list, operator.add]
    user_input: str
    next_agent: str
    stock_data: dict
    sentiment_data: dict
    portfolio_data: dict
    return_calculation: dict
    final_answer: str

# ============================================
# STEP 2: Stock Price Tool (Reused)
# ============================================

def get_stock_price(symbol: str) -> dict:
    """Fetch stock price using yfinance"""
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        info = stock.info
        
        current_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        previous_close = info.get('regularMarketPreviousClose', info.get('previousClose', 0))
        
        daily_change = current_price - previous_close if previous_close else 0
        daily_change_percent = (daily_change / previous_close) * 100 if previous_close else 0
        
        return {
            "symbol": symbol.upper(),
            "current_price": round(current_price, 2),
            "previous_close": round(previous_close, 2),
            "daily_change": round(daily_change, 2),
            "daily_change_percent": round(daily_change_percent, 2),
            "name": info.get('longName', symbol.upper()),
            "market_cap": info.get('marketCap', 'N/A')
        }
    except Exception as e:
        return {"symbol": symbol.upper(), "error": str(e), "current_price": 0}

# ============================================
# STEP 3: Portfolio Parser
# ============================================

def parse_portfolio_from_text(text: str) -> List[Dict]:
    """
    Parse natural language portfolio description.
    Examples:
    - "AAPL 10 shares at $150"
    - "I own TSLA 5 shares bought at 250"
    - "MSFT: 8 shares @ 300"
    """
    holdings = []
    
    # Pattern: SYMBOL shares/share at/ @ price
    patterns = [
        r'([A-Z]{3,5})\s+(\d+(?:\.\d+)?)\s+shares?\s+(?:at|@)\s+\$?(\d+(?:\.\d+)?)',
        r'([A-Z]{3,5})\s+(\d+(?:\.\d+)?)\s+shares?\s+at\s+\$?(\d+(?:\.\d+)?)',
        r'([A-Z]{3,5}):\s*(\d+(?:\.\d+)?)\s+shares?\s+@\s+\$?(\d+(?:\.\d+)?)',
        r'([A-Z]{3,5})\s+(\d+(?:\.\d+)?)\s+shares?\s+bought\s+at\s+\$?(\d+(?:\.\d+)?)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            symbol = match[0].upper()
            shares = float(match[1])
            buy_price = float(match[2])
            holdings.append({
                "symbol": symbol,
                "shares": shares,
                "buy_price": buy_price
            })
    
    return holdings

# ============================================
# STEP 4: Portfolio Tracker Agent
# ============================================

def portfolio_tracker_node(state: FinTechAgentState) -> dict:
    """Agent that tracks portfolio performance"""
    
    question = state.get("user_input", "")
    
    # Parse portfolio from question
    holdings = parse_portfolio_from_text(question)
    
    if not holdings:
        return {"portfolio_data": {"error": "No portfolio found. Use format: 'AAPL 10 shares at $150'"}}
    
    print(f"📊 Portfolio Agent: Tracking {len(holdings)} holdings")
    
    # Fetch current prices for each holding
    portfolio_summary = {
        "holdings": [],
        "total_cost": 0,
        "total_value": 0,
        "total_pnl": 0,
        "total_pnl_percent": 0,
        "best_performer": None,
        "worst_performer": None
    }
    
    for holding in holdings:
        symbol = holding["symbol"]
        shares = holding["shares"]
        buy_price = holding["buy_price"]
        
        stock_data = get_stock_price(symbol)
        
        if stock_data.get("error"):
            print(f"   ⚠️ Could not fetch {symbol}")
            continue
        
        current_price = stock_data.get("current_price", 0)
        current_value = shares * current_price
        cost = shares * buy_price
        pnl = current_value - cost
        pnl_percent = (pnl / cost) * 100 if cost > 0 else 0
        
        holding_summary = {
            "symbol": symbol,
            "name": stock_data.get("name", symbol),
            "shares": shares,
            "buy_price": buy_price,
            "current_price": current_price,
            "cost": round(cost, 2),
            "current_value": round(current_value, 2),
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "daily_change": stock_data.get("daily_change", 0),
            "daily_change_percent": stock_data.get("daily_change_percent", 0)
        }
        
        portfolio_summary["holdings"].append(holding_summary)
        portfolio_summary["total_cost"] += cost
        portfolio_summary["total_value"] += current_value
        portfolio_summary["total_pnl"] += pnl
    
    if portfolio_summary["holdings"]:
        portfolio_summary["total_pnl_percent"] = round(
            (portfolio_summary["total_pnl"] / portfolio_summary["total_cost"]) * 100, 2
        ) if portfolio_summary["total_cost"] > 0 else 0
        
        # Find best/worst performers
        sorted_by_pnl = sorted(portfolio_summary["holdings"], key=lambda x: x["pnl_percent"], reverse=True)
        if sorted_by_pnl:
            portfolio_summary["best_performer"] = sorted_by_pnl[0]
            portfolio_summary["worst_performer"] = sorted_by_pnl[-1]
    
    return {"portfolio_data": portfolio_summary}

# ============================================
# STEP 5: Supervisor Agent (Updated)
# ============================================

def supervisor_node(state: FinTechAgentState) -> dict:
    """Supervisor routes to appropriate agent"""
    
    question = state.get("user_input", "").lower()
    
    # Portfolio keywords
    portfolio_keywords = ["portfolio", "holdings", "track", "my stocks", 
                          "shares at", "bought at", "portfolio performance"]
    
    # Sentiment keywords
    sentiment_keywords = ["sentiment", "news", "feeling", "market mood"]
    
    # Price keywords
    price_keywords = ["price", "stock", "trading", "worth"]
    
    if any(k in question for k in portfolio_keywords) or "shares" in question:
        print("👔 Supervisor: Routing to Portfolio Tracker Agent")
        return {"next_agent": "portfolio_agent"}
    elif any(k in question for k in sentiment_keywords):
        print("👔 Supervisor: Routing to Sentiment Analysis Agent")
        return {"next_agent": "sentiment_agent"}
    elif any(k in question for k in price_keywords):
        print("👔 Supervisor: Routing to Stock Price Agent")
        return {"next_agent": "stock_price_agent"}
    else:
        print("👔 Supervisor: Routing to Final Answer")
        return {"next_agent": "final_answer"}

# ============================================
# STEP 6: Sentiment Agent (From Day 6)
# ============================================

def get_stock_news(symbol: str) -> list:
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        news = stock.news
        if not news:
            return []
        articles = []
        for item in news[:5]:
            articles.append({
                "title": item.get('title', 'No title'),
                "publisher": item.get('publisher', 'Unknown'),
                "link": item.get('link', '#')
            })
        return articles
    except Exception:
        return []

def analyze_sentiment(symbol: str, news_articles: list) -> dict:
    if not news_articles:
        return {
            "symbol": symbol,
            "overall_sentiment": "neutral",
            "confidence": 0,
            "summary": "No news available",
            "key_drivers": []
        }
    
    news_text = "\n".join([f"- {a['title']}" for a in news_articles[:5]])
    
    prompt = f"""
Analyze sentiment for {symbol} based on these news headlines:

{news_text}

Return JSON: {{"overall_sentiment": "positive/negative/neutral", "confidence": 0-100, "summary": "one sentence"}}
"""
    
    try:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
            json={"model": "mistral-small-latest", "messages": [{"role": "user", "content": prompt}], "max_tokens": 200}
        )
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            import json as json_lib
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json_lib.loads(json_match.group())
                return {
                    "symbol": symbol,
                    "overall_sentiment": data.get("overall_sentiment", "neutral"),
                    "confidence": data.get("confidence", 0),
                    "summary": data.get("summary", ""),
                    "articles_analyzed": len(news_articles)
                }
    except Exception:
        pass
    
    return {"symbol": symbol, "overall_sentiment": "neutral", "confidence": 0, "summary": "Analysis unavailable"}

def sentiment_agent_node(state: FinTechAgentState) -> dict:
    question = state.get("user_input", "")
    
    stock_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA"]
    stock_names = {"apple": "AAPL", "google": "GOOGL", "microsoft": "MSFT", "tesla": "TSLA", "amazon": "AMZN"}
    
    found_symbol = None
    for name, symbol in stock_names.items():
        if name in question.lower():
            found_symbol = symbol
            break
    if not found_symbol:
        for symbol in stock_symbols:
            if symbol.lower() in question.lower():
                found_symbol = symbol
                break
    
    if found_symbol:
        print(f"📰 Sentiment Agent: Analyzing {found_symbol}...")
        news = get_stock_news(found_symbol)
        sentiment = analyze_sentiment(found_symbol, news)
        return {"sentiment_data": sentiment}
    
    return {"sentiment_data": {"error": "Could not identify stock"}}

# ============================================
# STEP 7: Stock Price Agent
# ============================================

def stock_price_agent_node(state: FinTechAgentState) -> dict:
    question = state.get("user_input", "")
    
    stock_names = {"apple": "AAPL", "google": "GOOGL", "microsoft": "MSFT", "tesla": "TSLA", "amazon": "AMZN"}
    
    found_symbol = None
    for name, symbol in stock_names.items():
        if name in question.lower():
            found_symbol = symbol
            break
    if not found_symbol:
        for symbol in ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]:
            if symbol.lower() in question.lower():
                found_symbol = symbol
                break
    
    if found_symbol:
        print(f"💹 Stock Price Agent: Fetching {found_symbol}...")
        stock_data = get_stock_price(found_symbol)
        
        numbers = re.findall(r'\d+', question)
        return_calc = {}
        if numbers and ("bought" in question.lower() or "purchase" in question.lower()):
            buy_price = float(numbers[0])
            current_price = stock_data.get("current_price", 0)
            if current_price > 0:
                absolute_return = current_price - buy_price
                percentage_return = (absolute_return / buy_price) * 100
                return_calc = {
                    "buy_price": buy_price,
                    "absolute_return": round(absolute_return, 2),
                    "percentage_return": round(percentage_return, 2),
                    "is_profit": percentage_return > 0
                }
        return {"stock_data": stock_data, "return_calculation": return_calc}
    
    return {"stock_data": {"error": "Could not identify stock"}}

# ============================================
# STEP 8: Final Answer Node (Updated for Portfolio)
# ============================================

def final_answer_node(state: FinTechAgentState) -> dict:
    context_parts = []
    
    # Add portfolio data if available
    portfolio = state.get("portfolio_data", {})
    if portfolio and not portfolio.get("error") and portfolio.get("holdings"):
        context_parts.append(f"""
PORTFOLIO SUMMARY:
- Total Investment: ${portfolio.get('total_cost', 0):.2f}
- Current Value: ${portfolio.get('total_value', 0):.2f}
- Total P&L: ${portfolio.get('total_pnl', 0):.2f} ({portfolio.get('total_pnl_percent', 0)}%)
""")
        
        holdings_table = "Holdings:\n"
        for h in portfolio.get("holdings", []):
            profit_symbol = "✅" if h["pnl"] > 0 else "⚠️" if h["pnl"] < 0 else "📊"
            holdings_table += f"  {profit_symbol} {h['symbol']}: {h['shares']} shares | Cost: ${h['cost']} | Current: ${h['current_value']} | P&L: ${h['pnl']} ({h['pnl_percent']}%)\n"
        context_parts.append(holdings_table)
        
        if portfolio.get("best_performer"):
            bp = portfolio["best_performer"]
            context_parts.append(f"🏆 Best Performer: {bp['symbol']} (+{bp['pnl_percent']}%)")
        if portfolio.get("worst_performer"):
            wp = portfolio["worst_performer"]
            context_parts.append(f"📉 Worst Performer: {wp['symbol']} ({wp['pnl_percent']}%)")
    
    # Add sentiment data
    sentiment = state.get("sentiment_data", {})
    if sentiment and not sentiment.get("error") and sentiment.get("overall_sentiment"):
        context_parts.append(f"\nSentiment for {sentiment.get('symbol')}: {sentiment.get('overall_sentiment')} (confidence: {sentiment.get('confidence', 0)}%) - {sentiment.get('summary', '')}")
    
    # Add stock data
    stock = state.get("stock_data", {})
    if stock and not stock.get("error"):
        context_parts.append(f"\n{stock.get('symbol')}: ${stock.get('current_price')} (daily: {stock.get('daily_change_percent')}%)")
    
    if context_parts:
        context = "\n".join(context_parts)
        prompt = f"""
Based on this data:

{context}

Answer the user's question helpfully: {state.get('user_input')}

Be concise. For portfolio, include total P&L and best/worst performer.
"""
    else:
        prompt = f"Answer concisely: {state.get('user_input')}"
    
    try:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
            json={"model": "mistral-small-latest", "messages": [{"role": "user", "content": prompt}], "max_tokens": 300}
        )
        if response.status_code == 200:
            return {"final_answer": response.json()["choices"][0]["message"]["content"]}
        return {"final_answer": f"Error: {response.status_code}"}
    except Exception as e:
        return {"final_answer": f"Error: {e}"}

# ============================================
# STEP 9: Orchestrator
# ============================================

def run_fintech_agent(question: str):
    print("\n" + "="*60)
    print(f"❓ User: {question}")
    print("="*60)
    
    state = {
        "messages": [],
        "user_input": question,
        "next_agent": "",
        "stock_data": {},
        "sentiment_data": {},
        "portfolio_data": {},
        "return_calculation": {},
        "final_answer": ""
    }
    
    state.update(supervisor_node(state))
    
    if state.get("next_agent") == "portfolio_agent":
        state.update(portfolio_tracker_node(state))
    elif state.get("next_agent") == "sentiment_agent":
        state.update(sentiment_agent_node(state))
    elif state.get("next_agent") == "stock_price_agent":
        state.update(stock_price_agent_node(state))
    
    state.update(final_answer_node(state))
    
    print(f"\n🤖 Final Answer: {state['final_answer']}")
    print("="*60)
    return state

# ============================================
# STEP 10: Main
# ============================================

if __name__ == "__main__":
    print("="*60)
    print("🤖 DAY 7: PORTFOLIO TRACKER AGENT")
    print("="*60)
    
    try:
        import yfinance
        print("✅ yfinance ready")
    except ImportError:
        print("⚠️ Install yfinance: pip install yfinance")
    
    test_questions = [
        "Track my portfolio: AAPL 10 shares at $150, TSLA 5 shares at $250",
        "What is Apple stock price?",
        "What's the sentiment around Tesla?",
        "I own MSFT 8 shares at $300. How am I doing?"
    ]
    
    for q in test_questions:
        run_fintech_agent(q)
    
    print("\n" + "="*60)
    print("✅ Portfolio Tracker Agent Working!")
    print("="*60)