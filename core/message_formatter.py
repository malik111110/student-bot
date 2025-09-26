"""Message formatting utilities for better UI/UX in Telegram."""

import re


def clean_markdown(text: str) -> str:
    """
    Clean markdown formatting from text for better Telegram display.
    
    Args:
        text: Raw text with potential markdown formatting
        
    Returns:
        Cleaned text suitable for Telegram messages
    """
    if not text:
        return text
    
    # Remove markdown headers (# ## ### etc.)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold formatting (**text** or __text__)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # Remove italic formatting (*text* or _text_)
    text = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)', r'\1', text)
    text = re.sub(r'(?<!_)_(?!_)([^_]+?)(?<!_)_(?!_)', r'\1', text)
    
    # Remove strikethrough (~~text~~)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    
    # Remove code blocks (```code``` or `code`)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+?)`', r'\1', text)
    
    # Remove links but keep the text [text](url) -> text
    text = re.sub(r'\[([^\]]+?)\]\([^)]+?\)', r'\1', text)
    
    # Remove horizontal rules (--- or ***)
    text = re.sub(r'^[-*]{3,}$', '', text, flags=re.MULTILINE)
    
    # Clean up bullet points and lists
    # Convert markdown lists to simple bullet points
    text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '• ', text, flags=re.MULTILINE)
    
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
    text = re.sub(r'[ \t]+', ' ', text)     # Multiple spaces to single space
    
    # Clean up line breaks at start/end
    text = text.strip()
    
    return text


def format_ai_response(text: str) -> str:
    """
    Format AI response for optimal Telegram display.
    
    Args:
        text: Raw AI response text
        
    Returns:
        Formatted text optimized for Telegram
    """
    if not text:
        return text
    
    # First clean markdown
    text = clean_markdown(text)
    
    # Improve readability with better structure
    text = improve_readability(text)
    
    # Add emojis for better visual appeal (sparingly)
    text = enhance_with_emojis(text)
    
    # Ensure proper paragraph spacing
    text = format_paragraphs(text)
    
    return text


def improve_readability(text: str) -> str:
    """Improve text readability for Telegram messages."""
    
    # Add spacing around colons for better readability
    text = re.sub(r'([a-zA-Z]):', r'\1:', text)
    
    # Ensure proper spacing after periods
    text = re.sub(r'\.([A-Z])', r'. \1', text)
    
    # Clean up common AI response patterns
    text = re.sub(r'^(Here are|Here\'s|These are)', r'', text, flags=re.IGNORECASE)
    text = re.sub(r'^(In summary|To summarize)', r'Summary:', text, flags=re.IGNORECASE)
    text = re.sub(r'^(In conclusion)', r'Conclusion:', text, flags=re.IGNORECASE)
    
    # Remove redundant phrases
    text = re.sub(r'\b(as follows|as mentioned|as stated)\b', '', text, flags=re.IGNORECASE)
    
    # Clean up excessive enthusiasm
    text = re.sub(r'!{2,}', '!', text)
    
    return text


def enhance_with_emojis(text: str) -> str:
    """Add relevant emojis to make messages more engaging (limited to avoid overuse)."""
    
    # Only add emojis to key educational topics (first occurrence only)
    text = re.sub(r'\b(machine learning)\b', r'🤖 \1', text, flags=re.IGNORECASE, count=1)
    text = re.sub(r'\b(artificial intelligence)\b', r'🧠 \1', text, flags=re.IGNORECASE, count=1)
    text = re.sub(r'\b(cybersecurity)\b', r'🔒 \1', text, flags=re.IGNORECASE, count=1)
    text = re.sub(r'\b(network)\b', r'🌐 \1', text, flags=re.IGNORECASE, count=1)
    text = re.sub(r'\b(database)\b', r'💾 \1', text, flags=re.IGNORECASE, count=1)
    text = re.sub(r'\b(programming)\b', r'💻 \1', text, flags=re.IGNORECASE, count=1)
    
    # Add emojis to important callouts
    text = re.sub(r'\b(Important|Note|Remember):', r'⚡ \1:', text)
    text = re.sub(r'\b(Tip|Advice):', r'💡 \1:', text)
    text = re.sub(r'\b(Example|Instance):', r'📋 \1:', text)
    
    return text


def format_paragraphs(text: str) -> str:
    """Ensure proper paragraph formatting for readability."""
    
    # Split into paragraphs
    paragraphs = text.split('\n\n')
    
    formatted_paragraphs = []
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph:
            # Ensure sentences end with proper punctuation
            if paragraph and not paragraph[-1] in '.!?':
                paragraph += '.'
            formatted_paragraphs.append(paragraph)
    
    # Join with proper spacing
    return '\n\n'.join(formatted_paragraphs)


def format_voice_text(text: str) -> str:
    """
    Format text specifically for voice synthesis.
    
    Args:
        text: Text to be converted to speech
        
    Returns:
        Text optimized for voice synthesis
    """
    if not text:
        return text
    
    # Clean markdown first
    text = clean_markdown(text)
    
    # Remove emojis for voice (they don't speak well)
    text = re.sub(r'[^\w\s\.,!?;:\-\(\)]+', '', text)
    
    # Replace abbreviations with full words for better pronunciation
    replacements = {
        'AI': 'Artificial Intelligence',
        'ML': 'Machine Learning',
        'API': 'A P I',
        'URL': 'U R L',
        'HTTP': 'H T T P',
        'CSS': 'C S S',
        'HTML': 'H T M L',
        'SQL': 'S Q L',
        'JSON': 'J S O N',
        'XML': 'X M L',
        'UI': 'User Interface',
        'UX': 'User Experience',
        'OS': 'Operating System',
        'CPU': 'C P U',
        'GPU': 'G P U',
        'RAM': 'R A M',
        'SSD': 'S S D',
        'HDD': 'H D D',
    }
    
    for abbr, full in replacements.items():
        text = re.sub(r'\b' + re.escape(abbr) + r'\b', full, text, flags=re.IGNORECASE)
    
    # Ensure proper sentence structure
    text = re.sub(r'([.!?])\s*([a-z])', r'\1 \2', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[.]{2,}', '.', text)
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    
    return text.strip()