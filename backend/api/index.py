"""
Backend-scoped Vercel API entry point.
This mirrors the root-level api/index.py so that deployments
with Root Directory = "backend" still work.
"""

import sys
import os
from pathlib import Path

# Set Vercel environment flag
os.environ['VERCEL'] = '1'

# backend_dir is the parent of this file's directory (backend/)
backend_dir = Path(__file__).parent.parent
backend_path = str(backend_dir.resolve())

# Add backend directory to Python path
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Change working directory to backend for relative imports
try:
    os.chdir(backend_path)
except Exception:
    pass

app = None
application = None

try:
    from app import app  # noqa: E402
    application = app
    print(f"[VERCEL] Flask app loaded successfully from {backend_path}")
except Exception as e:
    import traceback
    error_msg = str(e)
    error_trace = traceback.format_exc()
    print(f"[VERCEL ERROR] Failed to load Flask app: {error_msg}")
    print(f"[VERCEL ERROR] Traceback: {error_trace}")

    try:
        from flask import Flask, jsonify  # type: ignore

        error_app = Flask(__name__)

        @error_app.route('/', defaults={'path': ''})
        @error_app.route('/<path:path>')
        def error_handler(path):
            try:
                return jsonify({
                    'error': 'Flask initialization failed',
                    'message': error_msg[:200],
                    'type': type(e).__name__,
                    'status': 'error'
                }), 500
            except Exception as json_error:  # noqa: F841
                return f"Error: Flask initialization failed - {error_msg[:200]}", 500

        app = error_app
        application = error_app
    except Exception as flask_error:  # noqa: F841
        def minimal_app(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'application/json')]
            body = b'{\"error\":\"Flask initialization failed\",\"status\":\"error\"}'
            start_response(status, headers)
            return [body]

        app = minimal_app
        application = minimal_app

if app is None:
    try:
        from flask import Flask, jsonify  # type: ignore

        app = Flask(__name__)

        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def fallback(path):
            return jsonify({'error': 'App not initialized', 'status': 'error'}), 500

        application = app
    except Exception:  # noqa: E722
        def minimal_wsgi(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'application/json')]
            body = b'{\"error\":\"App initialization failed\",\"status\":\"error\"}'
            start_response(status, headers)
            return [body]

        app = minimal_wsgi
        application = minimal_wsgi

__all__ = ['app', 'application']

"""
Vercel Serverless Function Entry Point for Flask App
This file is required by Vercel to run the Flask application as a serverless function.
"""

import sys
import os
from pathlib import Path

# Set Vercel environment flag
os.environ['VERCEL'] = '1'

# Add backend directory to Python path
# Handle both absolute and relative paths
backend_dir = Path(__file__).parent.parent
backend_path = str(backend_dir.resolve())

# Add to Python path
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Change working directory to backend for relative imports
os.chdir(backend_path)

try:
    # Import the Flask app instance
    from app import app
    
    # Vercel automatically wraps Flask WSGI apps
    # Just export the app instance - Vercel will handle the rest
    # Vercel looks for 'app' or 'application' variable
    application = app
    
    # Export both names for compatibility
    __all__ = ['app', 'application']
    
    # Debug output (won't show in production but helpful for logs)
    print(f"[VERCEL] Flask app loaded successfully from {backend_path}")
    print(f"[VERCEL] App routes: {[str(rule) for rule in app.url_map.iter_rules()][:5]}...")
    
except Exception as e:
    import traceback
    error_details = traceback.format_exc()
    print(f"[VERCEL ERROR] Failed to import Flask app: {e}")
    print(f"[VERCEL ERROR] Traceback: {error_details}")
    
    # If import fails, create a minimal error app
    from flask import Flask
    error_app = Flask(__name__)
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def error_handler(path):
        return {
            'error': 'Failed to initialize Flask app',
            'message': str(e),
            'type': type(e).__name__,
            'path': path,
            'sys_path': sys.path[:3]  # First 3 entries
        }, 500
    
    app = error_app
    application = error_app
    __all__ = ['app', 'application']
