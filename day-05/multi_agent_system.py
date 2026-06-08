
import requests
import os
import re
from typing import TypedDict, Annotated
from dotenv import load_dotenv
import operator

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    print("❌ Error: MISTRAL_API_KEY not found")
    exit(1)

print("✅ API key loaded")

# ============================================
# STEP 1: Define Agent State
# ============================================

class MultiAgentState(TypedDict):
    messages: Annotated[list, operator.add]
    user_input: str
    next_agent: str
    stock_data: dict
    return_calculation: dict
    final_answer: str

# ============================================
# STEP 2: Tools
# ============================================

def get_stock_price(symbol: str) -> dict:
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
            "current_price": current_price,
            "previous_close": previous_close,
            "daily_change": round(daily_change, 2),
            "daily_change_percent": round(daily_change_percent, 2),
            "name": info.get('longName', symbol.upper())
        }
    except Exception as e:
        return {"symbol": symbol.upper(), "error": str(e), "current_price": 0}

def calculate_return(buy_price: float, current_price: float) -> dict:
    if buy_price <= 0:
        return {"error": "Invalid buy price"}
    absolute_return = current_price - buy_price
    percentage_return = (absolute_return / buy_price) * 100
    return {
        "buy_price": buy_price,
        "current_price": current_price,
        "absolute_return": round(absolute_return, 2),
        "percentage_return": round(percentage_return, 2),
        "is_profit": percentage_return > 0
    }

# ============================================
# STEP 3: Stock Researcher Node
# ============================================

def stock_researcher_node(state: MultiAgentState) -> dict:
    question = state.get("user_input", "")
    
    stock_names = {
        "apple": "AAPL", "google": "GOOGL", "microsoft": "MSFT",
        "tesla": "TSLA", "amazon": "AMZN", "meta": "META", "nvidia": "NVDA"
    }
    
    found_symbol = None
    for name, symbol in stock_names.items():
        if name in question.lower():
            found_symbol = symbol
            break
    
    for symbol in ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA"]:
        if symbol.lower() in question.lower():
            found_symbol = symbol
            break
    
    result = {"stock_data": {}, "return_calculation": {}}
    
    if found_symbol:
        print(f"📊 Stock Researcher: Fetching data for {found_symbol}...")
        stock_data = get_stock_price(found_symbol)
        result["stock_data"] = stock_data
        
        numbers = re.findall(r'\d+', question)
        if numbers and ("bought" in question.lower() or "purchase" in question.lower()):
            buy_price = float(numbers[0])
            current_price = stock_data.get("current_price", 0)
            if current_price > 0:
                result["return_calculation"] = calculate_return(buy_price, current_price)
    else:
        result["stock_data"] = {"error": f"Could not identify stock"}
    
    return result

# ============================================
# STEP 4: Supervisor Node
# ============================================

def supervisor_node(state: MultiAgentState) -> dict:
    question = state.get("user_input", "")
    
    stock_keywords = ["stock", "price", "aapl", "googl", "msft", "tsla", 
                      "apple", "google", "microsoft", "tesla", "amazon"]
    
    if any(k in question.lower() for k in stock_keywords):
        print("👔 Supervisor: Routing to Stock Researcher")
        return {"next_agent": "stock_researcher"}
    else:
        print("👔 Supervisor: Routing to Final Answer")
        return {"next_agent": "final_answer"}

# ============================================
# STEP 5: Final Answer Node
# ============================================

def final_answer_node(state: MultiAgentState) -> dict:
    context = []
    
    stock_data = state.get("stock_data", {})
    if stock_data and not stock_data.get("error"):
        context.append(f"Stock {stock_data.get('symbol')}: ${stock_data.get('current_price')}")
    
    return_calc = state.get("return_calculation", {})
    if return_calc and not return_calc.get("error"):
        profit_status = "PROFIT" if return_calc.get("is_profit") else "LOSS"
        context.append(f"Return: {return_calc.get('absolute_return')} ({return_calc.get('percentage_return')}%) - {profit_status}")
    
    if context:
        prompt = f"Context: {' '.join(context)}\nQuestion: {state.get('user_input')}\nAnswer naturally."
    else:
        prompt = f"Answer this question concisely: {state.get('user_input')}"
    
    response = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
        json={"model": "mistral-small-latest", "messages": [{"role": "user", "content": prompt}], "max_tokens": 200}
    )
    
    if response.status_code == 200:
        return {"final_answer": response.json()["choices"][0]["message"]["content"]}
    return {"final_answer": f"Error: {response.status_code}"}

# ============================================
# STEP 6: Orchestrator
# ============================================

def run_multi_agent(question: str):
    print(f"\n❓ {question}")
    
    state = {
        "messages": [],
        "user_input": question,
        "next_agent": "",
        "stock_data": {},
        "return_calculation": {},
        "final_answer": ""
    }
    
    state.update(supervisor_node(state))
    
    if state.get("next_agent") == "stock_researcher":
        state.update(stock_researcher_node(state))
    
    state.update(final_answer_node(state))
    
    print(f"🤖 {state['final_answer']}")
    return state

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("="*50)
    print("MULTI-AGENT FINTECH SYSTEM")
    print("="*50)
    
    try:
        import yfinance
        print("✅ yfinance ready")
    except ImportError:
        print("⚠️ Install yfinance: pip install yfinance")
    
    test_questions = [
        "What is Apple stock price?",
        "What is an AI agent?"
    ]
    
    for q in test_questions:
        run_multi_agent(q)
    
    print("\n✅ Day 5 Complete!")