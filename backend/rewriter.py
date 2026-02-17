"""
Rewriter — Applies a user's style profile to rewrite generic text.

Uses Google Gemini (free tier) as the LLM backbone, but the prompt is built
entirely from the programmatic style analysis — not vague instructions.

The rewriting prompt includes:
1. Concrete quantitative targets (sentence length, question frequency, etc.)
2. The user's actual vocabulary preferences and signature phrases
3. Representative excerpts from the user's writing
4. Specific formatting instructions derived from analysis

This ensures the rewrite is structured, repeatable, and grounded in data.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


def _configure_gemini():
    """Configure the Gemini API with the free API key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com/app/apikey "
            "and add it to backend/.env"
        )
    genai.configure(api_key=api_key)


def build_rewrite_prompt(style_profile: dict, draft_text: str) -> str:
    """
    Construct a detailed, data-driven prompt for rewriting text.
    
    Instead of saying 'rewrite in this style', we give the LLM
    specific, measurable instructions based on the style analysis.
    """
    metrics = style_profile["metrics"]
    
    # Build sentence length instructions
    avg_len = metrics["avg_sentence_length"]
    short_ratio = metrics["short_sentence_ratio"]
    long_ratio = metrics["long_sentence_ratio"]
    
    sentence_instructions = f"""SENTENCE STRUCTURE:
- Target average sentence length: ~{avg_len:.0f} words per sentence
- About {short_ratio*100:.0f}% of sentences should be SHORT (5 words or fewer)
- About {long_ratio*100:.0f}% of sentences should be LONG (20+ words)
- Sentence length variation: {metrics['sentence_length_variation']}"""
    
    # Questions and hooks
    q_ratio = metrics["question_ratio"]
    exc_ratio = metrics["exclamation_ratio"]
    
    question_instructions = f"""QUESTIONS & EMPHASIS:
- Approximately {q_ratio*100:.0f}% of sentences should be questions{'  (use rhetorical questions to engage the reader)' if q_ratio > 0.1 else ''}
- Approximately {exc_ratio*100:.0f}% of sentences should use exclamation marks{'  (inject energy and enthusiasm)' if exc_ratio > 0.05 else ''}"""
    
    # Formatting
    formatting_instructions = f"""FORMATTING:
- {style_profile['formatting_style']}
- Average paragraph length: ~{metrics['avg_paragraph_length']:.0f} sentences
- {'USE bullet points where appropriate' if metrics['uses_bullet_points'] else 'AVOID bullet points — use flowing prose instead'}"""
    
    # Vocabulary
    vocab_prefs = style_profile.get("vocabulary_preferences", [])
    signature_phrases = style_profile.get("signature_phrases", [])
    transition_words = style_profile.get("transition_words", [])
    sentence_starters = style_profile.get("sentence_starters", [])
    
    vocab_instructions = f"""VOCABULARY & WORD CHOICE:
- Vocabulary richness (variety): {metrics['vocabulary_richness']:.2f} {'(use varied, rich vocabulary)' if metrics['vocabulary_richness'] > 0.5 else '(keep vocabulary focused and familiar)'}
- {'Use contractions freely (conversational tone)' if metrics['contraction_ratio'] > 0.02 else 'Minimize contractions (more formal tone)'}
- Preferred words to incorporate naturally: {', '.join(vocab_prefs[:10]) if vocab_prefs else 'N/A'}
- Signature phrases to use when fitting: {', '.join(signature_phrases[:7]) if signature_phrases else 'N/A'}
- Transition words this writer prefers: {', '.join(transition_words[:7]) if transition_words else 'N/A'}
- Common sentence openers: {', '.join(sentence_starters[:7]) if sentence_starters else 'N/A'}"""
    
    # Punctuation and emoji
    punct_instructions = ""
    if metrics["emoji_frequency"] > 0:
        punct_instructions += f"\n- Use emojis: approximately {metrics['emoji_frequency']:.1f} per 100 words"
    else:
        punct_instructions += "\n- Do NOT use emojis"
    
    if metrics["dash_frequency"] > 0.3:
        punct_instructions += "\n- Use dashes (—) for emphasis and asides"
    
    if metrics["ellipsis_frequency"] > 0:
        punct_instructions += "\n- Occasionally use ellipses (...) for dramatic effect"
    
    if metrics["parenthetical_frequency"] > 5:
        punct_instructions += "\n- Use parenthetical remarks for side notes"

    punct_section = f"""PUNCTUATION & SPECIAL CHARACTERS:{punct_instructions}"""
    
    # Rhythm
    rhythm_instructions = ""
    if metrics["opens_with_short_sentence"] > 0.4:
        rhythm_instructions += "\n- START paragraphs with a short, punchy statement"
    
    variation = metrics["sentence_length_variation"]
    if variation == "high":
        rhythm_instructions += "\n- Alternate between short punchy sentences and longer detailed ones"
    elif variation == "medium":
        rhythm_instructions += "\n- Mix sentence lengths naturally"
    else:
        rhythm_instructions += "\n- Keep sentence lengths relatively consistent"
    
    rhythm_section = f"""RHYTHM & FLOW:{rhythm_instructions}"""
    
    # Sample excerpts for reference
    excerpts = style_profile.get("sample_excerpts", [])
    excerpt_section = ""
    if excerpts:
        excerpt_section = "\nREFERENCE EXCERPTS (match this voice and feel):\n"
        for i, ex in enumerate(excerpts, 1):
            excerpt_section += f'  [{i}] "{ex}"\n'
    
    # Style summary
    summary = style_profile.get("raw_style_summary", "")
    
    prompt = f"""You are a writing style transfer engine. Your job is to rewrite the provided draft text 
so it sounds EXACTLY like a specific writer. You must follow the precise style specifications below.

Do NOT change the core meaning or key information in the draft.
Do NOT add new facts or claims not present in the original.
DO transform the voice, structure, rhythm, vocabulary, and formatting to match the writer's style.

=== WRITER'S STYLE PROFILE ===

OVERALL VOICE: {summary}

{sentence_instructions}

{question_instructions}

{formatting_instructions}

{vocab_instructions}

{punct_section}

{rhythm_section}

{excerpt_section}

=== DRAFT TEXT TO REWRITE ===

{draft_text}

=== INSTRUCTIONS ===

Rewrite the draft text above to match this writer's voice precisely. Follow EVERY style specification.
The output should read as if the writer personally wrote it from scratch.
Output ONLY the rewritten text — no explanations, no meta-commentary, no headers."""

    return prompt


