"""
MongoDB-based learning tracker with fallback to JSON for development.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict
from mongodb_config import get_mongo_manager


class LearningTracker:
    """Tracks user learning progress for characters and words with MongoDB backend."""
    
    def __init__(self):
        self.mongo = get_mongo_manager()
        
        # Fallback to JSON if MongoDB is not available
        if not self.mongo.is_connected():
            self.json_db_path = "data/learning_progress.json"
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
    
    def track_exposure(self, user_id: str, characters: Dict[str, int], words: Dict[str, int],
                      file_id: str, filename: str):
        """Track user exposure to characters and words from a file."""
        timestamp = datetime.now().isoformat()
        
        # Prepare session data
        session = {
            'session_id': f"{file_id}_{timestamp[:19]}",
            'file_id': file_id,
            'filename': filename,
            'timestamp': timestamp,
            'characters_encountered': len(characters),
            'words_encountered': len(words),
            'new_characters': 0,  # Will be calculated
            'new_words': 0        # Will be calculated
        }
        
        if self.mongo.is_connected():
            try:
                learning_collection = self.mongo.get_collection('learning_progress')
                
                # Get existing user data
                user_data = learning_collection.find_one({'user_id': user_id})
                
                if not user_data:
                    # Create new user record
                    user_data = {
                        'user_id': user_id,
                        'character_exposure': {},
                        'word_exposure': {},
                        'learning_sessions': [],
                        'mastery_levels': {'characters': {}, 'words': {}},
                        'total_exposures': 0,
                        'unique_files_analyzed': []
                    }
                
                # Track character exposure
                for char, frequency in characters.items():
                    if char not in user_data['character_exposure']:
                        user_data['character_exposure'][char] = {
                            'total_exposures': 0,
                            'files_seen_in': [],
                            'first_seen': timestamp,
                            'last_seen': timestamp,
                            'frequency_history': []
                        }
                        session['new_characters'] += 1
                    
                    char_data = user_data['character_exposure'][char]
                    char_data['total_exposures'] += frequency
                    char_data['last_seen'] = timestamp
                    char_data['frequency_history'].append({
                        'file_id': file_id,
                        'filename': filename,
                        'frequency': frequency,
                        'date': timestamp
                    })
                    
                    if file_id not in char_data['files_seen_in']:
                        char_data['files_seen_in'].append(file_id)
                
                # Track word exposure
                for word, frequency in words.items():
                    if word not in user_data['word_exposure']:
                        user_data['word_exposure'][word] = {
                            'total_exposures': 0,
                            'files_seen_in': [],
                            'first_seen': timestamp,
                            'last_seen': timestamp,
                            'frequency_history': []
                        }
                        session['new_words'] += 1
                    
                    word_data = user_data['word_exposure'][word]
                    word_data['total_exposures'] += frequency
                    word_data['last_seen'] = timestamp
                    word_data['frequency_history'].append({
                        'file_id': file_id,
                        'filename': filename,
                        'frequency': frequency,
                        'date': timestamp
                    })
                    
                    if file_id not in word_data['files_seen_in']:
                        word_data['files_seen_in'].append(file_id)
                
                # Add session and update counters
                user_data['learning_sessions'].append(session)
                user_data['total_exposures'] += 1
                
                if file_id not in user_data['unique_files_analyzed']:
                    user_data['unique_files_analyzed'].append(file_id)
                
                # Keep only last 50 sessions
                if len(user_data['learning_sessions']) > 50:
                    user_data['learning_sessions'] = user_data['learning_sessions'][-50:]
                
                # Update mastery levels
                self._update_mastery_levels(user_data)
                
                # Save to MongoDB
                learning_collection.replace_one(
                    {'user_id': user_id},
                    user_data,
                    upsert=True
                )
                return
                
            except Exception as e:
                print(f"MongoDB learning tracking error: {e}")
                # Fall back to JSON
                pass
        
        # JSON fallback
        data = self._load_json_data()
        
        if user_id not in data:
            data[user_id] = {
                'character_exposure': {},
                'word_exposure': {},
                'learning_sessions': [],
                'mastery_levels': {'characters': {}, 'words': {}},
                'total_exposures': 0,
                'unique_files_analyzed': []
            }
        
        user_data = data[user_id]
        
        # Track character exposure
        for char, frequency in characters.items():
            if char not in user_data['character_exposure']:
                user_data['character_exposure'][char] = {
                    'total_exposures': 0,
                    'files_seen_in': [],
                    'first_seen': timestamp,
                    'last_seen': timestamp,
                    'frequency_history': []
                }
                session['new_characters'] += 1
            
            char_data = user_data['character_exposure'][char]
            char_data['total_exposures'] += frequency
            char_data['last_seen'] = timestamp
            char_data['frequency_history'].append({
                'file_id': file_id,
                'filename': filename,
                'frequency': frequency,
                'date': timestamp
            })
            
            if file_id not in char_data['files_seen_in']:
                char_data['files_seen_in'].append(file_id)
        
        # Track word exposure
        for word, frequency in words.items():
            if word not in user_data['word_exposure']:
                user_data['word_exposure'][word] = {
                    'total_exposures': 0,
                    'files_seen_in': [],
                    'first_seen': timestamp,
                    'last_seen': timestamp,
                    'frequency_history': []
                }
                session['new_words'] += 1
            
            word_data = user_data['word_exposure'][word]
            word_data['total_exposures'] += frequency
            word_data['last_seen'] = timestamp
            word_data['frequency_history'].append({
                'file_id': file_id,
                'filename': filename,
                'frequency': frequency,
                'date': timestamp
            })
            
            if file_id not in word_data['files_seen_in']:
                word_data['files_seen_in'].append(file_id)
        
        # Add session and update counters
        user_data['learning_sessions'].append(session)
        user_data['total_exposures'] += 1
        
        if file_id not in user_data['unique_files_analyzed']:
            user_data['unique_files_analyzed'].append(file_id)
        
        # Keep only last 50 sessions
        if len(user_data['learning_sessions']) > 50:
            user_data['learning_sessions'] = user_data['learning_sessions'][-50:]
        
        # Update mastery levels
        self._update_mastery_levels(user_data)
        
        self._save_json_data(data)
    
    def _update_mastery_levels(self, user_data: Dict[str, Any]):
        """Update mastery levels based on exposure frequency."""
        
        # Character mastery levels
        for char, char_data in user_data['character_exposure'].items():
            exposures = char_data['total_exposures']
            files_count = len(char_data['files_seen_in'])
            
            if exposures >= 50 and files_count >= 5:
                level = 'mastered'
            elif exposures >= 20 and files_count >= 3:
                level = 'familiar'
            elif exposures >= 5:
                level = 'learning'
            else:
                level = 'beginner'
            
            user_data['mastery_levels']['characters'][char] = {
                'level': level,
                'exposures': exposures,
                'files_count': files_count,
                'last_updated': datetime.now().isoformat()
            }
        
        # Word mastery levels
        for word, word_data in user_data['word_exposure'].items():
            exposures = word_data['total_exposures']
            files_count = len(word_data['files_seen_in'])
            
            if exposures >= 30 and files_count >= 4:
                level = 'mastered'
            elif exposures >= 10 and files_count >= 2:
                level = 'familiar'
            elif exposures >= 3:
                level = 'learning'
            else:
                level = 'beginner'
            
            user_data['mastery_levels']['words'][word] = {
                'level': level,
                'exposures': exposures,
                'files_count': files_count,
                'last_updated': datetime.now().isoformat()
            }
    
    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning progress for a user."""
        if self.mongo.is_connected():
            try:
                learning_collection = self.mongo.get_collection('learning_progress')
                user_data = learning_collection.find_one({'user_id': user_id})
                if user_data:
                    user_data.pop('_id', None)  # Remove MongoDB ObjectId
                else:
                    return self._empty_progress()
            except Exception as e:
                print(f"MongoDB learning progress error: {e}")
                # Fall back to JSON
                user_data = None
        
        if not user_data:
            # JSON fallback
            data = self._load_json_data()
            user_data = data.get(user_id)
            if not user_data:
                return self._empty_progress()
        
        # Calculate statistics
        char_stats = self._calculate_character_stats(user_data)
        word_stats = self._calculate_word_stats(user_data)
        session_stats = self._calculate_session_stats(user_data)
        
        return {
            'character_stats': char_stats,
            'word_stats': word_stats,
            'session_stats': session_stats,
            'mastery_levels': user_data.get('mastery_levels', {}),
            'recent_sessions': user_data.get('learning_sessions', [])[-10:],
            'total_exposures': user_data.get('total_exposures', 0),
            'unique_files': len(user_data.get('unique_files_analyzed', []))
        }
    
    def _calculate_character_stats(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate character learning statistics."""
        char_exposure = user_data.get('character_exposure', {})
        mastery = user_data.get('mastery_levels', {}).get('characters', {})
        
        stats = {
            'total_characters_seen': len(char_exposure),
            'total_character_exposures': sum(data['total_exposures'] for data in char_exposure.values()),
            'mastery_breakdown': defaultdict(int)
        }
        
        for char_mastery in mastery.values():
            stats['mastery_breakdown'][char_mastery['level']] += 1
        
        return dict(stats)
    
    def _calculate_word_stats(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate word learning statistics."""
        word_exposure = user_data.get('word_exposure', {})
        mastery = user_data.get('mastery_levels', {}).get('words', {})
        
        stats = {
            'total_words_seen': len(word_exposure),
            'total_word_exposures': sum(data['total_exposures'] for data in word_exposure.values()),
            'mastery_breakdown': defaultdict(int)
        }
        
        for word_mastery in mastery.values():
            stats['mastery_breakdown'][word_mastery['level']] += 1
        
        return dict(stats)
    
    def _calculate_session_stats(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate learning session statistics."""
        sessions = user_data.get('learning_sessions', [])
        
        if not sessions:
            return {'total_sessions': 0}
        
        return {
            'total_sessions': len(sessions),
            'avg_characters_per_session': sum(s['characters_encountered'] for s in sessions) / len(sessions),
            'avg_words_per_session': sum(s['words_encountered'] for s in sessions) / len(sessions),
            'first_session': sessions[0]['timestamp'] if sessions else None,
            'last_session': sessions[-1]['timestamp'] if sessions else None
        }
    
    def _empty_progress(self) -> Dict[str, Any]:
        """Return empty progress structure."""
        return {
            'character_stats': {'total_characters_seen': 0, 'total_character_exposures': 0, 'mastery_breakdown': {}},
            'word_stats': {'total_words_seen': 0, 'total_word_exposures': 0, 'mastery_breakdown': {}},
            'session_stats': {'total_sessions': 0},
            'mastery_levels': {'characters': {}, 'words': {}},
            'recent_sessions': [],
            'total_exposures': 0,
            'unique_files': 0
        }
    
    def get_mastered_items(self, user_id: str, item_type: str = 'both') -> Dict[str, List[str]]:
        """Get list of mastered characters and/or words."""
        progress = self.get_user_progress(user_id)
        mastery = progress.get('mastery_levels', {})
        result = {}
        
        if item_type in ['characters', 'both']:
            result['characters'] = [
                char for char, data in mastery.get('characters', {}).items()
                if data['level'] == 'mastered'
            ]
        
        if item_type in ['words', 'both']:
            result['words'] = [
                word for word, data in mastery.get('words', {}).items()
                if data['level'] == 'mastered'
            ]
        
        return result
    
    def get_learning_recommendations(self, user_id: str) -> Dict[str, List[str]]:
        """Get recommendations for what to focus on learning."""
        progress = self.get_user_progress(user_id)
        mastery = progress.get('mastery_levels', {})
        
        # Recommend items at 'learning' level (not beginner, not mastered)
        recommendations = {
            'characters': [
                char for char, data in mastery.get('characters', {}).items()
                if data['level'] == 'learning'
            ][:20],  # Top 20 recommendations
            'words': [
                word for word, data in mastery.get('words', {}).items()
                if data['level'] == 'learning'
            ][:20]
        }
        
        return recommendations