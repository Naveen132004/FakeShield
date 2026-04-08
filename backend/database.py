"""
database.py
===========
Database service for storing analysis history.
Uses in-memory storage as default, with optional MongoDB support.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque


class InMemoryDB:
    """
    In-memory storage for development.
    Can be replaced with MongoDB in production.
    """
    
    def __init__(self, max_history: int = 1000):
        self.history: deque = deque(maxlen=max_history)
        self.stats = {
            "total_analyzed": 0,
            "fake_count": 0,
            "real_count": 0,
            "total_credibility": 0,
        }
    
    async def save_analysis(self, result: Dict) -> str:
        """Save an analysis result and return its ID."""
        record_id = result.get("analysis_id", str(uuid.uuid4())[:8])
        
        record = {
            "id": record_id,
            "text_preview": result.get("source_text", "")[:200],
            "prediction": result.get("prediction", "UNKNOWN"),
            "confidence": result.get("confidence", 0),
            "credibility_score": result.get("credibility_score", 50),
            "credibility_level": result.get("credibility_level", "Unknown"),
            "source_url": result.get("source_url"),
            "content_hash": result.get("content_hash"),
            "analyzed_at": result.get("analyzed_at", datetime.utcnow().isoformat()),
        }
        
        self.history.appendleft(record)
        
        # Update stats
        self.stats["total_analyzed"] += 1
        if record["prediction"] == "FAKE":
            self.stats["fake_count"] += 1
        elif record["prediction"] == "REAL":
            self.stats["real_count"] += 1
        self.stats["total_credibility"] += record["credibility_score"]
        
        return record_id
    
    async def get_history(self, limit: int = 50, offset: int = 0) -> Dict:
        """Get analysis history."""
        items = list(self.history)
        total = len(items)
        paginated = items[offset:offset + limit]
        
        return {
            "total": total,
            "items": paginated,
        }
    
    async def get_stats(self) -> Dict:
        """Get dashboard statistics."""
        total = self.stats["total_analyzed"]
        avg_credibility = (
            self.stats["total_credibility"] / total if total > 0 else 0
        )
        
        recent = list(self.history)[:10]
        
        return {
            "total_analyzed": total,
            "fake_count": self.stats["fake_count"],
            "real_count": self.stats["real_count"],
            "average_credibility": round(avg_credibility, 1),
            "recent_analyses": recent,
        }
    
    async def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict]:
        """Get a specific analysis by ID."""
        for record in self.history:
            if record["id"] == analysis_id:
                return record
        return None


# Singleton instance
db = InMemoryDB()