def build_style_notes_prompt(style_profile: dict, original: str, rewritten: str) -> str:
    """Build a prompt to generate notes about what style changes were made."""
    return f"""Analyze the differences between the original text and the rewritten version.
List 3-5 specific style adjustments that were made to match the target writer's voice.
Be concrete and specific (e.g., "Shortened average sentence length from ~18 to ~12 words").

Original:
{original[:500]}

Rewritten:
{rewritten[:500]}

Target style summary: {style_profile.get('raw_style_summary', '')}

Return ONLY a JSON array of strings, each describing one adjustment. Example:
["Shortened sentences to match target avg of 11 words", "Added rhetorical questions"]"""


async def rewrite_text(style_profile: dict, draft_text: str) -> dict:
    """
    Rewrite the draft text to match the user's style profile.
    
    Args:
        style_profile: Complete style profile from the analyzer
        draft_text: The generic/AI text to rewrite
        
    Returns:
        Dictionary with rewritten_text and style_notes
    """
    _configure_gemini()
    
    # Build the detailed, data-driven prompt
    prompt = build_rewrite_prompt(style_profile, draft_text)
    
    # Use Gemini Flash (free tier, fast)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    # Generate the rewrite
    response = await model.generate_content_async(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.7,  # Some creativity but mostly faithful
            top_p=0.9,
            max_output_tokens=2048,
        ),
    )
    
    rewritten_text = response.text.strip()
    
    # Generate style notes (what was changed)
    try:
        notes_prompt = build_style_notes_prompt(style_profile, draft_text, rewritten_text)
        notes_response = await model.generate_content_async(
            notes_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=512,
            ),
        )
        
        import json
        notes_text = notes_response.text.strip()
        # Try to parse JSON array from the response
        if notes_text.startswith("```"):
            notes_text = notes_text.split("```")[1]
            if notes_text.startswith("json"):
                notes_text = notes_text[4:]
        style_notes = json.loads(notes_text)
        if not isinstance(style_notes, list):
            style_notes = [str(style_notes)]
    except Exception:
        style_notes = ["Text was rewritten to match the user's writing style profile"]
    
    return {
        "rewritten_text": rewritten_text,
        "style_notes": style_notes,
    }
