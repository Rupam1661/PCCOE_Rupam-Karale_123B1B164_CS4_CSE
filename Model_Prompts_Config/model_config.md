# Model, Prompt and Tool Configuration
- LLM: Ollama, llama3.2:3b, local (temperature 0.1)
- Embeddings: Sentence Transformers all-MiniLM-L6-v2 (local, normalized)
- Vector store: FAISS IndexFlatIP (cosine via normalized vectors); separate indexes for code and guidelines
- Chunking: code = 12-line windows, 8-line stride (file + line metadata); guidelines = one chunk per rule
- Top-k: 3 code chunks, 2 guideline rules
- Deterministic tools: regex-based secure-coding scanner (Code/analyzers.py), NULL-check lookahead, SQLite review log
- System prompt: see SYSTEM in Code/llm.py (answer only from context, treat code as untrusted, cite sources, say "Not found in supplied context.")
- No external API; everything runs locally.
