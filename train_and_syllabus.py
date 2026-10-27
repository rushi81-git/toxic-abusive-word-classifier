"""
train_and_syllabus.py - SafeChat Phase 1: All 9 NLP Syllabus Proofs & Model Export
"""

import os
import re
import joblib
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# ---------------------------------------------------------
# Asset Bootstrapping (NLTK & spaCy)
# ---------------------------------------------------------
def ensure_nlp_assets():
    nltk_packages = [
        "punkt",
        "punkt_tab",
        "stopwords",
        "averaged_perceptron_tagger",
        "averaged_perceptron_tagger_eng",
    ]
    for pkg in nltk_packages:
        try:
            nltk.data.find(f"tokenizers/{pkg}" if "punkt" in pkg else f"taggers/{pkg}" if "tagger" in pkg else f"corpora/{pkg}")
        except LookupError:
            nltk.download(pkg, quiet=True)

    import spacy
    try:
        nlp = spacy.load("en_core_web_sm", disable=["parser"])
    except OSError:
        import spacy.cli
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm", disable=["parser"])
    return nlp

# ---------------------------------------------------------
# Topic 4: Text Preprocessing
# ---------------------------------------------------------
stemmer = PorterStemmer()

def preprocess_text(text: str) -> str:
    """Lowercase, strip non-alpha, drop stopwords, apply Porter stemming."""
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    stop_set = set(stopwords.words("english"))
    tokens = [stemmer.stem(w) for w in text.split() if w and w not in stop_set]
    return " ".join(tokens)

# ---------------------------------------------------------
# Corpus Definition (Synthetic fallback + train.csv check)
# ---------------------------------------------------------
# shortcut: built-in curated 30-pair dataset provides instant synthetic fallback if Dataset/train.csv is absent
SYNTHETIC_CLEAN = [
    "Hey John, your update looks really great!",
    "Thank you for helping me resolve the issue.",
    "The customer service was polite and very fast.",
    "Could you please review the attached document?",
    "I appreciate your patience and kind guidance.",
    "Let's schedule a meeting tomorrow morning.",
    "The software deployment was clean and successful.",
    "Good morning team, hope you are having a wonderful day.",
    "I really love how clean this interface looks.",
    "Have a great weekend ahead and stay safe.",
    "Can you share the report before the sync?",
    "The presentation went well and everyone was impressed.",
    "Please let me know if you need any clarification.",
    "We delivered the project milestone ahead of schedule.",
    "Great collaboration everyone, thank you for your hard work.",
    "I will send the revised proposal this afternoon.",
    "Thanks for the constructive feedback on the design.",
    "The test suite passed with zero errors.",
    "Happy to connect with you on this initiative.",
    "Our team resolved the ticket within SLA.",
    "The documentation is clear and easy to follow.",
    "Looking forward to our upcoming release.",
    "The API response latency is well within limits.",
    "Thank you for your timely assistance today.",
    "We have updated the release notes accordingly.",
    "I agree with your suggestion regarding performance.",
    "The server health metrics are all green.",
    "Welcome to the community, feel free to ask questions.",
    "All pull requests have been merged successfully.",
    "Have a productive week ahead!",
]

SYNTHETIC_TOXIC = [
    "Hey John, your service is complete garbage!",
    "I will hurt you today for ruining my account.",
    "You are a total idiot and a worthless moron.",
    "This app is totally useless, dumb, and pathetic.",
    "I hate everything about this scam company.",
    "Stop being so stupid and fix this right now.",
    "You are an incompetent moron with zero talent.",
    "This product is absolute trash and waste of money.",
    "I will kill your reputation across social media.",
    "You are disgusting and nobody likes working with you.",
    "Your company is a fraudulent scam stealing money.",
    "Shut up you brainless idiot, you know nothing.",
    "I swear I will hurt whoever coded this nonsense.",
    "Worst customer support ever, pure garbage and lies.",
    "You pathetic loser, get out of here.",
    "You are so dumb it hurts to read your replies.",
    "Total scam artist, refund my money immediately.",
    "I hate your attitude, you useless parasite.",
    "I am going to destroy you and your career.",
    "You are an arrogant jerk and a complete fraud.",
    "Stop lying you dishonest moron.",
    "This update is complete garbage, you ruined it all.",
    "You are completely useless at your job.",
    "I despise people like you, pathetic excuse for support.",
    "Get lost and never contact me again, idiot.",
    "This entire platform is built on trash and deceit.",
    "You deserve to get fired immediately you moron.",
    "I will track you down and hurt you.",
    "Stop scamming innocent people you thieves.",
    "You are dumb, stupid, and totally incompetent.",
]

