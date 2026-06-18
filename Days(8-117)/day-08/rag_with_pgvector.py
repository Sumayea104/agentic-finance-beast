"""
Day 8: RAG with Persistent Vector Storage (Supabase pgvector)
Using Mistral Embeddings (1024 dimensions) - fits within PostgreSQL limits
"""

import requests
import os
import math
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# ============================================
# CONFIGURATION
# ============================================
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for backend

if not all([MISTRAL_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    print("❌ Missing environment variables. Check .env file")
    print("Required: MISTRAL_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY")
    exit(1)

print("✅ All API keys loaded")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================
# STEP 1: Document Knowledge Base
# ============================================
document = """
An AI agent is a software system that perceives its environment and takes actions to achieve specific goals.
Unlike traditional programs that follow fixed rules, AI agents can make decisions, learn from feedback, and adapt to new situations.
Agents use large language models (LLMs) as their "brain" to reason about problems and choose which tools to use.
For example, a financial AI agent might check stock prices, calculate returns, and recommend investments - all without human intervention.
The most advanced agents can collaborate with other agents, remember past conversations, and even critique their own work.
For portfolio tracking, AI agents can monitor multiple stocks, calculate real-time P&L, and alert users to significant changes.
Sentiment analysis allows agents to gauge market mood from news and social media, helping investors make informed decisions.
"""

# Split into chunks (simple sentence-based)
chunks = [s.strip() + "." for s in document.replace("\n", " ").split(". ") if s.strip()]
print(f"📄 Document split into {len(chunks)} chunks")

# ============================================
# STEP 2: Embedding Function (Mistral - 1024 dims)
# ============================================
def get_embedding(text: str) -> list:
    """Generate embedding using Mistral AI API (1024 dimensions)"""
    url = "https://api.mistral.ai/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-embed",
        "input": text
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("data", [{}])[0].get("embedding", [])
            if embedding:
                return embedding
            else:
                print(f"   ⚠️ No embedding values in response")
                return None
        else:
            print(f"   ⚠️ API Error {response.status_code}: {response.text[:100]}")
            return None
    except Exception as e:
        print(f"   ⚠️ Request failed: {e}")
        return None

# ============================================
# STEP 3: Store Embeddings in Supabase
# ============================================
def store_documents():
    """Generate embeddings and store in Supabase"""
    print("\n🔢 Generating and storing embeddings...")
    
    # Check if documents already exist
    result = supabase.table("documents").select("id", count="exact").execute()
    if result.count and result.count > 0:
        print(f"   ⚠️ Documents already exist ({result.count} rows). Skipping storage.")
        print("   To re-store, truncate the documents table first.")
        return
    
    for i, chunk in enumerate(chunks):
        print(f"   Processing chunk {i+1}...")
        embedding = get_embedding(chunk)
        
        if embedding and len(embedding) == 1024:
            # Store in Supabase
            data = {
                "content": chunk,
                "embedding": embedding,
                "metadata": {"chunk_index": i, "source": "day8_document"}
            }
            try:
                result = supabase.table("documents").insert(data).execute()
                if result.data:
                    print(f"   ✓ Chunk {i+1} stored (embedding length: {len(embedding)})")
                else:
                    print(f"   ✗ Failed to store chunk {i+1}")
            except Exception as e:
                print(f"   ✗ Supabase error: {e}")
        else:
            print(f"   ✗ Invalid embedding for chunk {i+1} (length: {len(embedding) if embedding else 'None'})")

# ============================================
# STEP 4: Similarity Search from Supabase
# ============================================
def search_similar(query: str, limit: int = 3) -> list:
    """Search for similar documents using vector similarity"""
    print(f"\n🔍 Searching for: '{query}'")
    
    # Generate embedding for query
    query_embedding = get_embedding(query)
    if not query_embedding:
        print("   ⚠️ Could not generate embedding for query")
        return []
    
    if len(query_embedding) != 1024:
        print(f"   ⚠️ Query embedding length {len(query_embedding)} != 1024")
        return []
    
    try:
        # Call Supabase RPC function
        result = supabase.rpc(
            'match_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.5,
                'match_count': limit
            }
        ).execute()
        
        if result.data:
            print(f"   Found {len(result.data)} matches")
            for match in result.data:
                print(f"   Score: {match.get('similarity', 0):.4f} - {match['content'][:60]}...")
            return result.data
        else:
            print("   No matches found")
            return []
    except Exception as e:
        print(f"   ⚠️ Search error: {e}")
        return []

# ============================================
# STEP 5: Generate Answer with Mistral
# ============================================
def generate_answer(question: str, context_docs: list) -> str:
    """Generate answer using retrieved context"""
    if not context_docs:
        prompt = f"Answer this question based on your general knowledge: {question}"
    else:
        context = "\n\n".join([doc['content'] for doc in context_docs])
        prompt = f"""
Answer the question based ONLY on the following context:

Context:
{context}

Question: {question}

Answer concisely and accurately. If the answer isn't in the context, say "I don't have enough information to answer that."
"""
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error: API returned {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

# ============================================
# STEP 6: Complete RAG Pipeline
# ============================================
def ask_question(question: str):
    """Complete RAG pipeline: search + generate"""
    print("\n" + "="*60)
    print(f"❓ Question: {question}")
    print("="*60)
    
    # Step 1: Search for relevant documents
    similar_docs = search_similar(question)
    
    # Step 2: Generate answer
    answer = generate_answer(question, similar_docs)
    
    print(f"\n🤖 Answer: {answer}")
    print("="*60)
    return answer

# ============================================
# STEP 7: Database Setup Helper
# ============================================
def show_setup_instructions():
    """Print SQL setup instructions"""
    print("\n" + "="*60)
    print("📝 DATABASE SETUP INSTRUCTIONS")
    print("="*60)
    print("""
Run this SQL in Supabase SQL Editor FIRST:

-- Step 1: Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Create table with RLS
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1024),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Step 3: Enable Row Level Security
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Step 4: Create policy for service role
CREATE POLICY "Service role can do anything" 
    ON documents 
    USING (true) 
    WITH CHECK (true);

-- Step 5: Create index (fits within 2000 limit)
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Step 6: Create search function
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1024),
    match_threshold float,
    match_count int
)
RETURNS TABLE(
    id bigint,
    content text,
    similarity float
)
LANGUAGE sql
AS $$
    SELECT
        id,
        content,
        1 - (embedding <=> query_embedding) as similarity
    FROM documents
    WHERE 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;
""")

# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    print("="*60)
    print("🤖 DAY 8: RAG WITH PERSISTENT VECTOR STORAGE")
    print("   Using Mistral Embeddings (1024 dimensions)")
    print("="*60)
    
    # Show setup instructions first
    show_setup_instructions()
    
    input("\n✅ After running the SQL above, press Enter to continue...")
    
    # Store documents (only runs once)
    store_documents()
    
    # Test questions
    test_questions = [
        "What is an AI agent?",
        "How do AI agents differ from traditional programs?",
        "What can financial AI agents do?",
        "What is portfolio tracking?"
    ]
    
    for q in test_questions:
        ask_question(q)
    
    print("\n" + "="*60)
    print("✅ DAY 8 COMPLETE! RAG with pgvector working!")
    print("="*60)