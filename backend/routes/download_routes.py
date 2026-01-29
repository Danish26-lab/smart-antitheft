from flask import Blueprint, send_file, jsonify
from pathlib import Path
import zipfile
import io
import os

# Import embedded agent files for Vercel deployment
try:
    from utils.agent_files import AGENT_FILES
    EMBEDDED_FILES_AVAILABLE = True
except ImportError:
    AGENT_FILES = {}
    EMBEDDED_FILES_AVAILABLE = False

download_bp = Blueprint('download', __name__)

@download_bp.route('/download_agent', methods=['GET'])
def download_agent():
    """
    Generate and download agent installer ZIP file on-the-fly
    Includes: INSTALL.bat, agent.py, requirements.txt, and all necessary files
    """
    try:
        # Get the project root directory
        # This file is in backend/routes/, so go up 2 levels to get project root
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent
        project_root = backend_dir.parent
        
        # Try multiple paths for agent directory
        # Priority 1: In backend/device_agent (for Vercel deployment - files copied here)
        agent_dir = backend_dir / 'device_agent'
        
        # Priority 2: In project root (for local development)
        if not agent_dir.exists():
            agent_dir = project_root / 'device_agent'
        
        # Priority 3: Try relative to backend directory (fallback)
        if not agent_dir.exists():
            agent_dir = backend_dir.parent / 'device_agent'
        
        print(f"[DOWNLOAD] Checking agent directory: {agent_dir}")
        print(f"[DOWNLOAD] Agent directory exists: {agent_dir.exists()}")
        
        # Check if agent directory exists
        agent_dir_exists = agent_dir.exists()
        
        if not agent_dir_exists:
            # On serverless (Vercel), try embedded files
            if EMBEDDED_FILES_AVAILABLE and AGENT_FILES:
                print("[DOWNLOAD] Using embedded agent files (Vercel serverless)")
                # Create a virtual agent_dir for embedded files
                agent_dir_exists = True
            else:
                # No embedded files and no directory - return error with GitHub fallback
                return jsonify({
                    'error': 'Agent files not available on server',
                    'message': 'Agent installer will be available via GitHub releases',
                    'alternative': 'Please download from GitHub releases or contact administrator',
                    'note': 'The download endpoint requires agent files to be included in deployment',
                    'solution': 'Agent files have been copied to backend/device_agent - redeploy to include them'
                }), 404
        
        # Required files to include in ZIP
        required_files = [
            'INSTALL.bat',
            'UNINSTALL.bat',
            'CREATE_DISTRIBUTION.bat',
            'agent.py',
            'requirements.txt',
            'register_device.py',
            'hardware_detection.py',
            'wifi_monitor.py',
            'lock_screen.py',
            'prey_lock_screen.py',
            'README_AGENT_SETUP.md',
            'README_INSTALLER.md'
        ]
        
        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add required files
            for filename in required_files:
                file_content = None
                
                # Try to read from file system first (local development)
                if agent_dir.exists():
                    file_path = agent_dir / filename
                    if file_path.exists():
                        try:
                            with open(file_path, 'rb') as f:
                                file_content = f.read()
                        except Exception as e:
                            print(f"Warning: Could not read {filename} from filesystem: {e}")
                
                # If not found, try embedded files (Vercel serverless)
                if file_content is None and EMBEDDED_FILES_AVAILABLE:
                    if filename in AGENT_FILES:
                        file_content = AGENT_FILES[filename].encode('utf-8')
                        print(f"[DOWNLOAD] Using embedded {filename}")
                
                # Add to ZIP if we have content
                if file_content:
                    zip_file.writestr(f'device_agent/{filename}', file_content)
                else:
                    print(f"Warning: Could not include {filename} - file not found")
            
            # Add optional files if they exist
            optional_files = [
                'approved_folders.json',
                'check_agent_running.bat',
                'run_agent_silent.vbs',
                'install_agent_service.bat',
                'START_AGENT_BACKGROUND.bat',
                'EASY_SETUP.bat',
                'register_hardware.py'
            ]
            
            for filename in optional_files:
                file_content = None
                
                # Try file system first
                if agent_dir.exists():
                    file_path = agent_dir / filename
                    if file_path.exists():
                        try:
                            with open(file_path, 'rb') as f:
                                file_content = f.read()
                        except Exception as e:
                            print(f"Warning: Could not read optional {filename}: {e}")
                
                # Try embedded if available
                if file_content is None and EMBEDDED_FILES_AVAILABLE:
                    if filename in AGENT_FILES:
                        file_content = AGENT_FILES[filename].encode('utf-8')
                
                if file_content:
                    zip_file.writestr(f'device_agent/{filename}', file_content)
            
            # Add any remaining Python modules in agent directory (only if directory exists)
            if agent_dir.exists():
                for py_file in agent_dir.glob('*.py'):
                    # Skip if already added
                    if py_file.name not in [f for f in required_files if f.endswith('.py')] and \
                       py_file.name not in [f for f in optional_files if f.endswith('.py')]:
                        try:
                            with open(py_file, 'rb') as f:
                                zip_file.writestr(f'device_agent/{py_file.name}', f.read())
                        except Exception as e:
                            print(f"Warning: Could not add {py_file.name}: {e}")
        
        # Check if we have any files in the ZIP
        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, 'r') as test_zip:
            file_list = test_zip.namelist()
        
        if not file_list or len(file_list) == 0:
            # No files in ZIP - return helpful error
            return jsonify({
                'error': 'Agent files not available on server',
                'message': 'Agent installer files are not included in this deployment',
                'solution': 'Please download from one of these options:',
                'options': [
                    {
                        'method': 'GitHub Releases',
                        'description': 'Download from project repository releases',
                        'url': 'https://github.com/YOUR_USERNAME/YOUR_REPO/releases'
                    },
                    {
                        'method': 'Manual Setup',
                        'description': 'Run PRE_DEPLOY.bat then redeploy to include agent files',
                        'steps': [
                            '1. Run: PRE_DEPLOY.bat',
                            '2. Deploy: vercel --prod',
                            '3. Agent files will be included'
                        ]
                    }
                ],
                'note': 'The agent files need to be in backend/device_agent for Vercel deployment'
            }), 404
        
        # Reset buffer position
        zip_buffer.seek(0)
        
        # Return ZIP file
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='antitheft-agent-installer.zip'
        )
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[DOWNLOAD ERROR] {str(e)}")
        print(f"[DOWNLOAD ERROR] Traceback: {error_trace}")
        return jsonify({
            'error': f'Failed to create agent installer: {str(e)}',
            'message': 'Please try downloading from GitHub releases or contact administrator'
        }), 500
