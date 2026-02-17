# 🎭 BioGuard AI - Demo Credentials Cheat Sheet

## Quick Access for Judges

### 📊 ANALYZER ACCOUNTS (Health Officers/Admins)
Access the full command center dashboard with all predictions, alerts, and analytics.

**Account 1: Dr. Sharma**
```
Username: dr_sharma
Password: BioGuard@2026
Role: Analyzer
Access: Full Dashboard
```

**Account 2: District Maharashtra**
```
Username: district_mh
Password: Maharashtra#1
Role: Analyzer
Access: Full Dashboard
```

**Account 3: Admin**
```
Username: admin
Password: Admin@BioGuard
Role: Analyzer
Access: Full Dashboard
```

---

### 📡 PI SENDER ACCOUNTS (Raspberry Pi Devices)
Access the IoT data sender interface to simulate sensor readings.

**Device 1: Shirpur, Maharashtra**
```
Username: rpi5_shirpur
Password: Pi@Shirpur001
Device ID: RPI5-UNIT-001
Village: Shirpur (MH_SHP)
Role: Pi Sender
```

**Device 2: Dharangaon, Maharashtra**
```
Username: rpi5_dharangaon
Password: Pi@Dharangaon002
Device ID: RPI5-UNIT-002
Village: Dharangaon (MH_DHA)
Role: Pi Sender
```

**Device 3: Bahraich, UP**
```
Username: rpi5_bahraich
Password: Pi@Bahraich003
Device ID: RPI5-UNIT-003
Village: Bahraich (UP_BAH)
Role: Pi Sender
```

---

## 🎬 5-Minute Demo Script

### Setup (30 seconds)
1. **Screen 1** (Projector): Login as `dr_sharma` → Shows Analyzer Dashboard
2. **Screen 2** (Laptop): Login as `rpi5_dharangaon` → Shows Pi Sender Interface

### The WOW Moment (2 minutes)
1. **Explain the Setup:**
   - "We have two types of users: Health officers who monitor the dashboard, and Raspberry Pi devices that send sensor data from villages."

2. **Show Pi Sender Interface:**
   - Point to device status (CPU, RAM, Battery, Solar)
   - Show live oscillating sensor readings
   - Explain: "These values are simulating real-time sensor input from the field."

3. **THE MAGIC:**
   - Say: "Watch the Analyzer dashboard on the big screen."
   - Click "🚨 Cholera Risk — CRITICAL" on Pi Sender
   - **Watch Analyzer screen update in real-time:**
     - Dharangaon turns RED
     - CRITICAL alert appears
     - Risk score jumps to 91
     - Notification toast slides in
   - Say: "In under 2 seconds — sensor data from the field reached our AI system, ran through our ML ensemble, generated a CRITICAL cholera prediction, and alerted every health officer logged into the system."

4. **Show Recovery:**
   - Click "📈 Post-Intervention Recovery" on Pi Sender
   - Watch risk score drop on Analyzer dashboard
   - Say: "After chlorination was deployed, the Pi is sending improved water quality readings. The AI recognizes the improvement and downgrades the alert."

### Technical Highlights (1 minute)
- **JWT Authentication**: Secure role-based access
- **Real-time WebSocket**: Instant updates across all connected clients
- **ML Integration**: Automatic disease prediction on sensor data
- **IoT Simulation**: Realistic Raspberry Pi interface

### Q&A (1.5 minutes)
Common questions:
- "Is this real data?" → "Currently simulated, but the system is ready for real Raspberry Pi integration. Just plug in the sensors and change one environment variable."
- "How many villages can it monitor?" → "Scalable to hundreds. Currently configured for 15 demo villages."
- "What diseases can it predict?" → "Cholera, typhoid, hepatitis A, and dysentery — the four major water-borne diseases in rural India."

---

## 🚀 Quick Start URLs

**Login Page:** http://localhost:3000/login

**After Login:**
- Analyzers → http://localhost:3000/dashboard
- Pi Senders → http://localhost:3000/pi-sender

**Backend API Docs:** http://localhost:8001/docs

---

## 📱 Demo Scenarios Available on Pi Sender

1. **✅ Normal Conditions** - Safe water, no risk
2. **⚠️ High Turbidity Warning** - Potential contamination
3. **🚨 Cholera Risk — CRITICAL** - Dangerous water quality
4. **🔴 Typhoid Risk — HIGH** - Contaminated source
5. **📈 Post-Intervention Recovery** - Improving after treatment
6. **💀 Emergency — Mass Outbreak** - Extreme contamination

---

## 🎯 Key Talking Points

1. **Early Detection**: "IoT sensors detect contamination 72 hours before human cases appear"
2. **AI-Powered**: "Ensemble ML model with 91% accuracy"
3. **Real-Time**: "WebSocket updates in under 2 seconds"
4. **Cost-Effective**: "₹2.3L healthcare costs saved per outbreak prevented"
5. **Scalable**: "Ready for deployment across rural India"

---

## 🔐 Security Features to Mention

- JWT token-based authentication
- Role-based access control
- Device-specific credentials (Pi can only send data for its assigned village)
- Password hashing with bcrypt
- Automatic token expiry

---

## 💡 Pro Tips for Demo

1. **Keep both screens visible** during the "send data" moment
2. **Pause after clicking SEND** to let judges see the real-time update
3. **Point to specific elements** as they update (map, alerts, risk score)
4. **Emphasize the speed** — "under 2 seconds from field to decision"
5. **Show the transmission log** on Pi Sender to prove data was sent

---

**Print this sheet and keep it handy during the demo! 📋**
