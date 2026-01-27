from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import sys
from datetime import timedelta
from pathlib import Path
from models import db, init_db
from routes.device_routes import device_bp
from routes.user_routes import user_bp
from routes.breach_routes import breach_bp
from routes.automation_routes import automation_bp
from routes.wipe_routes import wipe_bp
from routes.download_routes import download_bp
from utils.scheduler import init_scheduler

# Create Flask app instance
app = Flask(__name__)

# Set FLASK_APP environment variable if not set (for flask CLI)
if not os.environ.get('FLASK_APP'):
    os.environ['FLASK_APP'] = 'app.py'

# Disable Flask's instance folder to avoid path conflicts
app.instance_path = None

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Fix database path - use absolute path
db_url = os.getenv('DATABASE_URL')

# Check if we're in a serverless environment (Vercel, AWS Lambda, etc.)
is_serverless = os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('FUNCTION_NAME')

if not db_url:
    if is_serverless:
        # On serverless, we MUST use DATABASE_URL environment variable
        # SQLite won't work - use PostgreSQL or another cloud database
        print("[ERROR] DATABASE_URL environment variable is required for serverless deployment")
        print("[ERROR] SQLite is not supported on Vercel. Please set DATABASE_URL to a PostgreSQL connection string.")
        print("[ERROR] For Supabase, use the CONNECTION POOLER URL (port 6543), not the direct connection (port 5432)")
        print("[ERROR] See CHECK_DATABASE_CONNECTION.md for instructions")
        # Use a placeholder that will fail gracefully
        db_url = 'sqlite:///:memory:'
    else:
        # Local development - use SQLite
        backend_dir = Path(__file__).parent.resolve()
        project_dir = backend_dir.parent.resolve()
        database_dir = project_dir / 'database'
        
        # Create directory with proper permissions
        try:
            database_dir.mkdir(exist_ok=True, parents=True)
        except PermissionError as e:
            print(f"Warning: Could not create database directory: {e}")
        
        # Use Windows-compatible path format
        db_path = database_dir / 'antitheft.db'
        
        # Convert to absolute path string
        db_path_str = str(db_path.resolve())
        
        # SQLite URI format: sqlite:///absolute/path/to/database.db
        if os.name == 'nt':  # Windows
            db_path_normalized = db_path_str.replace('\\', '/')
            db_url = f'sqlite:///{db_path_normalized}'
        else:
            db_url = f'sqlite:///{db_path_str}'
        
        print(f"Database path: {db_path_str}")
        print(f"Database URL: {db_url}")
        print(f"Database directory exists: {database_dir.exists()}")
        print(f"Database directory writable: {os.access(str(database_dir), os.W_OK)}")
else:
    # DATABASE_URL is set - check if it's correct format for serverless
    if is_serverless and 'supabase.co' in db_url and ':5432' in db_url:
        print("[WARNING] ⚠️ You're using Supabase direct connection (port 5432)")
        print("[WARNING] ⚠️ Vercel serverless functions need the CONNECTION POOLER (port 6543)")
        print("[WARNING] ⚠️ Update DATABASE_URL to use pooler.supabase.com:6543")
        print("[WARNING] ⚠️ See CHECK_DATABASE_CONNECTION.md for instructions")
    else:
        print(f"[OK] Using DATABASE_URL from environment: {db_url[:50]}...")

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
# Configure CORS to allow preflight requests and handle redirects properly
CORS(app, 
     origins=['https://antitheft-frontend-2.vercel.app', 'http://localhost:5173', 'http://localhost:3000'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True)
jwt = JWTManager(app)
db.init_app(app)

# Initialize database (lazy initialization for serverless)
# On serverless, don't initialize on startup - wait for first request
if not is_serverless:
    try:
        with app.app_context():
            # Try to initialize database (local development)
            try:
                init_db()
                print("[OK] Database tables initialized successfully")
            except Exception as init_error:
                print(f"[WARN] Database init error (will retry on first request): {init_error}")
            
            # Enable WAL mode for better concurrency (only for SQLite)
            if db_url and db_url.startswith('sqlite'):
                try:
                    engine = db.get_engine()
                    with engine.connect() as conn:
                        conn.execute(db.text("PRAGMA journal_mode=WAL"))
                        conn.commit()
                    print("[OK] SQLite WAL mode enabled for better concurrency")
                except Exception as e:
                    print(f"[WARN] Could not enable WAL mode: {e}")
    except Exception as e:
        error_msg = str(e)
        print(f"[WARN] Database initialization error: {e}")
        print(f"[WARN] Tables will be created on first request if database is available")
else:
    # Serverless: Skip initialization on startup
    print("[INFO] Serverless environment detected - database will be initialized on first request")

# Register blueprints with error handling
try:
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(device_bp, url_prefix='/api')
    app.register_blueprint(breach_bp, url_prefix='/api')
    app.register_blueprint(automation_bp, url_prefix='/api')
    app.register_blueprint(wipe_bp, url_prefix='/api')
    app.register_blueprint(download_bp, url_prefix='/api')
    print("[OK] All blueprints registered successfully")
except Exception as blueprint_error:
    print(f"[ERROR] Failed to register blueprints: {blueprint_error}")
    import traceback
    traceback.print_exc()

# Initialize scheduler (skip on serverless/Vercel - schedulers don't work in serverless)
# Check if we're in a serverless environment
is_serverless = os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME') or os.getenv('FUNCTION_NAME')
if not is_serverless:
    try:
        init_scheduler(app)
    except Exception as e:
        print(f"[WARN] Scheduler initialization failed (may be expected): {e}")
else:
    print("[INFO] Skipping scheduler initialization (serverless environment)")

@app.route('/', methods=['GET', 'OPTIONS'])
def root():
    """Root endpoint - simple response without database access"""
    return jsonify({
        'message': 'Anti-Theft System API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'api_base': '/api'
        }
    }), 200

