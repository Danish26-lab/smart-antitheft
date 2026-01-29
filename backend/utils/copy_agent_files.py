"""
Copy agent files to backend directory for Vercel deployment
This ensures agent files are available in serverless environment
"""
import shutil
import os
from pathlib import Path

def copy_agent_files():
    """Copy essential agent files to backend directory for deployment"""
    # Get paths
    backend_dir = Path(__file__).parent.parent
    project_root = backend_dir.parent
    agent_dir = project_root / 'device_agent'
    backend_agent_dir = backend_dir / 'device_agent'
    
    if not agent_dir.exists():
        print(f"Warning: Agent directory not found: {agent_dir}")
        return False
    
    # Create backend/device_agent directory
    backend_agent_dir.mkdir(exist_ok=True)
    
    # Essential files to copy
    essential_files = [
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
    
    copied = 0
    for filename in essential_files:
        src = agent_dir / filename
        dst = backend_agent_dir / filename
        
        if src.exists():
            try:
                shutil.copy2(src, dst)
                copied += 1
                print(f"Copied: {filename}")
            except Exception as e:
                print(f"Error copying {filename}: {e}")
    
    print(f"Copied {copied} files to {backend_agent_dir}")
    return copied > 0

if __name__ == '__main__':
    copy_agent_files()
