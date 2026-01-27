#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to diagnose why remote alarm and lock don't work
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

API_BASE_URL = 'http://localhost:5000/api'

def test_remote_actions():
    print("=" * 60)
    print("Testing Remote Actions (Alarm & Lock)")
    print("=" * 60)
    print()
    
    # Step 1: Login
    print("1. Logging in...")
    login_response = requests.post(
        f"{API_BASE_URL}/login",
        json={'email': 'admin@antitheft.com', 'password': 'admin123'},
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"[ERROR] Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.text}")
        return
    
    token = login_response.json().get('access_token')
    if not token:
        print("[ERROR] No access token received")
        return
    
    print("[OK] Login successful")
    print()
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Step 2: Get devices
    print("2. Fetching devices...")
    devices_response = requests.get(f"{API_BASE_URL}/get_devices", headers=headers, timeout=10)
    
    if devices_response.status_code != 200:
        print(f"[ERROR] Failed to get devices: {devices_response.status_code}")
        return
    
    devices = devices_response.json().get('devices', [])
    if not devices:
        print("[ERROR] No devices found")
        return
    
    print(f"[OK] Found {len(devices)} device(s)")
    print()
    
    # Step 3: Check each device
    for device in devices:
        device_id = device.get('device_id')
        device_type = device.get('device_type')
        status = device.get('status')
        name = device.get('name', 'Unknown')
        
        print(f"Device: {name}")
        print(f"  Device ID: {device_id}")
        print(f"  Device Type: {device_type}")
        print(f"  Status: {status}")
        
        # Check device status endpoint (what agent uses)
        print(f"\n3. Checking device status endpoint (agent view)...")
        status_response = requests.get(
            f"{API_BASE_URL}/get_device_status/{device_id}",
            timeout=10
        )
        
        if status_response.status_code == 200:
            agent_view = status_response.json()
            print(f"  [OK] Agent can see device")
            print(f"  Status (agent view): {agent_view.get('status')}")
        else:
            print(f"  [ERROR] Agent cannot see device: {status_response.status_code}")
        
        # Test alarm
        if device_type == 'os_device':
            print(f"\n  [WARNING] Device is 'os_device' - remote actions are blocked")
            print(f"     This device needs to be registered by the agent to enable remote control")
        else:
            print(f"\n4. Testing ALARM trigger...")
            alarm_response = requests.post(
                f"{API_BASE_URL}/trigger_action",
                json={'device_id': device_id, 'action': 'alarm'},
                headers=headers,
                timeout=10
            )
            
            if alarm_response.status_code == 200:
                print(f"  [OK] Alarm triggered successfully")
                result = alarm_response.json()
                print(f"  New status: {result.get('device', {}).get('status')}")
            else:
                print(f"  [ERROR] Alarm trigger failed: {alarm_response.status_code}")
                print(f"  Error: {alarm_response.text}")
            
            # Check status again
            print(f"\n5. Checking status after alarm...")
            status_response2 = requests.get(
                f"{API_BASE_URL}/get_device_status/{device_id}",
                timeout=10
            )
            if status_response2.status_code == 200:
                new_status = status_response2.json().get('status')
                print(f"  Status now: {new_status}")
                if new_status == 'alarm':
                    print(f"  [OK] Status updated to 'alarm' - agent should detect this!")
                else:
                    print(f"  [WARNING] Status is still '{new_status}' - might not have updated")
            
            # Test lock
            print(f"\n6. Testing LOCK trigger...")
            lock_response = requests.post(
                f"{API_BASE_URL}/trigger_action",
                json={
                    'device_id': device_id,
                    'action': 'lock',
                    'password': 'test123'
                },
                headers=headers,
                timeout=10
            )
            
            if lock_response.status_code == 200:
                print(f"  [OK] Lock triggered successfully")
                result = lock_response.json()
                print(f"  New status: {result.get('device', {}).get('status')}")
            else:
                print(f"  [ERROR] Lock trigger failed: {lock_response.status_code}")
                print(f"  Error: {lock_response.text}")
        
        print("\n" + "=" * 60)
        print()

if __name__ == '__main__':
    try:
        test_remote_actions()
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
