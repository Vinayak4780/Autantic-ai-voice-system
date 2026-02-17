"""
Style Analyzer — Programmatic extraction of writing style signals.

This module analyzes user writing samples to extract quantitative and qualitative
style metrics WITHOUT relying on an LLM. All analysis is deterministic and repeatable.

Style Signals Captured:
1. Sentence Structure: length distribution, short/long ratios
2. Questions & Hooks: interrogative frequency, exclamation usage
3. Formatting: paragraph patterns, bullet usage, line structure
4. Vocabulary: richness, word length, contractions, distinctive words
5. Punctuation & Emoji: special character usage patterns
6. Rhythm: sentence length variation, opening patterns
"""

import re
import math
import string
from collections import Counter
from typing import Optional
import numpy as np


# Common English words to filter when finding distinctive vocabulary
COMMON_WORDS = set([
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "don", "should", "now", "and", "but", "or", "if", "while", "that",
    "this", "these", "those", "it", "its", "i", "me", "my", "myself",
    "we", "our", "ours", "you", "your", "yours", "he", "him", "his",
    "she", "her", "hers", "they", "them", "their", "what", "which",
    "who", "whom", "about", "up", "like", "get", "got", "make", "go",
    "going", "know", "think", "see", "come", "want", "look", "use",
    "find", "give", "tell", "say", "said", "also", "well", "back",
    "even", "still", "way", "take", "thing", "things", "much", "because",
    "good", "new", "first", "last", "long", "great", "little", "right",
    "old", "big", "high", "different", "small", "large", "next", "early",
    "young", "important", "people", "time", "year", "day", "man", "woman",
    "child", "world", "life", "hand", "part", "place", "case", "week",
    "company", "system", "program", "question", "work", "point", "number",
    "let", "something", "really", "many", "every", "one", "two", "three",
    "anything", "nothing", "everything", "someone", "anyone", "everyone",
    "been", "being", "am", "s", "t", "re", "ve", "ll", "d", "m",
    "don't", "doesn't", "didn't", "won't", "wouldn't", "couldn't",
    "shouldn't", "isn't", "aren't", "wasn't", "weren't", "haven't",
    "hasn't", "hadn't", "can't", "couldn't", "it's", "that's", "there's",
])

# Emoji regex pattern
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f900-\U0001f9FF"  # supplemental
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended
    "\U00002702-\U000027B0"
    "\U0000200D"             # zero width joiner
    "\U0000FE0F"             # variation selector
    "]+",
    flags=re.UNICODE,
)

# Contraction patterns
CONTRACTIONS = re.compile(
    r"\b(i'm|i've|i'll|i'd|you're|you've|you'll|you'd|he's|she's|it's|"
    r"we're|we've|we'll|we'd|they're|they've|they'll|they'd|"
    r"that's|there's|here's|what's|who's|how's|where's|when's|"
    r"isn't|aren't|wasn't|weren't|hasn't|haven't|hadn't|"
    r"doesn't|don't|didn't|won't|wouldn't|shan't|shouldn't|"
    r"can't|couldn't|mustn't|let's|gonna|wanna|gotta)\b",
    re.IGNORECASE,
)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences using regex-based rules."""
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split on sentence-ending punctuation followed by space/end
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])|(?<=[.!?])$', text)
    
    # Clean and filter
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 1]
    return sentences


def split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs."""
    paragraphs = re.split(r'\n\s*\n|\n(?=\s*[-•*])', text)
    return [p.strip() for p in paragraphs if p.strip()]


def count_words(text: str) -> int:
    """Count words in text."""
    return len(re.findall(r'\b\w+\b', text))


def get_words(text: str) -> list[str]:
    """Get all words from text, lowercased."""
    return [w.lower() for w in re.findall(r'\b\w+\b', text)]


def extract_ngrams(words: list[str], n: int) -> list[tuple]:
    """Extract n-grams from a list of words."""
    return [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]


