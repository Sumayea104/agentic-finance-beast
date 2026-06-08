"""
Day 4: LangGraph Agent API - Deployed on Zeabur
FastAPI wrapper for calculator agent with Mistral AI
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import os
import re
import math
from typing import Optional


# Initialize FastAPI
app = FastAPI(
    title="Agentic Finance Beast API",
    description="LangGraph-style agent with calculator tool. Built on i3/8GB RAM. No GPU. No budget. No excuses.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# API Keys
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    print("❌ Error: MISTRAL_API_KEY not found in .env file")
    exit(1)

print("✅ API key loaded")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # For future RAG features

if not GEMINI_API_KEY:
    print("⚠️  Warning: GEMINI_API_KEY not found in .env file")

# Health check
@app.get("/")
def root():
    return {
        "message": "Agentic Finance Beast API is running!",
        "status": "active",
        "version": "1.0.0",
        "hardware": "Intel i3-8130U, 8GB RAM, no GPU",
        "philosophy": "No excuses. Just build."
    }

@app.get("/health")
def health():
    return {"status": "healthy", "api_keys_configured": bool(MISTRAL_API_KEY)}

# Request/Response Models
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    question: str
    answer: str
    tool_used: bool
    tool_result: Optional[str] = None

# ============================================
# CALCULATOR TOOL
# ============================================

def calculator(expression: str) -> str:

    try:
        # Allow only numbers, operators, parentheses, and spaces
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "Error: Invalid characters in expression"
        
        # Evaluate (safe for basic math)
        result = eval(expression)
        return f"Result: {result}"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: {str(e)}"

def should_use_tool(question: str) -> bool:
    """Determine if the question requires calculation"""
    question_lower = question.lower()

    math_keywords = [
        "calculate", "math", "plus", "minus", "multiply", "divide",
        "sum", "add", "subtract", "total", "average", "percent",
        "*", "+", "-", "/", "what is"
    ]
    
    # Check for numbers and operators
    has_numbers = bool(re.search(r'\d+', question))
    has_operator = bool(re.search(r'[+\-*/]', question))
    
    return (any(keyword in question_lower for keyword in math_keywords) or 
            (has_numbers and has_operator))

def extract_and_calculate(question: str) -> str:
    """Extract math expression from question and calculate"""
    # Find numbers
    numbers = re.findall(r'\d+', question)
    
    # Find operators
    operators = re.findall(r'[+\-*/]', question)
    
    # Case 1: Two numbers with operator (e.g., "25 + 17")
    if len(numbers) >= 2 and operators:
        expression = f"{numbers[0]} {operators[0]} {numbers[1]}"
        return calculator(expression)
    
    # Case 2: Single number with multiplication (e.g., "double 5" → 5 * 2)
    elif len(numbers) == 1 and operators and operators[0] == '*':
        expression = f"{numbers[0]} * 2"
        return calculator(expression)
    
    # Case 3: Percentage calculation (e.g., "15% of 100")
    elif '%' in question and len(numbers) >= 2:
        percentage = float(numbers[0]) / 100
        value = float(numbers[1])
        result = percentage * value
        return f"Result: {result}"
    
    # Case 4: Try to extract any math expression
    else:
        # Look for pattern: number operator number
        match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', question)
        if match:
            expression = f"{match.group(1)} {match.group(2)} {match.group(3)}"
            return calculator(expression)
    
    return "No calculation needed"

def generate_answer(question: str, tool_result: str = None) -> str:
    """Generate answer using Mistral AI API"""
    
    if not MISTRAL_API_KEY:
        return "Error: Mistral API key not configured. Please add MISTRAL_API_KEY to environment variables."
    
    # Build prompt based on whether tool was used
    if tool_result and "Result" in tool_result and "Error" not in tool_result:
        prompt = f"""User asked: {question}
Calculation result: {tool_result}
Provide a helpful, natural response that includes the calculation result. Be concise (1-2 sentences)."""
    else:
        prompt = f"""User asked: {question}
Provide a helpful, concise answer. Be friendly and informative. Keep it to 1-2 sentences."""
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant. Provide concise, accurate answers."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"Error: API returned status {response.status_code}"
            
    except requests.exceptions.Timeout:
        return "Error: API request timed out. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"

# ============================================
# MAIN API ENDPOINT
# ============================================

@app.post("/ask", response_model=AnswerResponse)
def ask(request: QuestionRequest):
    """
    Ask the agent a question.
    
    Examples:
    - "What is 25 + 17?" → Uses calculator tool
    - "What is an AI agent?" → Direct LLM answer
    - "Calculate 15% of 200" → Percentage calculation
    """
    question = request.question.strip()
    
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    tool_used = False
    tool_result = None
    
    # Check if tool is needed
    if should_use_tool(question):
        tool_used = True
        tool_result = extract_and_calculate(question)
    
    # Generate answer
    answer = generate_answer(question, tool_result)
    
    return AnswerResponse(
        question=question,
        answer=answer,
        tool_used=tool_used,
        tool_result=tool_result
    )

# ============================================
# INFO ENDPOINTS
# ============================================

@app.get("/info")
def info():
    """Get information about the agent"""
    return {
        "agent_name": "Agentic Finance Beast",
        "capabilities": ["calculator", "general_qa"],
        "tools": ["calculator"],
        "llm": "Mistral AI (mistral-small-latest)",
        "framework": "LangGraph-style (custom implementation)",
        "hardware": "Intel i3-8130U, 8GB RAM, no GPU",
        "cost": "$0 (free tier APIs)"
    }

@app.get("/tools")
def list_tools():
    """List available tools"""
    return {
        "tools": [
            {
                "name": "calculator",
                "description": "Perform mathematical calculations",
                "examples": ["25 + 17", "100 * 0.15", "144 / 12", "15% of 200"]
            }
        ]
    }

@app.get("/favicon.ico")
async def favicon():
    return {"message": "No icon available"}