"""
Pydantic models for the VoiceStyle API.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WritingSample(BaseModel):
    """A single writing sample from the user."""
    text: str = Field(..., min_length=50, description="Writing sample text (min 50 chars)")


class OnboardRequest(BaseModel):
    """Request to onboard a new user with their writing samples."""
    user_name: str = Field(..., min_length=1, max_length=100, description="Display name for the profile")
    samples: list[WritingSample] = Field(
        ..., min_length=3, max_length=10,
        description="5-7 writing samples from the user"
    )


class RewriteRequest(BaseModel):
    """Request to rewrite text in a user's voice."""
    profile_id: str = Field(..., description="ID of the user's style profile")
    draft_text: str = Field(..., min_length=20, description="Generic/AI text to rewrite")


class StyleMetrics(BaseModel):
    """Quantitative style metrics extracted from writing samples."""
    # Sentence structure
    avg_sentence_length: float = Field(description="Average words per sentence")
    sentence_length_std: float = Field(description="Std deviation of sentence length")
    short_sentence_ratio: float = Field(description="Ratio of sentences with <= 5 words")
    long_sentence_ratio: float = Field(description="Ratio of sentences with >= 20 words")
    
    # Questions & hooks
    question_ratio: float = Field(description="Ratio of sentences that are questions")
    exclamation_ratio: float = Field(description="Ratio of sentences with exclamation marks")
    
    # Formatting
    avg_paragraph_length: float = Field(description="Average sentences per paragraph")
    uses_bullet_points: bool = Field(description="Whether bullet points are used")
    bullet_frequency: float = Field(description="Ratio of lines that are bullet points")
    
    # Vocabulary
    vocabulary_richness: float = Field(description="Type-token ratio (unique/total words)")
    avg_word_length: float = Field(description="Average word length in characters")
    contraction_ratio: float = Field(description="Ratio of words that are contractions")
    
    # Punctuation & style
    emoji_frequency: float = Field(description="Emojis per 100 words")
    ellipsis_frequency: float = Field(description="Ellipses per 100 sentences")
    dash_frequency: float = Field(description="Dashes (—, –, -) per 100 words")
    parenthetical_frequency: float = Field(description="Parentheticals per 100 sentences")
    
    # Rhythm
    opens_with_short_sentence: float = Field(description="Ratio of paragraphs opening with short sentence")
    sentence_length_variation: str = Field(description="Pattern: 'high', 'medium', or 'low'")


class StyleProfile(BaseModel):
    """Complete style profile for a user."""
    id: str
    user_name: str
    created_at: str
    metrics: StyleMetrics
    signature_phrases: list[str] = Field(description="Recurring phrases/expressions")
    vocabulary_preferences: list[str] = Field(description="Frequently used distinctive words")
    sentence_starters: list[str] = Field(description="Common ways to start sentences")
    transition_words: list[str] = Field(description="Frequently used transition words")
    formatting_style: str = Field(description="Description of formatting patterns")
    sample_excerpts: list[str] = Field(description="Representative short excerpts")
    raw_style_summary: str = Field(description="Natural language summary of writing style")


class RewriteResponse(BaseModel):
    """Response containing the rewritten text."""
    original_text: str
    rewritten_text: str
    profile_id: str
    style_notes: list[str] = Field(description="Notes on what style adjustments were made")


class ProfileListItem(BaseModel):
    """Summary of a style profile for listing."""
    id: str
    user_name: str
    created_at: str
    sample_count: int
