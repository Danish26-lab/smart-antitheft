"""
Locust Load Test - Smart Anti-Theft Backend API
Run with: locust -f locustfile.py
Headless: locust -f locustfile.py --headless -u 5 -r 1 -t 30s --html report.html

Set LOCUST_HOST for different backend (default: http://localhost:5000)
"""

import os
import random
from locust import HttpUser, task, between


class AntiTheftAPIUser(HttpUser):
    """Simulates dashboard users hitting the backend API."""

    host = os.getenv("LOCUST_HOST", "http://localhost:5000")
    wait_time = between(1, 3)

    def on_start(self):
        """Login once per user to get JWT token, then fetch devices."""
        response = self.client.post(
            "/api/login",
            json={
                "email": os.getenv("TEST_EMAIL", "admin@antitheft.com"),
                "password": os.getenv("TEST_PASSWORD", "admin123"),
            },
            name="/api/login",
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token") or data.get("token")
            # Fetch devices for get_device_status / get_activity_logs
            if self.token:
                r2 = self.client.get(
                    "/api/get_devices",
                    headers={"Authorization": f"Bearer {self.token}"},
                    name="/api/get_devices",
                )
                data2 = r2.json() if r2.status_code == 200 else {}
                self.devices = data2.get("devices", [])
            else:
                self.devices = []
        else:
            self.token = None
            self.devices = []

    @task(3)
    def get_devices(self):
        """Fetch devices list - common dashboard action."""
        if not self.token:
            return
        self.client.get(
            "/api/get_devices",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/get_devices",
        )

    @task(5)
    def get_device_status(self):
        """Fetch single device status - most frequent dashboard call."""
        if not self.token:
            return
        device_id = self._get_device_id()
        if not device_id:
            return
        self.client.get(
            f"/api/get_device_status/{device_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/get_device_status",
        )

    @task(2)
    def get_activity_logs(self):
        """Fetch activity logs for a device."""
        if not self.token:
            return
        device_id = self._get_device_id()
        if not device_id:
            return
        self.client.get(
            f"/api/get_activity_logs/{device_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/get_activity_logs",
        )

    def _get_device_id(self):
        """Get a device ID from logged-in devices, or use placeholder."""
        if self.devices:
            return random.choice(self.devices).get("device_id")
        # Fallback for load test without real devices - may return 404 but still measures latency
        return "test-device-placeholder"


class DeviceAgentUser(HttpUser):
    """Simulates device agents reporting status (no auth required)."""

    host = os.getenv("LOCUST_HOST", "http://localhost:5000")
    wait_time = between(2, 5)

    @task
    def update_location(self):
        """Simulate agent sending location update."""
        self.client.post(
            "/api/update_location",
            json={
                "device_id": f"load-test-agent-{random.randint(1000, 9999)}",
                "user": "admin@antitheft.com",
                "status": "active",
                "location": {"lat": 3.1390 + random.uniform(-0.01, 0.01), "lng": 101.6869 + random.uniform(-0.01, 0.01)},
            },
            name="/api/update_location",
        )
