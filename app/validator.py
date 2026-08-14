from typing import Tuple, Optional

def validate_description(text: str) -> Tuple[bool, Optional[str]]:
    """Validates the generated collection description using lightweight rules.
    
    Args:
        text (str): The generated description text.
        
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_reason)
            - is_valid: True if the description is valid, False otherwise.
            - error_reason: The reason for validation failure, or None if valid.
    """
    if not isinstance(text, str):
        return False, "The description must be a string."
        
    cleaned_text = text.strip()
    
    # Check for empty or whitespace-only response
    if not cleaned_text:
        return False, "The description is empty."
        
    # Length Validation (40-600 characters is a reasonable range for a short, professional description)
    min_length = 25
    max_length = 600
    
    text_len = len(cleaned_text)
    if text_len < min_length:
        return False, f"The description is too short ({text_len} characters). Minimum allowed is {min_length}."
    if text_len > max_length:
        return False, f"The description is too long ({text_len} characters). Maximum allowed is {max_length}."
        
    # Check for raw markdown blocks or brackets indicative of code structure
    if "```" in cleaned_text:
        return False, "The response contains raw markdown code blocks (```)."
        
    # Check for raw structural html page tags (allowing normal inline tags like <b> or <p> but rejecting wrapper scaffolding)
    for tag in ["<html>", "<body>", "</div>", "</span>", "href="]:
        if tag in cleaned_text.lower():
            return False, f"The response contains raw structural code/links: '{tag}'."
            
    # Check if the output looks like structured JSON or lists rather than copy
    if (cleaned_text.startswith("{") and cleaned_text.endswith("}")) or \
       (cleaned_text.startswith("[") and cleaned_text.endswith("]")):
        return False, "The description appears to be JSON or structured data instead of plain text copy."
        
    # Check for common conversational boilerplate or prompt leakage from AI
    boilerplate_phrases = [
        "here is a description",
        "here's a description",
        "description:",
        "brand name:",
        "collection title",
        "as requested",
        "sure! here is",
        "sure, here's",
        "copywriting",
        "gpt-",
        "openai"
    ]
    
    lower_text = cleaned_text.lower()
    for phrase in boilerplate_phrases:
        if phrase in lower_text:
            return False, f"The description contains AI conversational text: '{phrase}'."
            
    return True, None
