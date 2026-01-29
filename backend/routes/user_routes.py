from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User, Device, ActivityLog, DeviceLinkToken
from datetime import datetime, timezone, timedelta
import uuid
import os
import requests
import hashlib
import random
import logging
from utils.email_alert import send_alert_email

user_bp = Blueprint('user', __name__)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '913466167374-2t1no6si29f0phe28pef83oaolv836pm.apps.googleusercontent.com')

def ensure_verification_columns_exist():
    """Ensure email verification columns exist in the users table"""
    try:
        db_url_str = str(db.engine.url)
        if 'postgresql' in db_url_str.lower() or 'postgres' in db_url_str.lower():
            # Check if columns exist by trying to query them
            try:
                db.session.execute(db.text("SELECT email_verified FROM users LIMIT 1"))
                return True  # Columns exist
            except Exception:
                # Columns don't exist, add them
                try:
                    db.session.execute(db.text("""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE,
                        ADD COLUMN IF NOT EXISTS verification_code VARCHAR(6),
                        ADD COLUMN IF NOT EXISTS verification_code_expires TIMESTAMP
                    """))
                    db.session.commit()
                    logging.info("Added email verification columns to users table")
                    return True
                except Exception as e:
                    logging.warning(f"Could not add verification columns: {e}")
                    return False
        return True  # For SQLite, columns will be added on next table creation
    except Exception as e:
        logging.warning(f"Error checking verification columns: {e}")
        return False