class StyleAnalyzer:
    """
    Analyzes writing samples to extract a comprehensive style profile.
    
    All analysis is programmatic and deterministic — no LLM calls.
    Given the same input samples, the output will always be identical.
    """
    
    def __init__(self, samples: list[str]):
        """
        Initialize with a list of writing sample texts.
        
        Args:
            samples: List of 3-10 writing samples from the user
        """
        self.samples = samples
        self.combined_text = "\n\n".join(samples)
        self.all_sentences = []
        self.all_paragraphs = []
        self.all_words = []
        
        # Pre-process all samples
        for sample in samples:
            self.all_sentences.extend(split_sentences(sample))
            self.all_paragraphs.extend(split_paragraphs(sample))
            self.all_words.extend(get_words(sample))
    
    def analyze_sentence_structure(self) -> dict:
        """Analyze sentence length distribution and structure."""
        if not self.all_sentences:
            return {
                "avg_sentence_length": 0,
                "sentence_length_std": 0,
                "short_sentence_ratio": 0,
                "long_sentence_ratio": 0,
            }
        
        lengths = [count_words(s) for s in self.all_sentences]
        avg_len = np.mean(lengths)
        std_len = np.std(lengths)
        short_ratio = sum(1 for l in lengths if l <= 5) / len(lengths)
        long_ratio = sum(1 for l in lengths if l >= 20) / len(lengths)
        
        return {
            "avg_sentence_length": round(float(avg_len), 2),
            "sentence_length_std": round(float(std_len), 2),
            "short_sentence_ratio": round(float(short_ratio), 3),
            "long_sentence_ratio": round(float(long_ratio), 3),
        }
    
    def analyze_questions_hooks(self) -> dict:
        """Analyze usage of questions and exclamations."""
        if not self.all_sentences:
            return {"question_ratio": 0, "exclamation_ratio": 0}
        
        question_count = sum(1 for s in self.all_sentences if s.rstrip().endswith('?'))
        exclamation_count = sum(1 for s in self.all_sentences if s.rstrip().endswith('!'))
        total = len(self.all_sentences)
        
        return {
            "question_ratio": round(question_count / total, 3),
            "exclamation_ratio": round(exclamation_count / total, 3),
        }
    
    def analyze_formatting(self) -> dict:
        """Analyze paragraph structure and formatting patterns."""
        if not self.all_paragraphs:
            return {
                "avg_paragraph_length": 0,
                "uses_bullet_points": False,
                "bullet_frequency": 0,
            }
        
        # Paragraph lengths (in sentences)
        para_lengths = [len(split_sentences(p)) for p in self.all_paragraphs]
        avg_para_len = np.mean(para_lengths) if para_lengths else 0
        
        # Bullet point detection
        lines = self.combined_text.split('\n')
        bullet_lines = sum(
            1 for line in lines
            if re.match(r'^\s*[-•*]\s', line.strip()) or re.match(r'^\s*\d+[.)]\s', line.strip())
        )
        total_lines = max(len(lines), 1)
        uses_bullets = bullet_lines > 0
        bullet_freq = bullet_lines / total_lines
        
        return {
            "avg_paragraph_length": round(float(avg_para_len), 2),
            "uses_bullet_points": uses_bullets,
            "bullet_frequency": round(float(bullet_freq), 3),
        }
    
    def analyze_vocabulary(self) -> dict:
        """Analyze vocabulary richness and word patterns."""
        if not self.all_words:
            return {
                "vocabulary_richness": 0,
                "avg_word_length": 0,
                "contraction_ratio": 0,
            }
        
        # Type-token ratio
        unique_words = set(self.all_words)
        ttr = len(unique_words) / len(self.all_words)
        
        # Average word length
        avg_word_len = np.mean([len(w) for w in self.all_words])
        
        # Contraction ratio
        contraction_matches = CONTRACTIONS.findall(self.combined_text.lower())
        contraction_ratio = len(contraction_matches) / max(len(self.all_words), 1)
        
        return {
            "vocabulary_richness": round(float(ttr), 3),
            "avg_word_length": round(float(avg_word_len), 2),
            "contraction_ratio": round(float(contraction_ratio), 3),
        }
    
    def analyze_punctuation_emoji(self) -> dict:
        """Analyze special punctuation and emoji usage."""
        total_words = max(len(self.all_words), 1)
        total_sentences = max(len(self.all_sentences), 1)
        
        # Emoji count
        emoji_matches = EMOJI_PATTERN.findall(self.combined_text)
        emoji_freq = (len(emoji_matches) / total_words) * 100
        
        # Ellipsis count
        ellipsis_count = len(re.findall(r'\.{3}|…', self.combined_text))
        ellipsis_freq = (ellipsis_count / total_sentences) * 100
        
        # Dash count (em dash, en dash, hyphen used as dash)
        dash_count = len(re.findall(r'[—–]|\s-\s', self.combined_text))
        dash_freq = (dash_count / total_words) * 100
        
        # Parenthetical count
        paren_count = len(re.findall(r'\([^)]+\)', self.combined_text))
        paren_freq = (paren_count / total_sentences) * 100
        
        return {
            "emoji_frequency": round(float(emoji_freq), 3),
            "ellipsis_frequency": round(float(ellipsis_freq), 3),
            "dash_frequency": round(float(dash_freq), 3),
            "parenthetical_frequency": round(float(paren_freq), 3),
        }
    
    def analyze_rhythm(self) -> dict:
        """Analyze sentence rhythm and opening patterns."""
        if not self.all_paragraphs:
            return {
                "opens_with_short_sentence": 0,
                "sentence_length_variation": "low",
            }
        
        # Check paragraph opening patterns
        short_openers = 0
        for para in self.all_paragraphs:
            sentences = split_sentences(para)
            if sentences and count_words(sentences[0]) <= 6:
                short_openers += 1
        
        opens_short = short_openers / max(len(self.all_paragraphs), 1)
        
        # Sentence length variation
        if len(self.all_sentences) >= 2:
            lengths = [count_words(s) for s in self.all_sentences]
            cv = np.std(lengths) / max(np.mean(lengths), 1)  # coefficient of variation
            if cv > 0.7:
                variation = "high"
            elif cv > 0.4:
                variation = "medium"
            else:
                variation = "low"
        else:
            variation = "low"
        
        return {
            "opens_with_short_sentence": round(float(opens_short), 3),
            "sentence_length_variation": variation,
        }
    
    def extract_signature_phrases(self, top_n: int = 10) -> list[str]:
        """
        Find recurring phrases (bigrams and trigrams) that appear across multiple samples.
        These are the user's 'signature' expressions.
        """
        all_bigrams = []
        all_trigrams = []
        
        for sample in self.samples:
            words = get_words(sample)
            # Filter out stop words for meaningful phrases
            all_bigrams.extend(extract_ngrams(words, 2))
            all_trigrams.extend(extract_ngrams(words, 3))
        
        # Count and filter
        bigram_counts = Counter(all_bigrams)
        trigram_counts = Counter(all_trigrams)
        
        phrases = []
        
        # Get trigrams that appear 2+ times and don't consist entirely of common words
        for trigram, count in trigram_counts.most_common(50):
            if count >= 2 and not all(w in COMMON_WORDS for w in trigram):
                phrases.append(" ".join(trigram))
                if len(phrases) >= top_n // 2:
                    break
        
        # Get bigrams that appear 3+ times
        for bigram, count in bigram_counts.most_common(50):
            if count >= 2 and not all(w in COMMON_WORDS for w in bigram):
                phrase = " ".join(bigram)
                if phrase not in phrases:
                    phrases.append(phrase)
                if len(phrases) >= top_n:
                    break
        
        return phrases[:top_n]
    
    def extract_vocabulary_preferences(self, top_n: int = 15) -> list[str]:
        """
        Find distinctive words the user prefers — words that appear frequently
        but are not common English stop words.
        """
        word_counts = Counter(self.all_words)
        distinctive = []
        
        for word, count in word_counts.most_common(200):
            if (word not in COMMON_WORDS 
                and len(word) > 2 
                and count >= 2
                and not word.isdigit()):
                distinctive.append(word)
            if len(distinctive) >= top_n:
                break
        
        return distinctive
    
    def extract_sentence_starters(self, top_n: int = 10) -> list[str]:
        """Find common ways the user starts sentences."""
        starters = []
        for sentence in self.all_sentences:
            words = sentence.split()
            if len(words) >= 2:
                starter = " ".join(words[:2]).lower()
                starters.append(starter)
            elif len(words) == 1:
                starters.append(words[0].lower())
        
        starter_counts = Counter(starters)
        # Filter out very generic starters
        generic_starters = {"the", "a", "an", "it is", "there is", "there are"}
        
        result = []
        for starter, count in starter_counts.most_common(30):
            if count >= 2 and starter not in generic_starters:
                result.append(starter)
            if len(result) >= top_n:
                break
        
        return result
    
    def extract_transition_words(self, top_n: int = 10) -> list[str]:
        """Find frequently used transition words and connectors."""
        transition_candidates = [
            "however", "but", "so", "and", "yet", "still", "also", "moreover",
            "furthermore", "meanwhile", "instead", "rather", "although", "though",
            "because", "since", "therefore", "thus", "hence", "consequently",
            "nevertheless", "nonetheless", "besides", "anyway", "actually",
            "basically", "honestly", "frankly", "literally", "obviously",
            "clearly", "simply", "essentially", "ultimately", "finally",
            "look", "listen", "here's the thing", "the truth is", "the point is",
            "in fact", "for example", "for instance",
        ]
        
        word_counts = Counter(self.all_words)
        found = []
        
        for word in transition_candidates:
            if word in word_counts and word_counts[word] >= 1:
                found.append((word, word_counts[word]))
        
        # Sort by frequency
        found.sort(key=lambda x: x[1], reverse=True)
        return [w for w, c in found[:top_n]]
    
    def describe_formatting_style(self) -> str:
        """Generate a natural language description of the formatting style."""
        formatting = self.analyze_formatting()
        sentence_info = self.analyze_sentence_structure()
        
        parts = []
        
        # Paragraph style
        avg_para = formatting["avg_paragraph_length"]
        if avg_para <= 2:
            parts.append("Uses very short paragraphs (1-2 sentences)")
        elif avg_para <= 4:
            parts.append("Uses moderate-length paragraphs (3-4 sentences)")
        else:
            parts.append("Uses longer paragraphs (5+ sentences)")
        
        # Bullet usage
        if formatting["uses_bullet_points"]:
            if formatting["bullet_frequency"] > 0.2:
                parts.append("Heavy use of bullet points and lists")
            else:
                parts.append("Occasional use of bullet points")
        else:
            parts.append("Rarely or never uses bullet points")
        
        # Sentence style
        if sentence_info["short_sentence_ratio"] > 0.3:
            parts.append("Frequently uses punchy, short sentences for emphasis")
        if sentence_info["long_sentence_ratio"] > 0.2:
            parts.append("Includes longer, detailed sentences")
        
        return ". ".join(parts) + "."
    
    def extract_sample_excerpts(self, count: int = 5, max_length: int = 200) -> list[str]:
        """Select representative short excerpts from the writing samples."""
        excerpts = []
        for sample in self.samples:
            sentences = split_sentences(sample)
            if sentences:
                # Take the first 2-3 sentences or up to max_length chars
                excerpt = ""
                for s in sentences[:3]:
                    if len(excerpt) + len(s) <= max_length:
                        excerpt += s + " "
                    else:
                        break
                if excerpt.strip():
                    excerpts.append(excerpt.strip())
        
        return excerpts[:count]
    
    def generate_style_summary(self) -> str:
        """Generate a comprehensive natural language summary of the writing style."""
        metrics_sent = self.analyze_sentence_structure()
        metrics_q = self.analyze_questions_hooks()
        metrics_fmt = self.analyze_formatting()
        metrics_vocab = self.analyze_vocabulary()
        metrics_punct = self.analyze_punctuation_emoji()
        metrics_rhythm = self.analyze_rhythm()
        
        summary_parts = []
        
        # Overall rhythm
        avg_len = metrics_sent["avg_sentence_length"]
        if avg_len < 10:
            summary_parts.append("This writer uses notably short, punchy sentences")
        elif avg_len < 15:
            summary_parts.append("This writer uses moderate-length sentences")
        else:
            summary_parts.append("This writer tends toward longer, more detailed sentences")
        
        # Variation
        variation = metrics_rhythm["sentence_length_variation"]
        if variation == "high":
            summary_parts.append("with high variation between short and long sentences, creating a dynamic rhythm")
        elif variation == "medium":
            summary_parts.append("with moderate variation in sentence length")
        else:
            summary_parts.append("with consistent sentence lengths throughout")
        
        # Questions
        if metrics_q["question_ratio"] > 0.15:
            summary_parts.append("They frequently use rhetorical questions to engage readers")
        elif metrics_q["question_ratio"] > 0.05:
            summary_parts.append("They occasionally use questions")
        
        # Exclamations
        if metrics_q["exclamation_ratio"] > 0.1:
            summary_parts.append("Exclamation marks are used liberally for emphasis and energy")
        
        # Vocabulary
        if metrics_vocab["vocabulary_richness"] > 0.6:
            summary_parts.append("The vocabulary is rich and varied")
        elif metrics_vocab["vocabulary_richness"] < 0.4:
            summary_parts.append("The vocabulary is focused and repetitive (which creates familiarity)")
        
        # Contractions
        if metrics_vocab["contraction_ratio"] > 0.03:
            summary_parts.append("Heavy use of contractions gives a conversational, informal tone")
        elif metrics_vocab["contraction_ratio"] < 0.01:
            summary_parts.append("Minimal contractions suggest a more formal tone")
        
        # Formatting
        if metrics_fmt["uses_bullet_points"]:
            summary_parts.append("Bullet points and lists are part of the formatting style")
        
        # Emoji
        if metrics_punct["emoji_frequency"] > 0.5:
            summary_parts.append("Emojis are used frequently as part of the communication style")
        elif metrics_punct["emoji_frequency"] > 0:
            summary_parts.append("Emojis are used sparingly")
        
        # Dashes
        if metrics_punct["dash_frequency"] > 0.5:
            summary_parts.append("Dashes are used frequently for emphasis or asides")
        
        # Opening style
        if metrics_rhythm["opens_with_short_sentence"] > 0.5:
            summary_parts.append("Paragraphs often open with a short, punchy statement")
        
        return ". ".join(summary_parts) + "."
    
    def analyze(self) -> dict:
        """
        Run the complete style analysis pipeline.
        
        Returns a dictionary with all style metrics and qualitative features.
        """
        # Quantitative metrics
        sentence_metrics = self.analyze_sentence_structure()
        question_metrics = self.analyze_questions_hooks()
        formatting_metrics = self.analyze_formatting()
        vocabulary_metrics = self.analyze_vocabulary()
        punctuation_metrics = self.analyze_punctuation_emoji()
        rhythm_metrics = self.analyze_rhythm()
        
        metrics = {
            **sentence_metrics,
            **question_metrics,
            **formatting_metrics,
            **vocabulary_metrics,
            **punctuation_metrics,
            **rhythm_metrics,
        }
        
        # Qualitative features
        signature_phrases = self.extract_signature_phrases()
        vocabulary_preferences = self.extract_vocabulary_preferences()
        sentence_starters = self.extract_sentence_starters()
        transition_words = self.extract_transition_words()
        formatting_style = self.describe_formatting_style()
        sample_excerpts = self.extract_sample_excerpts()
        style_summary = self.generate_style_summary()
        
        return {
            "metrics": metrics,
            "signature_phrases": signature_phrases,
            "vocabulary_preferences": vocabulary_preferences,
            "sentence_starters": sentence_starters,
            "transition_words": transition_words,
            "formatting_style": formatting_style,
            "sample_excerpts": sample_excerpts,
            "raw_style_summary": style_summary,
        }
