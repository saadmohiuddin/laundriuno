# Laundriuno Quick Start Guide

This guide will help you get the Laundriuno system up and running quickly.

## Prerequisites

- Python 3.7 or higher
- Arduino IDE (if using physical hardware)
- Arduino board with MPU6050 IMU sensor (optional for demo)

## Quick Setup (Demo Mode - No Hardware Required)

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/saadmohiuddin/laundriuno.git
cd laundriuno

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

### 2. Run the Demo

```bash
# Generate sample data and see system in action
python demo.py
```

This will create sample machine usage data and display:
- Current machine status
- Usage statistics
- Best times recommendations
- Hourly availability forecast
- Machine history

### 3. Start the Web Application

```bash
# Start the Flask server
python app.py
```

Open your browser and visit: `http://localhost:5000`

You'll see a beautiful dashboard showing:
- ✅ Available machines in real-time
- 📊 Usage statistics
- ⏰ Best times to do laundry
- 📈 Hourly availability forecast

## Quick Setup (With Arduino Hardware)

### 1. Hardware Setup

**Components:**
- Arduino board (Uno/Nano)
- MPU6050 IMU sensor
- USB cable

**Connections:**
```
MPU6050 → Arduino
VCC     → 5V
GND     → GND
SCL     → A5 (SCL)
SDA     → A4 (SDA)
```

### 2. Arduino Setup

1. Install Arduino IDE from https://www.arduino.cc/
2. Install libraries (Tools → Manage Libraries):
   - Adafruit MPU6050
   - Adafruit Unified Sensor
3. Open `arduino/laundriuno_sensor.ino`
4. Update `MACHINE_ID` (1, 2, 3, etc. for each machine)
5. Upload to Arduino
6. Attach sensor to laundry machine

### 3. Configure and Run

```bash
# Copy example config
cp .env.example .env

# Edit .env and set your Arduino port
# For Linux/Mac: /dev/ttyUSB0 or /dev/ttyACM0
# For Windows: COM3, COM4, etc.
nano .env

# Start the application
python app.py
```

### 4. Start Monitoring

Once the app is running, start Arduino monitoring:

**Via API:**
```bash
curl -X POST http://localhost:5000/api/monitoring/start
```

**Or via Python:**
```python
import requests
requests.post('http://localhost:5000/api/monitoring/start')
```

The system will now:
1. Read sensor data from Arduino
2. Detect machine vibrations
3. Track when machines are running
4. Build usage history database
5. Provide recommendations

## API Endpoints

### Machine Status
```bash
# Get all machines
curl http://localhost:5000/api/machines

# Get available machines
curl http://localhost:5000/api/machines/available

# Get specific machine
curl http://localhost:5000/api/machines/1
```

### Analytics
```bash
# Get best times
curl http://localhost:5000/api/best-times?days=7

# Get usage statistics
curl http://localhost:5000/api/statistics?days=7

# Get hourly availability
curl http://localhost:5000/api/availability?days=7
```

### Machine History
```bash
# Get history for machine 1
curl http://localhost:5000/api/machines/1/history?days=7
```

## Testing Without Hardware

Use the test simulator to test API endpoints:

```bash
python test_simulator.py
```

This will:
- Test all API endpoints
- Show simulated sensor data
- Verify the system is working

## Configuration

Edit `.env` to customize:

```bash
# Number of machines to track
NUM_MACHINES=4

# Vibration threshold (adjust based on your machines)
VIBRATION_THRESHOLD=1000

# Arduino serial port
ARDUINO_PORT=/dev/ttyUSB0
ARDUINO_BAUD_RATE=9600
```

## Troubleshooting

### Arduino Not Detected
```bash
# List available serial ports
# Linux/Mac:
ls /dev/tty*

# Windows: Check Device Manager
```

### Port Permission Issues (Linux)
```bash
sudo usermod -a -G dialout $USER
# Logout and login again
```

### Database Issues
```bash
# Reset database
rm laundriuno.db
python app.py  # Will recreate tables
```

## Next Steps

1. ✅ Run the demo to understand the system
2. ✅ Start the web application
3. ✅ Connect Arduino hardware (optional)
4. ✅ Start monitoring
5. ✅ Let it collect data for a few days
6. ✅ Get smart recommendations!

## Support

For issues or questions:
- Check the full README.md
- Review the code comments
- Test with the demo and simulator first

Enjoy smart laundry scheduling! 🧺✨
