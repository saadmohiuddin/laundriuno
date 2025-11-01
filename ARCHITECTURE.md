# System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         LAUNDRIUNO SYSTEM                        │
└─────────────────────────────────────────────────────────────────┘

┌────────────────────┐         ┌─────────────────────────────────┐
│   HARDWARE LAYER   │         │       SOFTWARE LAYER            │
├────────────────────┤         ├─────────────────────────────────┤
│                    │         │                                 │
│  ┌──────────────┐ │         │  ┌───────────────────────────┐  │
│  │   Machine 1   │ │         │  │      Flask Web App        │  │
│  │  (Vibration)  │ │         │  │      (main.py)           │  │
│  └───────┬───────┘ │         │  │                           │  │
│          │         │         │  │  ┌─────────────────────┐  │  │
│  ┌───────▼───────┐ │  USB    │  │  │   REST API         │  │  │
│  │   Machine 2   │ │  Serial │  │  │   8 Endpoints      │  │  │
│  │  (Vibration)  ├─┼─────────┼──┼──►                     │  │  │
│  └───────┬───────┘ │         │  │  └─────────────────────┘  │  │
│          │         │         │  │                           │  │
│  ┌───────▼───────┐ │         │  │  ┌─────────────────────┐  │  │
│  │   Machine 3   │ │         │  │  │ Arduino Interface   │  │  │
│  │  (Vibration)  │ │         │  │  │ (Serial Comm)       │  │  │
│  └───────┬───────┘ │         │  │  └─────────────────────┘  │  │
│          │         │         │  │                           │  │
│  ┌───────▼───────┐ │         │  │  ┌─────────────────────┐  │  │
│  │   Machine 4   │ │         │  │  │   Data Store        │  │  │
│  │  (Vibration)  │ │         │  │  │   (In-Memory)       │  │  │
│  └───────┬───────┘ │         │  │  └─────────────────────┘  │  │
│          │         │         │  │                           │  │
│  ┌───────▼───────┐ │         │  └───────────────────────────┘  │
│  │               │ │         │                                 │
│  │  Arduino Uno  │ │         └─────────────────────────────────┘
│  │  (Firmware)   │ │                        │
│  │               │ │                        │ HTTP
│  └───────────────┘ │                        │
│                    │                        ▼
└────────────────────┘         ┌─────────────────────────────────┐
                               │      USER INTERFACE             │
                               ├─────────────────────────────────┤
                               │                                 │
                               │  ┌──────────────────────────┐  │
                               │  │   Web Dashboard          │  │
                               │  │   (index.html)           │  │
                               │  │                          │  │
                               │  │  • Real-time Status      │  │
                               │  │  • Usage Statistics      │  │
                               │  │  • Machine Cards         │  │
                               │  │  • Auto-refresh (5s)     │  │
                               │  │  • Responsive Design     │  │
                               │  └──────────────────────────┘  │
                               │                                 │
                               └─────────────────────────────────┘
```

## Data Flow

```
1. SENSOR → ARDUINO
   Vibration sensors detect machine activity
   ↓
   Arduino counts vibrations over 5-second intervals
   ↓
   Arduino determines machine state (IN_USE or FREE)

2. ARDUINO → FLASK
   Arduino sends via serial: "MACHINE:0:IN_USE"
   ↓
   Arduino Interface reads and parses message
   ↓
   Data Store updates machine status

3. FLASK → USER
   User opens web dashboard
   ↓
   JavaScript fetches /api/status every 5 seconds
   ↓
   Dashboard displays real-time machine status
```

## Component Communication

```
┌──────────────┐   Serial Protocol    ┌──────────────────┐
│   Arduino    │ ──────────────────→  │  Flask App       │
│              │   MACHINE:ID:STATUS  │                  │
│   Firmware   │ ←──────────────────  │  Serial Reader   │
│              │   STATUS/PING        │  Thread          │
└──────────────┘                      └──────────────────┘
                                              │
                                              ▼
                                      ┌──────────────────┐
                                      │   Data Store     │
                                      │   (Thread-Safe)  │
                                      └──────────────────┘
                                              │
                                              ▼
                                      ┌──────────────────┐
                                      │   REST API       │
                                      │   JSON Response  │
                                      └──────────────────┘
                                              │
                                              ▼
                                      ┌──────────────────┐
                                      │  Web Dashboard   │
                                      │  (JavaScript)    │
                                      └──────────────────┘
```

## API Endpoints

```
GET  /                        → Web Dashboard
GET  /api/status             → All machines status
GET  /api/machine/<id>       → Single machine status  
GET  /api/history/<id>       → Machine usage history
GET  /api/stats              → Overall statistics
POST /api/arduino/connect    → Connect to Arduino
POST /api/arduino/disconnect → Disconnect from Arduino
GET  /api/arduino/status     → Connection status
```

## Serial Protocol

```
Arduino → Flask:
- "READY"                  (on startup)
- "MACHINE:0:IN_USE"       (machine started)
- "MACHINE:0:FREE"         (machine finished)
- "PONG"                   (response to PING)

Flask → Arduino:
- "STATUS\n"               (request all machine status)
- "PING\n"                 (test connection)
```

## Technology Stack

```
Hardware:
- Arduino Uno/Nano
- SW-420 Vibration Sensors
- USB Serial Connection

Backend:
- Python 3.8+
- Flask 3.0.0
- pySerial 3.5
- Threading

Frontend:
- HTML5
- CSS3 (Responsive)
- Vanilla JavaScript
- Fetch API

Development:
- pytest (testing)
- CodeQL (security)
- Git (version control)
```

## Statistics Tracked

```
Per Machine:
- Current status (in_use: bool)
- Last updated timestamp
- Total uses count
- Total time used (seconds)
- Usage history (up to 100 entries)

Overall:
- Machines in use
- Machines free
- Total uses (all machines)
- Total time (all machines)
- Average time per use
```

## Security Features

```
✓ No stack traces in API responses
✓ Debug mode disabled by default
✓ Secure error logging (server-side only)
✓ Patched dependencies (Werkzeug 3.0.3)
✓ Environment-based configuration
✓ CodeQL verified (0 alerts)
```
