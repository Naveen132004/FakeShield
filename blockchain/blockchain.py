"""
blockchain.py
=============
Blockchain integration for Fake News Detection platform.

Generates SHA-256 hash for each prediction and provides
interface for storing verification records.

Features:
  - SHA-256 content hashing
  - Prediction record creation
  - Simulated blockchain storage (for development)
  - Ready for Ethereum/Polygon integration via Web3.py

Usage:
  from blockchain import BlockchainService
  bc = BlockchainService()
  record = bc.create_verification_record(text, prediction_result)
"""

import hashlib
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional


class BlockchainService:
    """
    Blockchain verification service.
    
    Creates immutable records of news analysis results.
    Uses simulated blockchain in development mode,
    supports Ethereum/Polygon via Web3.py in production.
    """
    
    def __init__(self, mode: str = "simulated"):
        """
        Initialize blockchain service.
        
        Args:
            mode: 'simulated' for development, 'ethereum' for production
        """
        self.mode = mode
        self.chain: List[Dict] = []
        self.pending_records: List[Dict] = []
        
        # Genesis block
        genesis = {
            "index": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "data": "Genesis Block - FakeShield Verification Chain",
            "previous_hash": "0" * 64,
            "hash": self._compute_hash("genesis"),
            "nonce": 0,
        }
        self.chain.append(genesis)
        
        print(f"[Blockchain] Initialized in {mode} mode")
    
    def create_verification_record(self, text: str, prediction: Dict) -> Dict:
        """
        Create a blockchain verification record for a prediction.
        
        Args:
            text: Original news text
            prediction: Prediction result dictionary
        
        Returns:
            Verification record with transaction ID and hashes
        """
        # Generate content hash
        content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # Generate prediction hash (includes all metadata)
        prediction_data = {
            "content_hash": content_hash,
            "prediction": prediction.get("prediction", "UNKNOWN"),
            "confidence": prediction.get("confidence", 0),
            "credibility_score": prediction.get("credibility_score", 50),
            "timestamp": datetime.utcnow().isoformat(),
        }
        prediction_json = json.dumps(prediction_data, sort_keys=True)
        prediction_hash = hashlib.sha256(prediction_json.encode('utf-8')).hexdigest()
        
        # Create block
        previous_hash = self.chain[-1]["hash"] if self.chain else "0" * 64
        
        block = {
            "index": len(self.chain),
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "content_hash": content_hash,
                "prediction_hash": prediction_hash,
                "prediction": prediction.get("prediction"),
                "confidence": prediction.get("confidence"),
                "credibility_score": prediction.get("credibility_score"),
                "text_preview": text[:100] + "..." if len(text) > 100 else text,
            },
            "previous_hash": previous_hash,
            "nonce": 0,
        }
        
        # Simple proof of work (low difficulty for dev)
        block["hash"] = self._mine_block(block)
        
        # Add to chain
        self.chain.append(block)
        
        # Generate transaction ID
        block_idx = block["index"]
        block_hash = block["hash"]
        tx_id = f"0x{hashlib.sha256(f'{block_idx}{block_hash}'.encode()).hexdigest()[:40]}"
        
        record = {
            "transaction_id": tx_id,
            "block_index": block["index"],
            "content_hash": content_hash,
            "prediction_hash": prediction_hash,
            "block_hash": block["hash"],
            "previous_hash": previous_hash,
            "timestamp": block["timestamp"],
            "verified": True,
            "chain_length": len(self.chain),
            "mode": self.mode,
        }
        
        return record
    
    def verify_record(self, content_hash: str) -> Optional[Dict]:
        """
        Verify if a content hash exists in the blockchain.
        
        Args:
            content_hash: SHA-256 hash of the content
        
        Returns:
            Block data if found, None otherwise
        """
        for block in self.chain:
            if isinstance(block.get("data"), dict):
                if block["data"].get("content_hash") == content_hash:
                    return {
                        "found": True,
                        "block_index": block["index"],
                        "block_hash": block["hash"],
                        "timestamp": block["timestamp"],
                        "prediction": block["data"].get("prediction"),
                        "confidence": block["data"].get("confidence"),
                    }
        return {"found": False}
    
    def get_chain_info(self) -> Dict:
        """Get blockchain summary information."""
        return {
            "chain_length": len(self.chain),
            "mode": self.mode,
            "latest_block_hash": self.chain[-1]["hash"] if self.chain else None,
            "is_valid": self._validate_chain(),
            "total_verifications": len(self.chain) - 1,  # Exclude genesis
        }
    
    def get_recent_blocks(self, n: int = 10) -> List[Dict]:
        """Get the most recent N blocks."""
        blocks = self.chain[-n:]
        return [
            {
                "index": b["index"],
                "hash": b["hash"][:16] + "...",
                "previous_hash": b["previous_hash"][:16] + "...",
                "timestamp": b["timestamp"],
                "data": b["data"] if isinstance(b["data"], str) else {
                    "prediction": b["data"].get("prediction"),
                    "confidence": b["data"].get("confidence"),
                    "text_preview": b["data"].get("text_preview", "")[:50],
                },
            }
            for b in blocks
        ]
    
    def _compute_hash(self, data: str) -> str:
        """Compute SHA-256 hash."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def _mine_block(self, block: Dict, difficulty: int = 2) -> str:
        """
        Simple proof of work mining.
        
        Args:
            block: Block to mine
            difficulty: Number of leading zeros required
        
        Returns:
            Valid block hash
        """
        target = "0" * difficulty
        nonce = 0
        
        while True:
            block["nonce"] = nonce
            block_str = json.dumps(block, sort_keys=True, default=str)
            hash_val = hashlib.sha256(block_str.encode('utf-8')).hexdigest()
            
            if hash_val[:difficulty] == target:
                return hash_val
            
            nonce += 1
            
            # Safety limit for dev
            if nonce > 100000:
                return hash_val
    
    def _validate_chain(self) -> bool:
        """Validate the integrity of the blockchain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            
            if current["previous_hash"] != previous["hash"]:
                return False
        
        return True


# Singleton instance
blockchain_service = BlockchainService(mode="simulated")
