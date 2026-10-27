#!/usr/bin/env bash
# build.sh - Production build script for SafeChat NLP Cloud Deployment
set -o errexit

echo "==> [1/4] Upgrading pip..."
python -m pip install --upgrade pip

echo "==> [2/4] Installing Python requirements..."
pip install -r requirements.txt

echo "==> [3/4] Pre-downloading spaCy & NLTK linguistic corpora..."
python -m spacy download en_core_web_sm
python -m nltk.downloader punkt punkt_tab stopwords averaged_perceptron_tagger averaged_perceptron_tagger_eng

echo "==> [4/4] Pre-baking TF-IDF vectorizer and logistic regression models..."
python train_and_syllabus.py

echo "==> Build complete. SafeChat NLP is ready for instant RAM pre-loading on boot!"
