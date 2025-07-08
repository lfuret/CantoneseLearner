"""
MongoDB-based user database with fallback to JSON for development.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
from mongodb_config import get_mongo_manager


class UserDatabase:
    """Manages user authentication and data with MongoDB backend."""
    
    def __init__(self):
        self.mongo = get_mongo_manager()
        
        # Fallback to JSON if MongoDB is not available
        if not self.mongo.is_connected():
            self.json_db_path = "data/users.json"
            self.json_db_dir = os.path.dirname(self.json_db_path)
            self._ensure_json_db_exists()
    
    def _ensure_json_db_exists(self):
        """Ensure JSON database exists (fallback mode)."""
        if not os.path.exists(self.json_db_dir):
            os.makedirs(self.json_db_dir)
        
        if not os.path.exists(self.json_db_path):
            self._save_json_data({})
    
    def _load_json_data(self) -> Dict[str, Any]:
        """Load data from JSON file (fallback mode)."""
        try:
            with open(self.json_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json_data(self, data: Dict[str, Any]):
        """Save data to JSON file (fallback mode)."""
        with open(self.json_db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_user(self, username: str, email: str = None) -> Dict[str, Any]:
        """Create a new user account."""
        user_id = str(uuid.uuid4())[:12]
        user_data = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat(),
            'total_analyses': 0,
            'total_files_analyzed': 0,
            'preferences': {
                'preferred_analysis_type': 'both',
                'min_frequency': 5,
                'max_chars_display': 50,
                'show_chart_type': 'bar'
            },
            'analysis_history': []
        }
        
        if self.mongo.is_connected():
            # MongoDB storage
            try:
                users_collection = self.mongo.get_collection('users')
                users_collection.insert_one(user_data)
                return user_data
            except Exception as e:
                print(f"MongoDB insert error: {e}")
                # Fall back to JSON
                pass
        
        # JSON fallback storage
        data = self._load_json_data()
        data[user_id] = user_data
        self._save_json_data(data)
        return user_data
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        if self.mongo.is_connected():
            try:
                users_collection = self.mongo.get_collection('users')
                user = users_collection.find_one({'username': username})
                if user:
                    user.pop('_id', None)  # Remove MongoDB ObjectId
                return user
            except Exception as e:
                print(f"MongoDB query error: {e}")
                # Fall back to JSON
                pass
        
        # JSON fallback
        data = self._load_json_data()
        for user_data in data.values():
            if user_data.get('username') == username:
                return user_data
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user ID."""
        if self.mongo.is_connected():
            try:
                users_collection = self.mongo.get_collection('users')
                user = users_collection.find_one({'user_id': user_id})
                if user:
                    user.pop('_id', None)  # Remove MongoDB ObjectId
                return user
            except Exception as e:
                print(f"MongoDB query error: {e}")
                # Fall back to JSON
                pass
        
        # JSON fallback
        data = self._load_json_data()
        return data.get(user_id)
    
    def update_last_login(self, user_id: str):
        """Update user's last login time."""
        if self.mongo.is_connected():
            try:
                users_collection = self.mongo.get_collection('users')
                users_collection.update_one(
                    {'user_id': user_id},
                    {'$set': {'last_login': datetime.now().isoformat()}}
                )
                return
            except Exception as e:
                print(f"MongoDB update error: {e}")
                # Fall back to JSON
                pass
        
        # JSON fallback
        data = self._load_json_data()
        if user_id in data:
            data[user_id]['last_login'] = datetime.now().isoformat()
            self._save_json_data(data)
    
    def save_analysis_result(self, user_id: str, analysis_data: Dict[str, Any]):
        """Save analysis result to user's history."""
        analysis_record = {
            'analysis_id': str(uuid.uuid4())[:8],
            'timestamp': datetime.now().isoformat(),
            'filename': analysis_data['filename'],
            'file_size': analysis_data['file_size'],
            'analysis_type': analysis_data['analysis_type'],
            'character_count': analysis_data.get('character_stats', {}).get('total_chars', 0),
            'word_count': analysis_data.get('word_stats', {}).get('total_words', 0),
            'settings_used': analysis_data.get('settings_used', {})
        }
        
        if self.mongo.is_connected():
            try:
                users_collection = self.mongo.get_collection('users')
                # Add to analysis history and update counters
                users_collection.update_one(
                    {'user_id': user_id},
                    {
                        '$push': {'analysis_history': {'$each': [analysis_record], '$slice': -50}},
                        '$inc': {'total_analyses': 1, 'total_files_analyzed': 1}
                    }
                )
                return
            except Exception as e:
                print(f"MongoDB update error: {e}")
                # Fall back to JSON
                pass
        
        # JSON fallback
        data = self._load_json_data()
        if user_id in data:
            user_data = data[user_id]
            user_data['analysis_history'].append(analysis_record)
            # Keep only last 50 analyses
            user_data['analysis_history'] = user_data['analysis_history'][-50:]
            user_data['total_analyses'] = user_data.get('total_analyses', 0) + 1
            user_data['total_files_analyzed'] = user_data.get('total_files_analyzed', 0) + 1
            self._save_json_data(data)
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences."""
        user_data = self.get_user_by_id(user_id)
        if user_data:
            return user_data.get('preferences', {})
        return {}
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update user preferences."""
        if self.mongo.is_connected():
            try:
                users_collection = self.mongo.get_collection('users')
                users_collection.update_one(
                    {'user_id': user_id},
                    {'$set': {'preferences': preferences}}
                )
                return
            except Exception as e:
                print(f"MongoDB update error: {e}")
                # Fall back to JSON
                pass
        
        # JSON fallback
        data = self._load_json_data()
        if user_id in data:
            data[user_id]['preferences'] = preferences
            self._save_json_data(data)
    
    def get_analysis_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's analysis history."""
        user_data = self.get_user_by_id(user_id)
        if user_data:
            history = user_data.get('analysis_history', [])
            return history[-limit:] if limit else history
        return []
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics."""
        user_data = self.get_user_by_id(user_id)
        if user_data:
            return {
                'total_analyses': user_data.get('total_analyses', 0),
                'total_files_analyzed': user_data.get('total_files_analyzed', 0),
                'member_since': user_data.get('created_at', ''),
                'last_login': user_data.get('last_login', '')
            }
        return {}