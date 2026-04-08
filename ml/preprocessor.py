"""
preprocessor.py
===============
Text preprocessing pipeline for fake news detection.

Handles:
  - Text cleaning (HTML, URLs, special characters)
  - Tokenization
  - Stopword removal
  - Lemmatization
  - TF-IDF vectorization

Usage:
  from preprocessor import TextPreprocessor
  preprocessor = TextPreprocessor()
  X_tfidf = preprocessor.fit_transform(texts)
"""

import re
import string
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional, Tuple, Union

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split


# ─── Download NLTK resources ─────────────────────────────────────────────────
_NLTK_READY = False

def ensure_nltk_resources():
    """Download required NLTK resources if not present."""
    global _NLTK_READY
    if _NLTK_READY:
        return
    # Download all needed resources (quiet=True suppresses output if already present)
    for resource in ['punkt', 'punkt_tab', 'stopwords', 'wordnet', 'omw-1.4']:
        nltk.download(resource, quiet=True)
    _NLTK_READY = True


# ─── Text Preprocessor ───────────────────────────────────────────────────────
class TextPreprocessor:
    """
    Complete text preprocessing pipeline for fake news detection.
    
    Attributes:
        vectorizer: TF-IDF vectorizer instance
        max_features: Maximum number of TF-IDF features
        ngram_range: N-gram range for TF-IDF
        is_fitted: Whether the preprocessor has been fitted
    """
    
    def __init__(self, max_features: int = 50000, ngram_range: Tuple[int, int] = (1, 2),
                 min_df: int = 2, max_df: float = 0.95):
        """
        Initialize the preprocessor.
        
        Args:
            max_features: Maximum number of TF-IDF features
            ngram_range: Tuple of (min_n, max_n) for n-gram extraction
            min_df: Minimum document frequency for TF-IDF
            max_df: Maximum document frequency for TF-IDF
        """
        ensure_nltk_resources()
        
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_df = max_df
        
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=min_df,
            max_df=max_df,
            sublinear_tf=True,       # Apply sublinear TF scaling (1 + log(tf))
            strip_accents='unicode', # Handle unicode accents
            analyzer='word',
            token_pattern=r'\b[a-zA-Z]{2,}\b',  # Only words with 2+ letters
        )
        
        self.lemmatizer = WordNetLemmatizer()
        
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))
        
        # Add custom stop words common in news articles
        self.stop_words.update([
            'said', 'would', 'could', 'also', 'one', 'two', 'three',
            'new', 'like', 'get', 'make', 'know', 'time', 'year',
            'people', 'way', 'day', 'just', 'may', 'say', 'reuters',
            'ap', 'afp', 'according'
        ])
        
        self.is_fitted = False
    
    def clean_text(self, text: str) -> str:
        """
        Clean raw text by removing noise.
        
        Steps:
          1. Convert to lowercase
          2. Remove HTML tags
          3. Remove URLs
          4. Remove email addresses
          5. Remove special characters and digits
          6. Remove extra whitespace
        
        Args:
            text: Raw text string
        
        Returns:
            Cleaned text string
        """
        if not isinstance(text, str) or len(text.strip()) == 0:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', ' ', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', ' ', text)
        
        # Remove mentions and hashtags (social media)
        text = re.sub(r'[@#]\w+', ' ', text)
        
        # Remove digits
        text = re.sub(r'\d+', ' ', text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _safe_tokenize(self, text: str) -> list:
        """Tokenize text with robust fallback if NLTK punkt fails."""
        try:
            return word_tokenize(text)
        except Exception:
            # Fallback: simple regex-based tokenizer
            return re.findall(r'\b\w+\b', text)

    def tokenize_and_lemmatize(self, text: str) -> str:
        """
        Tokenize text, remove stopwords, and lemmatize.
        
        Args:
            text: Cleaned text string
        
        Returns:
            Processed text string with tokens joined by spaces
        """
        if not text:
            return ""
        
        tokens = self._safe_tokenize(text)
        
        # Remove stopwords and short tokens, then lemmatize
        processed = []
        for token in tokens:
            if (token not in self.stop_words 
                and len(token) > 2 
                and token.isalpha()):
                try:
                    lemma = self.lemmatizer.lemmatize(token)
                except Exception:
                    lemma = token
                processed.append(lemma)
        
        return ' '.join(processed)
    
    def preprocess_text(self, text: str) -> str:
        """
        Full preprocessing pipeline for a single text.
        
        Args:
            text: Raw text string
        
        Returns:
            Fully preprocessed text string
        """
        cleaned = self.clean_text(text)
        processed = self.tokenize_and_lemmatize(cleaned)
        return processed
    
    def preprocess_batch(self, texts: Union[List[str], pd.Series]) -> List[str]:
        """
        Preprocess a batch of texts.
        
        Args:
            texts: List or Series of raw text strings
        
        Returns:
            List of preprocessed text strings
        """
        if isinstance(texts, pd.Series):
            texts = texts.tolist()
        
        processed = []
        total = len(texts)
        for i, text in enumerate(texts):
            if (i + 1) % 500 == 0:
                print(f"  Processing: {i+1}/{total} texts...")
            processed.append(self.preprocess_text(text))
        
        print(f"  ✅ Preprocessed {total} texts")
        return processed
    
    def fit_transform(self, texts: Union[List[str], pd.Series]) -> np.ndarray:
        """
        Preprocess texts, fit TF-IDF vectorizer, and transform.
        
        Args:
            texts: List or Series of raw text strings
        
        Returns:
            TF-IDF feature matrix (sparse)
        """
        print("🔄 Preprocessing texts...")
        processed = self.preprocess_batch(texts)
        
        print("🔄 Fitting TF-IDF vectorizer...")
        X = self.vectorizer.fit_transform(processed)
        self.is_fitted = True
        
        print(f"  ✅ TF-IDF matrix shape: {X.shape}")
        print(f"  📊 Vocabulary size: {len(self.vectorizer.vocabulary_)}")
        
        return X
    
    def transform(self, texts: Union[List[str], pd.Series]) -> np.ndarray:
        """
        Preprocess texts and transform using fitted vectorizer.
        
        Args:
            texts: List or Series of raw text strings
        
        Returns:
            TF-IDF feature matrix (sparse)
        """
        if not self.is_fitted:
            raise RuntimeError("Preprocessor not fitted. Call fit_transform() first.")
        
        processed = self.preprocess_batch(texts)
        X = self.vectorizer.transform(processed)
        
        return X
    
    def get_feature_names(self) -> List[str]:
        """Get the feature names from the fitted vectorizer."""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor not fitted.")
        return self.vectorizer.get_feature_names_out().tolist()
    
    def get_top_features(self, n: int = 20) -> dict:
        """
        Get top N features by IDF score.
        
        Args:
            n: Number of top features to return
        
        Returns:
            Dictionary with feature names and IDF scores
        """
        if not self.is_fitted:
            raise RuntimeError("Preprocessor not fitted.")
        
        feature_names = self.vectorizer.get_feature_names_out()
        idf_scores = self.vectorizer.idf_
        
        sorted_idx = np.argsort(idf_scores)[::-1][:n]
        
        return {
            feature_names[i]: round(float(idf_scores[i]), 4)
            for i in sorted_idx
        }
    
    def save(self, filepath: str):
        """Save the preprocessor (vectorizer + config) to disk."""
        save_data = {
            'vectorizer': self.vectorizer,
            'max_features': self.max_features,
            'ngram_range': self.ngram_range,
            'min_df': self.min_df,
            'max_df': self.max_df,
            'stop_words': self.stop_words,
            'is_fitted': self.is_fitted,
        }
        joblib.dump(save_data, filepath)
        print(f"💾 Preprocessor saved to: {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'TextPreprocessor':
        """Load a saved preprocessor from disk."""
        save_data = joblib.load(filepath)
        
        preprocessor = cls(
            max_features=save_data['max_features'],
            ngram_range=save_data['ngram_range'],
            min_df=save_data['min_df'],
            max_df=save_data['max_df'],
        )
        preprocessor.vectorizer = save_data['vectorizer']
        preprocessor.stop_words = save_data['stop_words']
        preprocessor.is_fitted = save_data['is_fitted']
        
        return preprocessor


def prepare_train_test_data(df: pd.DataFrame, test_size: float = 0.2,
                            random_state: int = 42) -> Tuple:
    """
    Split dataset and prepare TF-IDF features.
    
    Args:
        df: DataFrame with 'text' and 'label' columns
        test_size: Fraction of data for testing
        random_state: Random seed
    
    Returns:
        Tuple of (X_train, X_test, y_train, y_test, preprocessor)
    """
    print("=" * 60)
    print("📐 PREPARING TRAIN/TEST DATA")
    print("=" * 60)
    
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        df['text'], df['label'],
        test_size=test_size,
        random_state=random_state,
        stratify=df['label']
    )
    
    print(f"\n📊 Split: {len(X_train_raw)} train, {len(X_test_raw)} test")
    
    preprocessor = TextPreprocessor()
    
    # Fit on training data only
    X_train = preprocessor.fit_transform(X_train_raw)
    
    # Transform test data
    print("\n🔄 Transforming test data...")
    X_test = preprocessor.transform(X_test_raw)
    
    return X_train, X_test, y_train, y_test, preprocessor


if __name__ == "__main__":
    # Quick test
    preprocessor = TextPreprocessor()
    
    test_texts = [
        "BREAKING: Scientists discover that 5G causes mind control! Big pharma cover-up!",
        "According to Reuters, the Federal Reserve announced a 0.25% rate increase today.",
        "You won't BELIEVE what happened! Click here to see the SHOCKING truth!!!",
    ]
    
    for text in test_texts:
        cleaned = preprocessor.preprocess_text(text)
        print(f"\n📝 Original: {text[:80]}...")
        print(f"   Cleaned:  {cleaned[:80]}...")
