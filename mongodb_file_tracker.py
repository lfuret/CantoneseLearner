"""
MongoDB-based file tracker with fallback to JSON for development.
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
import base64
from mongodb_config import get_mongo_manager


class FileTracker:
    """Manages file tracking and analysis history with MongoDB backend."""
    
    def __init__(self):
        self.mongo = get_mongo_manager()
        
        # Fallback to JSON if MongoDB is not available
        if not self.mongo.is_connected():
            self.json_db_path = "data/files.json"
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
    
    def _generate_file_hash(self, content: bytes) -> str:
        """Generate a unique hash for file content."""
        return hashlib.sha256(content).hexdigest()[:16]
    
    def register_file(self, filename: str, file_content: bytes, user_id: str, 
                     file_size: int, file_type: str = None) -> str:
        """Register a new file or retrieve existing file ID."""
        file_hash = self._generate_file_hash(file_content)
        
        if self.mongo.is_connected():
            try:
                files_collection = self.mongo.get_collection('files')
                
                # Check if file already exists
                existing_file = files_collection.find_one({'file_hash': file_hash})
                
                if existing_file:
                    # Update access information
                    files_collection.update_one(
                        {'file_id': existing_file['file_id']},
                        {
                            '$set': {'last_accessed': datetime.now().isoformat()},
                            '$inc': {'access_count': 1},
                            '$addToSet': {'accessed_by': user_id}
                        }
                    )
                    return existing_file['file_id']
                
                # Create new file record
                file_id = str(uuid.uuid4())[:12]
                file_content_b64 = base64.b64encode(file_content).decode('utf-8')
                
                file_data = {
                    'file_id': file_id,
                    'filename': filename,
                    'file_hash': file_hash,
                    'file_size': file_size,
                    'file_type': file_type,
                    'uploaded_by': user_id,
                    'uploaded_at': datetime.now().isoformat(),
                    'last_accessed': datetime.now().isoformat(),
                    'access_count': 1,
                    'accessed_by': [user_id],
                    'analysis_history': [],
                    'file_content': file_content_b64,
                    'metadata': {
                        'original_filename': filename,
                        'upload_session': str(uuid.uuid4())[:8]
                    }
                }
                
                files_collection.insert_one(file_data)
                return file_id
                
            except Exception as e:
                print(f"MongoDB file registration error: {e}")
                # Fall back to JSON
                pass
        
        # JSON fallback
        data = self._load_json_data()
        
        # Check if file already exists
        for file_id, file_data in data.items():
            if file_data.get('file_hash') == file_hash:
                # Update access information
                file_data['last_accessed'] = datetime.now().isoformat()
                file_data['access_count'] = file_data.get('access_count', 0) + 1
                if user_id not in file_data.get('accessed_by', []):
                    file_data.setdefault('accessed_by', []).append(user_id)
                self._save_json_data(data)
                return file_id
        
        # Create new file record
        file_id = str(uuid.uuid4())[:12]
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
        
        file_data = {
            'file_id': file_id,
            'filename': filename,
            'file_hash': file_hash,
            'file_size': file_size,
            'file_type': file_type,
            'uploaded_by': user_id,
            'uploaded_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'access_count': 1,
            'accessed_by': [user_id],
            'analysis_history': [],
            'file_content': file_content_b64,
            'metadata': {
                'original_filename': filename,
                'upload_session': str(uuid.uuid4())[:8]
            }
        }
        
        data[file_id] = file_data
        self._save_json_data(data)
        return file_id
    
    def add_analysis_record(self, file_id: str, user_id: str, analysis_results: Dict[str, Any]):
        """Add an analysis record to a file's history."""
        analysis_record = {
            'analysis_id': str(uuid.uuid4())[:8],
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'analysis_type': analysis_results.get('analysis_type', 'both'),
            'settings_used': analysis_results.get('settings_used', {}),
            'character_stats': {
                'total_chars': analysis_results.get('character_stats', {}).get('total_chars', 0),
                'unique_chars': analysis_results.get('character_stats', {}).get('unique_han_chars', 0),
                'top_10_chars': analysis_results.get('top_characters', {})
            },
            'word_stats': {
                'total_words': analysis_results.get('word_stats', {}).get('total_words', 0),
                'unique_words': analysis_results.get('word_stats', {}).get('unique_words', 0),
                'han_words_count': len(analysis_results.get('word_stats', {}).get('han_words', {})),
                'top_10_words': analysis_results.get('top_words', {})
            }
        }
        
        if self.mongo.is_connected():
            try:
                files_collection = self.mongo.get_collection('files')
                files_collection.update_one(
                    {'file_id': file_id},
                    {
                        '$push': {'analysis_history': {'$each': [analysis_record], '$slice': -20}},
                        '$set': {'last_accessed': datetime.now().isoformat()}
                    }
                )
                return True
            except Exception as e:
                print(f"MongoDB analysis record error: {e}")
                # Fall back to JSON
                pass
        
        # JSON fallback
        data = self._load_json_data()
        if file_id in data:
            data[file_id]['analysis_history'].append(analysis_record)
            data[file_id]['last_accessed'] = datetime.now().isoformat()
            # Keep only last 20 analysis records
            if len(data[file_id]['analysis_history']) > 20:
                data[file_id]['analysis_history'] = data[file_id]['analysis_history'][-20:]
            self._save_json_data(data)
            return True
        return False
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get complete information about a file."""
        if self.mongo.is_connected():
            try:
                files_collection = self.mongo.get_collection('files')
                file_data = files_collection.find_one({'file_id': file_id})
                if file_data:
                    file_data.pop('_id', None)  # Remove MongoDB ObjectId
                return file_data
            except Exception as e:
                print(f"MongoDB file info error: {e}")
                # Fall back to JSON
                pass
        
        # JSON fallback
        data = self._load_json_data()
        return data.get(file_id)
    
    def get_user_files(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all files accessed by a user."""
        if self.mongo.is_connected():
            try:
                files_collection = self.mongo.get_collection('files')
                user_files = list(files_collection.find(
                    {'accessed_by': user_id},
                    sort=[('last_accessed', -1)]
                ))
                for file_data in user_files:
                    file_data.pop('_id', None)  # Remove MongoDB ObjectId
                return user_files
            except Exception as e:
                print(f"MongoDB user files error: {e}")
                # Fall back to JSON
                pass
        
        # JSON fallback
        data = self._load_json_data()
        user_files = []
        for file_data in data.values():
            if user_id in file_data.get('accessed_by', []):
                user_files.append(file_data)
        
        # Sort by last accessed (most recent first)
        return sorted(user_files, key=lambda x: x.get('last_accessed', ''), reverse=True)
    
    def get_file_analysis_history(self, file_id: str, user_id: str = None) -> List[Dict[str, Any]]:
        """Get analysis history for a file, optionally filtered by user."""
        file_data = self.get_file_info(file_id)
        
        if not file_data:
            return []
        
        history = file_data.get('analysis_history', [])
        
        if user_id:
            history = [record for record in history if record['user_id'] == user_id]
        
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)
    
    def get_file_content(self, file_id: str) -> Optional[bytes]:
        """Get the original file content for re-analysis."""
        file_data = self.get_file_info(file_id)
        
        if not file_data or 'file_content' not in file_data:
            return None
        
        try:
            return base64.b64decode(file_data['file_content'])
        except Exception:
            return None