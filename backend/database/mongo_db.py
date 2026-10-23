import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import MONGODB_URI, MONGODB_DB_NAME

class MongoDBManager:
    """
    MongoDB client and repository for Member 6.
    Handles users, reports, analyses, and media metadata.
    Provides connection pooling and connection health checks.
    """

    def __init__(self):
        self._client: Optional[pymongo.MongoClient] = None
        self._db = None
        self._is_available = False
        self._init_connection()

    def _init_connection(self):
        try:
            # 2 second server selection timeout to avoid blocking if local mongod is offline
            self._client = pymongo.MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                maxPoolSize=50
            )
            # Force server check
            self._client.admin.command('ping')
            self._db = self._client[MONGODB_DB_NAME]
            self._is_available = True
            self._setup_indexes()
            print(f"[MongoDB] Connected successfully to database '{MONGODB_DB_NAME}'.")
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            self._is_available = False
            self._client = None
            self._db = None
            print(f"[MongoDB] Notice: MongoDB not reachable ({e}). Gracefully falling back to SQLite.")

    def _setup_indexes(self):
        if not self._is_available or self._db is None:
            return
        try:
            self._db.users.create_index("email", unique=True)
            self._db.users.create_index("id", unique=True)
            self._db.reports.create_index("id", unique=True)
            self._db.reports.create_index([("created_at", pymongo.DESCENDING)])
            self._db.reports.create_index("type")
        except Exception as e:
            print(f"[MongoDB] Warning creating indexes: {e}")

    @property
    def is_connected(self) -> bool:
        return self._is_available and self._db is not None

    # Reports collection methods
    def save_report(
        self,
        report_id: str,
        report_type: str,
        target: str,
        status: str,
        score: Optional[float],
        verdict: Optional[str],
        summary: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self.is_connected:
            raise ConnectionError("MongoDB is offline")
        
        created_at = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": report_id,
            "type": report_type,
            "target": target,
            "status": status,
            "score": score,
            "verdict": verdict,
            "summary": summary,
            "data": data,
            "created_at": created_at
        }
        self._db.reports.update_one({"id": report_id}, {"$set": doc}, upsert=True)
        return doc

    def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            return None
        doc = self._db.reports.find_one({"id": report_id}, {"_id": 0})
        return doc

    def list_reports(self, limit: int = 50, report_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_connected:
            return []
        query = {}
        if report_type:
            query["type"] = report_type
        cursor = self._db.reports.find(query, {"_id": 0}).sort("created_at", pymongo.DESCENDING).limit(limit)
        return list(cursor)

    def delete_report(self, report_id: str) -> bool:
        if not self.is_connected:
            return False
        res = self._db.reports.delete_one({"id": report_id})
        return res.deleted_count > 0

    # Users collection methods
    def create_user(self, user_doc: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_connected:
            raise ConnectionError("MongoDB is offline")
        doc_copy = dict(user_doc)
        self._db.users.insert_one(doc_copy)
        doc_copy.pop("_id", None)
        return doc_copy

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            return None
        doc = self._db.users.find_one({"email": email.strip().lower()}, {"_id": 0})
        return doc

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            return None
        doc = self._db.users.find_one({"id": user_id}, {"_id": 0})
        return doc

    def update_user(self, user_id: str, update_fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            return None
        self._db.users.update_one({"id": user_id}, {"$set": update_fields})
        return self.get_user_by_id(user_id)

mongo_manager = MongoDBManager()
