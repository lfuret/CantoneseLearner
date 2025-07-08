"""
MongoDB configuration and connection management.
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import streamlit as st
from typing import Optional


class MongoDBManager:
    """Manages MongoDB connections and database operations."""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.database = None
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB."""
        try:
            # Try to connect to MongoDB (local or cloud)
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            
            self.client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test the connection
            self.client.admin.command('ping')
            
            # Use cantonese_learning database
            database_name = os.getenv('MONGODB_DATABASE', 'cantonese_learning')
            self.database = self.client[database_name]
            
            print(f"✅ Connected to MongoDB database: {database_name}")
            
        except ConnectionFailure as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            print("🔄 Falling back to in-memory storage for development")
            self.client = None
            self.database = None
        except Exception as e:
            print(f"❌ MongoDB connection error: {e}")
            print("🔄 Falling back to in-memory storage for development")
            self.client = None
            self.database = None
    
    def is_connected(self) -> bool:
        """Check if MongoDB is connected."""
        return self.client is not None and self.database is not None
    
    def get_collection(self, collection_name: str):
        """Get a MongoDB collection."""
        if not self.is_connected():
            return None
        return self.database[collection_name]
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()


# Global MongoDB manager instance
_mongo_manager = None


def get_mongo_manager() -> MongoDBManager:
    """Get the global MongoDB manager instance."""
    global _mongo_manager
    if _mongo_manager is None:
        _mongo_manager = MongoDBManager()
    return _mongo_manager


def ensure_indexes():
    """Ensure proper indexes are created for performance."""
    mongo = get_mongo_manager()
    
    if not mongo.is_connected():
        return
    
    try:
        # Users collection indexes
        users = mongo.get_collection('users')
        users.create_index("user_id", unique=True)
        users.create_index("username", unique=True)
        
        # Files collection indexes
        files = mongo.get_collection('files')
        files.create_index("file_id", unique=True)
        files.create_index("file_hash")
        files.create_index("uploaded_by")
        files.create_index("accessed_by")
        
        # Learning progress collection indexes
        learning = mongo.get_collection('learning_progress')
        learning.create_index("user_id", unique=True)
        
        print("✅ MongoDB indexes ensured")
        
    except Exception as e:
        print(f"⚠️ Error creating indexes: {e}")