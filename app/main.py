import os
import sys
from flask import Flask, jsonify, request, send_from_directory
from app import config, shopify, generator

# Initialize Flask app
# Static assets are located in 'app/static'
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

app = Flask(__name__, static_folder=static_dir, static_url_path='')

@app.after_request
def add_security_headers(response):
    """Allows the application to be framed inside Shopify Admin by updating CSP and frame options."""
    response.headers.pop("X-Frame-Options", None)
    # Allow framing by Shopify admin and the specific shop domain
    shop = config.SHOPIFY_SHOP or "sarinskin.myshopify.com"
    shop_domain = shop.replace("https://", "").replace("http://", "").split("/")[0]
    csp_value = f"frame-ancestors https://admin.shopify.com https://{shop_domain} https://*.myshopify.com;"
    response.headers["Content-Security-Policy"] = csp_value
    return response

@app.route('/')
def index():
    """Serves the Single Page Application UI with dynamically injected API key."""
    index_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            html = f.read()
        # Injects the API Key for App Bridge v4
        client_id = config.SHOPIFY_CLIENT_ID or ""
        html = html.replace("%SHOPIFY_CLIENT_ID%", client_id)
        return html
    return "index.html not found", 404

@app.route('/api/config-check', methods=['GET'])
def get_config_check():
    """Checks if environment configuration variables are populated."""
    try:
        config.validate_config()
        return jsonify({
            "status": "valid",
            "shopify_shop_url": config.SHOPIFY_SHOP_URL,
            "shopify_api_version": config.SHOPIFY_API_VERSION,
            "openai_model": config.OPENAI_MODEL,
            "shopify_client_id": config.SHOPIFY_CLIENT_ID
        })
    except ValueError as e:
        return jsonify({
            "status": "invalid",
            "error": str(e)
        })

@app.route('/api/collections', methods=['GET'])
@shopify.shopify_auth_required
def get_collections():
    """Fetches paginated list of collections from Shopify."""
    limit = request.args.get('limit', 20, type=int)
    cursor = request.args.get('cursor', None, type=str)
    
    try:
        collections, next_cursor, has_next = shopify.fetch_collections(limit=limit, cursor=cursor)
        return jsonify({
            "status": "success",
            "collections": collections,
            "next_cursor": next_cursor,
            "has_next": has_next
        })
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/generate', methods=['POST'])
@shopify.shopify_auth_required
def post_generate():
    """Generates and validates a collection description based on the collection title (brand name)."""
    data = request.json or {}
    brand_name = data.get('brand_name', '')
    
    if not brand_name:
        return jsonify({
            "status": "error",
            "message": "Required parameter 'brand_name' is missing."
        }), 400
        
    try:
        result = generator.generate_and_validate(brand_name)
        if result["is_valid"]:
            return jsonify({
                "status": "success",
                "description": result["description"]
            })
        else:
            return jsonify({
                "status": "validation_error",
                "description": result["description"],
                "error": result["error"]
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/approve', methods=['POST'])
@shopify.shopify_auth_required
def post_approve():
    """Updates a collection's description in Shopify after user approval."""
    data = request.json or {}
    collection_id = data.get('collection_id', '')
    description = data.get('description', '')
    
    if not collection_id or not description:
        return jsonify({
            "status": "error",
            "message": "Required parameters 'collection_id' and 'description' are missing."
        }), 400
        
    try:
        result = shopify.update_collection_description(collection_id, description)
        return jsonify({
            "status": "success",
            "collection": result
        })
    except ValueError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
@app.route('/api/auth-debug', methods=['GET', 'POST'])
def get_auth_debug():
    """Allows checking or posting backend JWT authentication logs securely."""
    if request.method == 'POST':
        data = request.json or {}
        error = data.get('error')
        stack = data.get('stack')
        if error:
            shopify.add_debug_log(f"FRONTEND ERROR: {error} | Stack: {stack}")
        else:
            shopify.add_debug_log(f"FRONTEND DEBUG: {data}")
        return jsonify({"status": "logged"})
        
    return jsonify({
        "debug_logs": shopify._debug_logs,
        "shopify_shop": config.SHOPIFY_SHOP,
        "shopify_client_id": config.SHOPIFY_CLIENT_ID
    })

if __name__ == "__main__":
    print("Initializing Shopify Collection AI Description Generator...")
    # Port 5001 to avoid potential macOS conflicts on 5000
    app.run(host="127.0.0.1", port=5001, debug=True)
