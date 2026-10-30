"""
app.py - SafeChat NLP: Sub-150ms Production Web Server & Real-Time Engine
Complies with Latency Rules #1, #2, #3 and Ponytail Simplicity Standard.
"""

# GEVENT MONKEY-PATCHING: Must execute at line 1 before any other modules load
try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass

import os
import re
import time
import warnings
warnings.filterwarnings("ignore")
import joblib
import nltk
import spacy
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize

from train_and_syllabus import ensure_nlp_assets, train_and_export_if_missing

# ---------------------------------------------------------
# LATENCY RULE #1: GLOBAL RAM PRE-LOADING AT STARTUP
# ---------------------------------------------------------
ensure_nlp_assets()

if not os.path.exists("tfidf_vectorizer.pkl") or not os.path.exists("toxic_classifier.pkl"):
    print("[SafeChat RAM Loader] Artifacts missing. Training on startup...")
    train_and_export_if_missing()

print("[SafeChat RAM Loader] Loading models and NLP engines into RAM...")
TFIDF_VECTORIZER = joblib.load("tfidf_vectorizer.pkl")
TOXIC_CLASSIFIER = joblib.load("toxic_classifier.pkl")
NLP_SPACY = spacy.load("en_core_web_sm", disable=["parser"])
STEMMER = PorterStemmer()
STOPWORDS_SET = set(stopwords.words("english"))

# Pre-warm all NLP engines on module load to eliminate first-call cold-start
word_tokenize("warmup sentence")
NLP_SPACY("warmup entity sentence")
nltk.pos_tag(["warmup"])
_warmup_vec = TFIDF_VECTORIZER.transform(["warmup"])
TOXIC_CLASSIFIER.predict_proba(_warmup_vec)

# POS-Aware De-escalation Dictionary (Penn Treebank prefixes: NN, JJ, VB, DEFAULT)
DE_ESCALATION_LEXICON = {
    "garbage": {"NN": "subpar quality", "JJ": "unacceptable", "DEFAULT": "subpar"},
    "trash": {"NN": "low quality work", "JJ": "unacceptable", "DEFAULT": "subpar"},
    "idiot": {"NN": "misinformed person", "DEFAULT": "colleague"},
    "moron": {"NN": "uninformed individual", "DEFAULT": "individual"},
    "stupid": {"JJ": "illogical", "DEFAULT": "unwise"},
    "dumb": {"JJ": "short-sighted", "DEFAULT": "unwise"},
    "useless": {"JJ": "ineffective", "DEFAULT": "unhelpful"},
    "pathetic": {"JJ": "disappointing", "DEFAULT": "underwhelming"},
    "hate": {"VB": "strongly disagree with", "NN": "disapproval", "DEFAULT": "dislike"},
    "hurt": {"VB": "escalate a complaint against", "DEFAULT": "report"},
    "kill": {"VB": "formally penalize", "DEFAULT": "penalize"},
    "scam": {"NN": "misleading service", "DEFAULT": "issue"},
}

# Penn Treebank POS Explanations for Inspector
POS_DESCRIPTIONS = {
    "NN": "Noun (Singular)",
    "NNS": "Noun (Plural)",
    "NNP": "Proper Noun (Singular)",
    "NNPS": "Proper Noun (Plural)",
    "JJ": "Adjective (Quality)",
    "JJR": "Adjective (Comparative)",
    "JJS": "Adjective (Superlative)",
    "VB": "Verb (Base Form)",
    "VBD": "Verb (Past Tense)",
    "VBG": "Verb (Gerund / Participle)",
    "VBN": "Verb (Past Participle)",
    "VBP": "Verb (Present Non-3rd)",
    "VBZ": "Verb (Present 3rd Person)",
    "RB": "Adverb",
    "RBR": "Adverb (Comparative)",
    "RBS": "Adverb (Superlative)",
    "PRP": "Personal Pronoun",
    "PRP$": "Possessive Pronoun",
    "DT": "Determiner",
    "IN": "Preposition / Conjunction",
    "CC": "Coordinating Conjunction",
    "MD": "Modal Auxiliary",
}

