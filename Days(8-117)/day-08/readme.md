# Day 8: Production RAG with Persistent Vector Storage (Supabase pgvector)

**Date:** June 19, 2026
**Duration:** 1 day
**Status:** ✅ Complete

---

## 🎯 Why I Did This

In **Day 2**, I built a RAG pipeline from scratch. It worked, but it had a critical limitation:

| Limitation | Impact |
|------------|--------|
| **In-memory storage** | Embeddings regenerated every run (slow) |
| **No persistence** | Data lost when script stopped |
| **Not scalable** | Could only handle ~100 documents |
| **Demo-only** | Not suitable for production |

**Day 8 goal:** Upgrade to production-ready RAG with persistent vector storage.

---

## 🏗️ What I Built

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│ PRODUCTION RAG PIPELINE │
├─────────────────────────────────────────────────────────────┤
│ │
│ Document → Chunks → Embeddings → Supabase pgvector │
│ ↓ │
│ Question → Embedding → Similarity Search → Context → Answer│
│ │
└─────────────────────────────────────────────────────────────┘

```
### Technology Stack

| Component | Tool | Why |
|-----------|------|-----|
| **Vector Database** | Supabase pgvector | Free tier, PostgreSQL-native |
| **Embeddings** | Mistral AI | 1024 dimensions, free tier |
| **LLM** | Mistral AI | Answer generation |
| **Index** | ivfflat | Fast similarity search |
| **Language** | Python | Supabase SDK available |

---

## 🔧 Technical Implementation

### 1. Supabase Setup

**Database Schema:**
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1024),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```
**Vector Index:**
```sql
CREATE INDEX ON documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```
**Search Function:**
```sql
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1024),
    match_threshold float,
    match_count int
)
RETURNS TABLE(id bigint, content text, similarity float)
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
```
---
### 2. Python Implementation
```python
# Store embeddings
def store_documents():
    for chunk in chunks:
        embedding = get_embedding(chunk)
        supabase.table("documents").insert({
            "content": chunk,
            "embedding": embedding,
            "metadata": {"chunk_index": i}
        }).execute()

# Search and generate
def ask_question(question):
    query_embedding = get_embedding(question)
    results = supabase.rpc("match_documents", {
        "query_embedding": query_embedding,
        "match_threshold": 0.5,
        "match_count": 3
    }).execute()
    
    context = "\n".join([r["content"] for r in results.data])
    answer = generate_answer(question, context)
    return answer

```
---
### 🐛 Problems Faced & Solutions
**Problem 1: Gemini 3072 Dimensions Too High**

**Error:**
```
ERROR: 54000: column cannot have more than 2000 dimensions for ivfflat index
```
Root Cause: ivfflat index has a 2000-dimension limit. Gemini embeddings are 3072 dimensions.

Solution:

Switched from Gemini to Mistral embeddings (1024 dimensions)

Updated table schema: VECTOR(1024)

Recreated all tables and indexes

Key Lesson: Always check vector dimensions against your database's index limits.

**Problem 2: HNSW Index Also Has Limits**

**Error:**
```
ERROR: 54000: column cannot have more than 2000 dimensions for hnsw index
```

Root Cause: HNSW index also has a 2000-dimension limit in this Supabase version.

Solution:

Used ivfflat index instead

Both work, but ivfflat is simpler to configure

Key Lesson: Know your database's limitations before choosing an embedding model.

**Problem 3: Multiple Indexes Created**
-Issue: After multiple setup attempts, duplicate indexes existed.
**Solution:**
```
-- Drop duplicate indexes
DROP INDEX IF EXISTS documents_embedding_idx1;
DROP INDEX IF EXISTS documents_embedding_idx2;

-- Keep only one
SELECT indexname FROM pg_indexes 
WHERE tablename = 'documents' 
AND indexname LIKE '%embedding%';
```
Key Lesson: Clean up after yourself. Duplicate indexes waste storage and slow writes.


**Problem 4: RLS Policy Warning**

**Warning:**
```
RLS Policy Always True: Service role can do anything
```
Solution: For development, this is acceptable. For production, implement proper role-based access.

Key Lesson: Development security != Production security. Plan for the future.

Problem 5: Connection Testing
Issue: Script ran but no data inserted.

Solution:

Created a test script (test_supabase_connection.py)

Verified .env variables

Confirmed service role key permissions

Key Lesson: Always test your database connection before running complex scripts.

🎯 What I Learned
Technical Lessons
Vector dimensions matter — Choose embedding model based on database limits

Test early, test often — Validate database connection before full script

Clean up artifacts — Remove duplicate indexes, tables, policies

Know your free tier limits — Supabase has 2000-dimension index limit

Architecture Lessons
Persistent storage is non-negotiable for production AI systems

Indexing is critical for performance at scale

Row Level Security (RLS) needs proper planning

Document your schema for future maintenance

🔮 Future Considerations
Immediate Improvements
Add more documents to the knowledge base

Implement chunking strategies (overlapping chunks)

Add metadata filtering (e.g., date range, source)

Production Readiness
Move vector extension to separate schema

Implement proper RLS policies

Add monitoring and logging

Set up backup for vector data

Scaling
Implement hybrid search (keyword + vector)

Add reranking layer for better results

Consider partitioning for large datasets

Explore batch processing for updates

Integration
Connect RAG to LangGraph agents

Add real-time document updates

Build ingestion pipeline for new documents

Create evaluation suite for retrieval quality

💬 Final Thoughts
Moving from in-memory RAG to production-ready vector storage was a critical step in building real-world AI systems. The challenges I faced (dimension limits, index types, duplicate artifacts) are exactly what you encounter in production.

Key takeaway: Production AI isn't just about models. It's about infrastructure, persistence, and understanding your tools' limitations.

Built as part of my 117-day MBA → AI Engineer journey.
Day 8 complete. 109 days to go.




