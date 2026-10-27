# AGENTS.md — SafeChat NLP Engineering Guidelines

## Ponytail Simplicity Standard
- **Flat File Hierarchy**: Zero unnecessary directory nesting. Keep project structure flat and transparent.
- **Zero Speculative Abstractions**: No interfaces with single implementations, no factory wrappers, no redundant DTO classes or helper layers.
- **Direct Execution**: Reach for Python stdlib and direct library calls before building utility functions.
- **Debt Tracking**: Track any intentional shortcuts with `# shortcut:` or `// shortcut:` comments for `/ponytail-debt` tracking.

## Non-Negotiable Latency Rules
1. **Latency Rule #1 (Global RAM Pre-loading)**:
   - In `app.py`, load `tfidf_vectorizer.pkl`, `toxic_classifier.pkl`, `spacy.load("en_core_web_sm", disable=["parser"])`, `nltk` taggers, `PorterStemmer`, stopwords `set()`, and `DE_ESCALATION_LEXICON` ONCE in global module scope at startup.
   - NEVER load models, pipelines, or tokenizers inside a request or WebSocket event handler.
2. **Latency Rule #2 (Persistent WebSockets)**:
   - Use `Flask-SocketIO` (`async_mode='eventlet'`) for real-time bidirectional events (`send_message` -> `receive_message`).
   - Server compute pipeline latency must stay under 25ms so end-to-end client-to-client latency stays under 180ms.
3. **Latency Rule #3 (Render Cold-Start Wakeup)**:
   - Expose `GET /ping` returning `{"status": "awake", "message": "NLP Engine Ready in RAM"}` with `200 OK`.
   - The Flutter client calls `GET /ping` on `initState()` to immediately wake up the Render Free Tier instance before user typing begins.
