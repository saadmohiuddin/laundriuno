# MQTT Setup Guide for Laundriuno

This guide provides comprehensive instructions for setting up the Laundriuno system with MQTT (Message Queuing Telemetry Transport) communication protocol.

## Table of Contents

1. [What is MQTT?](#what-is-mqtt)
2. [Why Use MQTT?](#why-use-mqtt)
3. [System Architecture](#system-architecture)
4. [Prerequisites](#prerequisites)
5. [Installing MQTT Broker](#installing-mqtt-broker)
6. [Configuring the Flask Backend](#configuring-the-flask-backend)
7. [Programming the Arduino](#programming-the-arduino)
8. [Testing the Setup](#testing-the-setup)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Configuration](#advanced-configuration)

## What is MQTT?

MQTT (Message Queuing Telemetry Transport) is a lightweight publish-subscribe messaging protocol designed for IoT devices. It enables efficient communication between sensors (like our Arduino IMU) and applications (like our Flask backend).

### Key Concepts:

- **Broker**: Central message hub (like a post office)
- **Publisher**: Sends messages (Arduino sensors)
- **Subscriber**: Receives messages (Flask backend)
- **Topic**: Message category (e.g., `laundriuno/sensor/1/data`)
- **QoS**: Quality of Service level (delivery guarantee)

### Message Flow:

```
┌──────────┐                  ┌────────────┐                  ┌─────────────┐
│ Arduino  │───(publish)────>│ MQTT       │───(deliver)────>│ Flask App   │
│ + IMU    │                  │ Broker     │                  │ (Backend)   │
└──────────┘                  └────────────┘                  └─────────────┘
```

## Why Use MQTT?

### Advantages over Serial Connection:

1. **Wireless Communication**: No USB cables needed
2. **Multiple Subscribers**: Multiple apps can monitor same sensors
3. **Network Flexibility**: Sensors can be anywhere on the network
4. **Reliability**: Built-in reconnection and message queuing
5. **Scalability**: Easy to add more sensors
6. **Cloud Integration**: Can connect to cloud MQTT brokers

### Use Cases:

- Production deployments with multiple machines
- Remote monitoring setups
- Cloud-based data storage
- Multiple simultaneous displays/apps
- Distributed sensor networks

## System Architecture

### MQTT-Based Architecture:

```
                  Network (WiFi/Ethernet)
                          |
        ┌─────────────────┼─────────────────┐
        |                 |                 |
  ┌─────▼──────┐   ┌──────▼──────┐   ┌─────▼──────┐
  │ Arduino 1  │   │ Arduino 2   │   │ Arduino N  │
  │ + IMU      │   │ + IMU       │   │ + IMU      │
  │ + ESP8266  │   │ + ESP8266   │   │ + ESP8266  │
  └────────────┘   └─────────────┘   └────────────┘
        │                 │                 │
        └────(publish)────┴───(publish)─────┘
                          |
                          ▼
                  ┌───────────────┐
                  │ MQTT Broker   │
                  │ (Mosquitto)   │
                  └───────┬───────┘
                          │
                  (subscribe)
                          │
                          ▼
                  ┌───────────────┐
                  │ Flask Backend │
                  │ + Database    │
                  │ + Web UI      │
                  └───────────────┘
```

### Topic Structure:

- Sensor data: `laundriuno/sensor/{machine_id}/data`
- Status: `laundriuno/sensor/{machine_id}/status`
- Control: `laundriuno/control/{machine_id}/command`

### Message Format (JSON):

```json
{
  "machine_id": 1,
  "ax": 1234.56,
  "ay": 789.01,
  "az": 456.78,
  "timestamp": 1635724800
}
```

## Prerequisites

### Hardware:

- **ESP8266** (NodeMCU, Wemos D1 Mini) or **ESP32** board
  - Required for WiFi connectivity
  - Arduino Uno/Nano don't have built-in WiFi
- **MPU6050** IMU sensor
- **5V USB power supply** for each ESP8266/ESP32
- **WiFi network** (2.4GHz, WPA2 recommended)

### Software:

- **Python 3.7+** (for Flask backend)
- **Arduino IDE 1.8+** or **Arduino IDE 2.0+**
- **Mosquitto MQTT Broker** (or other MQTT broker)
- **pip** (Python package manager)

### Network Requirements:

- All devices on same local network
- Port 1883 open for MQTT (or 8883 for TLS)
- Static IP recommended for broker (or use mDNS/hostname)

## Installing MQTT Broker

### Option 1: Mosquitto (Recommended for Local Development)

#### On Ubuntu/Debian:

```bash
# Update package list
sudo apt update

# Install Mosquitto broker and clients
sudo apt install -y mosquitto mosquitto-clients

# Start Mosquitto service
sudo systemctl start mosquitto

# Enable auto-start on boot
sudo systemctl enable mosquitto

# Check status
sudo systemctl status mosquitto
```

#### On macOS:

```bash
# Install using Homebrew
brew install mosquitto

# Start Mosquitto
brew services start mosquitto

# Or run in foreground with verbose logging
/usr/local/opt/mosquitto/sbin/mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf -v
```

#### On Windows:

1. Download from: https://mosquitto.org/download/
2. Run installer
3. Add to PATH: `C:\Program Files\mosquitto`
4. Start service: `net start mosquitto`

Or run manually:
```cmd
cd "C:\Program Files\mosquitto"
mosquitto.exe -v
```

### Option 2: Docker (Cross-Platform)

```bash
# Pull Mosquitto image
docker pull eclipse-mosquitto

# Run Mosquitto container
docker run -d \
  --name mosquitto \
  -p 1883:1883 \
  -p 9001:9001 \
  eclipse-mosquitto

# Check logs
docker logs -f mosquitto
```

### Option 3: Cloud MQTT Brokers (For Production)

#### AWS IoT Core:

- Fully managed, scalable
- Integrated with AWS services
- https://aws.amazon.com/iot-core/

#### HiveMQ Cloud:

- Free tier available
- Easy setup
- https://www.hivemq.com/mqtt-cloud-broker/

#### Azure IoT Hub:

- Microsoft Azure integration
- Enterprise-grade security
- https://azure.microsoft.com/en-us/services/iot-hub/

### Verifying Broker Installation:

```bash
# Test publish
mosquitto_pub -h localhost -t "test/topic" -m "Hello MQTT"

# Test subscribe (in another terminal)
mosquitto_sub -h localhost -t "test/topic" -v
```

If you see "Hello MQTT", the broker is working!

## Configuring the Flask Backend

### Step 1: Update Configuration

Edit `.env` file (or create from `.env.example`):

```bash
# Copy example file
cp .env.example .env

# Edit configuration
nano .env
```

### Step 2: Set MQTT Parameters

Add/modify these lines in `.env`:

```bash
# Enable MQTT mode
USE_MQTT=true

# MQTT Broker Configuration
MQTT_BROKER_HOST=localhost      # Or IP address of broker
MQTT_BROKER_PORT=1883           # Standard MQTT port

# Machine Configuration
NUM_MACHINES=4                   # Number of machines to monitor
VIBRATION_THRESHOLD=1000         # Adjust based on testing
```

### Step 3: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (includes paho-mqtt)
pip install -r requirements.txt
```

### Step 4: Verify Configuration

```bash
# Test Flask app imports
python -c "from app import app; print('Config OK:', app.config['USE_MQTT'])"

# Should print: Config OK: True
```

## Programming the Arduino

### Step 1: Install Arduino IDE

Download from: https://www.arduino.cc/en/software

### Step 2: Add ESP8266/ESP32 Board Support

#### For ESP8266:

1. Open Arduino IDE
2. Go to: File → Preferences
3. In "Additional Board Manager URLs", add:
   ```
   http://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
4. Go to: Tools → Board → Boards Manager
5. Search for "esp8266"
6. Install "esp8266 by ESP8266 Community"
7. Select board: Tools → Board → ESP8266 Boards → NodeMCU 1.0 (or your board)

#### For ESP32:

1. In "Additional Board Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
2. Install "esp32 by Espressif Systems"
3. Select board: Tools → Board → ESP32 Arduino → ESP32 Dev Module

### Step 3: Install Required Libraries

Go to: Tools → Manage Libraries

Install these libraries:

1. **Adafruit MPU6050** (by Adafruit)
2. **Adafruit Unified Sensor** (by Adafruit)
3. **PubSubClient** (by Nick O'Leary)

### Step 4: Configure Arduino Sketch

Open `arduino/laundriuno_sensor_mqtt.ino`

Update these configuration constants:

```cpp
// Machine ID - UNIQUE for each Arduino!
const int MACHINE_ID = 1;  // Change to 2, 3, 4, etc.

// WiFi credentials
const char* WIFI_SSID = "YourWiFiName";
const char* WIFI_PASSWORD = "YourWiFiPassword";

// MQTT broker
const char* MQTT_SERVER = "192.168.1.100";  // Your broker IP
const int MQTT_PORT = 1883;
```

### Step 5: Upload to Arduino

1. Connect ESP8266/ESP32 via USB
2. Select correct port: Tools → Port
3. Click Upload button (→)
4. Wait for "Done uploading"

### Step 6: Monitor Serial Output

1. Open Serial Monitor: Tools → Serial Monitor
2. Set baud rate: 115200
3. Watch for connection messages:

```
========================================
Laundriuno IMU Sensor with MQTT
========================================
Machine ID: 1

[1/4] Initializing MPU6050 sensor...
MPU6050 sensor found!

[2/4] Connecting to WiFi...
WiFi connected!
IP address: 192.168.1.50

[3/4] Configuring MQTT client...
MQTT broker: 192.168.1.100:1883
MQTT topic: laundriuno/sensor/1/data

[4/4] Connecting to MQTT broker...
Attempting MQTT connection... connected!

========================================
System ready! Publishing sensor data...
========================================
```

## Testing the Setup

### Step 1: Verify MQTT Messages

Open terminal and subscribe to test topic:

```bash
# Subscribe to all sensor data
mosquitto_sub -h localhost -t "laundriuno/sensor/+/data" -v

# You should see JSON messages:
# laundriuno/sensor/1/data {"machine_id":1,"ax":1234.56,"ay":789.01,"az":456.78,"timestamp":12345}
```

### Step 2: Start Flask Backend

```bash
# Start Flask application
python app.py

# Should see:
# Initialized MQTT interface: localhost:1883
# Created 4 machines in database
#  * Running on http://0.0.0.0:5000
```

### Step 3: Start Monitoring

```bash
# Start monitoring via API
curl -X POST http://localhost:5000/api/monitoring/start

# Response:
# {"status":"success","message":"Monitoring started"}
```

### Step 4: Check Machine Status

```bash
# Get all machines
curl http://localhost:5000/api/machines | python -m json.tool

# Expected output:
# [
#   {
#     "id": 1,
#     "name": "Machine 1",
#     "is_running": false,
#     "last_status_change": "2024-11-01T10:30:00"
#   },
#   ...
# ]
```

### Step 5: Test Detection

Shake the IMU sensor vigorously, then check status:

```bash
curl http://localhost:5000/api/machines/1 | python -m json.tool

# Should show is_running: true when vibration detected
```

### Step 6: View Dashboard

Open browser: http://localhost:5000

You should see:
- Real-time machine status
- Available machine count
- Usage statistics
- Recommendations

## Troubleshooting

### Problem: Arduino can't connect to WiFi

**Symptoms:**
- LED blinking rapidly
- Serial: "Failed to connect to WiFi!"

**Solutions:**
1. Check WiFi credentials (SSID and password)
2. Ensure 2.4GHz network (ESP8266 doesn't support 5GHz)
3. Check signal strength (move closer to router)
4. Verify WPA2 encryption (some ESP8266 don't support WPA3)

```cpp
// Add to setup() for debugging:
Serial.print("Connecting to: ");
Serial.println(WIFI_SSID);
Serial.print("Signal strength: ");
Serial.println(WiFi.RSSI());
```

### Problem: Arduino can't connect to MQTT broker

**Symptoms:**
- LED blinking medium speed
- Serial: "Failed to connect to MQTT broker"

**Solutions:**
1. Verify broker is running: `sudo systemctl status mosquitto`
2. Check broker IP address is correct
3. Test broker from command line: `mosquitto_pub -h <IP> -t test -m hello`
4. Check firewall: `sudo ufw allow 1883`
5. Verify Arduino and broker on same network

```bash
# Check broker logs
journalctl -u mosquitto -f

# Or if running manually:
mosquitto -v
```

### Problem: Flask app doesn't receive messages

**Symptoms:**
- Arduino connected and publishing
- Flask app shows "Monitoring started"
- No machine state changes

**Solutions:**
1. Check Flask logs for connection messages
2. Verify topic subscription matches publisher
3. Test with mosquitto_sub:

```bash
# Subscribe to same topics as Flask
mosquitto_sub -h localhost -t "laundriuno/sensor/+/data" -v
```

4. Check Flask environment:

```bash
python -c "from app import app; print('MQTT:', app.config['USE_MQTT'])"
# Should print: MQTT: True
```

### Problem: False positives/negatives

**Symptoms:**
- Idle machines detected as running
- Running machines not detected

**Solutions:**
1. Adjust vibration threshold in `.env`:

```bash
# Lower value = more sensitive
VIBRATION_THRESHOLD=500

# Higher value = less sensitive
VIBRATION_THRESHOLD=2000
```

2. Test threshold with monitoring:

```bash
# Watch sensor readings
mosquitto_sub -h localhost -t "laundriuno/sensor/+/data" -v

# Look at ax, ay, az values
# Calculate magnitude: sqrt(ax² + ay² + az²)
# Set threshold between idle and running magnitudes
```

3. Check sensor mounting:
   - Ensure sensor is firmly attached to machine
   - Avoid loose connections
   - Mount near motor/drum for best vibration detection

### Problem: Connection drops intermittently

**Symptoms:**
- Connections work initially then fail
- Messages stop flowing
- LED indicates disconnection

**Solutions:**
1. Increase WiFi signal strength (move closer, add repeater)
2. Use static IP instead of DHCP
3. Increase MQTT keepalive:

```cpp
// In Arduino sketch:
mqttClient.setKeepAlive(90);  // Increase from 60 to 90 seconds
```

4. Add reconnection logic to Flask:

```python
# Already implemented in mqtt_interface.py
# Check connection regularly
```

### Problem: High latency or delayed updates

**Symptoms:**
- Machine states update slowly
- Dashboard shows stale data

**Solutions:**
1. Reduce sample rate in Arduino:

```cpp
const int SAMPLE_RATE = 50;  // Publish every 50ms instead of 100ms
```

2. Increase QoS level for guaranteed delivery:

```cpp
// In Arduino:
mqttClient.publish(mqttTopic, messageBuffer, 1);  // QoS 1
//                                           ^ change to 1 or 2
```

3. Optimize network:
   - Use wired Ethernet for broker
   - Reduce network congestion
   - Use local broker (not cloud)

## Advanced Configuration

### Security: Adding Authentication

#### Step 1: Configure Mosquitto Authentication

Create password file:

```bash
# Create password for user
sudo mosquitto_passwd -c /etc/mosquitto/passwd laundriuno

# Edit Mosquitto config
sudo nano /etc/mosquitto/mosquitto.conf
```

Add:

```
password_file /etc/mosquitto/passwd
allow_anonymous false
```

Restart:

```bash
sudo systemctl restart mosquitto
```

#### Step 2: Update Arduino Sketch

```cpp
// Add before mqttClient.connect():
mqttClient.setCredentials("laundriuno", "your_password");
```

#### Step 3: Update Flask Backend

Modify `mqtt_interface.py`:

```python
# In connect() method:
self.client.username_pw_set("laundriuno", "your_password")
```

### Security: Enabling TLS/SSL

#### Step 1: Generate Certificates

```bash
# Generate CA certificate
openssl req -new -x509 -days 365 -extensions v3_ca \
  -keyout ca.key -out ca.crt

# Generate server certificate
openssl genrsa -out server.key 2048
openssl req -new -out server.csr -key server.key
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 365
```

#### Step 2: Configure Mosquitto for TLS

Edit `/etc/mosquitto/mosquitto.conf`:

```
listener 8883
cafile /etc/mosquitto/certs/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
```

#### Step 3: Update Clients

Arduino:

```cpp
// Add WiFiClientSecure instead of WiFiClient
WiFiClientSecure wifiClient;
PubSubClient mqttClient(wifiClient);

// In setup():
wifiClient.setCACert(ca_cert);  // Load CA certificate
```

Flask:

```python
# In MQTTInterface:
self.client.tls_set(ca_certs="ca.crt")
```

### Performance: Tuning for High Frequency

For faster updates (lower latency):

```cpp
// Arduino:
const int SAMPLE_RATE = 20;  // 50Hz update rate
```

```python
# Flask mqtt_interface.py:
# Adjust buffer size if needed
mqttClient.max_queued_messages_set(100)
```

### Scalability: Multiple Brokers

For distributed deployments:

1. Set up multiple brokers
2. Configure bridge between brokers
3. Use different topic prefixes per location
4. Update Flask to subscribe to multiple brokers

### Monitoring: MQTT Broker Dashboard

Install monitoring tools:

```bash
# MQTT Explorer (GUI)
# Download from: https://mqtt-explorer.com/

# Or use command line:
mosquitto_sub -h localhost -t '#' -v  # Subscribe to all topics
```

---

## Next Steps

After successful MQTT setup:

1. ✅ Deploy to multiple machines
2. ✅ Configure automatic monitoring startup
3. ✅ Set up cloud broker for remote access
4. ✅ Add mobile app integration
5. ✅ Implement notifications (email/SMS)
6. ✅ Add data analytics and ML predictions

For more information:
- Main README: `README.md`
- Architecture: `ARCHITECTURE.md`
- Quick Start: `QUICKSTART.md`

---

**Happy monitoring with MQTT!** 🚀🧺

