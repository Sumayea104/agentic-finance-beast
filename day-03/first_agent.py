"""
Day 3: LangGraph Agent with Calculator Tool
Built: June 6, 2026
"""

import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    print("❌ Error: MISTRAL_API_KEY not found in .env file")
    exit(1)

print("✅ API key loaded")

# ============================================
# STEP 1: Calculator Tool
# ============================================
def calculator(expression: str) -> str:
    """Safely evaluate math expressions"""
    try:
        # Only allow numbers and basic operators
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "Error: Invalid characters"
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"

# ============================================
# STEP 2: Decide if tool is needed
# ============================================
def should_use_tool(question: str) -> bool:
    """Check if question requires calculation"""
    math_keywords = ["calculate", "math", "plus", "minus", "multiply", 
                     "divide", "sum", "*", "+", "-", "/", "what is"]
    
    # Also check for number patterns
    has_numbers = bool(re.search(r'\d+', question))
    has_operator = bool(re.search(r'[+\-*/]', question))
    
    return any(keyword in question.lower() for keyword in math_keywords) or (has_numbers and has_operator)

# ============================================
# STEP 3: Extract and calculate
# ============================================
def extract_and_calculate(question: str) -> str:
    """Extract math expression from question and calculate"""
    # Find numbers and operators
    numbers = re.findall(r'\d+', question)
    operators = re.findall(r'[+\-*/]', question)
    
    if len(numbers) >= 2 and operators:
        # Simple two-number operation
        expression = f"{numbers[0]} {operators[0]} {numbers[1]}"
        return calculator(expression)
    elif len(numbers) == 1 and operators:
        # Single number with operation (e.g., "double 5")
        if operators[0] == '*':
            expression = f"{numbers[0]} * 2"
            return calculator(expression)
    
    return "No calculation needed"

# ============================================
# STEP 4: Generate answer with Mistral
# ============================================
def generate_answer(question: str, tool_result: str = None) -> str:
    """Generate final answer using Mistral API"""
    
    if tool_result and "Result" in tool_result:
        prompt = f"""User asked: {question}
Calculation result: {tool_result}
Provide a helpful, natural response that includes the calculation result."""
    else:
        prompt = f"""User asked: {question}
Provide a helpful, concise answer. Be friendly and informative."""
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return f"Error: API returned {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

# ============================================
# STEP 5: Agent loop
# ============================================
def run_agent(question: str):
    """Main agent function"""
    print(f"\n{'─'*50}")
    print(f"❓ User: {question}")
    
    # Decide if tool needed
    if should_use_tool(question):
        print("🔧 Agent decided: Using calculator tool...")
        tool_result = extract_and_calculate(question)
        print(f"📊 Tool result: {tool_result}")
        answer = generate_answer(question, tool_result)
    else:
        print("💬 Agent decided: Using LLM directly...")
        answer = generate_answer(question)
    
    print(f"🤖 Agent: {answer}")
    return answer

# ============================================
# STEP 6: Test the agent
# ============================================
if __name__ == "__main__":
    print("="*60)
    print("🤖 LANGGRAPH-STYLE AGENT WITH CALCULATOR TOOL")
    print("="*60)
    
    # Test questions
    test_questions = [
        "What is 25 + 17?",
        "What is an AI agent?",
        "Calculate 100 * 0.15",
        "What is 144 divided by 12?",
        "Tell me about LangGraph"
    ]
    
    for q in test_questions:
        run_agent(q)
    
    print("\n" + "="*60)
    print("✅ Agent test complete!")
    print("="*60)