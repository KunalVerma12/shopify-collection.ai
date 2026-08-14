from openai import OpenAI
from app import config

def get_openai_client() -> OpenAI:
    """Initializes and returns the OpenAI client after validating configuration."""
    config.validate_config()
    return OpenAI(api_key=config.OPENAI_API_KEY)

def generate_brand_description(brand_name: str) -> str:
    """Generates a professional Shopify collection description using OpenAI.
    
    Args:
        brand_name (str): The name of the brand or collection.
        
    Returns:
        str: The generated text description.
        
    Raises:
        ValueError: If config is invalid or response is empty.
        Exception: If the OpenAI API request fails.
    """
    client = get_openai_client()
    
    system_prompt = (
        "You are an expert e-commerce copywriter. Write a concise, natural, and professional description "
        "for a Shopify collection page based ONLY on the provided brand or collection name.\n\n"
        "Guidelines:\n"
        "- Write a single, brief paragraph (typically 2 to 4 sentences, 40 to 80 words max).\n"
        "- Maintain a clean, professional, and natural tone.\n"
        "- Do NOT invent specific product names, formulas, or specific physical items (e.g., do not say 'includes the AhaGlow Face Wash').\n"
        "- Do NOT mention specific ingredients or chemical formulas.\n"
        "- Do NOT make unsupported medical, therapeutic, or health claims.\n"
        "- Avoid excessive marketing jargon, hyperbole, or exclamation marks.\n"
        "- Return ONLY the description text. Do NOT include markdown code blocks, titles, or headers like 'Description:'."
    )
    
    user_prompt = f"Brand name: {brand_name}"
    
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL or "gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=250
        )
        
        choices = response.choices
        if not choices or not choices[0].message or not choices[0].message.content:
            raise ValueError("OpenAI API returned an empty response.")
            
        generated_text = choices[0].message.content.strip()
        
        # Strip simple quotes or markdown code blocks if the model accidentally included them
        if generated_text.startswith("```"):
            lines = generated_text.split("\n")
            # If it's a code block, strip first and last line
            if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].startswith("```"):
                generated_text = "\n".join(lines[1:-1]).strip()
                
        # Strip quotes if the model wrapped the description in quotes
        if (generated_text.startswith('"') and generated_text.endswith('"')) or \
           (generated_text.startswith("'") and generated_text.endswith("'")):
            generated_text = generated_text[1:-1].strip()
            
        return generated_text
        
    except Exception as e:
        raise Exception(f"OpenAI API call failed: {str(e)}")
