# SafeChat NLP 🛡️
### Production Web Application for Real-Time Toxic Chat Moderation & Context-Aware De-escalation

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1%2B-black.svg)](https://flask.palletsprojects.com/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-v4-010101.svg)](https://socket.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Render](https://img.shields.io/badge/Render-Deploy%20Ready-46E3B7.svg)](https://render.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)
[![Latency](https://img.shields.io/badge/Server%20Compute-%3C25ms-brightgreen.svg)](#non-negotiable-latency-architecture)

**SafeChat NLP** is an ultra-low-latency, real-time toxic message moderation and context-aware de-escalation **web platform** designed for instant messaging systems, gaming chats, and workplace collaboration tools. 

Unlike traditional platforms that simply drop or censor toxic messages, SafeChat introduces a dual-tier processing engine:
1. **Free Tier (Keyword Masking)**: Replaces abusive and toxic terms with clean audio-style censors (`[BEEP]`).
2. **Premium Tier (POS-Guided AI De-escalation)**: Evaluates the grammatical context of toxic words using Part-of-Speech (POS) tagging and automatically rewrites abusive expressions into polite, constructive, and professional workplace communication in real-time.

---

## 📑 Table of Contents

- [Key Web Platform Features](#-key-web-platform-features)
- [How Context-Aware De-escalation Works](#-how-context-aware-de-escalation-works)
- [Comprehensive NLP Syllabus Proofs (Topics 1–9)](#-comprehensive-nlp-syllabus-proofs-topics-19)
- [Non-Negotiable Latency Architecture](#-non-negotiable-latency-architecture)
- [Web-Based Project Structure](#-web-based-project-structure)
- [Getting Started & Local Execution](#-getting-started--local-execution)
  - [Prerequisites](#prerequisites)
  - [1. Backend Setup](#1-backend-setup)
  - [2. Model Training & Syllabus Verification](#2-model-training--syllabus-verification)
  - [3. Running the Web Server](#3-running-the-web-server)
- [Deployment Guide](#-deployment-guide)
  - [Deploy to Render (1-Click Blueprint)](#deploy-to-render-1-click-blueprint)
  - [Deploy to Railway](#deploy-to-railway)
  - [Deploy with Docker](#deploy-with-docker)
- [API & WebSocket Specifications](#-api--websocket-specifications)
  - [REST Endpoints](#rest-endpoints)
  - [WebSocket Events](#websocket-events)
- [Example Test Scenarios](#-example-test-scenarios)
- [Tech Stack](#-tech-stack)
- [License](#-license)

---

## 🚀 Key Web Platform Features

- **⚡ Sub-25ms Server Compute**: Core NLP inference pipeline executes in under **25ms**; end-to-end client-to-client transmission is sub-150ms via persistent WebSockets.
- **🛡️ Asymmetric Delivery Simulation**: When User A types an aggressive message, User A sees what they sent, while User B receives the de-escalated/redacted message in real time with diagnostic badges.
- **🔬 Interactive NLP Test Bench**: Test any custom text live with instant breakdown of tokens, Porter stems, Penn Treebank POS tags, and spaCy Named Entities.
- **📚 9-Topic Syllabus Explorer & CYK Parser**: Interactive visual breakdown of all 9 NLP topics, including a live interactive CYK Chart Syntax Tree parser (`S -> NP VP`).
- **🌐 100% Cloud Deployable**: Pre-configured with `Procfile`, `render.yaml`, `Dockerfile`, `.dockerignore`, and `build.sh` for instant deployment on Render, Railway, Fly.io, or AWS.
- **🔄 Zero Cold-Start RAM Pre-Loading**: Models and lexicons are pre-warmed on module import, ensuring zero disk I/O during messaging.

---

## 💡 How Context-Aware De-escalation Works

Traditional profanity filters redact words into asterisks (`****`) or drop messages entirely, alienating users and breaking conversational continuity. SafeChat's **Premium Tier** reconstructs sentences grammatically:

| Original Toxic Input | Part of Speech | Free Tier Output | Premium Tier (SafeChat) |
| :--- | :--- | :--- | :--- |
| *"Your update is complete **garbage**."* | `NN` (Noun) | *"Your update is complete **[BEEP]**."* | *"Your update is complete **subpar quality**."* |
| *"This is a **garbage** idea."* | `JJ` (Adjective) | *"This is a **[BEEP]** idea."* | *"This is an **unacceptable** idea."* |
| *"You are being **stupid** right now."* | `JJ` (Adjective) | *"You are being **[BEEP]** right now."* | *"You are being **illogical** right now."* |
| *"I **hate** working with this company."* | `VB` (Verb) | *"I **[BEEP]** working with this company."* | *"I **strongly disagree with** working with this company."* |
| *"Stop acting like an **idiot**."* | `NN` (Noun) | *"Stop acting like an **[BEEP]**."* | *"Stop acting like a **misinformed person**."* |

---

## 📚 Comprehensive NLP Syllabus Proofs (Topics 1–9)

The project includes an end-to-end curriculum demonstration script in `train_and_syllabus.py` verifying **all 9 core NLP curriculum topics**:

```
                                  [ Raw Chat Message ]
                                           │
          ┌────────────────────────────────┴────────────────────────────────┐
          ▼                                                                 ▼
[ Topic 1: Tokenization ]                                       [ Topic 4: Preprocessing ]
  - Sentence Tokenizer (Punkt)                                    - Lowercase normalization
  - Word Tokenizer (Treebank)                                     - Regex non-alpha stripping
          │                                                       - Stopwords removal (NLTK)
          ▼                                                       - Porter Stemmer
[ Topic 2: POS Tagging ]                                                    │
  - Penn Treebank tagger                                                    ▼
  - Disambiguates NN vs JJ vs VB                                [ Topic 5: Vector Space Models ]
          │                                                       - CountVectorizer (BoW)
          ▼                                                       - Normalized Term Frequency
[ Topic 3: Named Entity Recognition ]                             - TF-IDF (1-2 n-grams)
  - spaCy en_core_web_sm                                          - Gensim Word2Vec embeddings
  - Identifies PERSON, ORG, GPE                                             │
          │                                                                 ▼
          │                                                     [ Topic 6, 8, 9: Classification ]
          │                                                       - Logistic Regression
          │                                                       - Calibrated Probabilities
          │                                                       - Dual-trigger detection
          └────────────────────────────────┬────────────────────────────────┘
                                           │
                                           ▼
                                [ Topic 7: Syntax Parsing ]
                                  - CFG Chart/CYK Parsing
                                  - Structural tree analysis
```

---

## ⚡ Non-Negotiable Latency Architecture

To achieve sub-150ms round-trip delivery in production:

1. **Latency Rule #1 (Global RAM Pre-Loading)**:
   In `app.py`, all models (`tfidf_vectorizer.pkl`, `toxic_classifier.pkl`), spaCy (`en_core_web_sm`), NLTK taggers, stemmers, stopwords, and `DE_ESCALATION_LEXICON` are loaded ONCE into global module scope at startup.
2. **Latency Rule #2 (Persistent WebSockets)**:
   Flask-SocketIO (`eventlet` in production) keeps a persistent duplex socket open between the client and server.
3. **Latency Rule #3 (Render Cold-Start Wakeup)**:
   `GET /ping` returns `{"status": "awake", "message": "NLP Engine Ready in RAM"}` in `<5ms`. The web client triggers this on load to eliminate spin-down cold starts.

---

## 📂 Web-Based Project Structure

```text
NLP Project/
├── AGENTS.md                  # Engineering guidelines & latency rules
├── Procfile                   # Cloud process definition (Gunicorn + Eventlet)
├── render.yaml                # Render Blueprint (1-click cloud deploy)
├── Dockerfile                 # Standalone production container definition
├── .dockerignore              # Excluded files for fast Docker build
├── build.sh                   # Cloud build script (downloads corpora & pre-trains)
├── .env.example               # Environment variables template
├── requirements.txt           # Python dependencies
├── app.py                     # Production Flask-SocketIO web server
├── train_and_syllabus.py      # All 9 syllabus topics & model training
├── tfidf_vectorizer.pkl       # Exported TF-IDF vectorizer artifact
├── toxic_classifier.pkl       # Exported Logistic Regression classifier artifact
│
├── templates/                 # Web HTML Templates
│   └── index.html             # High-end dashboard (Chat, Sandbox, Syllabus, Deploy)
│
├── static/                    # Frontend Web Assets
│   ├── css/
│   │   └── style.css          # Glassmorphic dark theme, animations, responsive grid
│   └── js/
│       └── app.js             # Socket.IO client, reactive UI, NLP inspector
│
├── Dataset/                   # Dataset directory
│   └── train.csv              # Kaggle Toxic Comment Classification dataset (optional)
│
└── flutter_client/            # Optional cross-platform mobile/desktop client
```

---

## 🛠️ Getting Started & Local Execution

### Prerequisites
- **Python**: 3.10 or 3.11
- **Git**

---

### 1. Backend Setup

```bash
# Clone the repository and navigate into the root directory
cd "NLP Project"

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 2. Model Training & Syllabus Verification

Run the verification script to download NLTK data & spaCy models and pre-train the classifier:

```bash
python train_and_syllabus.py
```

---

### 3. Running the Web Server

Start the production web server:

```bash
python app.py
```

Open **`http://localhost:5000`** in your browser.

- **Web Dashboard**: Interactive real-time dual-persona chat and deep NLP inspector.
- **Health Check**: `http://localhost:5000/ping`

---

## 🌐 Deployment Guide

### Deploy to Render (1-Click Blueprint)

1. Push this repository to GitHub.
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New +** ➔ **Blueprint**, select your repository. Render will automatically read `render.yaml`.
4. Alternatively, create a **Web Service**:
   - **Environment**: Python 3
   - **Build Command**: `bash build.sh`
   - **Start Command**: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app`
   - **Health Check Path**: `/ping`

### Deploy to Railway

1. Connect your GitHub repository to [Railway](https://railway.app).
2. Railway detects the `Procfile` and launches automatically with the dynamic `$PORT`.

### Deploy with Docker

```bash
# Build the container (pre-downloads models & pre-bakes weights)
docker build -t safechat-nlp .

# Run the container
docker run -p 5000:5000 safechat-nlp
```

---

## 🔌 API & WebSocket Specifications

### REST Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Web application dashboard |
| `GET` | `/ping` | Health check & cold-start warmup |
| `POST` | `/api/analyze` or `/api/test` | Complete NLP pipeline analysis on input text |
| `GET` | `/api/lexicon` | Retrieves active POS de-escalation lexicon rules |
| `POST` | `/api/parse-tree` | Context-Free Grammar Chart Parser (Topic 7) |
| `GET` | `/api/stats` | Server telemetry & RAM pre-loading health |

#### Example: Analyzing a Message via REST
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "Hey John, your update is complete garbage!", "tier": "premium", "sender": "User A"}'
```

---

### WebSocket Events

| Event Name | Direction | Payload Structure | Description |
| :--- | :--- | :--- | :--- |
| `connect` | Client ➔ Server | `None` | Establishes duplex WebSocket session |
| `send_message` | Client ➔ Server | `{"sender": "User A", "message": "...", "tier": "premium"}` | Submits message to the NLP pipeline |
| `receive_message` | Server ➔ Clients | Full JSON payload | Broadcasts sanitized and de-escalated message |
| `typing` | Client ➔ Server | `{"sender": "User A"}` | Broadcasts live typing indicator |
| `clear_chat` | Client ➔ Server | `{}` | Clears conversation feed |

---

## 🧪 Example Test Scenarios

Try these presets in the web interface:

| # | Scenario | Test Phrase | Expected Result |
| :--- | :--- | :--- | :--- |
| 1 | Workplace Frustration | *"Hey John, your update is complete garbage!"* | De-escalates to: *"Hey John, your update is complete subpar quality!"* |
| 2 | Hostile Threat | *"I will hurt you today for ruining my account."* | De-escalates to: *"I will escalate a complaint against you today for ruining my account."* |
| 3 | Gaming Toxicity | *"You are a total idiot and a worthless moron."* | De-escalates to: *"You are a total misinformed person and an individual."* |
| 4 | Service Complaint | *"I hate everything about this scam company."* | De-escalates to: *"I strongly disagree with everything about this misleading service company."* |
| 5 | Clean Collaboration | *"Great job team, let's schedule our design sync tomorrow morning."* | Clean Pass (Toxicity ~0.02) |

---

## 🧰 Tech Stack

- **Core NLP**: NLTK (Punkt, Averaged Perceptron Tagger, PorterStemmer), spaCy (`en_core_web_sm`), Gensim (`Word2Vec`)
- **Machine Learning**: Scikit-learn (`TfidfVectorizer`, `LogisticRegression`), Joblib, NumPy
- **Backend & WebSockets**: Flask, Flask-SocketIO, Eventlet, Gunicorn, Flask-CORS
- **Frontend Architecture**: Semantic HTML5, Vanilla CSS (Glassmorphism & CSS Variables), Vanilla JavaScript (Reactive & Socket.IO)
- **DevOps & Cloud**: Docker, Render Blueprint (`render.yaml`), Railway, Gunicorn Eventlet Worker

---

## 📄 License

This project is licensed under the MIT License — feel free to use and adapt it for academic, research, or commercial purposes.