# Topic 7: Context-Free Grammar Chart Parser Pre-load
GRAMMAR_TOPIC7 = nltk.CFG.fromstring("""
  S -> NP VP
  NP -> 'service' | 'garbage' | 'product' | 'code' | 'work' | 'system'
  VP -> V Adj | V NP
  V -> 'is' | 'looks' | 'seems'
  Adj -> 'garbage' | 'subpar' | 'clean' | 'great' | 'unacceptable'
""")
PARSER_TOPIC7 = nltk.ChartParser(GRAMMAR_TOPIC7)

SERVER_START_TIME = time.time()
TOTAL_MESSAGES_PROCESSED = 0

print("[SafeChat RAM Loader] RAM Pre-loading complete. Engine ready.")

# ---------------------------------------------------------
# Flask & SocketIO Server Initialization (LATENCY RULE #2)
# ---------------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "safechat-nlp-secret-key-prod")
CORS(app, resources={r"/*": {"origins": "*"}})

# Gevent-first async mode fallback
try:
    import gevent
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")
except Exception:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ---------------------------------------------------------
# Core NLP Processing Pipeline (Sub-25ms Target)
# ---------------------------------------------------------
def process_message_pipeline(raw_text: str, user_tier: str = "premium", sender: str = "Anonymous") -> dict:
    global TOTAL_MESSAGES_PROCESSED
    TOTAL_MESSAGES_PROCESSED += 1
    t0 = time.perf_counter()

    # Preprocessing (Syllabus Topic 4)
    cleaned_lower = raw_text.lower()
    stripped_text = re.sub(r"[^a-z\s]", " ", cleaned_lower)
    tokens_stemmed = [
        STEMMER.stem(w)
        for w in stripped_text.split()
        if w and w not in STOPWORDS_SET
    ]
    preprocessed_str = " ".join(tokens_stemmed)

    # Topic 6 & 8: Toxicity Probability via Logistic Regression
    vec = TFIDF_VECTORIZER.transform([preprocessed_str])
    prob_toxic = float(TOXIC_CLASSIFIER.predict_proba(vec)[0][1])

    # Topic 1 & 2: Tokenization & POS Tagging
    raw_tokens = word_tokenize(raw_text)
    pos_tagged = nltk.pos_tag(raw_tokens)

    # Dual-Trigger Detection: Check lexicon presence
    lexicon_hit = False
    lexicon_matches = []
    for word, tag in pos_tagged:
        lw = word.lower()
        if lw in DE_ESCALATION_LEXICON:
            lexicon_hit = True
            lexicon_matches.append((word, tag))

    is_toxic = (prob_toxic >= 0.50) or lexicon_hit
    if lexicon_hit and prob_toxic < 0.50:
        prob_toxic = 0.88  # calibrated high confidence trigger

    # Topic 3: Named Entity Recognition
    doc = NLP_SPACY(raw_text)
    ner_targets = [[ent.text, ent.label_] for ent in doc.ents]

    # Tier Routing & Text Reconstruction
    action_taken = "clean_pass"
    final_message = raw_text
    transformations = []

    # Generate both tier representations for side-by-side inspector
    free_tokens = []
    premium_tokens = []

    for word, tag in pos_tagged:
        lw = word.lower()
        if lw in DE_ESCALATION_LEXICON:
            # Free tier: beep mask
            free_tokens.append("[BEEP]")

            # Premium tier: POS-aware substitution
            pos_prefix = tag[:2].upper()
            replacement = DE_ESCALATION_LEXICON[lw].get(
                pos_prefix, DE_ESCALATION_LEXICON[lw].get("DEFAULT", lw)
            )
            if word.istitle():
                replacement = replacement.capitalize()
            premium_tokens.append(replacement)

            transformations.append({
                "original": word,
                "pos_tag": tag,
                "pos_desc": POS_DESCRIPTIONS.get(tag, "Word"),
                "replacement": replacement,
                "free_replacement": "[BEEP]"
            })
        else:
            free_tokens.append(word)
            premium_tokens.append(word)

    free_masked = re.sub(r'\s+([?.!,";:])', r"\1", " ".join(free_tokens))
    premium_de_escalated = re.sub(r'\s+([?.!,";:])', r"\1", " ".join(premium_tokens))

    if is_toxic:
        if user_tier == "free":
            action_taken = "free_beep_masked"
            final_message = free_masked
        else:
            action_taken = "premium_de_escalated"
            final_message = premium_de_escalated

    compute_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    return {
        "sender": sender,
        "original_message": raw_text,
        "final_message": final_message,
        "free_masked_message": free_masked,
        "premium_de_escalated_message": premium_de_escalated,
        "is_toxic": is_toxic,
        "toxicity_score": round(prob_toxic, 4),
        "tier_applied": user_tier,
        "action_taken": action_taken,
        "transformations": transformations,
        "pos_tags": [[w, t, POS_DESCRIPTIONS.get(t, t)] for w, t in pos_tagged],
        "ner_targets": ner_targets,
        "preprocessing": {
            "cleaned": stripped_text.strip(),
            "stemmed": preprocessed_str,
            "tokens_stemmed": tokens_stemmed,
        },
        "server_compute_ms": compute_ms,
    }

