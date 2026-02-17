# BioGuard AI — Login System + Role-Based Architecture
## Cursor Prompt: Analyzer Dashboard + Raspberry Pi Data Sender

---

## 🏗️ SYSTEM ARCHITECTURE (Understand Before Building)

```
┌─────────────────────────────────────────────────────────────────┐
│                     BioGuard AI System                          │
├─────────────────────┬───────────────────────────────────────────┤
│   ROLE 1: ANALYZER  │        ROLE 2: DATA SENDER (Pi)          │
│                     │                                           │
│  The actual backend │  Simulates Raspberry Pi 5 IoT device     │
│  Health officers,   │  Logs in from Pi's browser or any device │
│  District admins,   │  Sees "Send Demo Data" buttons           │
│  Researchers        │  Sends simulated sensor readings         │
│                     │  → Backend receives → ML runs →          │
│  Sees full          │  → Analyzer dashboard UPDATES LIVE       │
│  dashboard with     │                                           │
│  predictions,       │  Pi pretends to be a real sensor node    │
│  alerts, maps,      │  by clicking demo buttons                │
│  ML results         │                                           │
└─────────────────────┴───────────────────────────────────────────┘

DATA FLOW:
[Pi/Sender logs in] → [Clicks "Send Demo Data"] 
→ [POST /api/sensor-data with JWT token]
→ [Backend validates Pi token + runs ML prediction]
→ [WebSocket broadcasts updated prediction to ALL connected Analyzers]
→ [Analyzer dashboards update in REAL TIME]
```

---

## 🎯 THE ONE CURSOR PROMPT — Paste This Entirely

