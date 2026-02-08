from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Device, ActivityLog, User, DeviceLinkToken, PushSubscription
from datetime import datetime, timedelta
import os
from utils.geofence import check_geofence
import secrets
import math
import logging
import json

from utils.push import send_push_notifications

device_bp = Blueprint('device', __name__)


@device_bp.route('/push/subscribe', methods=['POST'])
@jwt_required()
def push_subscribe():
    """
    Save a browser push subscription for the logged-in user.
    Payload format (from browser PushManager):
      { endpoint: "...", keys: { p256dh: "...", auth: "..." } }
    """
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id

        data = request.get_json() or {}
        endpoint = data.get('endpoint')
        keys = data.get('keys') or {}
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not endpoint or not p256dh or not auth:
            return jsonify({'error': 'Invalid subscription payload'}), 400

        existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if existing:
            # Re-attach to this user (in case user changed)
            existing.user_id = user_id
            existing.p256dh = p256dh
            existing.auth = auth
            db.session.commit()
            return jsonify({'message': 'Subscription updated'}), 200

        sub = PushSubscription(user_id=user_id, endpoint=endpoint, p256dh=p256dh, auth=auth)
        db.session.add(sub)
        db.session.commit()
        return jsonify({'message': 'Subscription saved'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@device_bp.route('/push/unsubscribe', methods=['POST'])
@jwt_required()
def push_unsubscribe():
    try:
        data = request.get_json() or {}
        endpoint = data.get('endpoint')
        if not endpoint:
            return jsonify({'error': 'endpoint is required'}), 400

        existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
        return jsonify({'message': 'Unsubscribed'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def calculate_distance_meters(lat1, lng1, lat2, lng2):
    """
    Calculate distance between two coordinates in meters using Haversine formula
    """
    R = 6371000  # Earth radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def generate_connection_key():
    """Generate a secure random connection key"""
    return secrets.token_urlsafe(32)

@device_bp.route('/create_device', methods=['POST'])
@jwt_required()
def create_device():
    """Create a new device manually (for connecting physical devices later)"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        name = data.get('name')
        device_id = data.get('device_id')
        device_type = data.get('device_type', 'laptop')
        
        if not name or not device_id:
            return jsonify({'error': 'name and device_id are required'}), 400
        
        # Check if device_id already exists
        existing = Device.query.filter_by(device_id=device_id).first()
        if existing:
            return jsonify({'error': f'Device with ID "{device_id}" already exists'}), 400
        
        # Generate connection key
        connection_key = generate_connection_key()
        
        # Create device
        device = Device(
            device_id=device_id,
            name=name,
            device_type=device_type,
            user_id=user_id,
            status='pending',  # Status is 'pending' until physical device connects
            connection_key=connection_key
        )
        
        db.session.add(device)
        db.session.flush()  # Flush to get device.id before creating activity log
        
        # Log device creation
        log = ActivityLog(
            device_id=device.id,
            action='device_created',
            description=f'Device "{name}" created manually. Waiting for physical device connection.'
        )
        db.session.add(log)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Device created successfully',
            'device': device.to_dict(),
            'connection_key': connection_key
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@device_bp.route('/register_device', methods=['POST'])
@jwt_required()
def register_device():
    """Register a new device (for auto-registration)"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        device_id = data.get('device_id')
        name = data.get('name')
        device_type = data.get('device_type', 'laptop')
        connection_key = data.get('connection_key')  # Optional: connect to existing device
        
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        # If connection_key provided, connect to existing device
        if connection_key:
            device = Device.query.filter_by(connection_key=connection_key).first()
            if not device:
                return jsonify({'error': 'Invalid connection key'}), 404
            
            if device.device_id != device_id:
                # Update device_id if it changed
                old_device_id = device.device_id
                device.device_id = device_id
                
                log = ActivityLog(
                    device_id=device.id,
                    action='device_connected',
                    description=f'Physical device connected using connection key. Device ID: {device_id}'
                )
                db.session.add(log)
            else:
                log = ActivityLog(
                    device_id=device.id,
                    action='device_connected',
                    description='Physical device connected successfully'
                )
                db.session.add(log)
            
            # Update device status and clear connection key (one-time use)
            device.status = 'active'
            device.connection_key = None  # Clear key after connection
            
            db.session.commit()
            
            return jsonify({
                'message': 'Device connected successfully',
                'device': device.to_dict()
            }), 200
        
        # Otherwise, create new device (existing behavior)
        existing = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if existing:
            return jsonify({'error': f'Device with ID "{device_id}" already registered'}), 400
        
        device = Device(
            device_id=device_id,
            name=name or device_id,
            device_type=device_type,
            user_id=user_id,
            status='active'
        )
        
        db.session.add(device)
        db.session.commit()  # Commit first to get device.id
        
        log = ActivityLog(
            device_id=device.id,
            action='device_registered',
            description=f'Device "{device.name}" registered automatically'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Device registered successfully',
            'device': device.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@device_bp.route('/agent_register_device', methods=['POST'])
def agent_register_device():
    """
    Register a physical device from the background agent using user email.
    This endpoint does NOT use JWT – the agent authenticates by user email.
    Flow:
      - User signs up via web with their email
      - Agent is configured with the same user_email in config.json
      - Agent calls this endpoint once on startup to attach the real device_id
        to that user account.
    """
    try:
        data = request.get_json() or {}
        device_id = data.get('device_id')
        device_type = data.get('device_type', 'laptop')
        name = data.get('name') or device_id
        user_email = data.get('user_email')

        if not device_id or not user_email:
            return jsonify({'error': 'device_id and user_email are required'}), 400

        # Find user by email – user must already exist (created via web signup)
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return jsonify({'error': f'User with email {user_email} not found'}), 404

        # If device already exists for this user, just return it (idempotent)
        existing = Device.query.filter_by(device_id=device_id, user_id=user.id).first()
        if existing:
            return jsonify({
                'message': 'Device already registered',
                'device': existing.to_dict()
            }), 200

        # Otherwise, create a new device attached to this user
        device = Device(
            device_id=device_id,
            name=name,
            device_type=device_type,
            user_id=user.id,
            status='active'
        )

        db.session.add(device)
        db.session.commit()

        # Log registration
        log = ActivityLog(
            device_id=device.id,
            action='device_registered',
            description=f'Device "{device.name}" registered automatically by agent for user {user.email}'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'message': 'Device registered successfully by agent',
            'device': device.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@device_bp.route('/devices/agent/register', methods=['POST'])
def agent_register_with_hardware():
    """
    Prey Project-style native agent registration with comprehensive hardware info.
    Endpoint: POST /api/devices/agent/register
    
    Expected payload:
    {
        "device_id": "unique-device-id",
        "user_email": "user@example.com",  # Optional: if not provided, uses admin@antitheft.com
        "os_info": {
            "os_name": "Windows 11",
            "os_version": "10.0.22621",
            "hostname": "MYPC",
            "architecture": "AMD64"
        },
        "system_info": {
            "vendor": "ASUS",
            "model": "TUF Gaming",
            "serial_number": "ABC123456"
        },
        "bios_info": {
            "vendor": "American Megatrends Inc.",
            "version": "F1.23",
            "date": "20230101"
        },
        "motherboard_info": {
            "vendor": "ASUSTeK",
            "model": "TUF GAMING B550-PLUS",
            "serial_number": "MB123456"
        },
        "cpu_info": {
            "model": "AMD Ryzen 7 3700X",
            "cores": 8,
            "threads": 16,
            "speed_mhz": 3600,
            "speed_ghz": 3.6
        },
        "ram_info": {
            "total_mb": 16384,
            "total_gb": 16.0
        },
        "network_info": {
            "interfaces": [
                {
                    "name": "Ethernet",
                    "mac": "00:11:22:33:44:55",
                    "ip_addresses": ["192.168.1.100"]
                }
            ],
            "mac_addresses": ["00:11:22:33:44:55", "AA:BB:CC:DD:EE:FF"]
        }
    }
    """
    try:
        data = request.get_json() or {}
        device_id = data.get('device_id')
        user_email = data.get('user_email', 'admin@antitheft.com')
        
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        # Find or create user
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return jsonify({'error': f'User with email {user_email} not found. Please sign up first.'}), 404
        
        # Parse hardware info
        os_info = data.get('os_info', {})
        system_info = data.get('system_info', {})
        bios_info = data.get('bios_info', {})
        motherboard_info = data.get('motherboard_info', {})
        cpu_info = data.get('cpu_info', {})
        ram_info = data.get('ram_info', {})
        network_info = data.get('network_info', {})
        
        # Check if device already exists
        device = Device.query.filter_by(device_id=device_id).first()
        is_new_device = device is None
        
        if device:
            # Update existing device with hardware info
            device.device_type = 'agent_device'
            # Update fields if provided (use get with default to handle None/empty)
            if os_info.get('os_name'):
                device.os_name = os_info.get('os_name')
            if os_info.get('os_version'):
                device.os_version = os_info.get('os_version')
            if os_info.get('hostname'):
                device.hostname = os_info.get('hostname')
            if os_info.get('architecture'):
                device.architecture = os_info.get('architecture')
            if system_info.get('vendor'):
                device.brand = system_info.get('vendor')
            if system_info.get('model'):
                device.model_name = system_info.get('model')
            if system_info.get('serial_number'):
                device.serial_number = system_info.get('serial_number')
            if bios_info.get('vendor'):
                device.bios_vendor = bios_info.get('vendor')
            if bios_info.get('version'):
                device.bios_version = bios_info.get('version')
            if motherboard_info.get('vendor'):
                device.motherboard_vendor = motherboard_info.get('vendor')
            if motherboard_info.get('model'):
                device.motherboard_model = motherboard_info.get('model')
            if motherboard_info.get('serial_number'):
                device.motherboard_serial = motherboard_info.get('serial_number')
            if cpu_info.get('model'):
                device.cpu_model = cpu_info.get('model')
                device.cpu_info = cpu_info.get('model')  # Legacy field
            if cpu_info.get('cores') is not None:
                device.cpu_cores = cpu_info.get('cores')
            if cpu_info.get('threads') is not None:
                device.cpu_threads = cpu_info.get('threads')
            if cpu_info.get('speed_mhz') is not None:
                device.cpu_speed_mhz = cpu_info.get('speed_mhz')
            if ram_info.get('total_mb') is not None:
                device.ram_mb = ram_info.get('total_mb')
            if ram_info.get('total_gb') is not None:
                device.ram_gb = ram_info.get('total_gb')
            
            # Store network info as JSON
            if network_info.get('interfaces'):
                device.network_interfaces = json.dumps(network_info['interfaces'])
            if network_info.get('mac_addresses'):
                device.mac_addresses = json.dumps(network_info['mac_addresses'])
            
            device.status = 'active'
            device.last_seen = datetime.utcnow()
            
            logging.info(f"Updated device {device_id} with hardware information")
        else:
            # Create new device with hardware info
            device_name = system_info.get('model') or os_info.get('hostname') or device_id
            if system_info.get('vendor'):
                device_name = f"{system_info['vendor']} {device_name}".strip()
            
            device = Device(
                device_id=device_id,
                name=device_name,
                device_type='agent_device',
                user_id=user.id,
                status='active',
                os_name=os_info.get('os_name'),
                os_version=os_info.get('os_version'),
                hostname=os_info.get('hostname'),
                architecture=os_info.get('architecture'),
                brand=system_info.get('vendor'),
                model_name=system_info.get('model'),
                serial_number=system_info.get('serial_number'),
                bios_vendor=bios_info.get('vendor'),
                bios_version=bios_info.get('version'),
                motherboard_vendor=motherboard_info.get('vendor'),
                motherboard_model=motherboard_info.get('model'),
                motherboard_serial=motherboard_info.get('serial_number'),
                cpu_model=cpu_info.get('model'),
                cpu_info=cpu_info.get('model'),  # Legacy field
                cpu_cores=cpu_info.get('cores'),
                cpu_threads=cpu_info.get('threads'),
                cpu_speed_mhz=cpu_info.get('speed_mhz'),
                ram_mb=ram_info.get('total_mb'),
                ram_gb=ram_info.get('total_gb'),
                network_interfaces=json.dumps(network_info.get('interfaces', [])) if network_info.get('interfaces') else None,
                mac_addresses=json.dumps(network_info.get('mac_addresses', [])) if network_info.get('mac_addresses') else None
            )
            
            db.session.add(device)
            logging.info(f"Created new device {device_id} with hardware information")
        
        db.session.flush()
        
        # Only log "device_registered" when it's actually a NEW device
        # Updates should not create registration logs (they happen on every agent startup/check)
        if is_new_device:
            log = ActivityLog(
                device_id=device.id,
                action='device_registered',
                description=f'Device "{device.name}" registered by native agent with full hardware info'
            )
            db.session.add(log)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Device registered successfully with hardware information',
            'device': device.to_dict()
        }), 200 if device.id else 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in agent hardware registration: {e}")
        return jsonify({'error': str(e)}), 500

@device_bp.route('/devices/pending-link', methods=['GET'])
def get_pending_link_token():
    """
    Agent polls this endpoint to check for pending device_link_tokens.
    Agent should call: GET /api/devices/pending-link?user_email=user@example.com
    Returns the first unused, non-expired token for the user (if any).
    """
    try:
        user_email = request.args.get('user_email')
        if not user_email:
            return jsonify({'error': 'user_email parameter is required'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=user_email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Find first unused, non-expired token for this user
        now = datetime.utcnow()
        token = DeviceLinkToken.query.filter_by(
            user_id=user.id,
            used=False
        ).filter(
            DeviceLinkToken.expires_at > now
        ).order_by(
            DeviceLinkToken.created_at.desc()
        ).first()
        
        if token:
            return jsonify({
                'has_token': True,
                'token': token.token,
                'expires_at': token.expires_at.isoformat()
            }), 200
        else:
            return jsonify({
                'has_token': False,
                'message': 'No pending tokens found'
            }), 200
        
    except Exception as e:
        logging.error(f"Error getting pending link token: {e}")
        return jsonify({'error': str(e)}), 500

@device_bp.route('/devices/agent/auto-register', methods=['POST'])
def agent_auto_register():
    """
    Prey Project-style automatic device registration with hardware info.
    Agent calls this with device_link_token to auto-register device.
    
    Payload:
    {
        "device_link_token": "abc123...",
        "os_info": {...},
        "system_info": {...},
        "bios_info": {...},
        "motherboard_info": {...},
        "cpu_info": {...},
        "ram_info": {...},
        "network_info": {...}
    }
    """
    try:
        data = request.get_json() or {}
        token_value = data.get('device_link_token')
        
        if not token_value:
            return jsonify({'error': 'device_link_token is required'}), 400
        
        # Validate token
        token = DeviceLinkToken.query.filter_by(token=token_value).first()
        if not token:
            return jsonify({'error': 'Invalid token'}), 400
        if token.used:
            return jsonify({'error': 'Token already used'}), 400
        if token.expires_at < datetime.utcnow():
            return jsonify({'error': 'Token expired'}), 400
        
        user_id = token.user_id
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Parse hardware info
        os_info = data.get('os_info', {})
        system_info = data.get('system_info', {})
        bios_info = data.get('bios_info', {})
        motherboard_info = data.get('motherboard_info', {})
        cpu_info = data.get('cpu_info', {})
        ram_info = data.get('ram_info', {})
        network_info = data.get('network_info', {})
        
        # Generate device_id from hardware info (use serial number if available, else UUID)
        device_id = None
        if system_info.get('serial_number') and system_info.get('serial_number') != 'Unknown':
            # Use serial number as part of device_id for stability
            import platform
            hostname = os_info.get('hostname') or platform.node() or 'device'
            device_id = f"{hostname}-{system_info['serial_number'][:8]}"
        else:
            # Fallback to UUID-based ID
            import uuid
            device_id = f"device-{uuid.uuid4().hex[:16]}"
        
        # Check if device already exists for this user (same hardware)
        existing_device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        
        if existing_device:
            # Update existing device with hardware info
            existing_device.device_type = 'agent_device'
            if os_info.get('os_name'):
                existing_device.os_name = os_info.get('os_name')
            if os_info.get('os_version'):
                existing_device.os_version = os_info.get('os_version')
            if os_info.get('hostname'):
                existing_device.hostname = os_info.get('hostname')
            if os_info.get('architecture'):
                existing_device.architecture = os_info.get('architecture')
            if system_info.get('vendor'):
                existing_device.brand = system_info.get('vendor')
            if system_info.get('model'):
                existing_device.model_name = system_info.get('model')
            if system_info.get('serial_number'):
                existing_device.serial_number = system_info.get('serial_number')
            if bios_info.get('vendor'):
                existing_device.bios_vendor = bios_info.get('vendor')
            if bios_info.get('version'):
                existing_device.bios_version = bios_info.get('version')
            if motherboard_info.get('vendor'):
                existing_device.motherboard_vendor = motherboard_info.get('vendor')
            if motherboard_info.get('model'):
                existing_device.motherboard_model = motherboard_info.get('model')
            if motherboard_info.get('serial_number'):
                existing_device.motherboard_serial = motherboard_info.get('serial_number')
            if cpu_info.get('model'):
                existing_device.cpu_model = cpu_info.get('model')
                existing_device.cpu_info = cpu_info.get('model')
            if cpu_info.get('cores') is not None:
                existing_device.cpu_cores = cpu_info.get('cores')
            if cpu_info.get('threads') is not None:
                existing_device.cpu_threads = cpu_info.get('threads')
            if cpu_info.get('speed_mhz') is not None:
                existing_device.cpu_speed_mhz = cpu_info.get('speed_mhz')
            if ram_info.get('total_mb') is not None:
                existing_device.ram_mb = ram_info.get('total_mb')
            if ram_info.get('total_gb') is not None:
                existing_device.ram_gb = ram_info.get('total_gb')
            if network_info.get('interfaces'):
                existing_device.network_interfaces = json.dumps(network_info['interfaces'])
            if network_info.get('mac_addresses'):
                existing_device.mac_addresses = json.dumps(network_info['mac_addresses'])
            
            existing_device.status = 'active'
            existing_device.last_seen = datetime.utcnow()
            device = existing_device
            logging.info(f"Updated existing device {device_id} with hardware information")
        else:
            # Create new device with hardware info
            device_name = system_info.get('model') or os_info.get('hostname') or device_id
            if system_info.get('vendor'):
                device_name = f"{system_info['vendor']} {device_name}".strip()
            if os_info.get('os_name'):
                device_name = f"{device_name} – {os_info.get('os_name', '')}".strip()
            
            device = Device(
                device_id=device_id,
                name=device_name,
                device_type='agent_device',
                user_id=user_id,
                status='active',
                os_name=os_info.get('os_name'),
                os_version=os_info.get('os_version'),
                hostname=os_info.get('hostname'),
                architecture=os_info.get('architecture'),
                brand=system_info.get('vendor'),
                model_name=system_info.get('model'),
                serial_number=system_info.get('serial_number'),
                bios_vendor=bios_info.get('vendor'),
                bios_version=bios_info.get('version'),
                motherboard_vendor=motherboard_info.get('vendor'),
                motherboard_model=motherboard_info.get('model'),
                motherboard_serial=motherboard_info.get('serial_number'),
                cpu_model=cpu_info.get('model'),
                cpu_info=cpu_info.get('model'),
                cpu_cores=cpu_info.get('cores'),
                cpu_threads=cpu_info.get('threads'),
                cpu_speed_mhz=cpu_info.get('speed_mhz'),
                ram_mb=ram_info.get('total_mb'),
                ram_gb=ram_info.get('total_gb'),
                network_interfaces=json.dumps(network_info.get('interfaces', [])) if network_info.get('interfaces') else None,
                mac_addresses=json.dumps(network_info.get('mac_addresses', [])) if network_info.get('mac_addresses') else None
            )
            
            db.session.add(device)
            logging.info(f"Created new device {device_id} with hardware information")
        
        db.session.flush()
        
        # Mark token as used
        token.used = True
        token.used_at = datetime.utcnow()
        
        # Log registration
        log = ActivityLog(
            device_id=device.id,
            action='device_registered',
            description=f'Device "{device.name}" auto-registered via native agent with hardware info'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Device registered successfully',
            'device': device.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in agent auto-register: {e}")
        return jsonify({'error': str(e)}), 500

@device_bp.route('/update_location', methods=['POST'])
def update_location():
    """Update device location - can be called by device agent without auth"""
    try:
        data = request.get_json()
        location_method = data.get('location_method')
        
        if not data or not data.get('device_id'):
            return jsonify({'error': 'device_id is required'}), 400
        
        device = Device.query.filter_by(device_id=data['device_id']).first()
        if not device:
            # Auto-register device to avoid manual "Add Device" step.
            # Prefer the user whose email the agent sends (so "Danish" sees his device), else admin/first user.
            user_email = data.get('user') or data.get('user_email')
            owner = None
            if user_email:
                owner = User.query.filter_by(email=user_email).first()
            if not owner:
                owner = User.query.filter_by(email='admin@antitheft.com').first() or User.query.first()
            if not owner:
                return jsonify({'error': 'Device not found and no owner user exists'}), 404

            device = Device(
                device_id=data['device_id'],
                name=data.get('device_name', data['device_id']),
                device_type=data.get('device_type', 'laptop'),
                user_id=owner.id,
                status=data.get('status', 'active')
            )
            db.session.add(device)
        else:
            # Device exists: link to the user the agent reports (so the right account sees "My device").
            # Handles both unowned (user_id is None) and wrong-owner (e.g. was assigned to admin).
            user_email = data.get('user') or data.get('user_email')
            if user_email:
                owner = User.query.filter_by(email=user_email).first()
                if owner and device.user_id != owner.id:
                    device.user_id = owner.id
                    logging.info(f"Device {device.device_id} linked to user {user_email} (id={owner.id})")
                    db.session.commit()

        # If we already have a stored location and this update is IP-based / approximate,
        # we normally ignore it so IP doesn't overwrite a better GPS/browser fix.
        # EXCEPTION: If the device has moved (>100m), accept the update so the map follows the user
        # as they move (e.g. walking/driving). Otherwise the location would stay stuck.
        # When not accepting, we still run geofence check with incoming coords so we don't miss a breach.
        if device.last_lat is not None and device.last_lng is not None:
            if location_method == 'ip' or data.get('location_approximate'):
                # Parse incoming location (same as below)
                loc = data.get('location', {})
                inc_lat = loc.get('lat') if isinstance(loc, dict) else None
                inc_lng = loc.get('lng') if isinstance(loc, dict) else None
                if inc_lat is None:
                    inc_lat = data.get('lat')
                if inc_lng is None:
                    inc_lng = data.get('lng')
                distance_moved = None
                if inc_lat is not None and inc_lng is not None:
                    distance_moved = calculate_distance_meters(
                        device.last_lat, device.last_lng, inc_lat, inc_lng
                    )
                # If user moved (e.g. walking/driving), accept so map follows device
                if distance_moved is not None and distance_moved > 100:
                    logging.info(
                        f"Accepting IP/approximate location: device moved {distance_moved:.0f}m - "
                        f"updating stored location so map follows user"
                    )
                    # Fall through: do not return; location will be updated below
                else:
                    # Same place or small move: run geofence check but don't update stored location
                    if (device.geofence_enabled and device.geofence_center_lat and device.geofence_center_lng
                            and inc_lat is not None and inc_lng is not None):
                        radius_km = device.geofence_radius_m / 1000.0
                        geofence_config = {
                            'center_lat': device.geofence_center_lat,
                            'center_lng': device.geofence_center_lng,
                            'radius_km': radius_km
                        }
                        is_inside, distance_km = check_geofence(inc_lat, inc_lng, geofence_config)
                        distance_m = distance_km * 1000 if distance_km else None
                        if device.was_inside_geofence and not is_inside:
                            logging.warning(
                                f"[GEOFENCE] BREACH (ignored update path) device={device.device_id} "
                                f"incoming lat={inc_lat} lng={inc_lng} distance_m={distance_m:.1f} radius_m={device.geofence_radius_m}"
                            )
                            device.status = 'alarm'
                            breach_log = ActivityLog(
                                device_id=device.id,
                                action='geofence_breach',
                                description=f'Device left geofence (from IP/approximate update)! Distance: {distance_m:.1f}m outside radius ({device.geofence_radius_m}m)',
                                lat=inc_lat,
                                lng=inc_lng
                            )
                            db.session.add(breach_log)
                            alarm_log = ActivityLog(
                                device_id=device.id,
                                action='alarm',
                                description=f'Auto-triggered alarm: Device breached geofence (moved {distance_m:.1f}m outside {device.geofence_radius_m}m radius)',
                                lat=inc_lat,
                                lng=inc_lng
                            )
                            db.session.add(alarm_log)
                            try:
                                from utils.email_alert import send_geofence_alert
                                user = User.query.get(device.user_id)
                                if user and user.email:
                                    send_geofence_alert(
                                        user.email,
                                        device.name,
                                        {
                                            'lat': inc_lat,
                                            'lng': inc_lng,
                                            'breach_type': 'GPS Geofence',
                                            'radius_m': device.geofence_radius_m,
                                            'distance_m': distance_m,
                                            'reason': 'Device left GPS geofence area (location from IP/approximate)'
                                        },
                                        device_id=device.device_id
                                    )
                                    logging.info(f"Notification sent to {user.email} for GPS geofence breach (ignored location update)")
                                if user:
                                    subs = PushSubscription.query.filter_by(user_id=user.id).all()
                                    subscription_payloads = [
                                        {"endpoint": s.endpoint, "keys": {"p256dh": s.p256dh, "auth": s.auth}}
                                        for s in subs
                                    ]
                                    if subscription_payloads:
                                        dashboard_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/") + f"/device/{device.device_id}"
                                        send_push_notifications(
                                            subscription_payloads,
                                            title="🚨 Anti-Theft Alert (GPS Geofence)",
                                            body=f'{device.name} left the GPS geofence area. Tap to open dashboard.',
                                            url=dashboard_url,
                                        )
                            except Exception as e:
                                logging.error(f"Error sending GPS geofence notification (ignored update path): {e}")
                            device.was_inside_geofence = False
                        else:
                            device.was_inside_geofence = is_inside
                        db.session.commit()
                    logging.warning(
                        f"⚠️ Ignoring IP/approximate location update for {device.device_id}: "
                        f"lat={data.get('lat') or data.get('location', {}).get('lat')}, "
                        f"lng={data.get('lng') or data.get('location', {}).get('lng')} "
                        f"(we already have a stored location)."
                    )
                    return jsonify({
                        'message': 'Approximate IP location ignored; existing coordinates preserved',
                        'device': device.to_dict()
                    }), 200
        
        # CRITICAL: Handle status updates FIRST, before location validation
        # This ensures status updates (like unlock: locked -> active) always work,
        # even if location is rejected or missing
        incoming_status = data.get('status')
        if incoming_status:
            old_status = device.status
            device.status = incoming_status
            
            # Log status change if it changed
            if old_status != incoming_status:
                logging.info(f"📊 Device status updated: {old_status} -> {incoming_status} (device_id: {device.device_id})")
                
                # If device was locked and now active, log unlock
                if old_status == 'locked' and incoming_status == 'active':
                    unlock_log = ActivityLog(
                        device_id=device.id,
                        action='unlock',
                        description=f'Device unlocked. Status changed from locked to active',
                        lat=None,  # Location may not be available yet
                        lng=None
                    )
                    db.session.add(unlock_log)
                    logging.info(f"🔓 Device unlocked successfully: {device.device_id}")
                # If device was in alarm and now sends a non-alarm status, log alarm cleared
                elif old_status == 'alarm' and incoming_status != 'alarm':
                    clear_log = ActivityLog(
                        device_id=device.id,
                        action='alarm_cleared',
                        description=f'Alarm cleared: Device status updated to {incoming_status}',
                        lat=None,
                        lng=None
                    )
                    db.session.add(clear_log)
        
        # Accept location from nested object or top-level (so different clients work)
        location = data.get('location', {})
        new_lat = location.get('lat') if isinstance(location, dict) else None
        new_lng = location.get('lng') if isinstance(location, dict) else None
        if new_lat is None:
            new_lat = data.get('lat')
        if new_lng is None:
            new_lng = data.get('lng')
        
        # CRITICAL: Reject KL area locations (wrong ISP location)
        # KL coordinates: ~3.14, 101.69
        # BUT: Always accept locations NOT in KL area (they're real GPS)
        if new_lat and new_lng:
            kl_area_lat = 3.14
            kl_area_lng = 101.69
            distance_from_kl = calculate_distance_meters(kl_area_lat, kl_area_lng, new_lat, new_lng)
            
            # If location is NOT in KL area, always accept it (it's real GPS)
            if distance_from_kl >= 20000:
                logging.info(f"✅ Accepting location update: New location is NOT in KL area (real GPS): {new_lat}, {new_lng}")
                # Continue to update - don't reject
            # If location is in KL area (within 20km) and device doesn't have a previous GPS location,
            # ACCEPT it for the first location (so device can show on map), but warn user.
            # If we already have a non-KL location, and the NEW location is KL + comes from IP,
            # REJECT it so a good GPS/browser fix (e.g. Merlimau) is not overwritten by ISP IP (KL).
            elif distance_from_kl < 20000:
                if not device.last_lat or not device.last_lng:
                    # No previous location - ACCEPT first location even if KL area (so device shows on map)
                    # But log a warning that GPS should be enabled for accuracy
                    logging.warning(f"⚠️ Accepting first location in KL area (may be IP geolocation): {new_lat}, {new_lng}")
                    logging.warning(f"   For accurate tracking, enable Windows Location Services: Settings > Privacy & Security > Location > Turn ON")
                    # Continue to update - don't reject (this allows device to show on map)
                else:
                    # Device has previous location - check if it's a significant jump
                    prev_dist_from_kl = calculate_distance_meters(kl_area_lat, kl_area_lng, device.last_lat, device.last_lng)
                    if prev_dist_from_kl > 20000:  # Previous location was NOT in KL
                        # New KL position from IP trying to overwrite a good non-KL fix (e.g. Merlimau).
                        # If location comes from IP/approximate, reject it and keep the better GPS/browser fix.
                        if location_method == 'ip' or data.get('location_approximate'):
                            logging.warning(
                                f"⚠️ Rejecting KL IP location {new_lat}, {new_lng} "
                                f"because last known location is non-KL ({device.last_lat}, {device.last_lng})."
                            )
                            return jsonify({
                                'message': 'Location update ignored: IP KL location would overwrite accurate non-KL fix',
                                'device': device.to_dict()
                            }), 200
                        # Otherwise (non-IP), accept – device might really be in KL now.
                        logging.warning(f"⚠️ Non-IP location jumped to KL area from {device.last_lat}, {device.last_lng}")
                        # Continue to update - don't reject
                    # else: both locations are in KL, might be correct (device actually in KL) - accept it
        
        # Validate location accuracy - reject if location changed too dramatically
        # This prevents IP geolocation drift from causing false alarms
        # BUT: Always accept if new location is NOT in KL area (it's likely real GPS)
        if device.last_lat and device.last_lng and new_lat and new_lng:
            distance = calculate_distance_meters(
                device.last_lat, device.last_lng,
                new_lat, new_lng
            )
            
            # Check if new location is in KL area
            kl_area_lat = 3.14
            kl_area_lng = 101.69
            new_dist_from_kl = calculate_distance_meters(kl_area_lat, kl_area_lng, new_lat, new_lng)
            
            # If new location is NOT in KL area, always accept it (it's real GPS, not ISP location)
            if new_dist_from_kl >= 20000:
                logging.info(f"Accepting location update: New location is NOT in KL area (real GPS): {new_lat}, {new_lng}")
                # Continue to update - don't reject
            # If location changed by more than 10km, it's likely inaccurate (IP geolocation issue)
            # Only reject if: not approximate, AND location_unchanged, AND new location is in KL area
            # When location_approximate=True, user/agent accepts KL IP geolocation (device may be in KL)
            elif (distance > 10000 and data.get('location_unchanged') and new_dist_from_kl < 20000
                  and not data.get('location_approximate')):
                logging.warning(f"Rejecting location update: device moved {distance:.0f}m to KL area, likely inaccurate IP geolocation")
                # Commit status update before returning (status was already updated above)
                db.session.commit()
                return jsonify({
                    'message': 'Location update rejected - location change too large, likely inaccurate',
                    'distance_meters': round(distance),
                    'device': device.to_dict()
                }), 200  # Return 200 but don't update location
            
            # If location changed by more than 5km and less than 10km, log warning but accept
            elif distance > 5000:
                logging.warning(f"Large location change detected: {distance:.0f}m - accepting but may be inaccurate")
        
        # Check geofence BEFORE updating location (if enabled)
        geofence_breach = False
        alarm_triggered = False
        
        if device.geofence_enabled and device.geofence_center_lat and device.geofence_center_lng:
            if new_lat and new_lng:
                # Convert radius from meters to kilometers for check_geofence
                radius_km = device.geofence_radius_m / 1000.0
                geofence_config = {
                    'center_lat': device.geofence_center_lat,
                    'center_lng': device.geofence_center_lng,
                    'radius_km': radius_km
                }
                
                is_inside, distance_km = check_geofence(new_lat, new_lng, geofence_config)
                distance_m = distance_km * 1000 if distance_km else None
                logging.info(
                    f"[GEOFENCE] device={device.device_id} was_inside={device.was_inside_geofence} "
                    f"is_inside={is_inside} distance_m={distance_m:.1f} radius_m={device.geofence_radius_m} "
                    f"lat={new_lat} lng={new_lng}"
                )
                # Check if device left the geofence (was inside, now outside)
                if device.was_inside_geofence and not is_inside:
                    logging.warning(
                        f"[GEOFENCE] BREACH device={device.device_id} lat={new_lat} lng={new_lng} "
                        f"distance_m={distance_m:.1f} radius_m={device.geofence_radius_m} - triggering alarm and email"
                    )
                    geofence_breach = True
                    # Trigger alarm automatically
                    device.status = 'alarm'
                    alarm_triggered = True
                    
                    # Log geofence breach and alarm
                    breach_log = ActivityLog(
                        device_id=device.id,
                        action='geofence_breach',
                        description=f'Device left geofence! Distance: {distance_m:.1f}m outside radius ({device.geofence_radius_m}m)',
                        lat=new_lat,
                        lng=new_lng
                    )
                    db.session.add(breach_log)
                    
                    alarm_log = ActivityLog(
                        device_id=device.id,
                        action='alarm',
                        description=f'Auto-triggered alarm: Device breached geofence (moved {distance_m:.1f}m outside {device.geofence_radius_m}m radius)',
                        lat=new_lat,
                        lng=new_lng
                    )
                    db.session.add(alarm_log)
                    
                    # Send notification to user (email + push) for GPS geofence breach
                    try:
                        from utils.email_alert import send_geofence_alert
                        user = User.query.get(device.user_id)
                        if user and user.email:
                            send_geofence_alert(
                                user.email,
                                device.name,
                                {
                                    'lat': new_lat,
                                    'lng': new_lng,
                                    'breach_type': 'GPS Geofence',
                                    'radius_m': device.geofence_radius_m,
                                    'distance_m': distance_m,
                                    'reason': 'Device left GPS geofence area'
                                },
                                device_id=device.device_id
                            )
                            logging.info(f"Notification sent to {user.email} for GPS geofence breach")

                            # Push notification (best-effort)
                            subs = PushSubscription.query.filter_by(user_id=user.id).all()
                            subscription_payloads = [
                                {
                                    "endpoint": s.endpoint,
                                    "keys": {"p256dh": s.p256dh, "auth": s.auth},
                                }
                                for s in subs
                            ]
                            if subscription_payloads:
                                dashboard_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/") + f"/device/{device.device_id}"
                                send_push_notifications(
                                    subscription_payloads,
                                    title="🚨 Anti-Theft Alert (GPS Geofence)",
                                    body=f'{device.name} left the GPS geofence area. Tap to open dashboard.',
                                    url=dashboard_url,
                                )
                    except Exception as e:
                        logging.error(f"Error sending GPS geofence notification: {e}")
                
                # Check if device returned to safe zone (was outside/alarm, now inside)
                elif not device.was_inside_geofence and is_inside and device.status == 'alarm':
                    # Clear alarm status - device is back inside geofence
                    device.status = 'active'
                    
                    # Log alarm cleared
                    clear_log = ActivityLog(
                        device_id=device.id,
                        action='alarm_cleared',
                        description=f'Alarm cleared: Device returned to geofence (now {distance_m:.1f}m inside {device.geofence_radius_m}m radius)',
                        lat=new_lat,
                        lng=new_lng
                    )
                    db.session.add(clear_log)
                
                # Update geofence state
                device.was_inside_geofence = is_inside
        
        # Update device location - ensure coordinates are valid numbers
        # CRITICAL: Validate and fix swapped coordinates before storing
        if new_lat is not None and new_lng is not None:
            try:
                raw_lat = float(new_lat)
                raw_lng = float(new_lng)
                
                # Detect and fix swapped coordinates
                # Latitude must be between -90 and 90, Longitude must be between -180 and 180
                if abs(raw_lat) > 90:
                    # Latitude is invalid - coordinates are swapped
                    logging.warning(f"⚠️ Detected swapped coordinates in backend: lat={raw_lat}, lng={raw_lng}")
                    logging.warning(f"   Swapping to correct order: lat={raw_lng}, lng={raw_lat}")
                    new_lat = raw_lng
                    new_lng = raw_lat
                elif abs(raw_lng) > 180:
                    # Longitude is invalid - coordinates are swapped
                    logging.warning(f"⚠️ Detected swapped coordinates (invalid lng) in backend: lat={raw_lat}, lng={raw_lng}")
                    logging.warning(f"   Swapping to correct order: lat={raw_lng}, lng={raw_lat}")
                    new_lat = raw_lng
                    new_lng = raw_lat
                elif (99 <= abs(raw_lat) <= 180 and abs(raw_lng) <= 90) or (abs(raw_lng) <= 25 and 90 < abs(raw_lat) <= 180):
                    # In-range swap: e.g. (101.68, 3.14) where 101 is lng and 3 is lat - common Windows/API bug
                    # If lat looks like lng (99-180) and lng looks like lat (-90 to 90), swap
                    logging.warning(f"⚠️ Detected in-range swapped coordinates: lat={raw_lat}, lng={raw_lng}")
                    logging.warning(f"   Swapping to correct order: lat={raw_lng}, lng={raw_lat}")
                    new_lat = raw_lng
                    new_lng = raw_lat
                else:
                    new_lat = raw_lat
                    new_lng = raw_lng
                
                # Final validation: ensure coordinates are in valid ranges after swap check
                if not (-90 <= new_lat <= 90) or not (-180 <= new_lng <= 180):
                    logging.error(f"❌ Invalid coordinate ranges after swap check: lat={new_lat}, lng={new_lng}")
                    return jsonify({'error': 'Invalid coordinate ranges'}), 400
            except (ValueError, TypeError):
                logging.warning(f"Invalid coordinate types: lat={new_lat}, lng={new_lng}")
                return jsonify({'error': 'Invalid coordinate types'}), 400
        
        device.last_lat = new_lat
        device.last_lng = new_lng
        device.last_location_update = datetime.utcnow()
        
        # Log the coordinates being stored for debugging
        logging.info(f"Storing location for device {device.device_id}: lat={new_lat}, lng={new_lng}")
        if location_method:
            logging.info(f"Location method reported by agent: {location_method}")
        logging.info(f"Previous location was: lat={device.last_lat}, lng={device.last_lng}")
        device.last_seen = datetime.utcnow()
        
        # Update current WiFi SSID if provided
        if data.get('current_wifi_ssid'):
            device.current_wifi_ssid = data.get('current_wifi_ssid')
        
        # Update battery percentage if provided
        if 'battery_percentage' in data:
            battery_percentage = data.get('battery_percentage')
            if battery_percentage is not None:
                try:
                    battery_percentage = int(battery_percentage)
                    # Validate battery percentage is between 0-100
                    if 0 <= battery_percentage <= 100:
                        device.battery_percentage = battery_percentage
                        logging.debug(f"Updated battery percentage for device {device.device_id}: {battery_percentage}%")
                except (ValueError, TypeError):
                    logging.warning(f"Invalid battery percentage value: {battery_percentage}")
        
        # Handle WiFi geofence breach (from device agent)
        wifi_geofence_breach = data.get('wifi_geofence_breach', False)
        if wifi_geofence_breach and not alarm_triggered:
            # WiFi geofence breach detected by device agent
            breach_details = data.get('breach_details', {})
            required_ssid = breach_details.get('required_ssid', 'Unknown')
            current_ssid = breach_details.get('current_ssid', 'DISCONNECTED')
            
            device.status = 'alarm'
            alarm_triggered = True
            
            # Log WiFi geofence breach
            breach_log = ActivityLog(
                device_id=device.id,
                action='wifi_geofence_breach',
                description=f'WiFi Geofence Breach: Device disconnected from required network "{required_ssid}". Current: {current_ssid}',
                lat=new_lat,
                lng=new_lng
            )
            db.session.add(breach_log)
            
            # Log alarm triggered
            alarm_log = ActivityLog(
                device_id=device.id,
                action='alarm',
                description=f'🚨 ALARM TRIGGERED: Device stolen or moved out of WiFi range! Disconnected from "{required_ssid}"',
                lat=new_lat,
                lng=new_lng
            )
            db.session.add(alarm_log)
            
            # Send notification to user (email + push)
            try:
                # User model is imported at the top of this file.
                # Only import the email helper here to avoid making User a local variable.
                from utils.email_alert import send_geofence_alert
                user = User.query.get(device.user_id)
                if user and user.email:
                    send_geofence_alert(
                        user.email,
                        device.name,
                        {
                            'lat': new_lat,
                            'lng': new_lng,
                            'breach_type': 'WiFi Geofence',
                            'required_ssid': required_ssid,
                            'current_ssid': current_ssid,
                            'signal_strength': breach_details.get('signal_strength'),
                            'signal_threshold': breach_details.get('signal_threshold'),
                            'reason': breach_details.get('reason', 'WiFi geofence breach detected')
                        },
                        device_id=device.device_id
                    )
                    logging.info(f"Notification sent to {user.email} for WiFi geofence breach")

                    # Push notification (best-effort)
                    subs = PushSubscription.query.filter_by(user_id=user.id).all()
                    subscription_payloads = [
                        {
                            "endpoint": s.endpoint,
                            "keys": {"p256dh": s.p256dh, "auth": s.auth},
                        }
                        for s in subs
                    ]
                    if subscription_payloads:
                        dashboard_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/") + f"/device/{device.device_id}"
                        send_push_notifications(
                            subscription_payloads,
                            title="🚨 Anti-Theft Alert (WiFi Geofence)",
                            body=f'{device.name} may have been moved/stolen (WiFi: {current_ssid}). Tap to open dashboard.',
                            url=dashboard_url,
                        )
            except Exception as e:
                logging.error(f"Error sending notification: {e}")
        
        # Status was already updated at the beginning of the function
        # But if alarm was triggered by geofence, it will override the status
        # This is intentional - geofence alarms take priority
        
        # Log location update (include method if provided for easier debugging)
        method_suffix = f" [method={location_method}]" if location_method else ""
        log = ActivityLog(
            device_id=device.id,
            action='location_update',
            description=f'Location updated{method_suffix}: {new_lat}, {new_lng}' + (' - ALARM TRIGGERED!' if alarm_triggered else ''),
            lat=new_lat,
            lng=new_lng
        )
        db.session.add(log)
        db.session.commit()
        
        response_data = {
            'message': 'Location updated',
            'device': device.to_dict()
        }
        
        if geofence_breach or wifi_geofence_breach:
            response_data['geofence_breach'] = True
            response_data['alarm_triggered'] = True
            if wifi_geofence_breach:
                response_data['message'] = '🚨 ALARM TRIGGERED: Device disconnected from WiFi network - Possible theft!'
            else:
                response_data['message'] = 'Location updated - ALARM TRIGGERED: Device left geofence!'
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@device_bp.route('/devices/verify_location', methods=['POST'])
@jwt_required()
def verify_location():
    """
    Verify device location using browser GPS (weather.com-style assist).
    - Requires JWT (user must be logged in)
    - Requires device_id and browser-provided lat/lng/accuracy
    - Updates device.last_lat/lng and logs a 'location_verified' activity
    """
    try:
        data = request.get_json() or {}
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id

        device_id = data.get('device_id')
        lat = data.get('lat')
        lng = data.get('lng')
        accuracy = data.get('accuracy')

        if not device_id or lat is None or lng is None:
            return jsonify({'error': 'device_id, lat and lng are required'}), 400

        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        # Validate and cast coordinates
        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid coordinate types'}), 400

        if not (-90 <= lat_f <= 90) or not (-180 <= lng_f <= 180):
            return jsonify({'error': 'Invalid coordinate ranges'}), 400

        # Trust browser GPS: no KL/IP heuristics here
        device.last_lat = lat_f
        device.last_lng = lng_f
        device.last_location_update = datetime.utcnow()
        device.last_seen = datetime.utcnow()

        # Log verification
        acc_text = f"±{accuracy:.0f}m" if isinstance(accuracy, (int, float)) else f"±{accuracy}m" if accuracy else "unknown accuracy"
        log = ActivityLog(
            device_id=device.id,
            action='location_verified',
            description=f'Location verified by user via browser GPS ({acc_text})',
            lat=lat_f,
            lng=lng_f
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'message': 'Location verified via browser GPS',
            'device': device.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@device_bp.route('/check_config_update/<device_id>', methods=['GET'])
def check_config_update(device_id):
    """
    Check for pending configuration updates for a device.
    Used by device agent to auto-update config.json
    
    This checks if:
    1. A device with this device_id is already registered to a user
    2. If so, returns that user's email for auto-config update
    """
    try:
        # Check if there's a device registered with this device_id
        device = Device.query.filter_by(device_id=device_id).first()
        if device:
            user = User.query.get(device.user_id)
            if user:
                return jsonify({
                    'has_update': True,
                    'user_email': user.email,
                    'device_id': device_id
                }), 200
        
        # Also check for recently registered users (within last 30 minutes)
        # This helps with auto-setup when user just registered
        # Extended to 30 minutes to give more time for agent to check
        recent_cutoff = datetime.utcnow() - timedelta(minutes=30)
        recent_users = User.query.filter(User.created_at >= recent_cutoff).order_by(User.created_at.desc()).limit(1).all()
        
        # If there's a recent user and no device registered yet, suggest the most recent user
        # The agent can try updating to this email and see if registration succeeds
        if recent_users and not device:
            # Return the most recently registered user's email
            # Agent will try updating config and registering
            logging.info(f"Suggesting auto-setup: device_id={device_id}, suggested_email={recent_users[0].email}")
            return jsonify({
                'has_update': True,
                'user_email': recent_users[0].email,
                'device_id': device_id,
                'suggested': True  # Indicates this is a suggestion, not a confirmed match
            }), 200
        
        return jsonify({'has_update': False}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@device_bp.route('/get_device_status/<device_id>', methods=['GET'])
@jwt_required(optional=True)
def get_device_status(device_id):
    """
    Get device status - can be accessed by device agent without JWT
    If JWT provided, returns full device details
    """
    try:
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # If JWT provided, verify ownership
        user_id = get_jwt_identity()
        if user_id:
            user_id = int(user_id) if isinstance(user_id, str) else user_id
            if device.user_id != user_id:
                logging.warning(f"Unauthorized access attempt: device {device_id} belongs to user {device.user_id}, but user {user_id} tried to access it")
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'This device belongs to another user account'
                }), 403
            return jsonify(device.to_dict()), 200
        
        # For agent access without JWT, return limited info
        return jsonify({
            'device_id': device.device_id,
            'status': device.status,
            'is_missing': device.is_missing,
            'geofence_enabled': device.geofence_enabled,
            'geofence_type': device.geofence_type,
            'geofence_wifi_ssid': device.geofence_wifi_ssid,
            'geofence_radius_m': device.geofence_radius_m  # For WiFi signal threshold
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@device_bp.route('/get_devices', methods=['GET'])
@jwt_required()
def get_devices():
    """Get all devices for the current user"""
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        devices = Device.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'devices': [device.to_dict() for device in devices]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@device_bp.route('/trigger_action', methods=['POST'])
@jwt_required()
def trigger_action():
    """Trigger remote action on device (lock, alarm, wipe)"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        device_id = data.get('device_id')
        action = data.get('action')
        
        if not device_id or not action:
            return jsonify({'error': 'device_id and action are required'}), 400
        
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        # OS-based devices (detected via browser) are view-only: they cannot be locked, wiped or alarmed
        # Only agent-based devices (device_type = 'agent_device' or physical device types) can be controlled
        if device.device_type == 'os_device' and action in ('lock', 'alarm', 'wipe'):
            return jsonify({'error': 'This action is not supported for OS-based devices. Install the device agent for full control.'}), 400
        
        # Update device status based on action (agent-based / physical devices only)
        # CRITICAL: Update status IMMEDIATELY and commit to ensure agent detects it fast
        if action == 'lock':
            device.status = 'locked'
        elif action == 'alarm':
            device.status = 'alarm'
        elif action == 'wipe':
            device.status = 'wiped'
        
        # Commit immediately to ensure status is available for agent polling
        db.session.commit()
        
        # Log the status change for debugging
        logging.info(f"✅ Status updated to '{device.status}' for device {device_id} (action: {action})")
        
        # Create activity log with action details
        description = f'Remote {action} action triggered by user'
        if action == 'lock':
            # Get password exactly as sent (preserve case and all characters)
            password = str(data.get('password', 'antitheft2024')).strip()
            message = data.get('message', '')
            if message:
                description += f'. password: {password}, Message: {message}'
            else:
                description += f'. password: {password}'
        
        log = ActivityLog(
            device_id=device.id,
            action=action,
            description=description
        )
        
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': f'{action} action triggered',
            'device': device.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@device_bp.route('/update_device', methods=['PUT'])
@jwt_required()
def update_device():
    """Update device name"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        device_id = data.get('device_id')
        name = data.get('name')
        
        if not device_id or not name:
            return jsonify({'error': 'device_id and name are required'}), 400
        
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        old_name = device.name
        device.name = name
        db.session.commit()
        
        # Log rename
        log = ActivityLog(
            device_id=device.id,
            action='device_renamed',
            description=f'Device renamed from "{old_name}" to "{name}"'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Device updated successfully',
            'device': device.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@device_bp.route('/delete_device', methods=['DELETE'])
@jwt_required()
def delete_device():
    """Delete a device"""
    try:
        device_id = request.args.get('device_id')
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Delete all activity logs first
        ActivityLog.query.filter_by(device_id=device.id).delete()
        
        # Delete device
        db.session.delete(device)
        db.session.commit()
        
        return jsonify({'message': 'Device deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@device_bp.route('/mark_as_missing', methods=['POST'])
@jwt_required()
def mark_as_missing():
    """Mark device as missing or found (toggle)"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        device_id = data.get('device_id')
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Toggle missing status
        if device.is_missing:
            # Mark as found
            device.is_missing = False
            device.missing_since = None
            device.status = 'active'
            action = 'missing_mode_deactivated'
            description = 'Device marked as found - missing mode deactivated'
        else:
            # Mark as missing
            device.is_missing = True
            device.missing_since = datetime.utcnow()
            device.status = 'missing'
            action = 'missing_mode_activated'
            description = 'Device marked as missing - tracking activated'
        
        db.session.commit()
        
        # Log the action
        log = ActivityLog(
            device_id=device.id,
            action=action,
            description=description
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': description,
            'device': device.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@device_bp.route('/set_geofence', methods=['POST'])
@jwt_required()
def set_geofence():
    """Set geofence for a device"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        device_id = data.get('device_id')
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Update geofence settings
        if 'center_lat' in data and 'center_lng' in data:
            device.geofence_center_lat = data['center_lat']
            device.geofence_center_lng = data['center_lng']
        
        if 'radius_m' in data:
            device.geofence_radius_m = float(data['radius_m'])
        elif device.geofence_radius_m is None:
            device.geofence_radius_m = 200.0  # Default 200m
        
        if 'geofence_type' in data:
            device.geofence_type = data['geofence_type']  # 'gps' or 'wifi'
        
        if 'wifi_ssid' in data:
            device.geofence_wifi_ssid = data['wifi_ssid']
        
        if 'enabled' in data:
            device.geofence_enabled = bool(data['enabled'])
        
        # Initialize was_inside_geofence based on geofence type
        if device.geofence_enabled:
            if device.geofence_type == 'gps' and device.last_lat and device.last_lng and device.geofence_center_lat and device.geofence_center_lng:
                radius_km = device.geofence_radius_m / 1000.0
                geofence_config = {
                    'center_lat': device.geofence_center_lat,
                    'center_lng': device.geofence_center_lng,
                    'radius_km': radius_km
                }
                is_inside, _ = check_geofence(device.last_lat, device.last_lng, geofence_config)
                device.was_inside_geofence = is_inside
            elif device.geofence_type == 'wifi' and device.geofence_wifi_ssid:
                # For WiFi, assume device is "inside" if it's connected to the required network
                # The agent will check this and update the status
                device.was_inside_geofence = True
        
        # Log geofence update
        log = ActivityLog(
            device_id=device.id,
            action='geofence_updated',
            description=f'Geofence {"enabled" if device.geofence_enabled else "disabled"}: Type={device.geofence_type}, Radius={device.geofence_radius_m}m'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Geofence updated successfully',
            'device': device.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@device_bp.route('/clear_alarm', methods=['POST'])
@jwt_required()
def clear_alarm():
    """Manually clear alarm status for a device"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        device_id = data.get('device_id')
        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # Only clear if currently in alarm
        if device.status == 'alarm':
            device.status = 'active'
            
            # Log alarm cleared
            log = ActivityLog(
                device_id=device.id,
                action='alarm_cleared',
                description='Alarm manually cleared by user'
            )
            db.session.add(log)
            # Commit immediately to ensure agent detects status change fast
            db.session.commit()
            
            # Log the status change for debugging
            logging.info(f"✅ Alarm cleared - Status updated to 'active' for device {device_id}")
            
            return jsonify({
                'message': 'Alarm cleared successfully',
                'device': device.to_dict()
            }), 200
        else:
            return jsonify({
                'message': f'Device is not in alarm status (current: {device.status})',
                'device': device.to_dict()
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@device_bp.route('/register_os_device', methods=['POST'])
@jwt_required()
def register_os_device():
    """
    Register an OS-level device detected from the web interface using User-Agent Client Hints.
    This automatically creates a device entry when user registers or logs in.
    """
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        user_id = int(user_id) if isinstance(user_id, str) else user_id
        
        device_id = data.get('device_id')
        device_name = data.get('device_name') or data.get('name') or 'OS Device'
        user_email = data.get('user_email')

        if not device_id:
            return jsonify({'error': 'device_id is required'}), 400
        
        # Verify user owns this (or use user_email if provided)
        if user_email:
            user = User.query.filter_by(email=user_email).first()
            if user and user.id != user_id:
                return jsonify({'error': 'User mismatch'}), 403
            user_id = user.id if user else user_id
        
        # Resolve IP for this call
        forwarded_for = request.headers.get('X-Forwarded-For', '')
        if forwarded_for:
            raw_ip = forwarded_for.split(',')[0].strip()
        else:
            raw_ip = request.remote_addr

        # Check if device already exists globally
        existing_global = Device.query.filter_by(device_id=device_id).first()
        if existing_global and existing_global.user_id != user_id:
            return jsonify({'error': 'Device ID is already registered to another user'}), 409

        # Check if device already exists for this user
        existing = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        if existing:
            # Update metadata and last seen / IP on re-registration
            existing.device_type = existing.device_type or 'os_device'
            # Update OS-level fields
            existing.os_name = data.get('os_name') or existing.os_name
            existing.os_version = data.get('os_version') or existing.os_version
            existing.architecture = data.get('architecture') or existing.architecture
            existing.device_class = data.get('device_class') or existing.device_class
            existing.gpu = data.get('gpu') or existing.gpu
            # Update browser fields
            existing.browser = data.get('browser') or existing.browser
            existing.browser_name = data.get('browser_name') or existing.browser_name
            existing.browser_version = data.get('browser_version') or existing.browser_version
            # Update environment fields
            existing.platform = data.get('platform') or existing.platform
            existing.user_agent = data.get('user_agent') or existing.user_agent
            existing.screen_resolution = data.get('screen_resolution') or existing.screen_resolution
            existing.timezone = data.get('timezone') or existing.timezone
            existing.last_ip = data.get('last_ip') or raw_ip or existing.last_ip
            existing.last_seen = datetime.utcnow()
            # Legacy field
            existing.os = data.get('os') or data.get('os_version') or existing.os

            db.session.commit()

            return jsonify({
                'message': 'OS device updated',
                'device': existing.to_dict()
            }), 200
        
        # Create OS device
        has_any_device = Device.query.filter_by(user_id=user_id).count() > 0
        device = Device(
            device_id=device_id,
            name=device_name,
            device_type='os_device',
            user_id=user_id,
            status='active',
            # OS-level fields
            os_name=data.get('os_name'),
            os_version=data.get('os_version'),
            architecture=data.get('architecture'),
            device_class=data.get('device_class'),
            gpu=data.get('gpu'),
            # Browser fields
            browser=data.get('browser'),
            browser_name=data.get('browser_name'),
            browser_version=data.get('browser_version'),
            # Environment fields
            platform=data.get('platform'),
            user_agent=data.get('user_agent'),
            screen_resolution=data.get('screen_resolution'),
            timezone=data.get('timezone'),
            last_ip=data.get('last_ip') or raw_ip,
            is_primary=not has_any_device,
            last_seen=datetime.utcnow(),
            # Legacy field
            os=data.get('os') or data.get('os_version')
        )
        
        db.session.add(device)
        db.session.flush()  # Flush to get device.id
        
        # Log registration
        log = ActivityLog(
            device_id=device.id,
            action='device_registered',
            description=f'OS device "{device_name}" registered automatically from web interface'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'OS device registered successfully',
            'device': device.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Native agent registration using a short-lived link token
@device_bp.route('/devices/agent-register', methods=['POST'])
def agent_register_with_token():
    """
    Register/link a device via the native agent using a short-lived device_link_token.
    No JWT required; token-based.
    """
    try:
        data = request.get_json() or {}
        token_value = data.get('device_link_token')
        device_id = data.get('device_id')

        if not token_value or not device_id:
            return jsonify({'error': 'device_link_token and device_id are required'}), 400

        # Validate token
        token_row = DeviceLinkToken.query.filter_by(token=token_value).first()
        if not token_row:
            return jsonify({'error': 'Invalid token'}), 400
        if token_row.used:
            return jsonify({'error': 'Token already used'}), 400
        if token_row.expires_at < datetime.utcnow():
            return jsonify({'error': 'Token expired'}), 400

        user_id = token_row.user_id

        # Reject if device_id belongs to another user
        existing_global = Device.query.filter_by(device_id=device_id).first()
        if existing_global and existing_global.user_id != user_id:
            return jsonify({'error': 'Device ID already linked to another user'}), 409

        # Build device name
        brand = data.get('brand') or data.get('hardware_info', {}).get('brand')
        model = data.get('model') or data.get('hardware_info', {}).get('model')
        os_version = data.get('os_version') or data.get('real_os_info', {}).get('os_version')
        os_name = data.get('os_name') or data.get('real_os_info', {}).get('os_name')

        name_parts = []
        if brand:
            name_parts.append(brand)
        if model:
            name_parts.append(model)
        name_label = " ".join(name_parts).strip()
        os_label = os_version or os_name or ''
        if name_label and os_label:
            device_name = f"{name_label} – {os_label}"
        elif name_label:
            device_name = name_label
        elif os_label:
            device_name = os_label
        else:
            device_name = "Agent Device"

        # Create or update device for this user
        device = Device.query.filter_by(device_id=device_id, user_id=user_id).first()
        now_utc = datetime.utcnow()

        if device:
            device.device_type = 'agent_device'
        else:
            has_any_device = Device.query.filter_by(user_id=user_id).count() > 0
            device = Device(
                device_id=device_id,
                user_id=user_id,
                name=device_name,
                device_type='agent_device',
                status='active',
                is_primary=not has_any_device,
                created_at=now_utc
            )
            db.session.add(device)
            db.session.flush()

        # Update fields
        device.os_name = os_name or device.os_name
        device.os_version = os_version or device.os_version
        device.architecture = data.get('architecture') or device.architecture
        device.device_class = data.get('device_class') or device.device_class
        device.gpu = data.get('gpu') or device.gpu
        device.brand = brand or device.brand
        device.model_name = model or device.model_name
        device.cpu_info = data.get('cpu_info') or device.cpu_info
        device.hostname = data.get('hostname') or device.hostname
        device.platform = data.get('platform') or device.platform
        device.last_ip = data.get('last_ip') or request.remote_addr or device.last_ip
        device.last_seen = now_utc

        # Mark token used
        token_row.used = True
        token_row.used_at = now_utc

        # Log registration
        log = ActivityLog(
            device_id=device.id,
            action='device_registered',
            description=f'Agent device "{device.name}" registered via token'
        )
        db.session.add(log)

        db.session.commit()

        return jsonify({
            'message': 'Agent device registered successfully',
            'device': device.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Legacy endpoint for backward compatibility
@device_bp.route('/register_browser_device', methods=['POST'])
@jwt_required()
def register_browser_device():
    """Legacy endpoint - redirects to register_os_device"""
    return register_os_device()

@device_bp.route('/get_activity_logs/<device_id>', methods=['GET'])
@jwt_required(optional=True)
def get_activity_logs(device_id):
    """
    Get activity logs for a device - can be accessed by device agent without JWT
    """
    try:
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        # If JWT provided, verify ownership
        user_id = get_jwt_identity()
        if user_id:
            user_id = int(user_id) if isinstance(user_id, str) else user_id
            if device.user_id != user_id:
                return jsonify({'error': 'Unauthorized'}), 403
        
        # Get activity logs
        logs = ActivityLog.query.filter_by(device_id=device.id).order_by(ActivityLog.created_at.desc()).limit(100).all()
        
        return jsonify({
            'logs': [{
                'id': log.id,
                'action': log.action,
                'description': log.description,
                'created_at': log.created_at.isoformat(),
                'lat': log.lat,
                'lng': log.lng
            } for log in logs]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
