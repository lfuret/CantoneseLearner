"""
File tracking and analysis history management module.
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid


class FileTracker:
    """Manages file tracking and analysis history with detailed metadata."""
    
    def __init__(self, db_path: str = "data/files.json"):
        """
        Initialize the file tracker.
        
        Args:
            db_path: Path to the JSON database file for files
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
    
    def _generate_file_hash(self, content: bytes) -> str:
        """Generate a unique hash for file content."""
        return hashlib.sha256(content).hexdigest()[:16]
    
    def register_file(self, filename: str, file_content: bytes, user_id: str, 
                     file_size: int, file_type: str = None) -> str:
        """
        Register a new file or retrieve existing file ID.
        
        Args:
            filename: Original filename
            file_content: Raw file content as bytes
            user_id: User who uploaded the file
            file_size: Size of file in bytes
            file_type: MIME type of file
            
        Returns:
            File ID string
        """
        data = self._load_data()
        file_hash = self._generate_file_hash(file_content)
        
        # Check if file already exists
        for file_id, file_data in data.items():
            if file_data.get('file_hash') == file_hash:
                # Update last accessed
                file_data['last_accessed'] = datetime.now().isoformat()
                file_data['access_count'] = file_data.get('access_count', 0) + 1
                
                # Add user to accessed_by if not already there
                if user_id not in file_data.get('accessed_by', []):
                    file_data.setdefault('accessed_by', []).append(user_id)
                
                self._save_data(data)
                return file_id
        
        # Create new file record
        file_id = str(uuid.uuid4())[:12]
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
            'metadata': {
                'original_filename': filename,
                'upload_session': str(uuid.uuid4())[:8]
            }
        }
        
        data[file_id] = file_data
        self._save_data(data)
        
        return file_id
    
    def add_analysis_record(self, file_id: str, user_id: str, analysis_results: Dict[str, Any]):
        """
        Add an analysis record to a file's history.
        
        Args:
            file_id: File identifier
            user_id: User who performed the analysis
            analysis_results: Complete analysis results
        """
        data = self._load_data()
        
        if file_id not in data:
            return False
        
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
        
        data[file_id]['analysis_history'].append(analysis_record)
        data[file_id]['last_accessed'] = datetime.now().isoformat()
        
        # Keep only last 20 analysis records per file
        if len(data[file_id]['analysis_history']) > 20:
            data[file_id]['analysis_history'] = data[file_id]['analysis_history'][-20:]
        
        self._save_data(data)
        return True
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get complete information about a file."""
        data = self._load_data()
        return data.get(file_id)
    
    def get_user_files(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all files accessed by a user."""
        data = self._load_data()
        user_files = []
        
        for file_data in data.values():
            if user_id in file_data.get('accessed_by', []):
                user_files.append(file_data)
        
        # Sort by last accessed (most recent first)
        return sorted(user_files, key=lambda x: x.get('last_accessed', ''), reverse=True)
    
    def get_file_analysis_history(self, file_id: str, user_id: str = None) -> List[Dict[str, Any]]:
        """Get analysis history for a file, optionally filtered by user."""
        data = self._load_data()
        
        if file_id not in data:
            return []
        
        history = data[file_id]['analysis_history']
        
        if user_id:
            history = [record for record in history if record['user_id'] == user_id]
        
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)