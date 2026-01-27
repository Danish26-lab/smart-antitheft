"""
Vercel Root API Entry Point
This is a simpler entry point at the root api/ directory
"""

import sys
import os
from pathlib import Path

# Set Vercel environment flag
os.environ['VERCEL'] = '1'

# Add backend directory to Python path
project_root = Path(__file__).parent.parent
backend_dir = project_root / 'backend'
backend_path = str(backend_dir.resolve())

# Add to Python path
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Change working directory to backend for relative imports
try:
    os.chdir(backend_path)
except Exception:
    pass  # Ignore if can't change directory

# Initialize Flask app variable
app = None
application = None

try:
    # Import the Flask app instance
    from app import app
    
    # Vercel automatically wraps Flask WSGI apps
    # Export both 'app' and 'application' for compatibility
    application = app
    
    print(f"[VERCEL] Flask app loaded successfully from {backend_path}")
    
except Exception as e:
    import traceback
    error_msg = str(e)
    error_trace = traceback.format_exc()
    
    print(f"[VERCEL ERROR] Failed to load Flask app: {error_msg}")
    print(f"[VERCEL ERROR] Traceback: {error_trace}")
    
    # Create minimal error handler Flask app
    try:
        from flask import Flask, jsonify
        error_app = Flask(__name__)
        
        @error_app.route('/', defaults={'path': ''})
        @error_app.route('/<path:path>')
        def error_handler(path):
            try:
                return jsonify({
                    'error': 'Flask initialization failed',
                    'message': error_msg[:200],  # Limit message length
                    'type': type(e).__name__,
                    'status': 'error'
                }), 500
            except Exception as json_error:
                # If jsonify fails, return plain text
                return f"Error: Flask initialization failed - {error_msg[:200]}", 500
        
        app = error_app
        application = error_app
    except Exception as flask_error:
        # If Flask itself fails to import, create a minimal WSGI app
        print(f"[CRITICAL] Cannot create Flask error handler: {flask_error}")
        
        def minimal_app(environ, start_response):
            """Minimal WSGI app as last resort"""
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'application/json')]
            body = b'{"error":"Flask initialization failed","status":"error"}'
            start_response(status, headers)
            return [body]
        
        app = minimal_app
        application = minimal_app

# Ensure app and application are always defined
if app is None:
    # Last resort - create minimal app
    try:
        from flask import Flask, jsonify
        app = Flask(__name__)
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def fallback(path):
            return jsonify({'error': 'App not initialized', 'status': 'error'}), 500
        application = app
    except:
        def minimal_wsgi(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'application/json')]
            body = b'{"error":"App initialization failed","status":"error"}'
            start_response(status, headers)
            return [body]
        app = minimal_wsgi
        application = minimal_wsgi

__all__ = ['app', 'application']
