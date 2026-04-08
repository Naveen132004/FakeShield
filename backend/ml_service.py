"""
ml_service.py
=============
ML prediction service that wraps the trained model.
Provides a clean interface for the API to use.
"""

import os
import sys
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

# Add ML module to path
ML_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml")
if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)

from predict import FakeNewsPredictor


class MLService:
    """
    Singleton service for ML predictions.
    
    Loads the model once and provides prediction methods
    for use by the API endpoints.
    """
    
    _instance = None
    _predictor = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, model_path: str, preprocessor_path: str):
        """Load the ML model and preprocessor."""
        if self._predictor is not None:
            return  # Already initialized
        
        try:
            self._predictor = FakeNewsPredictor(
                model_path=model_path,
                preprocessor_path=preprocessor_path
            )
            print("[ML Service] Model loaded successfully!")
        except Exception as e:
            print(f"[ML Service] ERROR loading model: {e}")
            raise
    
    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._predictor is not None
    
    def predict(self, text: str, source_url: Optional[str] = None) -> Dict:
        """
        Run prediction on text.
        
        Args:
            text: News text to analyze
            source_url: Optional source URL
        
        Returns:
            Prediction result dictionary
        """
        if not self.is_loaded:
            raise RuntimeError("ML model not loaded. Call initialize() first.")
        
        result = self._predictor.predict(text)
        
        # Add metadata
        analysis_id = str(uuid.uuid4())[:8]
        result["analysis_id"] = analysis_id
        result["analyzed_at"] = datetime.utcnow().isoformat()
        result["source_url"] = source_url
        
        # Generate content hash for blockchain
        content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        result["content_hash"] = content_hash
        
        return result
    
    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """Run predictions on multiple texts."""
        return [self.predict(text) for text in texts]
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        if not self.is_loaded:
            return {"loaded": False}
        
        info = self._predictor.get_model_info()
        info["loaded"] = True
        return info


# Singleton instance
ml_service = MLService()