@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    response.headers.add('Access-Control-Allow-Origin', 'https://antitheft-frontend-2.vercel.app')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/api/health')
def health():
    """Health check endpoint"""
    try:
        # Initialize database tables if needed (lazy initialization)
        try:
            with app.app_context():
                init_db()
        except Exception as init_error:
            # Tables might already exist or will be created on first use
            pass
        
        # Test database connection
        db_status = 'unknown'
        db_error = None
        db_url_info = 'not set'
        
        try:
            db_url_current = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_url_current:
                # Mask password in connection string
                if '@' in db_url_current:
                    parts = db_url_current.split('@')
                    if len(parts) > 1:
                        user_pass = parts[0].split('//')[-1]
                        if ':' in user_pass:
                            user = user_pass.split(':')[0]
                            db_url_info = f"{db_url_current.split('@')[0].split('//')[0]}//{user}:***@{parts[1]}"
                        else:
                            db_url_info = db_url_current.split('@')[0] + '@***'
                    else:
                        db_url_info = db_url_current[:50] + '...'
                else:
                    db_url_info = db_url_current[:50] + '...'
            
            with app.app_context():
                db.session.execute(db.text('SELECT 1'))
                db_status = 'connected'
                
                # Try to check if tables exist
                try:
                    from models import User
                    user_count = User.query.count()
                    db_status = f'connected ({user_count} users)'
                except Exception as table_error:
                    # Tables might not exist yet
                    if 'does not exist' in str(table_error) or 'no such table' in str(table_error).lower():
                        db_status = 'connected (tables will be created on first use)'
                    else:
                        db_status = 'connected (checking tables...)'
                    
        except Exception as e:
            db_error = str(e)
            if 'sqlite:///:memory:' in db_error or 'DATABASE_URL' in db_error:
                db_status = 'error: PostgreSQL required (see SETUP_VERCEL_DATABASE.md)'
            elif 'connection' in db_error.lower() or 'timeout' in db_error.lower():
                db_status = f'error: Connection failed - {str(e)[:100]}'
            else:
                db_status = f'error: {str(e)[:100]}'
        
        response = {
            'status': 'ok' if db_status.startswith('connected') else 'warning',
            'message': 'Anti-Theft System API is running',
            'database': {
                'status': db_status,
                'url': db_url_info,
                'error': db_error[:200] if db_error else None
            },
            'environment': 'serverless' if os.getenv('VERCEL') else 'local',
            'setup_required': db_status.startswith('error') and 'PostgreSQL' in db_status
        }
        
        status_code = 200 if db_status.startswith('connected') else 503
        return jsonify(response), status_code
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()[:500] if os.getenv('VERCEL') else None
        }), 500

# Global error handler - register after all routes
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"[ERROR] Unhandled exception: {e}")
    print(f"[ERROR] Traceback: {error_trace}")
    
    # Don't show traceback in production unless DEBUG is enabled
    show_traceback = os.getenv('VERCEL') and os.getenv('DEBUG')
    
    return jsonify({
        'error': 'Internal server error',
        'message': str(e) if not os.getenv('VERCEL') else 'An error occurred. Please try again.',
        'traceback': error_trace[:500] if show_traceback else None
    }), 500

@app.errorhandler(404)
def handle_404(e):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist',
        'available_endpoints': {
            'health': '/api/health',
            'api_base': '/api'
        }
    }), 404

@app.errorhandler(500)
def handle_500(e):
    """Handle 500 errors"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"[ERROR] 500 error: {e}")
    print(f"[ERROR] Traceback: {error_trace}")
    
    return jsonify({
        'error': 'Internal server error',
        'message': 'The server encountered an error. Please try again later.'
    }), 500

# Export for Vercel serverless function
# Vercel looks for 'app' or 'application' variable
application = app

if __name__ == '__main__':
    # Disable reloader on Windows to avoid database path issues
    use_reloader = sys.platform != 'win32'
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=use_reloader)