```
Add a complete role-based login and authentication system to 
BioGuard AI. The existing project already has the full dashboard,
ML backend, and mock sensor service. Now add login with 2 roles:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROLE 1: ANALYZER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Who: Health officers, district admins, researchers
What they see: The full BioGuard AI command center dashboard
              (the entire existing dashboard we already built)
              All predictions, alerts, maps, Pi device panel,
              ML results, demo scenarios — everything
Key detail: Dashboard data updates in real-time when a Pi
            sender submits new sensor data

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROLE 2: DATA SENDER (Raspberry Pi)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Who: A Raspberry Pi 5 device (or anyone pretending to be one)
What they see: A completely SEPARATE, minimal UI — NOT the
              main dashboard. Just a Pi-themed data sending panel.
Key detail: Has "Send Demo Data" buttons that POST simulated
            sensor readings to the backend, which then updates
            the Analyzer's dashboard in real time

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

════════════════════════════════════════════════════════════
BACKEND CHANGES (FastAPI)
════════════════════════════════════════════════════════════

FILE: auth/auth.py
Build complete JWT authentication:

User model (SQLAlchemy):
  id: int (primary key)
  username: str (unique)
  email: str (unique)
  hashed_password: str
  role: str  → "analyzer" OR "pi_sender"
  device_id: str | None  → for pi_sender: "RPI5-UNIT-001" etc
  village_id: str | None → which village this Pi monitors
  village_name: str | None
  is_active: bool
  created_at: datetime
  last_login: datetime | None

JWT Token:
  Include in payload: {user_id, username, role, device_id, village_id}
  Expiry: 24 hours for analyzer, 30 days for pi_sender (Pi stays logged in)
  Secret: from .env JWT_SECRET

Dependencies to create:
  get_current_user(token) → User
  require_analyzer(user) → User (raises 403 if not analyzer)
  require_pi_sender(user) → User (raises 403 if not pi_sender)

FILE: routers/auth.py
New endpoints:

POST /api/auth/login
  Body: {username: str, password: str}
  Returns: {
    access_token: str,
    token_type: "bearer",
    role: "analyzer" | "pi_sender",
    user: {id, username, email, role, device_id, village_id, village_name},
    redirect_to: "/dashboard" | "/pi-sender"
  }

POST /api/auth/logout
  Invalidate token (add to blacklist in Redis/memory set)

GET /api/auth/me
  Returns current user profile from token

POST /api/auth/register (admin only — disable for public)
  Protected: only existing analyzer can create new users
  Body: {username, email, password, role, device_id, village_id}

FILE: database/seed_users.py
Seed these demo users on startup if they don't exist:

ANALYZER ACCOUNTS:
  username: "dr_sharma"     password: "BioGuard@2026"
  username: "district_mh"  password: "Maharashtra#1"
  username: "admin"         password: "Admin@BioGuard"

PI SENDER ACCOUNTS:
  username: "rpi5_shirpur"
  password: "Pi@Shirpur001"
  role: pi_sender
  device_id: "RPI5-UNIT-001"
  village_id: "MH_SHP"
  village_name: "Shirpur"

  username: "rpi5_dharangaon"
  password: "Pi@Dharangaon002"
  role: pi_sender
  device_id: "RPI5-UNIT-002"
  village_id: "MH_DHA"
  village_name: "Dharangaon"

  username: "rpi5_bahraich"
  password: "Pi@Bahraich003"
  role: pi_sender
  device_id: "RPI5-UNIT-003"
  village_id: "UP_BAH"
  village_name: "Bahraich"

FILE: routers/sensor_ingest.py
New endpoint that Pi sender uses to push data:

POST /api/sensor-data/submit
  Auth: require_pi_sender
  Body: SensorSubmission {
    device_id: str         (from token — validate matches)
    village_id: str        (from token — validate matches)
    ph_level: float
    turbidity_ntu: float
    tds_ppm: float
    water_temp_celsius: float
    air_temp_celsius: float
    humidity_percent: float
    flow_rate_lpm: float
    submitted_at: datetime
    is_demo_data: bool     (always True for now — simulated)
    demo_scenario: str | None  ("normal"|"high_turbidity"|"cholera_risk"|
                                "improving"|"critical_event")
  }

  On receive:
  1. Validate device_id + village_id match the Pi's JWT token
  2. Store raw reading in sensor_readings table
  3. Run ML prediction using this new sensor data for that village
  4. Update village's current prediction in database
  5. Check if new alert should be generated
  6. Broadcast via WebSocket to ALL connected Analyzer clients:
     {
       type: "sensor_update",
       device_id: str,
       village_id: str,
       village_name: str,
       sensor_reading: {...},
       updated_prediction: {...},
       new_alert: Alert | None,
       submitted_by: "pi_sender",
       is_demo_data: true,
       timestamp: datetime
     }
  7. Return: {received: true, prediction: {...}, alert_triggered: bool}

GET /api/sensor-data/history/{village_id}
  Auth: require_analyzer
  Returns last 50 submissions for this village (with is_demo_data flag)

GET /api/sensor-data/demo-scenarios
  Auth: require_pi_sender
  Returns available demo scenarios with descriptions:
  [
    {
      id: "normal",
      label: "Normal Conditions",
      description: "Safe water quality, no disease risk",
      icon: "✅",
      expected_alert: "baseline",
      values: {ph: 7.2, turbidity: 1.1, tds: 312, ...}
    },
    {
      id: "high_turbidity",
      label: "High Turbidity Warning",
      description: "Turbidity spike detected, potential contamination",
      icon: "⚠️",
      expected_alert: "medium",
      values: {ph: 6.9, turbidity: 5.8, tds: 445, ...}
    },
    {
      id: "cholera_risk",
      label: "Cholera Risk — CRITICAL",
      description: "Dangerous water quality + symptom cluster detected",
      icon: "🚨",
      expected_alert: "critical",
      values: {ph: 6.1, turbidity: 8.7, tds: 512, ...}
    },
    {
      id: "typhoid_risk",
      label: "Typhoid Risk — HIGH",
      description: "Contaminated water source, rising fever cases",
      icon: "🔴",
      expected_alert: "high",
      values: {ph: 6.4, turbidity: 4.2, tds: 487, ...}
    },
    {
      id: "improving",
      label: "Post-Intervention Recovery",
      description: "Chlorination deployed, water quality improving",
      icon: "📈",
      expected_alert: "low",
      values: {ph: 7.0, turbidity: 2.1, tds: 380, ...}
    },
    {
      id: "critical_event",
      label: "Emergency — Mass Outbreak",
      description: "Extreme contamination, immediate response required",
      icon: "💀",
      expected_alert: "critical",
      values: {ph: 5.8, turbidity: 12.4, tds: 620, ...}
    }
  ]

Add JWT middleware to protect existing routes:
  /api/predictions/* → require_analyzer
  /api/alerts/* → require_analyzer
  /api/analytics/* → require_analyzer
  /api/raspberry-pi/* → require_analyzer OR require_pi_sender
  /api/sensor-data/submit → require_pi_sender only
  /api/demo/scenario/* → require_analyzer only
  /ws/live → authenticate via token in query param ?token=xxx

════════════════════════════════════════════════════════════
FRONTEND CHANGES (Next.js)
════════════════════════════════════════════════════════════

FILE: src/app/login/page.tsx
Build a stunning login page:

DESIGN CONCEPT: Split-screen design.
Left half (60%): 
  Deep navy background (#0a0f1e) with animated particle 
  network connecting dots (simulate sensor network).
  Large BioGuard AI logo + tagline.
  "Protecting Rural India Through AI + IoT"
  Bottom: 3 animated stats counting up:
    15 Villages | 2,847 Readings | 47 Lives Protected

Right half (40%):
  Slightly lighter panel (#0f1729)
  Clean login form:

  [BioGuard AI Shield Logo]
  
  "Sign In"
  subtitle: "Select your role and enter credentials"

  ROLE SELECTOR (two clickable cards, not a dropdown):
  ┌─────────────────────┐  ┌─────────────────────┐
  │  📊 ANALYZER        │  │  📡 DATA SENDER      │
  │                     │  │                     │
  │  Health Officers    │  │  Raspberry Pi 5     │
  │  District Admins    │  │  IoT Sensor Node    │
  │  Researchers        │  │                     │
  │                     │  │  Send real-time     │
  │  Full Dashboard     │  │  sensor data to     │
  │  Access             │  │  the system         │
  └─────────────────────┘  └─────────────────────┘
  Selected card: glowing cyan border + checkmark

  Username field (icon: person)
  Password field (icon: lock, toggle visibility)
  
  [Sign In] button → full width, cyan background
  
  After role select, show demo credentials hint:
  If ANALYZER selected:
    "Demo: dr_sharma / BioGuard@2026"
  If DATA SENDER selected:
    "Demo: rpi5_shirpur / Pi@Shirpur001"
    "Demo: rpi5_dharangaon / Pi@Dharangaon002"

  Loading state: spinner + "Authenticating..."
  Error state: shake animation + red error message

On login success:
  Store token in localStorage: bioguard_token
  Store user in localStorage: bioguard_user
  If role === "analyzer" → redirect to /dashboard
  If role === "pi_sender" → redirect to /pi-sender

FILE: src/app/pi-sender/page.tsx
Build the RASPBERRY PI DATA SENDER interface:
This is a COMPLETELY SEPARATE page from the main dashboard.

DESIGN CONCEPT: 
Dark green terminal/IoT aesthetic. Feels like you are 
inside the Raspberry Pi itself.
Colors:
  Background: #0d1117 (GitHub dark)
  Terminal green: #00ff41 (matrix green)
  Accent: #39d353
  Cards: #161b22 with #30363d border
  Font: JetBrains Mono throughout (monospace, feels techy)

LAYOUT:
┌────────────────────────────────────────────────────────┐
│  HEADER                                                │
│  [Pi Logo] RPI5-UNIT-001 | Shirpur, Maharashtra       │
│  🟢 CONNECTED  |  Logged in as: rpi5_shirpur          │
│  [Logout button]                                       │
├────────────────────────────────────────────────────────┤
│  DEVICE STATUS CARD                                    │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Raspberry Pi 5 — 16GB RAM                        │ │
│  │ CPU: 34°C  ████░░░░ 35%    RAM: 2.1 / 16 GB     │ │
│  │ Uptime: 47h 23m            Storage: 18% used     │ │
│  │ Network: 4G LTE  Signal: ████░ -71 dBm           │ │
│  │ Solar Panel: ⚡ Charging   Battery: 94%          │ │
│  │                                                   │ │
│  │ MODE: DEMO DATA (Simulated)                       │ │
│  │ Last sent: 2 minutes ago                          │ │
│  │ Total sent this session: 12 readings              │ │
│  └──────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────┤
│  CURRENT READINGS (animate values like a live terminal)│
│  ┌──────────┬──────────┬──────────┬───────────────┐  │
│  │ pH       │ Turb.    │ TDS      │ Water Temp    │  │
│  │ 7.21     │ 1.14 NTU │ 312 ppm  │ 26.5°C        │  │
│  │ ✅ Safe  │ ✅ Safe  │ ✅ Safe  │ ✅ Normal     │  │
│  └──────────┴──────────┴──────────┴───────────────┘  │
│  (values flicker slightly every 3 seconds — alive feel)│
├────────────────────────────────────────────────────────┤
│  SEND DEMO DATA                                        │
│                                                        │
│  ┌───────────────────────────────────────────────────┐│
│  │ ✅ Normal Conditions          [SEND] ──────────── ││
│  │    Safe water, no risk                            ││
│  ├───────────────────────────────────────────────────┤│
│  │ ⚠️  High Turbidity Warning    [SEND] ──────────── ││
│  │    Turbidity spike, caution                       ││
│  ├───────────────────────────────────────────────────┤│
│  │ 🔴 Typhoid Risk — HIGH        [SEND] ──────────── ││
│  │    Contaminated source                            ││
│  ├───────────────────────────────────────────────────┤│
│  │ 🚨 Cholera Risk — CRITICAL    [SEND] ──────────── ││
│  │    DANGEROUS — Emergency                          ││
│  ├───────────────────────────────────────────────────┤│
│  │ 📈 Post-Intervention Recovery [SEND] ──────────── ││
│  │    Improving after chlorination                   ││
│  ├───────────────────────────────────────────────────┤│
│  │ 💀 Emergency Mass Outbreak   [SEND] ──────────── ││
│  │    Extreme — Immediate response                   ││
│  └───────────────────────────────────────────────────┘│
│                                                        │
│  [📡 SEND ALL NORMAL — AUTO SEQUENCE] (send 1/min)    │
├────────────────────────────────────────────────────────┤
│  TRANSMISSION LOG (terminal-style, newest on top)     │
│  ┌────────────────────────────────────────────────── │
│  │ > 14:23:01 SENT: cholera_risk → 🚨 CRITICAL alert │
│  │ > 14:22:01 SENT: normal → ✅ baseline             │
│  │ > 14:21:00 SENT: high_turbidity → ⚠️ medium alert │
│  │ > [cursor blinking]                                │
│  └────────────────────────────────────────────────── │
├────────────────────────────────────────────────────────┤
│  ANALYZER RESPONSE (what the backend said)            │
│  After last send:                                     │
│  Village: Shirpur | Risk Score: 91 | Alert: CRITICAL  │
│  Disease: Cholera | Confidence: 91%                   │
│  "Alert dispatched to District Health Officer"         │
└────────────────────────────────────────────────────────┘

BEHAVIOR:

On [SEND] button click for any scenario:
  1. Button shows loading spinner: "Sending..."
  2. POST /api/sensor-data/submit with JWT token
     Body includes the scenario's sensor values + is_demo_data: true
  3. On success:
     - Update "Current Readings" panel with the sent values
     - Add entry to Transmission Log with timestamp
     - Show "Analyzer Response" panel with returned prediction
     - Flash the sent button green briefly then reset
     - Increment "Total sent this session" counter
  4. On error:
     - Flash button red + show error in log
     - "TRANSMISSION FAILED — Retry?"

Current readings panel:
  Values slowly oscillate every 3 seconds (±0.02 noise)
  Using setInterval — makes it feel like live sensors
  When SEND is clicked: values jump to that scenario's values
  Then slowly drift back to noise pattern

Auto-sequence button:
  When clicked: sends "normal" data every 60 seconds
  Button label changes to "⏸ STOP AUTO-SEND"
  Countdown timer shows: "Next send in: 43s"

The entire page should feel like you ARE the Raspberry Pi.
Every interaction should feel like commanding physical hardware.

FILE: src/middleware.ts
Next.js middleware for route protection:
  /dashboard → redirect to /login if no token
  /pi-sender → redirect to /login if no token
  /login → redirect to /dashboard if already logged in 
           (check role for correct redirect)
  
  After getting token, decode role:
  If accessing /dashboard with pi_sender role → redirect /pi-sender
  If accessing /pi-sender with analyzer role → redirect /dashboard

FILE: src/hooks/useAuth.ts
Custom hook:
  getCurrentUser() → User from localStorage
  getToken() → string from localStorage
  isAnalyzer() → bool
  isPiSender() → bool
  logout() → clear localStorage + redirect /login

FILE: src/components/ProtectedRoute.tsx
Wrapper that:
  Checks localStorage for valid token
  Shows loading spinner while checking
  Redirects if role doesn't match required role
  Shows "Access Denied" if wrong role with helpful message:
    "This page is for Raspberry Pi sensor nodes only.
     Redirecting you to the Analyzer dashboard..."

FILE: src/app/dashboard/layout.tsx
Wrap existing dashboard in ProtectedRoute (analyzer only)
Add user info to header:
  "👤 dr_sharma  |  📊 Analyzer  |  [Logout]"

UPDATE: src/services/api.ts
All API calls must now include Authorization header:
  headers: { "Authorization": `Bearer ${getToken()}` }

UPDATE: src/services/websocket.ts
Pass token in WebSocket connection:
  ws://localhost:8000/ws/live?token=${getToken()}

════════════════════════════════════════════════════════════
REAL-TIME CONNECTION — The Magic Moment
════════════════════════════════════════════════════════════

When Pi Sender clicks [SEND] → Analyzer dashboard updates live.

This is the WOW moment for judges:
  - Open ANALYZER dashboard on one screen (logged in as dr_sharma)
  - Open PI SENDER on another screen (logged in as rpi5_dharangaon)
  - Click "🚨 Cholera Risk — CRITICAL" on Pi Sender screen
  - Watch ANALYZER dashboard: new CRITICAL alert appears,
    Dharangaon village turns red on map, risk gauge spikes,
    notification toast slides in — all in under 2 seconds

The data flow that makes this happen:
  Pi Sender → POST /api/sensor-data/submit
  → Backend runs ML prediction
  → WebSocket broadcasts to all Analyzer clients
  → Analyzer's useQuery auto-invalidates
  → Map + alerts + predictions all update simultaneously

════════════════════════════════════════════════════════════
DEMO ACCOUNTS CHEAT SHEET (show to judges)
════════════════════════════════════════════════════════════

ANALYZER LOGIN:
  Username: dr_sharma
  Password: BioGuard@2026
  → Sees: Full command center dashboard

PI SENDER — SHIRPUR:
  Username: rpi5_shirpur
  Password: Pi@Shirpur001
  → Device: RPI5-UNIT-001, Village: Shirpur, Maharashtra

PI SENDER — DHARANGAON:
  Username: rpi5_dharangaon
  Password: Pi@Dharangaon002
  → Device: RPI5-UNIT-002, Village: Dharangaon, Maharashtra

PI SENDER — BAHRAICH:
  Username: rpi5_bahraich
  Password: Pi@Bahraich003
  → Device: RPI5-UNIT-003, Village: Bahraich, UP

════════════════════════════════════════════════════════════
DEMO SCRIPT — 5 Minutes with Login System
════════════════════════════════════════════════════════════

SETUP (before demo starts):
  Screen 1 (projector): Analyzer dashboard — dr_sharma logged in
  Screen 2 (laptop): Pi Sender — rpi5_dharangaon logged in
  Or: Use two browser windows side by side

[0:00 – 0:30] SHOW LOGIN PAGE
  "BioGuard AI has two types of users — Analyzers who monitor
  the dashboard, and Data Senders which are our Raspberry Pi
  IoT devices deployed in villages."
  
  Show login page. Point to role cards.
  "Each Pi device has its own secure login. When it authenticates,
  it can only send data for its assigned village."

[0:30 – 1:00] SHOW PI SENDER SCREEN
  "This is what our Raspberry Pi 5 sees when it's deployed in
  Dharangaon village. It shows device health — CPU temp, RAM
  usage out of 16GB, battery level, solar charging status."
  
  Point to live oscillating readings:
  "See these values changing? That's simulating live sensor input —
  pH, turbidity, TDS, water temperature — all updating in real time."

[1:00 – 2:00] THE WOW MOMENT
  Show BOTH screens simultaneously.
  
  "Watch the Analyzer dashboard on the big screen.
  I'm now going to send a CRITICAL cholera risk reading
  from our Raspberry Pi in Dharangaon."
  
  Click "🚨 Cholera Risk — CRITICAL" on Pi Sender
  
  Watch Analyzer screen: Dharangaon turns RED on map,
  CRITICAL alert slides in, risk score jumps to 91,
  toast notification appears.
  
  "In under 2 seconds — sensor data from the field reached
  our AI system, ran through our ML ensemble, generated a
  CRITICAL cholera prediction, and alerted every health
  officer logged into the system. That's the power of
  real-time IoT + AI."

[2:00 – 2:30] SHOW TRANSMISSION LOG
  Point to Pi Sender's log:
  "The Pi keeps a log of everything it transmitted.
  Notice: is_demo_data: true. This is honest — we're
  simulating. But plug in real sensors, change one .env
  variable, and this is live data from the field."

[2:30 – 3:00] INTERVENTION + RECOVERY
  Click "📈 Post-Intervention Recovery" on Pi Sender
  Watch Analyzer: risk score drops, alert level goes down
  "After chlorination was deployed, the Pi is sending
  improved water quality readings. The AI system
  recognizes the improvement and downgrades the alert."

════════════════════════════════════════════════════════════
PACKAGES TO ADD
════════════════════════════════════════════════════════════

Backend additions:
  python-jose[cryptography]==3.3.0   # JWT tokens
  passlib[bcrypt]==1.7.4             # Password hashing
  python-multipart==0.0.6            # Form data

Frontend additions (already have most):
  jwt-decode  # Decode JWT in browser to get role
  (everything else already installed)

════════════════════════════════════════════════════════════
BUILD ORDER FOR CURSOR (do in this exact sequence)
════════════════════════════════════════════════════════════

Step 1: Backend auth (30 mins)
  → auth/auth.py (JWT functions + dependencies)
  → database/models.py (add User model)
  → database/seed_users.py (5 demo users)
  → routers/auth.py (login/logout/me endpoints)
  → Update main.py (include auth router, seed on startup)

Step 2: Sensor ingest endpoint (20 mins)
  → routers/sensor_ingest.py (POST /api/sensor-data/submit)
  → Connect to existing ML predictor
  → Connect to existing WebSocket broadcast

Step 3: Protect existing routes (10 mins)
  → Add require_analyzer to all existing routers
  → Add token auth to WebSocket endpoint

Step 4: Login page (25 mins)
  → src/app/login/page.tsx
  → Split screen design with role cards

Step 5: Pi Sender page (35 mins)
  → src/app/pi-sender/page.tsx
  → Terminal aesthetic + send buttons + transmission log

Step 6: Auth hooks + middleware (20 mins)
  → src/hooks/useAuth.ts
  → src/middleware.ts
  → Update api.ts + websocket.ts with auth headers

Step 7: Protect dashboard routes (10 mins)
  → Wrap /dashboard in ProtectedRoute
  → Add user info to header
  → Logout button

Total: ~2.5 hours added to existing project
```

---

## 📁 NEW FILES SUMMARY

```
backend/
├── auth/
│   └── auth.py              ← JWT logic + role dependencies
├── routers/
│   ├── auth.py              ← Login/logout/me endpoints  
│   └── sensor_ingest.py     ← Pi data submission endpoint
└── database/
    └── seed_users.py        ← 5 demo user accounts

frontend/src/
├── app/
│   ├── login/
│   │   └── page.tsx         ← Split-screen login with role cards
│   ├── pi-sender/
│   │   └── page.tsx         ← Raspberry Pi data sender UI
│   └── dashboard/
│       └── layout.tsx       ← Wrap in auth protection
├── hooks/
│   └── useAuth.ts           ← Auth state management
├── middleware.ts             ← Route protection
└── components/
    └── ProtectedRoute.tsx   ← Role-based access wrapper
```

---

## 🏆 WHY THIS WINS JUDGES

The two-screen demo is the most powerful moment in the entire presentation:

**One screen shows the Pi clicking SEND → the other screen's dashboard updates LIVE**

That single moment proves: IoT → AI → Real-time decision making → All working together.

No other team will have a live bidirectional demo like this.
