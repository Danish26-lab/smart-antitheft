# Performance Testing with Locust

Load testing for the Smart Anti-Theft backend API using [Locust](https://locust.io/).

## Prerequisites

```bash
pip install locust
```

Or from project root:

```bash
pip install -r requirements-perf.txt
```

## Setup

1. **Start the backend** (local or use deployed URL):

   ```bash
   # Local
   cd backend && python app.py

   # Or use start_all.bat
   ```

2. **Ensure you have a test user** (default: `admin@antitheft.com` / `admin123`)

## Running Tests

### Interactive Mode (Web UI)

```bash
locust -f locustfile.py
```

Then open http://localhost:8089 and configure:
- Number of users
- Spawn rate
- Host: `http://localhost:5000` (or your backend URL)

### Headless Mode (Generate Report)

**Dashboard API only** (recommended - login, get_devices, get_device_status):

```bash
python -m locust -f locustfile.py AntiTheftAPIUser --headless -u 5 -r 1 -t 30s --html report.html
```

**All user types** (includes DeviceAgentUser - may show update_location failures with fake devices):

```bash
python -m locust -f locustfile.py --headless -u 5 -r 1 -t 30s --html report.html
```

- `-u 5`: 5 simulated users
- `-r 1`: 1 user per second spawn rate
- `-t 30s`: Run for 30 seconds
- `--html report.html`: Output HTML report

### Test Against Deployed Backend

```bash
set LOCUST_HOST=https://antitheft-backend-2.vercel.app
locust -f locustfile.py --headless -u 5 -r 1 -t 30s --html report.html
```

### Custom Credentials

```bash
set TEST_EMAIL=your@email.com
set TEST_PASSWORD=yourpassword
locust -f locustfile.py --headless -u 5 -r 1 -t 30s --html report.html
```

## What Gets Tested

| Endpoint | Description |
|----------|-------------|
| POST /api/login | User authentication |
| GET /api/get_devices | Fetch all devices |
| GET /api/get_device_status/{id} | Fetch single device status |
| GET /api/get_activity_logs/{id} | Fetch activity logs |

## Report Output

After running with `--html report.html`, open `report.html` in a browser to see:

- **Statistics**: Request counts, failures, response times (min/avg/max)
- **Charts**: Response time distribution, requests per second
- **Failures**: Any failed requests with error details

Share this report with your supervisor as proof of performance testing.
