import jieba
import re
from collections import Counter
from typing import Dict, Any, List

class WordAnalyzer:
    """Analyzes text for word frequency and statistics using Chinese word segmentation."""
    
    def __init__(self):
        # Enable paddle mode for better accuracy (if available)
        try:
            jieba.enable_paddle()
        except:
            pass  # Fall back to default mode if paddle is not available
        
        # Pre-compile regex for Han characters
        self.han_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]+')
        
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for word frequency and statistics.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing analysis results:
            - word_frequency: Counter object with word frequencies
            - total_words: Total number of words found
            - unique_words: Number of unique words
            - han_words: Words containing Han characters
            - word_lengths: Distribution of word lengths
            - avg_word_length: Average word length
        """
        if not text:
            return {
                'word_frequency': Counter(),
                'total_words': 0,
                'unique_words': 0,
                'han_words': Counter(),
                'word_lengths': Counter(),
                'avg_word_length': 0.0
            }
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Perform word segmentation
        words = list(jieba.cut(cleaned_text))
        
        # Filter out empty strings and whitespace
        words = [word.strip() for word in words if word.strip()]
        
        # Count word frequencies
        word_frequency = Counter(words)
        
        # Extract Han character words
        han_words = Counter()
        for word in words:
            if self.han_pattern.search(word):
                han_words[word] += 1
        
        # Calculate word length distribution
        word_lengths = Counter(len(word) for word in words)
        
        # Calculate statistics
        total_words = len(words)
        unique_words = len(word_frequency)
        avg_word_length = sum(len(word) for word in words) / total_words if total_words > 0 else 0.0
        
        return {
            'word_frequency': word_frequency,
            'total_words': total_words,
            'unique_words': unique_words,
            'han_words': han_words,
            'word_lengths': word_lengths,
            'avg_word_length': avg_word_length
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
    
    def get_word_difficulty_level(self, word_frequency: Counter, total_words: int) -> Dict[str, Dict[str, Any]]:
        """
        Categorize words by difficulty level based on frequency.
        
        Args:
            word_frequency: Counter object with word frequencies
            total_words: Total number of words
            
        Returns:
            Dictionary with difficulty levels and word counts
        """
        if not word_frequency or total_words == 0:
            return {
                'very_common': {'count': 0, 'words': []},
                'common': {'count': 0, 'words': []},
                'uncommon': {'count': 0, 'words': []},
                'rare': {'count': 0, 'words': []}
            }
        
        # Define thresholds based on percentage of total occurrences
        very_common_threshold = total_words * 0.005  # > 0.5% of all words
        common_threshold = total_words * 0.002       # > 0.2% of all words
        uncommon_threshold = total_words * 0.0005    # > 0.05% of all words
        
        levels = {
            'very_common': {'count': 0, 'words': []},
            'common': {'count': 0, 'words': []},
            'uncommon': {'count': 0, 'words': []},
            'rare': {'count': 0, 'words': []}
        }
        
        for word, freq in word_frequency.items():
            if freq >= very_common_threshold:
                levels['very_common']['words'].append((word, freq))
                levels['very_common']['count'] += 1
            elif freq >= common_threshold:
                levels['common']['words'].append((word, freq))
                levels['common']['count'] += 1
            elif freq >= uncommon_threshold:
                levels['uncommon']['words'].append((word, freq))
                levels['uncommon']['count'] += 1
            else:
                levels['rare']['words'].append((word, freq))
                levels['rare']['count'] += 1
        
        # Sort words within each level by frequency
        for level in levels.values():
            level['words'].sort(key=lambda x: x[1], reverse=True)
        
        return levels
    
    def get_top_words(self, word_frequency: Counter, n: int = 50) -> Dict[str, int]:
        """
        Get the top N most frequent words.
        
        Args:
            word_frequency: Counter object with word frequencies
            n: Number of top words to return
            
        Returns:
            Dictionary with top N words and their frequencies
        """
        return dict(word_frequency.most_common(n))
    
    def get_top_han_words(self, han_words: Counter, n: int = 50) -> Dict[str, int]:
        """
        Get the top N most frequent Han character words.
        
        Args:
            han_words: Counter object with Han word frequencies
            n: Number of top words to return
            
        Returns:
            Dictionary with top N Han words and their frequencies
        """
        return dict(han_words.most_common(n))
    
    def calculate_word_percentage(self, word_frequency: Counter, total_words: int) -> Dict[str, float]:
        """
        Calculate percentage for each word.
        
        Args:
            word_frequency: Counter object with word frequencies
            total_words: Total number of words
            
        Returns:
            Dictionary with words and their percentage of total
        """
        if total_words == 0:
            return {}
        
        return {
            word: (freq / total_words) * 100 
            for word, freq in word_frequency.items()
        }
    
    def get_word_stats_summary(self, analysis_results: Dict[str, Any]) -> str:
        """
        Generate a text summary of word analysis results.
        
        Args:
            analysis_results: Results from analyze_text method
            
        Returns:
            Formatted string summary of the analysis
        """
        word_freq = analysis_results['word_frequency']
        han_words = analysis_results['han_words']
        total_words = analysis_results['total_words']
        unique_words = analysis_results['unique_words']
        avg_word_length = analysis_results['avg_word_length']
        
        summary = f"""Word Analysis Summary:

Total words found: {total_words:,}
Unique words: {unique_words:,}
Han character words: {len(han_words):,}
Average word length: {avg_word_length:.1f} characters

Top 10 most frequent words:
"""
        
        for i, (word, freq) in enumerate(word_freq.most_common(10), 1):
            percentage = (freq / total_words) * 100 if total_words > 0 else 0
            summary += f"{i:2d}. {word} - {freq:4d} times ({percentage:5.1f}%)\n"
        
        summary += f"\nTop 10 most frequent Han words:\n"
        for i, (word, freq) in enumerate(han_words.most_common(10), 1):
            percentage = (freq / total_words) * 100 if total_words > 0 else 0
            summary += f"{i:2d}. {word} - {freq:4d} times ({percentage:5.1f}%)\n"
        
        return summary
    
    def filter_words_by_length(self, word_frequency: Counter, min_length: int = 1, max_length: int = 10) -> Counter:
        """
        Filter words by length.
        
        Args:
            word_frequency: Counter object with word frequencies
            min_length: Minimum word length
            max_length: Maximum word length
            
        Returns:
            Filtered Counter object
        """
        return Counter({
            word: freq for word, freq in word_frequency.items()
            if min_length <= len(word) <= max_length
        })
    
    def get_words_by_length(self, word_frequency: Counter) -> Dict[int, List[tuple]]:
        """
        Group words by their character length.
        
        Args:
            word_frequency: Counter object with word frequencies
            
        Returns:
            Dictionary with length as key and list of (word, frequency) tuples as value
        """
        words_by_length = {}
        for word, freq in word_frequency.items():
            length = len(word)
            if length not in words_by_length:
                words_by_length[length] = []
            words_by_length[length].append((word, freq))
        
        # Sort words within each length group by frequency
        for length in words_by_length:
            words_by_length[length].sort(key=lambda x: x[1], reverse=True)
        
        return words_by_length