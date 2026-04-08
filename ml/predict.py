"""
predict.py
==========
Prediction module for Fake News Detection.

Loads saved model and preprocessor, provides prediction functions
that return fake/real label, confidence score, and credibility rating.

Usage:
  # As a script:
  python predict.py "This is some news article text to check"
  
  # As a module:
  from predict import FakeNewsPredictor
  predictor = FakeNewsPredictor()
  result = predictor.predict("Some news text")
"""

import os
import sys
import json
import argparse
import numpy as np
import joblib
from typing import Dict, List, Optional, Union

from preprocessor import TextPreprocessor


# ─── Credibility Score Mapping ────────────────────────────────────────────────
CREDIBILITY_LEVELS = {
    (80, 100): {"level": "Highly Credible", "emoji": "🟢", "color": "#22c55e"},
    (60, 79):  {"level": "Likely Credible", "emoji": "🟡", "color": "#84cc16"},
    (40, 59):  {"level": "Uncertain", "emoji": "🟠", "color": "#f59e0b"},
    (20, 39):  {"level": "Likely Fake", "emoji": "🔴", "color": "#ef4444"},
    (0, 19):   {"level": "Highly Suspicious", "emoji": "⛔", "color": "#dc2626"},
}


class FakeNewsPredictor:
    """
    Production-ready predictor for fake news detection.
    
    Loads saved model and preprocessor, provides prediction with
    confidence scores, credibility ratings, and explanations.
    """
    
    def __init__(self, model_path: str = "models/fake_news_model.joblib",
                 preprocessor_path: str = "models/preprocessor.joblib"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at: {model_path}\n"
                "Run 'python train.py' first to train the model."
            )
        if not os.path.exists(preprocessor_path):
            raise FileNotFoundError(
                f"Preprocessor not found at: {preprocessor_path}\n"
                "Run 'python train.py' first to train the model."
            )
        
        print(f"Loading model from: {model_path}")
        self.model = joblib.load(model_path)
        
        print(f"Loading preprocessor from: {preprocessor_path}")
        self.preprocessor = TextPreprocessor.load(preprocessor_path)
        
        self.model_path = model_path
        print("Predictor ready!")
    
    def predict(self, text: str) -> Dict:
        """
        Predict whether the given text is fake or real news.
        
        The credibility scoring uses a multi-factor approach:
        1. Model probability (primary factor)
        2. Text quality signals (length, punctuation patterns)
        3. Linguistic red flags (all-caps, exclamation marks, etc.)
        """
        if not text or not text.strip():
            return {
                "prediction": "UNKNOWN",
                "confidence": 0.0,
                "credibility_score": 50,
                "credibility_level": "Uncertain",
                "credibility_color": "#f59e0b",
                "fake_probability": 50.0,
                "real_probability": 50.0,
                "text_length": 0,
                "suspicious_words": [],
                "error": "Empty text provided"
            }
        
        # Preprocess and vectorize
        X = self.preprocessor.transform([text])
        
        # Get prediction
        prediction = self.model.predict(X)[0]
        label = "FAKE" if prediction == 1 else "REAL"
        
        # Get probabilities
        if hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(X)[0]
            confidence = float(max(probabilities)) * 100
            fake_probability = float(probabilities[1]) * 100
            real_probability = float(probabilities[0]) * 100
        elif hasattr(self.model, 'decision_function'):
            decision = float(self.model.decision_function(X)[0])
            confidence = min(abs(decision) * 20, 100)
            fake_probability = confidence if prediction == 1 else 100 - confidence
            real_probability = 100 - fake_probability
        else:
            confidence = 75.0
            fake_probability = 75.0 if prediction == 1 else 25.0
            real_probability = 100 - fake_probability
        
        # ── Advanced Credibility Scoring ──────────────────────────────
        # Start with model's real probability as base
        base_credibility = real_probability
        
        # Analyze text for red flags
        text_signals = self._analyze_text_signals(text)
        
        # Adjust credibility based on text signals
        signal_adjustment = 0
        
        # Penalize sensationalist patterns
        if text_signals["caps_ratio"] > 0.3:
            signal_adjustment -= 15  # Lots of caps = suspicious
        elif text_signals["caps_ratio"] > 0.15:
            signal_adjustment -= 8
        
        if text_signals["exclamation_count"] > 2:
            signal_adjustment -= 10  # Multiple exclamation marks
        elif text_signals["exclamation_count"] > 0:
            signal_adjustment -= 3
        
        if text_signals["has_clickbait"]:
            signal_adjustment -= 20  # Clickbait phrases detected
        
        if text_signals["has_urgency"]:
            signal_adjustment -= 12  # Urgency language
        
        if text_signals["has_conspiracy"]:
            signal_adjustment -= 20  # Conspiracy language
        
        # Reward credible patterns
        if text_signals["has_sources"]:
            signal_adjustment += 10  # Cites sources
        
        if text_signals["has_data"]:
            signal_adjustment += 8   # Contains data/statistics
        
        if text_signals["word_count"] > 200:
            signal_adjustment += 5   # Longer articles tend to be more credible
        elif text_signals["word_count"] < 30:
            signal_adjustment -= 5   # Very short = suspicious
        
        # Calculate final credibility score
        credibility_score = base_credibility + signal_adjustment
        credibility_score = max(0, min(100, round(credibility_score)))
        
        # Get credibility level
        credibility_info = self._get_credibility_level(credibility_score)
        
        # Get suspicious words
        suspicious_words = self._get_important_words(text, prediction)
        
        result = {
            "prediction": label,
            "confidence": round(confidence, 2),
            "credibility_score": credibility_score,
            "credibility_level": credibility_info["level"],
            "credibility_emoji": credibility_info["emoji"],
            "credibility_color": credibility_info["color"],
            "fake_probability": round(fake_probability, 2),
            "real_probability": round(real_probability, 2),
            "text_length": len(text),
            "suspicious_words": suspicious_words,
            "text_signals": text_signals,
        }
        
        return result
    
    def _analyze_text_signals(self, text: str) -> Dict:
        """Analyze text for credibility signals and red flags."""
        words = text.split()
        word_count = len(words)
        
        # Caps analysis
        caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
        caps_ratio = caps_words / max(word_count, 1)
        
        # Punctuation
        exclamation_count = text.count('!')
        question_count = text.count('?')
        
        # Red flag phrases
        text_lower = text.lower()
        
        clickbait_phrases = [
            "you won't believe", "shocking", "breaking:", "exposed",
            "they don't want you to know", "share before", "must see",
            "what they're hiding", "the truth about", "wake up",
            "you need to see this", "this will blow your mind",
            "doctors hate this", "one weird trick",
        ]
        has_clickbait = any(phrase in text_lower for phrase in clickbait_phrases)
        
        urgency_phrases = [
            "share now", "act now", "before it's too late",
            "share before they delete", "going viral", "spread the word",
            "don't ignore", "must read", "urgent",
        ]
        has_urgency = any(phrase in text_lower for phrase in urgency_phrases)
        
        conspiracy_phrases = [
            "illuminati", "new world order", "deep state", "cover-up",
            "big pharma", "they are hiding", "secret agenda",
            "mind control", "chemtrails", "microchip", "government hiding",
            "mainstream media won't", "suppressed", "silenced",
        ]
        has_conspiracy = any(phrase in text_lower for phrase in conspiracy_phrases)
        
        # Credible patterns
        source_phrases = [
            "according to", "reuters", "associated press", "study published",
            "research shows", "data from", "peer-reviewed",
            "official statement", "press release", "scientists found",
            "university of", "journal of", "published in",
        ]
        has_sources = any(phrase in text_lower for phrase in source_phrases)
        
        data_phrases = [
            "percent", "%", "million", "billion", "statistics",
            "data", "survey", "poll", "study", "research",
            "findings", "results show", "evidence",
        ]
        has_data = any(phrase in text_lower for phrase in data_phrases)
        
        return {
            "word_count": word_count,
            "caps_ratio": round(caps_ratio, 3),
            "exclamation_count": exclamation_count,
            "question_count": question_count,
            "has_clickbait": has_clickbait,
            "has_urgency": has_urgency,
            "has_conspiracy": has_conspiracy,
            "has_sources": has_sources,
            "has_data": has_data,
        }
    
    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """Predict for multiple texts."""
        return [self.predict(text) for text in texts]
    
    def _get_credibility_level(self, score: int) -> Dict:
        """Map credibility score to human-readable level."""
        for (low, high), info in CREDIBILITY_LEVELS.items():
            if low <= score <= high:
                return info
        return {"level": "Unknown", "emoji": "?", "color": "#6b7280"}
    
    def _get_important_words(self, text: str, prediction: int, top_n: int = 10) -> List[Dict]:
        """Identify the most important words contributing to the prediction."""
        if not hasattr(self.model, 'coef_'):
            return []
        
        try:
            X = self.preprocessor.transform([text])
            feature_names = self.preprocessor.get_feature_names()
            coefficients = self.model.coef_[0]
            
            nonzero_indices = X.nonzero()[1]
            
            if len(nonzero_indices) == 0:
                return []
            
            word_scores = []
            for idx in nonzero_indices:
                tfidf_val = float(X[0, idx])
                coef_val = float(coefficients[idx])
                importance = tfidf_val * coef_val
                word_scores.append({
                    "word": feature_names[idx],
                    "importance": round(abs(importance), 4),
                    "direction": "fake" if coef_val > 0 else "real",
                    "tfidf_score": round(tfidf_val, 4),
                })
            
            word_scores.sort(key=lambda x: x['importance'], reverse=True)
            return word_scores[:top_n]
        
        except Exception as e:
            print(f"  Warning: Could not extract important words: {e}")
            return []
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        info = {
            "model_type": type(self.model).__name__,
            "model_path": self.model_path,
            "features_count": len(self.preprocessor.get_feature_names()) if self.preprocessor.is_fitted else 0,
        }
        
        if hasattr(self.model, 'n_features_in_'):
            info['n_features'] = int(self.model.n_features_in_)
        if hasattr(self.model, 'classes_'):
            info['classes'] = self.model.classes_.tolist()
        
        return info


def main():
    """CLI entry point for predictions."""
    parser = argparse.ArgumentParser(description="Fake News Prediction")
    parser.add_argument("text", nargs="?", type=str, default=None,
                        help="Text to analyze (omit for interactive mode)")
    parser.add_argument("--model", type=str, default="models/fake_news_model.joblib")
    parser.add_argument("--preprocessor", type=str, default="models/preprocessor.joblib")
    parser.add_argument("--json", action="store_true")
    
    args = parser.parse_args()
    
    if args.text is None:
        print("Usage: python predict.py 'text to check' --json")
        return
    
    predictor = FakeNewsPredictor(model_path=args.model, preprocessor_path=args.preprocessor)
    result = predictor.predict(args.text)
    
    if args.json:
        # Remove text_signals from JSON output for cleanliness
        result.pop("text_signals", None)
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{result['credibility_emoji']} {result['prediction']} "
              f"(Confidence: {result['confidence']:.1f}%, "
              f"Credibility: {result['credibility_score']}/100)")


if __name__ == "__main__":
    main()
