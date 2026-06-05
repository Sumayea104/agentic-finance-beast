"""
Day 2: RAG from Scratch - WORKING VERSION
Uses gemini-embedding-001 (the current supported model)
"""

import requests
import math
import os
from dotenv import load_dotenv

# Load API keys
load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not MISTRAL_API_KEY or not GEMINI_API_KEY:
    print("❌ Error: Missing API keys in .env file")
    exit(1)

print("✅ API keys loaded")

# ============================================
# DOCUMENT (our knowledge base)
# ============================================
document = """
An AI agent is a software system that perceives its environment and takes actions to achieve specific goals.
Unlike traditional programs that follow fixed rules, AI agents can make decisions, learn from feedback, and adapt to new situations.
Agents use large language models (LLMs) as their "brain" to reason about problems and choose which tools to use.
For example, a financial AI agent might check stock prices, calculate returns, and recommend investments - all without human intervention.
The most advanced agents can collaborate with other agents, remember past conversations, and even critique their own work.
"""

# Split into sentences
chunks = [s.strip() + "." for s in document.replace("\n", " ").split(". ") if s.strip()]
print(f"📄 Document split into {len(chunks)} chunks")

# ============================================
# CORRECTED: Gemini Embedding Function
# ============================================
def get_embedding(text):
    """Get embedding using gemini-embedding-001 (current model)"""
    
    # CORRECTED URL and model name
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={GEMINI_API_KEY}"
    
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {
            "parts": [{"text": text}]
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # The embedding is in data['embedding']['values']
            embedding = data.get("embedding", {}).get("values", [])
            if embedding:
                return embedding
            else:
                print(f"   ⚠️ No embedding in response")
                return None
        else:
            print(f"   ⚠️ Error {response.status_code}: {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"   ⚠️ Request failed: {e}")
        return None

# ============================================
# Generate embeddings
# ============================================
print("\n🔢 Generating embeddings...")
chunk_embeddings = []

for i, chunk in enumerate(chunks):
    print(f"   Chunk {i+1}: {chunk[:50]}...")
    emb = get_embedding(chunk)
    if emb:
        chunk_embeddings.append(emb)
        print(f"      ✓ Embedded (dimensions: {len(emb)})")
    else:
        print(f"      ✗ Failed")

if not chunk_embeddings:
    print("\n❌ No embeddings generated. Check your Gemini API key.")
    exit(1)

# ============================================
# Cosine Similarity
# ============================================
def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0

# ============================================
# Search function
# ============================================
def search(query, embeddings, chunks):
    print(f"\n🔍 Searching: '{query}'")
    
    query_emb = get_embedding(query)
    if not query_emb:
        return None, 0
    
    similarities = [cosine_similarity(query_emb, emb) for emb in embeddings]
    best_idx = similarities.index(max(similarities))
    best_score = similarities[best_idx]
    
    print(f"   Best score: {best_score:.4f}")
    print(f"   Matched: {chunks[best_idx][:80]}...")
    return chunks[best_idx], best_score

# ============================================
# Answer with Mistral
# ============================================
def generate_answer(context, question):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": "Answer based ONLY on the context. Be concise."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

# ============================================
# TEST
# ============================================
print("\n" + "="*60)
print("🧠 RAG PIPELINE TEST")
print("="*60)

questions = [
    "What is an AI agent?",
    "How do AI agents differ from traditional programs?",
    "What can financial AI agents do?"
]

for q in questions:
    print(f"\n{'─'*40}")
    context, score = search(q, chunk_embeddings, chunks)
    if context:
        answer = generate_answer(context, q)
        print(f"\n🤖 Answer: {answer}")

print("\n" + "="*60)
print("✅ RAG pipeline complete!")
print("="*60)