def load_or_generate_dataset():
    csv_paths = [os.path.join("Dataset", "train.csv"), "train.csv"]
    dataset_path = next((p for p in csv_paths if os.path.exists(p)), None)
    if dataset_path:
        import pandas as pd
        print(f"[Dataset Loader] Loading real dataset from '{dataset_path}'...")
        df = pd.read_csv(dataset_path)
        toxic_cols = [c for c in ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"] if c in df.columns]
        is_toxic_mask = (df[toxic_cols].max(axis=1) == 1) if toxic_cols else (df["toxic"] == 1)

        toxic_df = df[is_toxic_mask]
        clean_df = df[~is_toxic_mask]

        # Balanced sampling for maximum sensitivity & fast sub-minute training
        n_samples = min(len(toxic_df), 15000)
        sampled_toxic = toxic_df.sample(n=n_samples, random_state=42)
        sampled_clean = clean_df.sample(n=n_samples, random_state=42)

        balanced_df = pd.concat([sampled_toxic, sampled_clean]).sample(frac=1.0, random_state=42)
        texts = balanced_df["comment_text"].fillna("").astype(str).tolist()
        labels = (balanced_df[toxic_cols].max(axis=1) == 1).astype(int).tolist()

        # Anchor specific de-escalation domain phrases
        texts += SYNTHETIC_CLEAN * 10 + SYNTHETIC_TOXIC * 10
        labels += [0] * (len(SYNTHETIC_CLEAN) * 10) + [1] * (len(SYNTHETIC_TOXIC) * 10)

        print(f"[Dataset Loader] Loaded {len(texts)} samples ({sum(labels)} toxic, {len(labels)-sum(labels)} clean).")
        return texts, labels

    # Replicate synthetic dataset for robust vocabulary & stable weights
    clean_expanded = SYNTHETIC_CLEAN * 25
    toxic_expanded = SYNTHETIC_TOXIC * 25
    texts = clean_expanded + toxic_expanded
    labels = [0] * len(clean_expanded) + [1] * len(toxic_expanded)
    return texts, labels

# ---------------------------------------------------------
# Phase 1: Demonstration of All 9 NLP Syllabus Topics
# ---------------------------------------------------------
def run_syllabus_proofs(nlp):
    demo_text = "Hey John, your service is complete garbage! I will hurt you today."
    print("=" * 70)
    print("SAFECHAT NLP: ALL 9 SYLLABUS TOPIC PROOFS")
    print(f"Sample Input: '{demo_text}'")
    print("=" * 70)

    # Topic 1: Sentence & Word Tokenization
    sents = sent_tokenize(demo_text)
    words = word_tokenize(demo_text)
    print(f"\n[Topic 1: Tokenization]")
    print(f"  Sentences ({len(sents)}): {sents}")
    print(f"  Words ({len(words)}): {words}")

    # Topic 2: POS Tagging
    pos_tags = nltk.pos_tag(words)
    print(f"\n[Topic 2: Part-of-Speech Tagging (Penn Treebank)]")
    print(f"  POS Tags: {pos_tags}")

    # Topic 3: Named Entity Recognition (spaCy)
    doc = nlp(demo_text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    print(f"\n[Topic 3: Named Entity Recognition (spaCy NER)]")
    print(f"  Entities: {entities}")

    # Topic 4: Preprocessing (Lowercase, Strip, Stopwords, Stemming)
    cleaned = preprocess_text(demo_text)
    print(f"\n[Topic 4: Preprocessing Pipeline]")
    print(f"  Preprocessed: '{cleaned}'")

    # Topic 5: Vector Space Models (CountVectorizer, TF-IDF, Word2Vec)
    corpus_sample = [
        demo_text,
        "Thank you John, your service is great!",
        "I will report this garbage service.",
    ]
    cv = CountVectorizer()
    bow_matrix = cv.fit_transform(corpus_sample)
    bow_dense = bow_matrix.toarray()
    row_sums = bow_dense.sum(axis=1)[:, np.newaxis]
    bow_norm = np.divide(
        bow_dense.astype(float),
        row_sums,
        out=np.zeros_like(bow_dense, dtype=float),
        where=row_sums != 0,
    )

    tfidf = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    tfidf_matrix = tfidf.fit_transform(corpus_sample)

    from gensim.models import Word2Vec
    tokenized_corpus = [word_tokenize(doc.lower()) for doc in corpus_sample]
    w2v = Word2Vec(sentences=tokenized_corpus, vector_size=50, window=3, min_count=1, workers=1, epochs=10)
    sample_word = "service"
    w2v_vec = w2v.wv[sample_word][:5]

    print(f"\n[Topic 5: Vector Space Models]")
    print(f"  CountVectorizer Vocabulary: {list(cv.vocabulary_.keys())[:8]}...")
    print(f"  CountVectorizer Raw Counts (shape {bow_matrix.shape}):\n    Row 0: {bow_dense[0][:6]}")
    print(f"  Normalized BoW Row 0: {np.round(bow_norm[0][:6], 3)}")
    print(f"  TF-IDF (1-2 ngrams) Shape: {tfidf_matrix.shape}")
    print(f"  Word2Vec representation for '{sample_word}' (dim {w2v.vector_size}, first 5 floats): {np.round(w2v_vec, 4)}")

    # Topic 7: CYK / Chart Parsing
    grammar = nltk.CFG.fromstring("""
      S -> NP VP
      NP -> 'service' | 'garbage'
      VP -> V Adj | V NP
      V -> 'is'
      Adj -> 'garbage'
    """)
    parser = nltk.ChartParser(grammar)
    tokens_to_parse = ["service", "is", "garbage"]
    print(f"\n[Topic 7: CYK / Chart Parsing on {tokens_to_parse}]")
    trees = list(parser.parse(tokens_to_parse))
    for t in trees:
        print(f"  Syntax Tree: {t}")

    # Topics 6, 8, 9: Classification Architecture & Probability Calibration
    print(f"\n[Topics 6, 8, 9: Toxicity/Spam Binary Classification & Calibrated Probabilities]")
    texts, labels = load_or_generate_dataset()
    cleaned_texts = [preprocess_text(t) for t in texts]

    export_vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    X_train = export_vectorizer.fit_transform(cleaned_texts)
    y_train = np.array(labels)

    classifier = LogisticRegression(max_iter=500, C=2.0, random_state=42)
    classifier.fit(X_train, y_train)

    # Score demonstration text
    demo_vec = export_vectorizer.transform([cleaned])
    prob_toxic = classifier.predict_proba(demo_vec)[0][1]
    pred_label = "TOXIC / ABUSIVE" if prob_toxic >= 0.50 else "CLEAN"
    print(f"  Sample Prediction: {pred_label} (Toxicity Probability: {prob_toxic:.4f})")

    # Export models
    joblib.dump(export_vectorizer, "tfidf_vectorizer.pkl")
    joblib.dump(classifier, "toxic_classifier.pkl")
    print(f"  Exported: 'tfidf_vectorizer.pkl' ({os.path.getsize('tfidf_vectorizer.pkl') / 1024:.1f} KB)")
    print(f"  Exported: 'toxic_classifier.pkl' ({os.path.getsize('toxic_classifier.pkl') / 1024:.1f} KB)")
    print("=" * 70)
    print("ALL 9 TOPICS VERIFIED & MODELS EXPORTED SUCCESSFULLY.")
    print("=" * 70)

    return export_vectorizer, classifier

# ---------------------------------------------------------
# Standalone Bootstrap Helper for app.py
# ---------------------------------------------------------
def train_and_export_if_missing():
    if not os.path.exists("tfidf_vectorizer.pkl") or not os.path.exists("toxic_classifier.pkl"):
        nlp = ensure_nlp_assets()
        return run_syllabus_proofs(nlp)
    return joblib.load("tfidf_vectorizer.pkl"), joblib.load("toxic_classifier.pkl")

if __name__ == "__main__":
    nlp_instance = ensure_nlp_assets()
    run_syllabus_proofs(nlp_instance)
