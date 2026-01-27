#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test script to verify agent-first architecture works with hosted backend
Run this to diagnose issues
"""

import requests
import json
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

BACKEND_URL = "https://antitheft-backend.vercel.app"

def test_backend_health():
    """Test if backend is accessible"""
    print("\n[TEST 1] Testing Backend Health...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Backend is accessible")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database')}")
            print(f"   Environment: {data.get('environment')}")
            
            if data.get('database') != 'connected':
                print("\n[WARN] WARNING: Database is not connected!")
                print("   You need to set up PostgreSQL and add DATABASE_URL environment variable in Vercel")
                return False
            return True
        else:
            print(f"[ERROR] Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Cannot connect to backend: {e}")
        print(f"   URL: {BACKEND_URL}")
        return False

def test_agent_registration():
    """Test agent registration endpoint"""
    print("\n[TEST 2] Testing Agent Registration Endpoint...")
    try:
        test_payload = {
            "fingerprint_hash": f"test-{hash('test-device') % 1000000}",
            "os_info": {
                "os_name": "Windows 11",
                "os_version": "10.0.26200",
                "hostname": "TEST-PC",
                "architecture": "AMD64"
            },
            "hardware_info": {
                "system_info": {
                    "vendor": "Test Vendor",
                    "model": "Test Model",
                    "serial_number": "TEST123"
                },
                "cpu_info": {
                    "model": "Test CPU",
                    "cores": 4
                }
            },
            "agent_version": "1.0.0"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/agent/register",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code in (200, 201):
            data = response.json()
            print(f"[OK] Agent registration works")
            print(f"   Device ID: {data.get('device_id')}")
            print(f"   User Linked: {data.get('user_linked', False)}")
            return True, data.get('device_id')
        else:
            print(f"[ERROR] Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Registration request failed: {e}")
        return False, None

def test_root_endpoint():
    """Test root endpoint"""
    print("\n[TEST 3] Testing Root Endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        if response.status_code == 200:
            print(f"[OK] Root endpoint accessible")
            return True
        else:
            print(f"[ERROR] Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Root endpoint error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Agent-First Architecture Diagnostic Test")
    print("=" * 60)
    
    # Test 1: Backend health
    health_ok = test_backend_health()
    
    # Test 2: Root endpoint
    root_ok = test_root_endpoint()
    
    # Test 3: Agent registration (only if backend is healthy)
    if health_ok:
        reg_ok, device_id = test_agent_registration()
    else:
        print("\n⏭️  Skipping agent registration test (backend not healthy)")
        reg_ok = False
        device_id = None
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if health_ok and reg_ok:
        print("[OK] All tests passed! Agent-first architecture should work.")
        print("\nNext steps:")
        print("1. Run agent: cd device_agent && python agent.py")
        print("2. Open frontend: https://frontend-wine-iota-46.vercel.app")
        print("3. Sign up or log in - device will be linked automatically")
    else:
        print("[ERROR] Some tests failed. Fix the issues above.")
        
        if not health_ok:
            print("\n[FIX] Set up PostgreSQL database:")
            print("   1. Create free database at https://supabase.com")
            print("   2. Copy connection string")
            print("   3. Go to Vercel Dashboard → Settings → Environment Variables")
            print("   4. Add: DATABASE_URL = your_postgresql_connection_string")
            print("   5. Redeploy backend")
        
        if health_ok and not reg_ok:
            print("\n[FIX] Check backend logs in Vercel Dashboard")
