import re
from collections import Counter
from typing import Dict, Any

class CharacterAnalyzer:
    """Analyzes text for Han character frequency and statistics."""
    
    def __init__(self):
        # Unicode ranges for Han characters (CJK Unified Ideographs)
        self.han_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')
        
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for Han character frequency and statistics.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing analysis results:
            - character_frequency: Counter object with character frequencies
            - total_chars: Total number of Han characters found
            - unique_han_chars: Number of unique Han characters
            - text_length: Total length of input text
            - han_character_ratio: Ratio of Han characters to total text
        """
        if not text:
            return {
                'character_frequency': Counter(),
                'total_chars': 0,
                'unique_han_chars': 0,
                'text_length': 0,
                'han_character_ratio': 0.0
            }
        
        # Clean text - remove extra whitespace and normalize
        cleaned_text = self._clean_text(text)
        
        # Extract all Han characters
        han_characters = self.han_pattern.findall(cleaned_text)
        
        # Count character frequencies
        char_frequency = Counter(han_characters)
        
        # Calculate statistics
        total_han_chars = len(han_characters)
        unique_han_chars = len(char_frequency)
        text_length = len(cleaned_text)
        han_ratio = total_han_chars / text_length if text_length > 0 else 0.0
        
        return {
            'character_frequency': char_frequency,
            'total_chars': total_han_chars,
            'unique_han_chars': unique_han_chars,
            'text_length': text_length,
            'han_character_ratio': han_ratio
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common formatting artifacts
        text = re.sub(r'[\r\n\t]+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def get_character_difficulty_level(self, char_frequency: Counter, total_chars: int) -> Dict[str, Dict[str, int]]:
        """
        Categorize characters by difficulty level based on frequency.
        
        Args:
            char_frequency: Counter object with character frequencies
            total_chars: Total number of characters
            
        Returns:
            Dictionary with difficulty levels and character counts
        """
        if not char_frequency or total_chars == 0:
            return {
                'very_common': {'count': 0, 'characters': []},
                'common': {'count': 0, 'characters': []},
                'uncommon': {'count': 0, 'characters': []},
                'rare': {'count': 0, 'characters': []}
            }
        
        # Define thresholds based on percentage of total occurrences
        very_common_threshold = total_chars * 0.01  # > 1% of all characters
        common_threshold = total_chars * 0.005      # > 0.5% of all characters
        uncommon_threshold = total_chars * 0.001    # > 0.1% of all characters
        
        levels = {
            'very_common': {'count': 0, 'characters': []},
            'common': {'count': 0, 'characters': []},
            'uncommon': {'count': 0, 'characters': []},
            'rare': {'count': 0, 'characters': []}
        }
        
        for char, freq in char_frequency.items():
            if freq >= very_common_threshold:
                levels['very_common']['characters'].append(char)
                levels['very_common']['count'] += 1
            elif freq >= common_threshold:
                levels['common']['characters'].append(char)
                levels['common']['count'] += 1
            elif freq >= uncommon_threshold:
                levels['uncommon']['characters'].append(char)
                levels['uncommon']['count'] += 1
            else:
                levels['rare']['characters'].append(char)
                levels['rare']['count'] += 1
        
        return levels
    
    def get_top_characters(self, char_frequency: Counter, n: int = 50) -> Dict[str, int]:
        """
        Get the top N most frequent characters.
        
        Args:
            char_frequency: Counter object with character frequencies
            n: Number of top characters to return
            
        Returns:
            Dictionary with top N characters and their frequencies
        """
        return dict(char_frequency.most_common(n))
    
    def calculate_character_percentage(self, char_frequency: Counter, total_chars: int) -> Dict[str, float]:
        """
        Calculate percentage for each character.
        
        Args:
            char_frequency: Counter object with character frequencies
            total_chars: Total number of characters
            
        Returns:
            Dictionary with characters and their percentage of total
        """
        if total_chars == 0:
            return {}
        
        return {
            char: (freq / total_chars) * 100 
            for char, freq in char_frequency.items()
        }
    
    def is_han_character(self, char: str) -> bool:
        """
        Check if a character is a Han character.
        
        Args:
            char: Single character to check
            
        Returns:
            True if the character is a Han character, False otherwise
        """
        return bool(self.han_pattern.match(char))
    
    def get_character_stats_summary(self, analysis_results: Dict[str, Any]) -> str:
        """
        Generate a text summary of character analysis results.
        
        Args:
            analysis_results: Results from analyze_text method
            
        Returns:
            Formatted string summary of the analysis
        """
        char_freq = analysis_results['character_frequency']
        total_chars = analysis_results['total_chars']
        unique_chars = analysis_results['unique_han_chars']
        text_length = analysis_results['text_length']
        han_ratio = analysis_results['han_character_ratio']
        
        summary = f"""Text Analysis Summary:
        
Total text length: {text_length:,} characters
Han characters found: {total_chars:,} ({han_ratio:.1%} of text)
Unique Han characters: {unique_chars:,}
Average character frequency: {total_chars/unique_chars:.1f} (if unique_chars > 0 else 0)

Top 10 most frequent characters:
"""
        
        for i, (char, freq) in enumerate(char_freq.most_common(10), 1):
            percentage = (freq / total_chars) * 100 if total_chars > 0 else 0
            summary += f"{i:2d}. {char} - {freq:4d} times ({percentage:5.1f}%)\n"
        
        return summary
