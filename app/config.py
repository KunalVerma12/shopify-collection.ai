import os
from pathlib import Path
from dotenv import load_dotenv

# Find the project root directory containing the .env file
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

# Load environment variables from the .env file
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # Fallback to system environment variables
    load_dotenv()

# Shopify API Configuration
SHOPIFY_SHOP = os.getenv("SHOPIFY_SHOP") or os.getenv("SHOPIFY_SHOP_URL")
# Keep aliases for maximum backward compatibility
SHOPIFY_SHOP_URL = SHOPIFY_SHOP

# Strip spaces if loaded with spaces from custom .env setups
SHOPIFY_CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID", "").strip()
SHOPIFY_CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET", "").strip()
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2026-07").strip()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o").strip()

def get_shopify_graphql_url() -> str:
    """Cleans the SHOPIFY_SHOP_URL and constructs the GraphQL API endpoint.
    
    Returns:
        str: The full URL to the Shopify Admin GraphQL API endpoint, or empty string if not configured.
    """
    if not SHOPIFY_SHOP_URL:
        return ""
    
    url = SHOPIFY_SHOP_URL.strip()
    # Remove protocol prefix if present
    if url.startswith("http://"):
        url = url[7:]
    elif url.startswith("https://"):
        url = url[8:]
    
    # Remove trailing slash if present
    url = url.rstrip("/")
    
    return f"https://{url}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"

def validate_config() -> None:
    """Validates that all required environment variables are configured.
    
    Raises:
        ValueError: If any required configuration variable is missing or empty.
    """
    missing_vars = []
    
    if not SHOPIFY_SHOP or not SHOPIFY_SHOP.strip():
        missing_vars.append("SHOPIFY_SHOP or SHOPIFY_SHOP_URL")
    if not SHOPIFY_CLIENT_ID or not SHOPIFY_CLIENT_ID.strip():
        missing_vars.append("SHOPIFY_CLIENT_ID")
    if not SHOPIFY_CLIENT_SECRET or not SHOPIFY_CLIENT_SECRET.strip():
        missing_vars.append("SHOPIFY_CLIENT_SECRET")
    if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
        missing_vars.append("OPENAI_API_KEY")
        
    if missing_vars:
        vars_list = ", ".join(missing_vars)
        raise ValueError(
            f"Configuration Error: Missing required environment variable(s): {vars_list}.\n"
            f"Please check your .env file and ensure these are defined."
        )
