import pycantonese
from typing import Dict, List, Tuple, Any
import re

class PronunciationAnalyzer:
    """Provides Jyutping pronunciation analysis for Chinese characters and words."""
    
    def __init__(self):
        """Initialize the pronunciation analyzer."""
        self.han_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]+')
        
    def get_character_pronunciations(self, char_frequency: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
        """
        Get Jyutping pronunciations for characters.
        
        Args:
            char_frequency: Dictionary with character frequencies
            
        Returns:
            Dictionary with character data including pronunciation
        """
        character_data = {}
        
        for char, freq in char_frequency.items():
            try:
                # Convert character to Jyutping
                jyutping_result = pycantonese.characters_to_jyutping(char)
                
                if jyutping_result and len(jyutping_result) > 0:
                    # Extract the Jyutping pronunciation
                    jyutping = jyutping_result[0][1] if jyutping_result[0][1] else "unknown"
                else:
                    jyutping = "unknown"
                    
            except Exception:
                jyutping = "unknown"
            
            character_data[char] = {
                'frequency': freq,
                'jyutping': jyutping,
                'character': char
            }
        
        return character_data
    
    def get_word_pronunciations(self, word_frequency: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
        """
        Get Jyutping pronunciations for words.
        
        Args:
            word_frequency: Dictionary with word frequencies
            
        Returns:
            Dictionary with word data including pronunciation
        """
        word_data = {}
        
        for word, freq in word_frequency.items():
            # Only process words that contain Han characters
            if not self.han_pattern.search(word):
                continue
                
            try:
                # Convert word to Jyutping
                jyutping_result = pycantonese.characters_to_jyutping(word)
                
                if jyutping_result:
                    # Combine all Jyutping pronunciations for the word
                    jyutping_parts = []
                    for char_group, pronunciation in jyutping_result:
                        if pronunciation:
                            jyutping_parts.append(pronunciation)
                    
                    jyutping = ' '.join(jyutping_parts) if jyutping_parts else "unknown"
                else:
                    jyutping = "unknown"
                    
            except Exception:
                jyutping = "unknown"
            
            word_data[word] = {
                'frequency': freq,
                'jyutping': jyutping,
                'word': word,
                'length': len(word)
            }
        
        return word_data
    
    def get_pronunciation_summary(self, character_data: Dict[str, Dict[str, Any]], 
                                 word_data: Dict[str, Dict[str, Any]] = None) -> str:
        """
        Generate a summary of pronunciation data.
        
        Args:
            character_data: Character pronunciation data
            word_data: Optional word pronunciation data
            
        Returns:
            Formatted string summary
        """
        summary = "Pronunciation Analysis Summary:\n\n"
        
        # Character pronunciation summary
        total_chars = len(character_data)
        chars_with_pronunciation = sum(1 for data in character_data.values() 
                                     if data['jyutping'] != "unknown")
        
        summary += f"Characters with Jyutping: {chars_with_pronunciation}/{total_chars} "
        summary += f"({chars_with_pronunciation/total_chars*100:.1f}%)\n\n"
        
        # Top characters with pronunciation
        sorted_chars = sorted(character_data.items(), 
                            key=lambda x: x[1]['frequency'], reverse=True)
        
        summary += "Top 10 Characters with Pronunciation:\n"
        for i, (char, data) in enumerate(sorted_chars[:10], 1):
            summary += f"{i:2d}. {char} ({data['jyutping']}) - {data['frequency']} times\n"
        
        # Word pronunciation summary if provided
        if word_data:
            summary += f"\n\nWords with Jyutping:\n"
            total_words = len(word_data)
            words_with_pronunciation = sum(1 for data in word_data.values() 
                                         if data['jyutping'] != "unknown")
            
            summary += f"Words with pronunciation: {words_with_pronunciation}/{total_words} "
            summary += f"({words_with_pronunciation/total_words*100:.1f}%)\n\n"
            
            # Top words with pronunciation
            sorted_words = sorted(word_data.items(), 
                                key=lambda x: x[1]['frequency'], reverse=True)
            
            summary += "Top 10 Words with Pronunciation:\n"
            for i, (word, data) in enumerate(sorted_words[:10], 1):
                summary += f"{i:2d}. {word} ({data['jyutping']}) - {data['frequency']} times\n"
        
        return summary
    
    def filter_by_pronunciation_availability(self, data: Dict[str, Dict[str, Any]], 
                                           has_pronunciation: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Filter data by pronunciation availability.
        
        Args:
            data: Character or word data
            has_pronunciation: If True, return items with pronunciation; if False, return items without
            
        Returns:
            Filtered data dictionary
        """
        if has_pronunciation:
            return {key: value for key, value in data.items() 
                   if value['jyutping'] != "unknown"}
        else:
            return {key: value for key, value in data.items() 
                   if value['jyutping'] == "unknown"}
    
    def get_tone_distribution(self, data: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """
        Analyze tone distribution in Jyutping pronunciations.
        
        Args:
            data: Character or word data with Jyutping
            
        Returns:
            Dictionary with tone counts
        """
        tone_counts = {str(i): 0 for i in range(1, 7)}  # Tones 1-6
        tone_counts['unknown'] = 0
        
        for item_data in data.values():
            jyutping = item_data['jyutping']
            if jyutping == "unknown":
                tone_counts['unknown'] += item_data['frequency']
                continue
            
            # Extract tones from Jyutping (numbers 1-6)
            tones = re.findall(r'[1-6]', jyutping)
            for tone in tones:
                tone_counts[tone] += item_data['frequency']
        
        return tone_counts
    
    def search_by_jyutping(self, data: Dict[str, Dict[str, Any]], 
                          jyutping_pattern: str) -> Dict[str, Dict[str, Any]]:
        """
        Search for characters or words by Jyutping pattern.
        
        Args:
            data: Character or word data
            jyutping_pattern: Jyutping pattern to search for (e.g., "hou", "gong2")
            
        Returns:
            Filtered data matching the pattern
        """
        pattern = jyutping_pattern.lower()
        matching_data = {}
        
        for key, value in data.items():
            jyutping = value['jyutping'].lower()
            if pattern in jyutping:
                matching_data[key] = value
        
        return matching_data