# Smart Anti-Theft System — Poster Content for Examiner Presentation

Use this content to build your poster (e.g. in PowerPoint, Canva, Google Slides, or LaTeX). Sections are ordered for a typical **academic/presentation poster** layout.

---

## 1. TITLE (top, centre, large)

**Smart Anti-Theft System**  
*Real-Time Device Tracking & Remote Security Monitoring*

*(Optional subtitle: Inspired by Prey Project — Full-Stack Implementation)*

---

## 2. INTRODUCTION / PROBLEM (left or top-left)

**Why this system?**
- Device theft and loss are common; users need to **locate** and **control** devices remotely.
- No single solution that combines: **tracking**, **remote lock/alarm/wipe**, **geofencing**, and **account security** in one full-stack system.
- **Goal:** Build a production-ready anti-theft platform with verified accounts, real-time maps, and remote actions.

**Objectives**
- Provide **real-time location tracking** (GPS → WiFi → GeoIP).
- Enable **remote actions**: lock screen, alarm, selective wipe.
- Support **geofencing** (GPS and WiFi-based) with automatic alerts.
- Ensure **verified user accounts** (email verification) and secure device linking.
- Deploy on **Vercel + Supabase** for scalability and reliability.

---

## 3. SYSTEM ARCHITECTURE (centre or top-right)

**High-level architecture (simplified for poster):**

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React + Vite) — Vercel                        │
│  Dashboard • Maps • Device control • Login / Verify Email │
└───────────────────────────┬─────────────────────────────┘
                             │ REST API + JWT
┌────────────────────────────▼─────────────────────────────┐
│  Backend (Flask) — Vercel Serverless                    │
│  REST API • JWT • Email verification • Scheduler        │
└────────────────────────────┬────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Device Agents │   │ Supabase        │   │ Email (SMTP)     │
│ (Python)      │   │ PostgreSQL      │   │ Verification     │
│ Windows/Mac/  │   │ Devices, Users, │   │ Alerts           │
│ Linux, iOS    │   │ Logs, Geofence  │   │                  │
└───────────────┘   └─────────────────┘   └─────────────────┘
```

**Technology stack**
| Layer      | Technologies |
|-----------|--------------|
| Frontend  | React, Vite, Tailwind CSS, Leaflet/OpenStreetMap |
| Backend   | Flask, SQLAlchemy, JWT, APScheduler |
| Database  | Supabase (PostgreSQL) — production; SQLite for dev |
| Agent     | Python 3.8+ (Windows/Mac/Linux), iOS support |
| Deployment| Vercel (frontend + serverless API) |

---

## 4. KEY FEATURES (middle section — use icons or short bullets)

**Device management**
- Agent-first registration; device linking via local discovery (`device_id`).
- Support for multiple devices per user; hardware info display (no fingerprinting).

**Real-time tracking**
- Location: GPS → WiFi geolocation → GeoIP fallback.
- Updates every 15–60 s; interactive map (OpenStreetMap/Leaflet).
- Activity log with location history.

**Remote actions**
- **Lock:** Screen lock, custom password, lock message.
- **Alarm:** Remote sound + visual alert; remote stop.
- **Wipe:** Selective folder deletion (user-approved paths); progress tracking.
- **Screenshot:** Capture and upload to backend.

**Geofencing**
- GPS: circular zone (center + radius); exit/entry detection.
- WiFi: SSID-based zone; works indoors.
- Alerts via email; checks every 5 minutes.

**Security & verification**
- Email verification (6-digit code, 15 min expiry) before full access.
- JWT authentication; password hashing.
- Breach detection (e.g. HaveIBeenPwned); breach reports and alerts.
- Activity logging for audit trail.

---

## 5. CORE FLOWS (simplified — pick 1–2 for poster)

**A. Device registration & linking**
1. Agent starts → registers device (or uses existing `device_id`).
2. Agent runs local server; browser discovers `device_id`.
3. User logs in → backend links device to user → device appears in dashboard.

**B. Location tracking**
1. Agent gets location (GPS / WiFi / GeoIP) every 15–60 s.
2. Agent sends `POST /api/update_location` to backend.
3. Backend updates Supabase; frontend polls status and updates map.

**C. Remote action (e.g. lock)**
1. User clicks “Lock” in dashboard → `POST /api/trigger_action`.
2. Backend stores command; agent polls and executes locally.
3. Agent reports status → dashboard and activity log update.

*(Use simple flow diagrams or numbered steps in boxes.)*

---

## 6. SECURITY & DEPLOYMENT

**Security**
- **Auth:** JWT, email verification, optional Google OAuth.
- **Device ID:** Single identifier (`device_id`); no hardware fingerprinting.
- **Data:** HTTPS in production; Supabase encrypted at rest; user-approved wipe only.
- **Audit:** All actions and location updates in activity logs.

**Deployment**
- **Production:** Frontend + API on Vercel; database on Supabase (PostgreSQL).
- **Agent:** Runs on device; can be installed as Windows service; auto-start on login.
- **Result:** Production-ready, scalable, and suitable for real-world use.

---

## 7. RESULTS / IMPLEMENTATION (optional)

- **Implemented:** Full registration, verification, device linking, tracking, map view, lock/alarm/wipe, geofencing, breach detection, activity logs.
- **Database:** Users, devices, activity_logs, breach_reports, geofence settings, wipe_operations.
- **APIs:** 20+ REST endpoints (auth, devices, location, actions, geofence, breach, automation).
- **Platforms:** Web (responsive, including mobile); agent on Windows, Mac, Linux, iOS.

---

## 8. CONCLUSION (bottom)

**Summary**
- The system delivers a **complete anti-theft solution**: real-time tracking, remote lock/alarm/wipe, geofencing, and breach detection.
- **Verified accounts** and **device_id-based linking** simplify security and usability.
- **Supabase + Vercel** provide a scalable, production-ready deployment.

**Future work (optional)**
- Push notifications (e.g. web push) for instant geofence alerts.
- More automation rules and integrations.
- Enhanced mobile app or PWA for field use.

---

## 9. REFERENCES / CONTACT (bottom, small)

- System report: `SYSTEM_REPORT_LATEST.md`
- Stack: Flask, React, Supabase, Vercel, Leaflet/OSM
- *(Add your name, course, institution, date)*

---

## Poster layout suggestion

- **Top:** Title + subtitle.
- **Row 2:** Introduction/Problem (left) | Architecture diagram (right).
- **Row 3:** Key features (left) | Core flows (right).
- **Row 4:** Security & deployment (left) | Results/Implementation (right).
- **Bottom:** Conclusion | References/Contact.

Use a **single main colour** (e.g. blue or green) and keep text **short** (bullets, not long paragraphs). Use **one simple architecture diagram** and **one or two flow diagrams** so the examiner can grasp the system quickly.
