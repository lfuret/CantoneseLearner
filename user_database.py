"""
User database module for managing user data and progress using JSON-based NoSQL storage.
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid


class UserDatabase:
    """Simple NoSQL database for user management and progress tracking."""
    
    def __init__(self, db_path: str = "data/users.json"):
        """
        Initialize the user database.
        
        Args:
            db_path: Path to the JSON database file
        """
        self.db_path = db_path
        self.db_dir = os.path.dirname(db_path)
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure the database directory and file exist."""
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
        
        if not os.path.exists(self.db_path):
            self._save_data({})
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from the JSON database file."""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_data(self, data: Dict[str, Any]):
        """Save data to the JSON database file."""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _generate_user_id(self, username: str) -> str:
        """Generate a unique user ID based on username."""
        return hashlib.md5(username.encode()).hexdigest()[:12]
    
    def create_user(self, username: str, email: str = "") -> str:
        """
        Create a new user account.
        
        Args:
            username: User's chosen username
            email: User's email address (optional)
            
        Returns:
            User ID string
            
        Raises:
            ValueError: If username already exists
        """
        data = self._load_data()
        user_id = self._generate_user_id(username)
        
        # Check if username already exists
        for existing_user in data.values():
            if existing_user.get('username') == username:
                raise ValueError(f"Username '{username}' already exists")
        
        # Create new user
        user_data = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat(),
            'analysis_history': [],
            'preferences': {
                'preferred_analysis_type': 'both',
                'min_frequency': 1,
                'max_chars_display': 50,
                'show_chart_type': 'bar'
            },
            'statistics': {
                'total_analyses': 0,
                'total_characters_analyzed': 0,
                'total_words_analyzed': 0,
                'files_processed': 0
            }
        }
        
        data[user_id] = user_data
        self._save_data(data)
        
        return user_id
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data by user ID.
        
        Args:
            user_id: User ID to look up
            
        Returns:
            User data dictionary or None if not found
        """
        data = self._load_data()
        return data.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user data by username.
        
        Args:
            username: Username to look up
            
        Returns:
            User data dictionary or None if not found
        """
        data = self._load_data()
        for user_data in data.values():
            if user_data.get('username') == username:
                return user_data
        return None
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp."""
        data = self._load_data()
        if user_id in data:
            data[user_id]['last_login'] = datetime.now().isoformat()
            self._save_data(data)
    
    def save_analysis_result(self, user_id: str, analysis_data: Dict[str, Any]):
        """
        Save analysis result to user's history.
        
        Args:
            user_id: User ID
            analysis_data: Analysis results to save
        """
        data = self._load_data()
        if user_id not in data:
            return False
        
        # Create analysis record
        analysis_record = {
            'analysis_id': str(uuid.uuid4())[:8],
            'timestamp': datetime.now().isoformat(),
            'filename': analysis_data.get('filename', 'Unknown'),
            'file_size': analysis_data.get('file_size', 0),
            'analysis_type': analysis_data.get('analysis_type', 'both'),
            'character_stats': analysis_data.get('character_stats', {}),
            'word_stats': analysis_data.get('word_stats', {}),
            'top_characters': analysis_data.get('top_characters', {}),
            'top_words': analysis_data.get('top_words', {}),
            'settings_used': analysis_data.get('settings_used', {})
        }
        
        # Add to history
        data[user_id]['analysis_history'].append(analysis_record)
        
        # Update statistics
        stats = data[user_id]['statistics']
        stats['total_analyses'] += 1
        stats['files_processed'] += 1
        if 'character_stats' in analysis_data:
            stats['total_characters_analyzed'] += analysis_data['character_stats'].get('total_chars', 0)
        if 'word_stats' in analysis_data:
            stats['total_words_analyzed'] += analysis_data['word_stats'].get('total_words', 0)
        
        # Keep only last 50 analyses to prevent database from growing too large
        if len(data[user_id]['analysis_history']) > 50:
            data[user_id]['analysis_history'] = data[user_id]['analysis_history'][-50:]
        
        self._save_data(data)
        return True
    
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's analysis history.
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            List of analysis records, most recent first
        """
        data = self._load_data()
        if user_id not in data:
            return []
        
        history = data[user_id]['analysis_history']
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """
        Update user preferences.
        
        Args:
            user_id: User ID
            preferences: Dictionary of preferences to update
        """
        data = self._load_data()
        if user_id in data:
            data[user_id]['preferences'].update(preferences)
            self._save_data(data)
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences.
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences dictionary
        """
        data = self._load_data()
        if user_id in data:
            return data[user_id]['preferences']
        return {}
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Args:
            user_id: User ID
            
        Returns:
            User statistics dictionary
        """
        data = self._load_data()
        if user_id in data:
            return data[user_id]['statistics']
        return {}
    
    def list_all_users(self) -> List[Dict[str, Any]]:
        """
        Get list of all users (for admin purposes).
        
        Returns:
            List of user data dictionaries
        """
        data = self._load_data()
        return list(data.values())
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user account.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            True if user was deleted, False if not found
        """
        data = self._load_data()
        if user_id in data:
            del data[user_id]
            self._save_data(data)
            return True
        return False