@user_bp.route('/register_user', methods=['POST'])
def register_user():
    try:
        # Check database connection first
        try:
            db.session.execute(db.text('SELECT 1'))
        except Exception as db_error:
            error_msg = str(db_error)
            if 'sqlite:///:memory:' in error_msg or 'DATABASE_URL' in error_msg or 'no such table' in error_msg.lower():
                return jsonify({
                    'error': 'Database not configured',
                    'message': 'PostgreSQL database is required for Vercel deployment',
                    'solution': 'Please set DATABASE_URL environment variable in Vercel',
                    'guide': 'See SETUP_VERCEL_DATABASE.md for instructions',
                    'quick_fix': '1. Sign up for free PostgreSQL at https://supabase.com\n2. Get connection string\n3. Add DATABASE_URL in Vercel Settings → Environment Variables\n4. Redeploy'
                }), 503
            else:
                return jsonify({
                    'error': 'Database connection failed',
                    'message': str(db_error)[:200]
                }), 503
        
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Ensure verification columns exist BEFORE checking if user exists
        # This prevents "column does not exist" errors when querying
        ensure_verification_columns_exist()
        
        # Check if user exists
        try:
            # Use raw SQL to avoid SQLAlchemy trying to select non-existent columns
            result = db.session.execute(
                db.text("SELECT id, email FROM users WHERE email = :email"),
                {'email': data['email']}
            ).first()
            if result:
                return jsonify({'error': 'User already exists'}), 400
        except Exception as db_error:
            # Database table might not exist
            error_str = str(db_error).lower()
            if 'no such table' in error_str or 'does not exist' in error_str:
                return jsonify({
                    'error': 'Database not initialized',
                    'message': 'Database tables need to be created',
                    'solution': 'The backend will create tables automatically on first request. Please try again in a moment.'
                }), 503
            # If it's a column error, try to add columns and retry
            if 'email_verified' in error_str or 'column' in error_str:
                ensure_verification_columns_exist()
                # Retry the check
                try:
                    result = db.session.execute(
                        db.text("SELECT id, email FROM users WHERE email = :email"),
                        {'email': data['email']}
                    ).first()
                    if result:
                        return jsonify({'error': 'User already exists'}), 400
                except Exception:
                    pass  # Continue to registration
            else:
                raise
        
        # Ensure database tables exist (create if needed)
        try:
            from models import init_db
            init_db()
        except Exception as init_error:
            # If init fails, try to continue - tables might already exist
            print(f"[WARN] Database init check: {init_error}")
        
        # Generate verification code (6 digits)
        verification_code = str(random.randint(100000, 999999))
        verification_expires = datetime.now(timezone.utc) + timedelta(minutes=15)  # Code expires in 15 minutes
        
        # Try to create user with verification fields first
        # If columns don't exist, we'll catch the error and create without them
        has_verification_columns = True
        user = None
        
        try:
            # First, try to create user with verification fields
            user = User(
                email=data['email'],
                name=data.get('name', data['email'].split('@')[0]),
                is_admin=data.get('is_admin', False),
                email_verified=False,
                verification_code=verification_code,
                verification_code_expires=verification_expires
            )
            user.set_password(data['password'])
            db.session.add(user)
            db.session.flush()  # Flush to get user.id
        except Exception as db_error:
            error_str = str(db_error)
            
            if 'no such table' in error_str.lower():
                # Tables don't exist - try to create them
                try:
                    from models import init_db
                    init_db()
                    # Retry creating user with verification fields
                    user = User(
                        email=data['email'],
                        name=data.get('name', data['email'].split('@')[0]),
                        is_admin=data.get('is_admin', False),
                        email_verified=False,
                        verification_code=verification_code,
                        verification_code_expires=verification_expires
                    )
                    user.set_password(data['password'])
                    db.session.add(user)
                    db.session.flush()
                except Exception as retry_error:
                    return jsonify({
                        'error': 'Database setup required',
                        'message': 'Database tables need to be created. Please try again in a moment.',
                        'details': str(retry_error)[:200]
                    }), 503
            elif 'no such column' in error_str.lower() or 'column' in error_str.lower() or 'email_verified' in error_str.lower():
                # Verification columns don't exist - create user without them
                logging.warning(f"Email verification columns not found, creating user without verification: {error_str}")
                has_verification_columns = False
                
                # Try to add columns for PostgreSQL
                try:
                    db_url_str = str(db.engine.url)
                    if 'postgresql' in db_url_str.lower() or 'postgres' in db_url_str.lower():
                        db.session.rollback()  # Rollback the failed attempt
                        db.session.execute(db.text("""
                            ALTER TABLE users 
                            ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE,
                            ADD COLUMN IF NOT EXISTS verification_code VARCHAR(6),
                            ADD COLUMN IF NOT EXISTS verification_code_expires TIMESTAMP
                        """))
                        db.session.commit()
                        logging.info("Added email verification columns to users table")
                        has_verification_columns = True
                        
                        # Now retry with verification fields
                        user = User(
                            email=data['email'],
                            name=data.get('name', data['email'].split('@')[0]),
                            is_admin=data.get('is_admin', False),
                            email_verified=False,
                            verification_code=verification_code,
                            verification_code_expires=verification_expires
                        )
                        user.set_password(data['password'])
                        db.session.add(user)
                        db.session.flush()
                    else:
                        # SQLite - create without verification fields
                        db.session.rollback()
                        user = User(
                            email=data['email'],
                            name=data.get('name', data['email'].split('@')[0]),
                            is_admin=data.get('is_admin', False)
                        )
                        user.set_password(data['password'])
                        db.session.add(user)
                        db.session.flush()
                        logging.warning("Created user without email verification (SQLite - columns will be added on next table creation)")
                except Exception as retry_error:
                    # If adding columns fails, create user without verification
                    try:
                        db.session.rollback()
                        user = User(
                            email=data['email'],
                            name=data.get('name', data['email'].split('@')[0]),
                            is_admin=data.get('is_admin', False)
                        )
                        user.set_password(data['password'])
                        db.session.add(user)
                        db.session.flush()
                        has_verification_columns = False
                        logging.warning(f"Created user without email verification: {retry_error}")
                    except Exception as final_error:
                        # Last resort - log and return error
                        logging.error(f"Failed to create user after all retries: {final_error}")
                        db.session.rollback()
                        return jsonify({
                            'error': 'Registration failed',
                            'message': 'Could not create user account. Please try again or contact support.',
                            'details': str(final_error)[:200]
                        }), 500
            else:
                # Other database error - log and return
                logging.error(f"Database error during user creation: {db_error}")
                db.session.rollback()
                return jsonify({
                    'error': 'Registration failed',
                    'message': 'Database error occurred. Please try again.',
                    'details': str(db_error)[:200]
                }), 500
        
        # Prey Project-style Device Linking
        # Link existing agent device if device_id is provided (browser discovers agent via localhost)
        device_id = data.get('device_id')
        linked_device = None
        
        if device_id:
            # Link by device_id
            device = Device.query.filter_by(device_id=device_id).first()
            if device:
                if device.user_id is not None:
                    return jsonify({'error': f'Device {device_id} is already linked to another user'}), 409
                device.user_id = user.id
                linked_device = device
                logging.info(f"Linked device {device_id} to user {user.email}")
        
        # Legacy: Automatically register an OS-level device if provided (browser detection - deprecated)
        os_device = data.get('os_device') or data.get('browser_device')
        if os_device and not linked_device:
            try:
                device_id = os_device.get('device_id')
                if device_id:
                    # Use provided device_name or build from OS + device_class + browser
                    device_name = os_device.get('device_name') or 'Unknown Device'

                    # Derive last_ip from payload or from request
                    raw_ip = os_device.get('last_ip')
                    if not raw_ip:
                        # Prefer X-Forwarded-For when behind proxies
                        forwarded_for = request.headers.get('X-Forwarded-For', '')
                        if forwarded_for:
                            raw_ip = forwarded_for.split(',')[0].strip()
                        else:
                            raw_ip = request.remote_addr

                    # Check if this OS device already exists globally
                    existing_device = Device.query.filter_by(device_id=device_id).first()
                    if existing_device and existing_device.user_id != user.id:
                        # Device ID is already bound to a different user; skip creating to avoid conflict
                        print(f"Skipping OS device registration: device_id {device_id} belongs to another user")
                    elif not existing_device:
                        now_utc = datetime.now(timezone.utc)

                        device = Device(
                            device_id=device_id,
                            name=device_name,
                            device_type='os_device',
                            user_id=user.id,
                            status='active',
                            # OS-level fields
                            os_name=os_device.get('os_name'),
                            os_version=os_device.get('os_version'),
                            architecture=os_device.get('architecture'),
                            device_class=os_device.get('device_class'),
                            gpu=os_device.get('gpu'),
                            # Browser fields
                            browser=os_device.get('browser'),
                            browser_name=os_device.get('browser_name'),
                            browser_version=os_device.get('browser_version'),
                            # Environment fields
                            platform=os_device.get('platform'),
                            user_agent=os_device.get('user_agent'),
                            screen_resolution=os_device.get('screen_resolution'),
                            timezone=os_device.get('timezone'),
                            last_ip=raw_ip,
                            is_primary=True,
                            last_seen=now_utc,
                            # Legacy field for backward compatibility
                            os=os_device.get('os') or os_device.get('os_version')
                        )
                        db.session.add(device)
                        db.session.flush()  # Get device.id for activity log
                        
                        # Log device creation
                        log = ActivityLog(
                            device_id=device.id,
                            action='device_registered',
                            description=f'OS device "{device_name}" automatically registered during signup'
                        )
                        db.session.add(log)
                    elif existing_device and existing_device.user_id == user.id:
                        # Update metadata and continue without creating a new row
                        existing_device.device_type = existing_device.device_type or 'os_device'
                        existing_device.os_name = os_device.get('os_name') or existing_device.os_name
                        existing_device.os_version = os_device.get('os_version') or existing_device.os_version
                        existing_device.architecture = os_device.get('architecture') or existing_device.architecture
                        existing_device.device_class = os_device.get('device_class') or existing_device.device_class
                        existing_device.gpu = os_device.get('gpu') or existing_device.gpu
                        existing_device.browser = os_device.get('browser') or existing_device.browser
                        existing_device.browser_name = os_device.get('browser_name') or existing_device.browser_name
                        existing_device.browser_version = os_device.get('browser_version') or existing_device.browser_version
                        existing_device.platform = os_device.get('platform') or existing_device.platform
                        existing_device.user_agent = os_device.get('user_agent') or existing_device.user_agent
                        existing_device.screen_resolution = os_device.get('screen_resolution') or existing_device.screen_resolution
                        existing_device.timezone = os_device.get('timezone') or existing_device.timezone
                        existing_device.last_ip = raw_ip or existing_device.last_ip
                        existing_device.last_seen = datetime.now(timezone.utc)
                        existing_device.os = os_device.get('os') or os_device.get('os_version') or existing_device.os
            except Exception as device_err:
                # Don't fail registration if device creation fails
                print(f"Warning: Could not auto-register OS device: {device_err}")
        
        # Log device linking if device was linked
        if linked_device:
            log = ActivityLog(
                device_id=linked_device.id,
                action='device_linked',
                description=f'Device "{linked_device.name}" linked to user {user.email}'
            )
            db.session.add(log)
        
        try:
            db.session.commit()
        except Exception as commit_error:
            db.session.rollback()
            error_str = str(commit_error)
            
            # Check for specific database errors
            if 'sqlite:///:memory:' in error_str or 'DATABASE_URL' in error_str:
                return jsonify({
                    'error': 'Database not configured',
                    'message': 'PostgreSQL database is required for Vercel deployment',
                    'solution': 'Please set DATABASE_URL environment variable',
                    'quick_fix': 'See QUICK_FIX_DATABASE.md for 5-minute setup guide',
                    'guide': '1. Sign up at https://supabase.com (free)\n2. Create project\n3. Copy connection string\n4. Add DATABASE_URL in Vercel Settings\n5. Redeploy'
                }), 503
            elif 'no such table' in error_str.lower():
                return jsonify({
                    'error': 'Database tables not created',
                    'message': 'Database tables need to be initialized',
                    'solution': 'The backend will create tables automatically. Please try again in a moment.'
                }), 503
            else:
                raise
        
        # Send verification email (only if verification columns exist)
        verification_sent = False
        if has_verification_columns:
            try:
                frontend_url = os.getenv('FRONTEND_BASE_URL', 'https://antitheft.vercel.app')
                subject = "Enter this code to sign in"
                html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .code {{ font-size: 32px; font-weight: bold; text-align: center; letter-spacing: 8px; color: #1a73e8; margin: 20px 0; padding: 20px; background-color: #f5f5f5; border-radius: 8px; }}
                    .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 style="font-size: 24px; margin-bottom: 20px;">Enter this code to sign in</h1>
                    <div class="code">{verification_code}</div>
                    <p>Enter the code above on your device to sign in to Smart Anti-Theft System.</p>
                    <p style="color: #666; font-size: 14px;"><strong>This code will expire in 15 minutes.</strong></p>
                    <div class="warning">
                        <p style="margin: 0;"><strong>Security Notice:</strong></p>
                        <p style="margin: 5px 0 0 0;">If you didn't send this request, you can ignore this email or review your recent device activity.</p>
                        <p style="margin: 5px 0 0 0;">To help security, don't share this code with anyone outside your household.</p>
                    </div>
                    <div class="footer">
                        <p style="margin: 0;">The Smart Anti-Theft System team</p>
                    </div>
                </div>
            </body>
            </html>
            """
                body = f"""Enter this code to sign in

{verification_code}

Enter the code above on your device to sign in to Smart Anti-Theft System.

This code will expire in 15 minutes.

If you didn't send this request, you can ignore this email or review your recent device activity.
To help security, don't share this code with anyone outside your household.

The Smart Anti-Theft System team
"""
                send_alert_email(data['email'], subject, body, html_body)
                logging.info(f"Verification email sent to {data['email']}")
                verification_sent = True
            except Exception as email_error:
                logging.error(f"Failed to send verification email: {email_error}")
                # Don't fail registration if email fails - user can request resend
        
        # Safely convert user to dict
        try:
            user_dict = user.to_dict()
        except Exception as dict_error:
            logging.error(f"Error converting user to dict: {dict_error}")
            # Fallback to basic user info
            user_dict = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'is_admin': getattr(user, 'is_admin', False),
                'email_verified': getattr(user, 'email_verified', True)
            }
        
        response_data = {
            'message': 'User registered successfully.',
            'user': user_dict
        }
        
        # Only require verification if columns exist and email was sent
        if has_verification_columns:
            response_data['message'] = 'User registered successfully. Please check your email for verification code.'
            response_data['verification_required'] = True
        else:
            response_data['message'] = 'User registered successfully. Email verification is not available yet.'
            response_data['verification_required'] = False
        
        if linked_device:
            try:
                response_data['device_linked'] = True
                response_data['device'] = linked_device.to_dict()
            except Exception as device_dict_error:
                logging.error(f"Error converting device to dict: {device_dict_error}")
                response_data['device_linked'] = True
                response_data['device'] = {
                    'id': linked_device.id,
                    'device_id': linked_device.device_id,
                    'name': linked_device.name,
                    'status': linked_device.status
                }
        else:
            response_data['device_linked'] = False
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        logging.error(f"Registration error: {e}\n{error_trace}")
        
        # Provide helpful error message
        error_str = str(e).lower()
        
        # Check for specific error types
        if 'duplicate' in error_str or 'unique' in error_str or 'already exists' in error_str:
            return jsonify({
                'error': 'User already exists',
                'message': 'An account with this email already exists. Please sign in instead.'
            }), 400
        elif 'database_url' in error_str or 'sqlite:///:memory:' in error_str:
            return jsonify({
                'error': 'Database configuration required',
                'message': 'PostgreSQL database is required. See QUICK_FIX_DATABASE.md',
                'details': str(e)[:200]
            }), 503
        elif 'connection' in error_str or 'timeout' in error_str:
            return jsonify({
                'error': 'Database connection failed',
                'message': 'Unable to connect to database. Please try again later.'
            }), 503
        elif 'no such table' in error_str:
            return jsonify({
                'error': 'Database not initialized',
                'message': 'Database tables are being created. Please try again in a moment.'
            }), 503
        elif 'email' in error_str and ('invalid' in error_str or 'format' in error_str):
            return jsonify({
                'error': 'Invalid email',
                'message': 'Please enter a valid email address.'
            }), 400
        else:
            # Generic error - but include the actual error message
            return jsonify({
                'error': 'Registration failed',
                'message': str(e)[:300] if len(str(e)) > 0 else 'An unexpected error occurred. Please try again.',
                'details': 'If this problem persists, please contact support.'
            }), 500

@user_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    # Handle OPTIONS preflight request explicitly for Vercel
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', 'https://antitheft-frontend-2.vercel.app'))
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Max-Age', '3600')
        return response, 200
    
    try:
        # Check database connection first
        try:
            db.session.execute(db.text('SELECT 1'))
        except Exception as db_error:
            error_msg = str(db_error)
            logging.error(f"Database connection error in login: {db_error}")
            if 'sqlite:///:memory:' in error_msg or 'DATABASE_URL' in error_msg:
                return jsonify({
                    'error': 'Database not configured',
                    'message': 'PostgreSQL database is required for Vercel deployment',
                    'solution': 'Please set DATABASE_URL environment variable in Vercel'
                }), 503
            else:
                return jsonify({
                    'error': 'Database connection failed',
                    'message': str(db_error)[:200]
                }), 503
        
        # Ensure database tables exist
        try:
            from models import init_db
            init_db()
        except Exception as init_error:
            # Tables might already exist, continue anyway
            logging.debug(f"Database init check: {init_error}")
        
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        try:
            user = User.query.filter_by(email=data['email']).first()
        except Exception as query_error:
            logging.error(f"Database query error in login: {query_error}")
            return jsonify({
                'error': 'Database error',
                'message': 'Failed to query user. Please try again.'
            }), 500
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if email is verified (only if verification columns exist)
        try:
            # Try to access email_verified attribute
            if hasattr(user, 'email_verified') and user.email_verified is not None:
                if not user.email_verified:
                    return jsonify({
                        'error': 'Email not verified',
                        'message': 'Please verify your email address before logging in. Check your email for the verification code.',
                        'email_verified': False
                    }), 403
        except Exception:
            # email_verified column doesn't exist - allow login
            pass
        
        # Create access token (identity must be string)
        access_token = create_access_token(identity=str(user.id))

        # Prey Project-style Device Linking on Login
        # Link existing agent device if device_id is provided (browser discovers agent via localhost)
        device_id = data.get('device_id')
        linked_device = None
        
        if device_id:
            device = Device.query.filter_by(device_id=device_id).first()
            if device:
                if device.user_id is None:
                    # Link unowned device to this user
                    device.user_id = user.id
                    linked_device = device
                    logging.info(f"Linked device {device_id} to user {user.email} on login")
                elif device.user_id == user.id:
                    # Already linked to this user
                    linked_device = device
                else:
                    # Device belongs to another user - skip
                    logging.warning(f"Device {device_id} belongs to another user, skipping link")
        
        # Log device linking
        if linked_device and linked_device.user_id == user.id:
            try:
                log = ActivityLog(
                    device_id=linked_device.id,
                    action='device_linked',
                    description=f'Device "{linked_device.name}" linked to user {user.email} on login'
                )
                db.session.add(log)
                db.session.commit()
            except:
                pass
        
        # Legacy: Optionally update or auto-register an OS device on login (browser detection - deprecated)
        os_device = data.get('os_device') or data.get('browser_device')
        if os_device and not linked_device:
            try:
                device_id = os_device.get('device_id')
                if device_id:
                    # Determine IP address for this login
                    raw_ip = os_device.get('last_ip')
                    if not raw_ip:
                        forwarded_for = request.headers.get('X-Forwarded-For', '')
                        if forwarded_for:
                            raw_ip = forwarded_for.split(',')[0].strip()
                        else:
                            raw_ip = request.remote_addr

                    device_name = os_device.get('device_name') or 'Unknown Device'
                    now_utc = datetime.now(timezone.utc)

                    # First, check if device_id exists globally and belongs to another user
                    device_global = Device.query.filter_by(device_id=device_id).first()
                    if device_global and device_global.user_id != user.id:
                        # Do not re-use a device_id owned by another user; skip creation
                        print(f"Skipping OS device update/registration: device_id {device_id} belongs to another user")
                        db.session.commit()
                        return jsonify({
                            'access_token': access_token,
                            'user': user.to_dict()
                        }), 200

                    # Try to find an existing OS device for this user/device_id
                    device = Device.query.filter_by(device_id=device_id, user_id=user.id).first()
                    if device:
                        # Update metadata and last seen
                        device.device_type = device.device_type or 'os_device'
                        # Update OS-level fields
                        device.os_name = os_device.get('os_name') or device.os_name
                        device.os_version = os_device.get('os_version') or device.os_version
                        device.architecture = os_device.get('architecture') or device.architecture
                        device.device_class = os_device.get('device_class') or device.device_class
                        device.gpu = os_device.get('gpu') or device.gpu
                        # Update browser fields
                        device.browser = os_device.get('browser') or device.browser
                        device.browser_name = os_device.get('browser_name') or device.browser_name
                        device.browser_version = os_device.get('browser_version') or device.browser_version
                        # Update environment fields
                        device.platform = os_device.get('platform') or device.platform
                        device.user_agent = os_device.get('user_agent') or device.user_agent
                        device.screen_resolution = os_device.get('screen_resolution') or device.screen_resolution
                        device.timezone = os_device.get('timezone') or device.timezone
                        device.last_ip = raw_ip or device.last_ip
                        device.last_seen = now_utc
                        # Legacy field
                        device.os = os_device.get('os') or os_device.get('os_version') or device.os
                    else:
                        # No existing device – auto-register a new OS device
                        # Mark as primary only if user has no other devices yet
                        has_any_device = Device.query.filter_by(user_id=user.id).count() > 0
                        device = Device(
                            device_id=device_id,
                            name=device_name,
                            device_type='os_device',
                            user_id=user.id,
                            status='active',
                            # OS-level fields
                            os_name=os_device.get('os_name'),
                            os_version=os_device.get('os_version'),
                            architecture=os_device.get('architecture'),
                            device_class=os_device.get('device_class'),
                            gpu=os_device.get('gpu'),
                            # Browser fields
                            browser=os_device.get('browser'),
                            browser_name=os_device.get('browser_name'),
                            browser_version=os_device.get('browser_version'),
                            # Environment fields
                            platform=os_device.get('platform'),
                            user_agent=os_device.get('user_agent'),
                            screen_resolution=os_device.get('screen_resolution'),
                            timezone=os_device.get('timezone'),
                            last_ip=raw_ip,
                            is_primary=not has_any_device,
                            last_seen=now_utc,
                            # Legacy field
                            os=os_device.get('os') or os_device.get('os_version')
                        )
                        db.session.add(device)
                        db.session.flush()

                        log = ActivityLog(
                            device_id=device.id,
                            action='device_registered',
                            description=f'OS device "{device_name}" automatically registered during login'
                        )
                        db.session.add(log)

                    db.session.commit()
            except Exception as device_err:
                # Do not block login if device update/registration fails
                print(f"Warning: Could not update/register OS device on login: {device_err}")
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logging.error(f"Login error: {e}\n{error_trace}")
        
        # Provide more helpful error messages
        error_str = str(e).lower()
        if 'no such table' in error_str or 'does not exist' in error_str:
            return jsonify({
                'error': 'Database not initialized',
                'message': 'Database tables need to be created. Please try again in a moment.',
                'details': 'The database connection is working, but tables are missing.'
            }), 503
        elif 'connection' in error_str or 'timeout' in error_str:
            return jsonify({
                'error': 'Database connection failed',
                'message': 'Unable to connect to the database. Please check your DATABASE_URL configuration.',
                'details': str(e)[:200]
            }), 503
        elif 'sqlite:///:memory:' in str(e) or 'DATABASE_URL' in str(e):
            return jsonify({
                'error': 'Database not configured',
                'message': 'PostgreSQL database is required for Vercel deployment',
                'solution': 'Please set DATABASE_URL environment variable in Vercel'
            }), 503
        else:
            # Generic error - don't expose internal details in production
            return jsonify({
                'error': 'Internal server error',
                'message': 'An error occurred during login. Please try again.',
                'details': str(e)[:200] if not os.getenv('VERCEL') else None
            }), 500

@user_bp.route('/google_login', methods=['POST'])
def google_login():
    """
    Handle Google OAuth login
    Verifies the Google ID token and creates/updates user account
    """
    try:
        data = request.get_json()
        id_token = data.get('id_token')
        
        if not id_token:
            return jsonify({'error': 'ID token is required'}), 400
        
        # Verify the Google ID token
        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token as google_id_token
            
            # Verify the token
            idinfo = google_id_token.verify_oauth2_token(
                id_token, 
                google_requests.Request(), 
                GOOGLE_CLIENT_ID
            )
            
            # Get user info from Google
            google_email = idinfo.get('email')
            google_name = idinfo.get('name', google_email.split('@')[0])
            google_picture = idinfo.get('picture')
            
            if not google_email:
                return jsonify({'error': 'Email not provided by Google'}), 400
            
            # Check if user exists
            user = User.query.filter_by(email=google_email).first()
            
            if not user:
                # Create new user
                user = User(
                    email=google_email,
                    name=google_name,
                    is_admin=False
                )
                # Set a random password (won't be used for Google login)
                user.set_password(os.urandom(32).hex())
                db.session.add(user)
                db.session.flush()  # Flush to get user.id
                
                # Note: Browser device registration for Google login would need to be done
                # from the frontend after login, as we don't have browser info here
                
                db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=str(user.id))
            
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict()
            }), 200
            
        except ValueError as e:
            # Invalid token
            return jsonify({'error': 'Invalid Google token'}), 401
        except Exception as e:
            return jsonify({'error': f'Google authentication failed: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/me', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/admin/register_missing_devices', methods=['POST'])
@jwt_required()
def register_missing_devices():
    """
    Admin endpoint to register browser devices for users without any devices
    This can be called while the server is running
    """
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        # Check if user is admin
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        registered_devices = []
        skipped_users = []
        
        # Get all users
        users = User.query.all()
        
        for u in users:
            # Check if user has any devices
            device_count = Device.query.filter_by(user_id=u.id).count()
            
            if device_count == 0:
                # Generate browser device ID
                hash_obj = hashlib.md5(f"browser_{u.email}".encode())
                device_id = f"browser-{hash_obj.hexdigest()[:12]}"
                
                # Check if device ID already exists
                existing = Device.query.filter_by(device_id=device_id).first()
                if existing:
                    skipped_users.append({
                        'email': u.email,
                        'reason': 'Device ID already exists'
                    })
                    continue
                
                # Create device name
                device_name = f"{u.name or u.email.split('@')[0]}'s Browser"
                
                # Create browser device
                device = Device(
                    device_id=device_id,
                    name=device_name,
                    device_type='desktop',
                    user_id=u.id,
                    status='active',
                    last_seen=datetime.now(timezone.utc)
                )
                
                db.session.add(device)
                db.session.flush()  # Flush to get device.id
                
                # Log registration
                log = ActivityLog(
                    device_id=device.id,
                    action='device_registered',
                    description=f'Browser device auto-registered for user {u.email}'
                )
                db.session.add(log)
                
                registered_devices.append({
                    'user_email': u.email,
                    'device_id': device_id,
                    'device_name': device_name
                })
        
        db.session.commit()
        
        return jsonify({
            'message': f'Registered {len(registered_devices)} browser device(s)',
            'registered_devices': registered_devices,
            'skipped_users': skipped_users,
            'total_registered': len(registered_devices)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@user_bp.route('/verify_email', methods=['POST'])
def verify_email():
    """Verify email with code"""
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({'error': 'Email and verification code are required'}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if verification columns exist
        if not hasattr(user, 'email_verified') or user.email_verified is None:
            return jsonify({
                'error': 'Email verification not available',
                'message': 'Email verification is not configured for this account. Please contact support.'
            }), 400
        
        # Check if already verified
        if user.email_verified:
            return jsonify({
                'message': 'Email already verified',
                'user': user.to_dict()
            }), 200
        
        # Check if code matches
        if not hasattr(user, 'verification_code') or not user.verification_code or user.verification_code != code:
            return jsonify({'error': 'Invalid verification code'}), 400
        
        # Check if code expired (handle naive vs aware datetimes safely)
        if hasattr(user, 'verification_code_expires') and user.verification_code_expires:
            now_utc = datetime.now(timezone.utc)
            expires = user.verification_code_expires

            # If the stored datetime is naive (no tzinfo), assume UTC to avoid comparison errors
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)

            if expires < now_utc:
                return jsonify({'error': 'Verification code has expired. Please request a new one.'}), 400
        
        # Verify email
        user.email_verified = True
        user.verification_code = None
        user.verification_code_expires = None
        db.session.commit()
        
        logging.info(f"Email verified for user {user.email}")
        
        return jsonify({
            'message': 'Email verified successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Email verification error: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/resend_verification', methods=['POST'])
def resend_verification():
    """Resend verification code"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if verification columns exist
        if not hasattr(user, 'email_verified') or user.email_verified is None:
            return jsonify({
                'error': 'Email verification not available',
                'message': 'Email verification is not configured for this account. Please contact support.'
            }), 400
        
        # Check if already verified
        if user.email_verified:
            return jsonify({
                'message': 'Email already verified',
                'user': user.to_dict()
            }), 200
        
        # Generate new verification code
        verification_code = str(random.randint(100000, 999999))
        verification_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        if hasattr(user, 'verification_code'):
            user.verification_code = verification_code
        if hasattr(user, 'verification_code_expires'):
            user.verification_code_expires = verification_expires
        db.session.commit()
        
        # Send verification email
        try:
            subject = "Enter this code to sign in"
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .code {{ font-size: 32px; font-weight: bold; text-align: center; letter-spacing: 8px; color: #1a73e8; margin: 20px 0; padding: 20px; background-color: #f5f5f5; border-radius: 8px; }}
                    .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }}
                    .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 style="font-size: 24px; margin-bottom: 20px;">Enter this code to sign in</h1>
                    <div class="code">{verification_code}</div>
                    <p>Enter the code above on your device to sign in to Smart Anti-Theft System.</p>
                    <p style="color: #666; font-size: 14px;"><strong>This code will expire in 15 minutes.</strong></p>
                    <div class="warning">
                        <p style="margin: 0;"><strong>Security Notice:</strong></p>
                        <p style="margin: 5px 0 0 0;">If you didn't send this request, you can ignore this email or review your recent device activity.</p>
                        <p style="margin: 5px 0 0 0;">To help security, don't share this code with anyone outside your household.</p>
                    </div>
                    <div class="footer">
                        <p style="margin: 0;">The Smart Anti-Theft System team</p>
                    </div>
                </div>
            </body>
            </html>
            """
            body = f"""Enter this code to sign in

{verification_code}

Enter the code above on your device to sign in to Smart Anti-Theft System.

This code will expire in 15 minutes.

If you didn't send this request, you can ignore this email or review your recent device activity.
To help security, don't share this code with anyone outside your household.

The Smart Anti-Theft System team
"""
            send_alert_email(email, subject, body, html_body)
            logging.info(f"Verification email resent to {email}")
        except Exception as email_error:
            logging.error(f"Failed to resend verification email: {email_error}")
            return jsonify({'error': 'Failed to send verification email'}), 500
        
        return jsonify({
            'message': 'Verification code resent successfully. Please check your email.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Resend verification error: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/client_info', methods=['GET'])
def client_info():
    """
    Lightweight endpoint to return basic client networking info.
    Currently used by the frontend to:
      - Capture the public IP address for browser-based devices
    """
    try:
        forwarded_for = request.headers.get('X-Forwarded-For', '')
        if forwarded_for:
            ip = forwarded_for.split(',')[0].strip()
        else:
            ip = request.remote_addr

        return jsonify({
            'ip': ip
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

