# Why I Built RAG From Scratch Before Using LangChain

When learning AI engineering, one piece of advice appears everywhere:

> "Use LangChain for RAG."

And honestly, it works.

A few lines of code later, you have a chatbot capable of answering questions from documents.

But I kept wondering:

**What actually happens underneath?**

If retrieval quality becomes poor, how would I debug it?

If the wrong context is returned, where would I even start looking?

Before using any framework, I decided to build a minimal Retrieval-Augmented Generation (RAG) pipeline from scratch.

This project became Day 2 of my Agentic Finance Beast journey and taught me more than I expected.

## What Is RAG?

Retrieval-Augmented Generation combines two ideas:

1. Retrieve relevant information from a knowledge source.
2. Generate an answer using that retrieved information.

Instead of relying solely on what an LLM learned during training, the model receives external context at runtime.

The pipeline I built looked like this:

Document
→ Chunking
→ Embeddings
→ Similarity Search
→ Context Retrieval
→ Mistral LLM
→ Final Answer

Simple architecture.

Interesting lessons.

## Step 1: Chunking the Document

I started with a small knowledge base about AI agents.

The first task was splitting the document into chunks.

```python
chunks = [
    s.strip() + "."
    for s in document.replace("\n", " ").split(". ")
    if s.strip()
]
```

Nothing fancy.

Each sentence became a chunk.

At first, this seemed like a trivial step.

Later I realized chunking is one of the most important parts of retrieval quality.

Poor chunking can separate related information and make retrieval less effective.

## Step 2: Generating Embeddings

For embeddings, I used Gemini's embedding API.

```python
embedding = data.get("embedding", {}).get("values", [])
```

This was the moment RAG stopped feeling magical.

The API converted text into a high-dimensional vector representing semantic meaning.

What surprised me most was the size of the embedding vectors.

Before this project, embeddings were just a concept I heard people discuss.

After seeing thousands of numerical dimensions returned from the API, the process became much more tangible.

## Step 3: Building Similarity Search

Instead of using a vector database, I implemented cosine similarity myself.

```python
def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b)
```

Many AI systems sound complex until you build the simplest version yourself.

The underlying mathematics was surprisingly approachable.

The real challenge wasn't the formula.

The challenge was retrieving the most useful information consistently.

## Step 4: Retrieval

When a user asks a question, the question is embedded using the same model.

I then compare the query embedding against all document embeddings and select the highest-scoring chunk.

```python
best_idx = similarities.index(max(similarities))
```

This became the retrieval layer of my RAG system.

Simple.

Fast.

Effective enough for a first implementation.

## Step 5: Grounded Generation

After retrieving the most relevant chunk, I passed it to Mistral.

```python
Context: {context}

Question: {question}
```

The model was instructed to answer only from the provided context.

This is where retrieval and generation come together.

Without retrieval, the model answers from its training knowledge.

With retrieval, the model answers from the information I provide.

## What Surprised Me Most

Before building this project, I assumed the language model was the most important component.

I was wrong.

Most problems came from retrieval.

If retrieval returned weak context, answer quality suffered.

If retrieval returned strong context, answer quality improved dramatically.

This changed how I think about AI systems.

The quality of information entering the model often matters more than the prompt itself.

## Limitations of My Current Implementation

This project is intentionally simple.

Several improvements are already on my roadmap.

### Better Chunking

Currently, I split text by sentences.

Future versions will use more advanced chunking strategies that preserve context better.

### Top-K Retrieval

Right now I retrieve only the best matching chunk.

A better approach would retrieve multiple relevant chunks and combine them.

### Persistent Vector Storage

Embeddings are regenerated each run.

In the future, I plan to store embeddings in a vector database such as pgvector through Supabase.

### Conversation Memory

The current system treats every question independently.

Future versions will maintain conversation history and context across interactions.

## Why I Still Plan to Use LangChain

After building this pipeline, I understand why frameworks exist.

They save time.

They provide abstractions.

They solve common problems.

But now I also understand what those abstractions are doing behind the scenes.

When something breaks, I have a mental model for debugging it.

That understanding is the real value of building from scratch.

## Final Thoughts

Building a simple RAG system taught me more than reading tutorials ever could.

I learned about:

* Chunking
* Embeddings
* Semantic search
* Cosine similarity
* Retrieval quality
* Context grounding

Most importantly, I learned that AI systems are not magic.

They are collections of smaller components working together.

Understanding those components has made me a more confident builder.

And this is only the beginning.