# ---------------------------------------------------------
# HTTP REST Endpoints (LATENCY RULE #3: Cold-Start Warmup)
# ---------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "status": "awake",
        "message": "NLP Engine Ready in RAM",
        "uptime_seconds": round(time.time() - SERVER_START_TIME, 1),
        "total_processed": TOTAL_MESSAGES_PROCESSED
    }), 200

@app.route("/api/test", methods=["POST"])
@app.route("/api/analyze", methods=["POST"])
def api_test():
    data = request.get_json(force=True) or {}
    sender = data.get("sender", "User A")
    message = data.get("message", "")
    tier = data.get("tier", "premium")

    if not message.strip():
        return jsonify({"error": "Message cannot be empty"}), 400

    result = process_message_pipeline(message, user_tier=tier, sender=sender)
    return jsonify(result), 200

@app.route("/api/lexicon", methods=["GET"])
def api_lexicon():
    return jsonify({
        "lexicon": DE_ESCALATION_LEXICON,
        "total_rules": len(DE_ESCALATION_LEXICON)
    }), 200

@app.route("/api/parse-tree", methods=["POST"])
def api_parse_tree():
    data = request.get_json(force=True) or {}
    sentence = data.get("sentence", "service is garbage")
    tokens = [w.lower() for w in sentence.split() if w]

    try:
        trees = list(PARSER_TOPIC7.parse(tokens))
        trees_str = [str(t) for t in trees]
        return jsonify({
            "sentence": sentence,
            "tokens": tokens,
            "trees": trees_str,
            "parsed": len(trees) > 0
        }), 200
    except Exception:
        return jsonify({
            "sentence": sentence,
            "tokens": tokens,
            "trees": [],
            "parsed": False,
            "note": "Sentence words not in demonstration grammar subset. Default sample: 'service is garbage'."
        }), 200

@app.route("/api/stats", methods=["GET"])
def api_stats():
    return jsonify({
        "status": "healthy",
        "models_in_ram": True,
        "engine": "Scikit-Learn + NLTK + spaCy",
        "uptime_seconds": round(time.time() - SERVER_START_TIME, 1),
        "messages_processed": TOTAL_MESSAGES_PROCESSED
    }), 200

# ---------------------------------------------------------
# WebSocket Event Handlers (LATENCY RULE #2)
# ---------------------------------------------------------
@socketio.on("connect")
def handle_connect():
    emit("connection_ack", {"status": "connected", "server": "SafeChat-NLP-Engine"})

@socketio.on("send_message")
def handle_send_message(data):
    if not isinstance(data, dict):
        return
    sender = data.get("sender", "User A")
    raw_message = data.get("message", "")
    tier = data.get("tier", "premium")

    if not raw_message.strip():
        return

    result = process_message_pipeline(raw_message, user_tier=tier, sender=sender)
    emit("receive_message", result, broadcast=True)

@socketio.on("typing")
def handle_typing(data):
    if isinstance(data, dict):
        emit("user_typing", data, broadcast=True, include_self=False)

@socketio.on("clear_chat")
def handle_clear_chat():
    emit("chat_cleared", {}, broadcast=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"[SafeChat Server] Starting on port {port}...")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
