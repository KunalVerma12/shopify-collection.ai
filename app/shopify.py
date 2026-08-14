import time
import base64
import hmac
import hashlib
import json
import requests
from typing import Dict, Any, Tuple, List, Optional
from functools import wraps
from flask import request, jsonify
from app import config

# Thread-safe in-memory cache for the offline access token
_cached_offline_token: Optional[str] = None

# In-memory debug logs to inspect authentication issues securely
_debug_logs: List[str] = []

def add_debug_log(msg: str) -> None:
    global _debug_logs
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    _debug_logs.append(f"[{timestamp}] {msg}")
    if len(_debug_logs) > 100:
        _debug_logs.pop(0)

def base64url_decode(input_str: str) -> bytes:
    """Decodes a base64url encoded string (JWT format)."""
    input_str = input_str.replace('-', '+').replace('_', '/')
    padding = len(input_str) % 4
    if padding == 2:
        input_str += '=='
    elif padding == 3:
        input_str += '='
    return base64.b64decode(input_str)

def decode_and_verify_shopify_token(token: str, client_secret: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a Shopify JWT session token.
    
    Verified claims include signature (using Client Secret and HS256), exp, nbf, aud, and dest.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            add_debug_log("JWT Error: Token does not have exactly 3 parts.")
            return None
            
        header_b64, payload_b64, signature_b64 = parts
        
        # 1. Verify alg is HS256 in header
        header_data = json.loads(base64url_decode(header_b64).decode('utf-8'))
        if header_data.get('alg') != 'HS256':
            add_debug_log(f"JWT Error: Unsupported algorithm '{header_data.get('alg')}'. Expected HS256.")
            return None
            
        # 2. Recalculate signature to verify integrity
        key = client_secret.encode('utf-8')
        message = f"{header_b64}.{payload_b64}".encode('utf-8')
        
        expected_sig = hmac.new(key, message, hashlib.sha256).digest()
        actual_sig = base64url_decode(signature_b64)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            add_debug_log("JWT Error: JWT signature verification failed.")
            return None
            
        # 3. Decode and parse payload claims
        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        
        # Safe logging of claims for telemetry debugging (Step 5)
        add_debug_log(
            f"[Auth Debug] JWT Claims decoded - "
            f"iss: {payload.get('iss')}, "
            f"dest: {payload.get('dest')}, "
            f"aud: {payload.get('aud')}, "
            f"exp: {payload.get('exp')}, "
            f"nbf: {payload.get('nbf')}, "
            f"sub: {payload.get('sub')}"
        )
        
        # 4. Verify time-based claims (exp & nbf with 60s clock skew tolerance)
        now = time.time()
        if 'exp' in payload and now > payload['exp'] + 60:
            add_debug_log(f"JWT Error: Token expired. now={now}, exp={payload['exp']}")
            return None
        if 'nbf' in payload and now < payload['nbf'] - 60:
            add_debug_log(f"JWT Error: Token not active yet. now={now}, nbf={payload['nbf']}")
            return None
            
        # 5. Verify audience matches Client ID
        if payload.get("aud") != config.SHOPIFY_CLIENT_ID:
            add_debug_log(f"JWT Error: Audience mismatch. aud={payload.get('aud')}, expected={config.SHOPIFY_CLIENT_ID}")
            return None
            
        # 6. Verify dest matches expected shop
        dest = payload.get("dest", "")
        if dest.startswith("https://"):
            dest_shop = dest[8:]
        elif dest.startswith("http://"):
            dest_shop = dest[7:]
        else:
            dest_shop = dest
            
        expected_shop = config.SHOPIFY_SHOP
        if expected_shop.startswith("http://"):
            expected_shop = expected_shop[7:]
        elif expected_shop.startswith("https://"):
            expected_shop = expected_shop[8:]
        expected_shop = expected_shop.rstrip("/")
        
        if dest_shop != expected_shop:
            add_debug_log(f"JWT Error: Destination shop mismatch. dest={dest_shop}, expected={expected_shop}")
            return None
            
        add_debug_log("JWT Success: Token verified successfully.")
        return payload
    except Exception as e:
        add_debug_log(f"JWT Error: Exception during decoding: {e}")
        return None

def get_shopify_access_token(session_token: Optional[str] = None) -> str:
    """Retrieves the cached Shopify offline access token or exchanges the session token for a new one."""
    global _cached_offline_token
    
    if _cached_offline_token:
        return _cached_offline_token
        
    if not session_token:
        raise ValueError("Shopify session token is required to perform token exchange.")
        
    config.validate_config()
    
    shop = config.SHOPIFY_SHOP
    if shop.startswith("http://"):
        shop = shop[7:]
    elif shop.startswith("https://"):
        shop = shop[8:]
    shop = shop.rstrip("/")
    
    token_url = f"https://{shop}/admin/oauth/access_token"
    
    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "client_id": config.SHOPIFY_CLIENT_ID,
        "client_secret": config.SHOPIFY_CLIENT_SECRET,
        "subject_token": session_token,
        "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
        "requested_token_type": "urn:shopify:params:oauth:token-type:offline-access-token"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    add_debug_log(f"Token Exchange: Requesting token from: {token_url}...")
    try:
        response = requests.post(token_url, data=payload, headers=headers, timeout=15)
    except requests.RequestException as e:
        add_debug_log(f"Token Exchange Error: Network error: {e}")
        raise ValueError(f"Network error executing Shopify token exchange: {e}")
        
    if response.status_code != 200:
        add_debug_log(f"Token Exchange Error: API status {response.status_code}: {response.text}")
        raise ValueError(
            f"Failed to perform Shopify token exchange. API returned status code {response.status_code}: {response.text}"
        )
        
    try:
        res_json = response.json()
    except ValueError:
        add_debug_log("Token Exchange Error: Invalid JSON response.")
        raise ValueError("Shopify token exchange response was not valid JSON.")
        
    access_token = res_json.get("access_token")
    if not access_token:
        add_debug_log(f"Token Exchange Error: Missing access_token in response: {res_json}")
        raise ValueError(f"Token exchange response did not contain 'access_token'. Response: {res_json}")
        
    add_debug_log("Token Exchange Success: Token received and cached.")
    _cached_offline_token = access_token
    return _cached_offline_token

def get_shopify_headers() -> Dict[str, str]:
    """Helper to return the headers required for Shopify Admin API requests."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise ValueError("Authorization header is missing or does not contain a Bearer token.")
        
    session_token = auth_header.split(" ")[1]
    token = get_shopify_access_token(session_token)
    
    return {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": token
    }

def shopify_auth_required(f):
    """Decorator to require and validate a Shopify session token (JWT) on Flask endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            add_debug_log("[Auth Debug] Authorization header received: False")
            return jsonify({
                "status": "error",
                "message": "Shopify session token missing."
            }), 401
            
        add_debug_log("[Auth Debug] Authorization header received: True")
        if not auth_header.startswith("Bearer "):
            add_debug_log(f"[Auth Debug] Bearer format check failed. Header: {auth_header[:15]}...")
            return jsonify({
                "status": "error",
                "message": "Shopify session token invalid format."
            }), 401
            
        session_token = auth_header.split(" ")[1]
        masked_token = f"{session_token[:10]}...{session_token[-10:]}" if len(session_token) > 20 else "short_token"
        add_debug_log(f"[Auth Debug] Processing token verification for: {masked_token}")
        
        payload = decode_and_verify_shopify_token(session_token, config.SHOPIFY_CLIENT_SECRET)
        if not payload:
            return jsonify({
                "status": "error",
                "message": "Shopify session token verification failed."
            }), 401
            
        return f(*args, **kwargs)
    return decorated

def fetch_collections(limit: int = 50, cursor: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Optional[str], bool]:
    """Fetches shop collections from the Shopify GraphQL API."""
    url = config.get_shopify_graphql_url()
    
    query = """
    query GetCollections($first: Int!, $after: String) {
      collections(first: $first, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            id
            title
            descriptionHtml
            description
          }
        }
      }
    }
    """
    
    variables = {
        "first": limit,
        "after": cursor
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    headers = get_shopify_headers()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
    except requests.RequestException as e:
        raise requests.RequestException(f"Network error communicating with Shopify: {e}")
        
    if response.status_code == 401:
        raise ValueError(
            "Shopify authentication failed. Please verify that your Client credentials are correct and active."
        )
    elif response.status_code != 200:
        raise ValueError(
            f"Shopify Admin API returned status code {response.status_code}: {response.text}"
        )
        
    try:
        res_json = response.json()
    except ValueError:
        raise ValueError("Shopify Admin API response was not valid JSON.")
        
    if "errors" in res_json:
        err_msg = "; ".join([err.get("message", "Unknown error") for err in res_json["errors"]])
        raise ValueError(f"Shopify GraphQL Error: {err_msg}")
        
    data = res_json.get("data", {})
    collections_data = data.get("collections", {})
    
    if not collections_data:
        return [], None, False
        
    edges = collections_data.get("edges", [])
    collections = []
    
    for edge in edges:
        node = edge.get("node", {})
        if node:
            collections.append({
                "id": node.get("id"),
                "title": node.get("title"),
                "descriptionHtml": node.get("descriptionHtml") or "",
                "description": node.get("description") or ""
            })
            
    page_info = collections_data.get("pageInfo", {})
    has_next_page = page_info.get("hasNextPage", False)
    end_cursor = page_info.get("endCursor") if has_next_page else None
    
    return collections, end_cursor, has_next_page

def update_collection_description(collection_id: str, description_html: str) -> Dict[str, Any]:
    """Updates a collection's description in Shopify using the collectionUpdate mutation."""
    url = config.get_shopify_graphql_url()
    
    if not collection_id or not collection_id.startswith("gid://shopify/Collection/"):
        raise ValueError(
            f"Invalid collection ID format: '{collection_id}'. Must be a valid Shopify GID starting with 'gid://shopify/Collection/'"
        )
        
    mutation = """
    mutation collectionUpdate($input: CollectionInput!) {
      collectionUpdate(input: $input) {
        collection {
          id
          title
          descriptionHtml
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    
    variables = {
        "input": {
          "id": collection_id,
          "descriptionHtml": description_html
        }
    }
    
    payload = {
        "query": mutation,
        "variables": variables
    }
    
    headers = get_shopify_headers()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
    except requests.RequestException as e:
        raise requests.RequestException(f"Network error communicating with Shopify: {e}")
        
    if response.status_code == 401:
        raise ValueError(
            "Shopify authentication failed. Please verify that your Client credentials are correct and active."
        )
    elif response.status_code != 200:
        raise ValueError(
            f"Shopify Admin API returned status code {response.status_code}: {response.text}"
        )
        
    try:
        res_json = response.json()
    except ValueError:
        raise ValueError("Shopify Admin API response was not valid JSON.")
        
    if "errors" in res_json:
        err_msg = "; ".join([err.get("message", "Unknown error") for err in res_json["errors"]])
        raise ValueError(f"Shopify GraphQL Error: {err_msg}")
        
    data = res_json.get("data", {})
    mutation_result = data.get("collectionUpdate", {})
    
    if not mutation_result:
        raise ValueError("Shopify returned an empty result for the collection update mutation.")
        
    user_errors = mutation_result.get("userErrors", [])
    if user_errors:
        err_msg = "; ".join([f"{err.get('field', 'General')}: {err.get('message')}" for err in user_errors])
        raise ValueError(f"Shopify User Error: {err_msg}")
        
    updated_collection = mutation_result.get("collection")
    if not updated_collection:
        raise ValueError("No collection data was returned after update.")
        
    return {
        "id": updated_collection.get("id"),
        "title": updated_collection.get("title"),
        "descriptionHtml": updated_collection.get("descriptionHtml") or ""
    }
