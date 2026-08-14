from typing import Dict, Any
from app.openai_client import generate_brand_description
from app.validator import validate_description

def generate_and_validate(brand_name: str) -> Dict[str, Any]:
    """Orchestrates generation of a collection description and validates the output.
    
    Args:
        brand_name (str): The brand or collection title.
        
    Returns:
        Dict[str, Any]: A result dictionary with:
            - 'description' (str): The generated description.
            - 'is_valid' (bool): True if validation passed.
            - 'error' (str): None if valid, or a validation/API error message.
    """
    cleaned_name = brand_name.strip() if brand_name else ""
    if not cleaned_name:
        return {
            "description": "",
            "is_valid": False,
            "error": "The brand or collection name is empty."
        }
        
    try:
        # Generate description using OpenAI
        description = generate_brand_description(cleaned_name)
        
        # Run validation
        is_valid, error_reason = validate_description(description)
        
        return {
            "description": description,
            "is_valid": is_valid,
            "error": error_reason
        }
        
    except Exception as e:
        # Catch API issues, configuration errors, and propagation failures
        return {
            "description": "",
            "is_valid": False,
            "error": str(e)
        }
