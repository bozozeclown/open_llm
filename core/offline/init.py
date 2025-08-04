import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pickle

class OfflineManager:
    def __init__(self, storage_path: str = "data/offline"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.cache_db = self.storage_path / "cache.db"
        self.models_dir = self.storage_path / "models"
        self.models_dir.mkdir(exist_ok=True)
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Initialize SQLite cache database"""
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
            """)
    
    def cache_response(self, query: str, response: Dict[str, Any], ttl_hours: int = 24):
        """Cache a response for offline use"""
        key = hashlib.sha256(query.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cache 
                (key, value, created_at, expires_at, access_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                key,
                pickle.dumps(response),
                datetime.now(),
                expires_at,
                0,
                datetime.now()
            ))
    
    def get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        key = hashlib.sha256(query.encode()).hexdigest()
        
        with sqlite3.connect(self.cache_db) as conn:
            cursor = conn.execute("""
                SELECT value, expires_at, access_count 
                FROM cache 
                WHERE key = ? AND expires_at > ?
            """, (key, datetime.now()))
            
            row = cursor.fetchone()
            if row:
                # Update access stats
                conn.execute("""
                    UPDATE cache 
                    SET access_count = access_count + 1, last_accessed = ?
                    WHERE key = ?
                """, (datetime.now(), key))
                
                return pickle.loads(row[0])
        
        return None
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute("DELETE FROM cache WHERE expires_at <= ?", (datetime.now(),))
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with sqlite3.connect(self.cache_db) as conn:
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            expired = conn.execute("SELECT COUNT(*) FROM cache WHERE expires_at <= ?", 
                                 (datetime.now(),)).fetchone()[0]
            
            return {
                "total_entries": total,
                "expired_entries": expired,
                "active_entries": total - expired,
                "storage_path": str(self.storage_path)
            }
    
    def download_model(self, model_name: str, model_url: str):
        """Download a model for offline use"""
        import requests
        
        model_path = self.models_dir / f"{model_name}.pkl"
        
        try:
            response = requests.get(model_url, stream=True)
            response.raise_for_status()
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"Failed to download model {model_name}: {e}")
            return False
    
    def list_local_models(self) -> List[str]:
        """List available local models"""
        return [f.stem for f in self.models_dir.glob("*.pkl")]
    
    def load_local_model(self, model_name: str):
        """Load a local model"""
        model_path = self.models_dir / f"{model_name}.pkl"
        
        if model_path.exists():
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        
        return None