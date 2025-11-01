# Laundriuno - Smart Laundry Machine Monitoring System

A Flask-based web application that interfaces with Arduino boards equipped with IMU sensors to detect when laundry machines are running. The system builds a database of machine usage patterns and provides users with real-time availability information and recommendations for the best times to do laundry.

## Features

- **Real-time Machine Monitoring**: Track the status of multiple laundry machines simultaneously
- **IMU Sensor Integration**: Uses accelerometer data from MPU6050 sensors to detect machine vibrations
- **Usage Analytics**: Historical data analysis to identify usage patterns
- **Smart Recommendations**: Algorithm-based suggestions for optimal laundry times
- **REST API**: Complete API for machine status, history, and analytics
- **Web Dashboard**: User-friendly interface to view machine availability and recommendations
- **Database Tracking**: SQLite database for storing machine sessions and sensor readings

## System Architecture

```
Arduino + IMU Sensor → Serial Communication → Flask App → SQLite Database
                                                    ↓
                                              Web Interface
                                                    ↓
                                              REST API
```

## Hardware Requirements

- Arduino board (Uno, Nano, or compatible)
- MPU6050 IMU sensor(s)
- USB cable for Arduino connection
- Computer/Server to run Flask application

## Software Requirements

- Python 3.7+
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- pyserial 3.5
- python-dotenv 1.0.0

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/saadmohiuddin/laundriuno.git
cd laundriuno
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings
# Set ARDUINO_PORT to match your Arduino's serial port
# Common values: /dev/ttyUSB0 (Linux), /dev/ttyACM0 (Linux), COM3 (Windows)
```

### 4. Upload Arduino Sketch

1. Install Arduino IDE from https://www.arduino.cc/en/software
2. Install required libraries via Library Manager:
   - Adafruit MPU6050
   - Adafruit Unified Sensor
3. Open `arduino/laundriuno_sensor.ino`
4. Update `MACHINE_ID` if using multiple Arduinos
5. Upload sketch to Arduino board

### 5. Hardware Setup

1. Connect MPU6050 to Arduino:
   - VCC → 5V
   - GND → GND
   - SCL → A5 (SCL)
   - SDA → A4 (SDA)
2. Attach sensor to laundry machine (secure mounting is important)
3. Connect Arduino to computer via USB

## Usage

### Starting the Application

```bash
# Ensure virtual environment is activated
python app.py
```

The application will start on `http://localhost:5000`

### Starting Monitoring

To start monitoring Arduino sensors:

```bash
# Using the API
curl -X POST http://localhost:5000/api/monitoring/start
```

Or access the web interface and use the monitoring controls.

### Accessing the Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

## API Endpoints

### Machine Status

- `GET /api/machines` - Get status of all machines
- `GET /api/machines/<id>` - Get status of specific machine
- `GET /api/machines/available` - Get list of available machines
- `GET /api/machines/<id>/history?days=7` - Get usage history

### Analytics

- `GET /api/statistics?days=7` - Get usage statistics
- `GET /api/best-times?days=7` - Get recommended times
- `GET /api/availability?days=7` - Get hourly availability forecast

### Monitoring Control

- `POST /api/monitoring/start` - Start Arduino monitoring
- `POST /api/monitoring/stop` - Stop Arduino monitoring
- `GET /api/monitoring/status` - Get monitoring status

## Configuration

Edit `.env` file to customize settings:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///laundriuno.db

# Arduino
ARDUINO_PORT=/dev/ttyUSB0
ARDUINO_BAUD_RATE=9600

# Machines
NUM_MACHINES=4              # Number of machines to track
VIBRATION_THRESHOLD=1000     # Vibration threshold for detection
IDLE_TIMEOUT=300            # Timeout in seconds
```

## How It Works

### Detection Algorithm

1. **Sensor Reading**: MPU6050 measures acceleration in 3 axes (X, Y, Z)
2. **Vibration Calculation**: Magnitude = √(ax² + ay² + az²)
3. **State Detection**: If magnitude > threshold → Machine is running
4. **Session Tracking**: Start/end times recorded in database

### Recommendation Algorithm

The system analyzes historical usage patterns to recommend optimal laundry times:

1. Collects usage data over specified period (default: 7 days)
2. Aggregates sessions by hour of day
3. Identifies hours with lowest usage
4. Returns top 5 least busy time slots

### Availability Forecast

Hourly forecast shows average machine availability based on historical patterns, helping users plan when to do laundry.

## Multiple Machine Setup

To monitor multiple machines:

1. Use separate Arduino + IMU sensor for each machine
2. Update `MACHINE_ID` in Arduino sketch for each board (1, 2, 3, etc.)
3. Update `NUM_MACHINES` in `.env` file
4. All Arduinos can connect to same computer or different computers running the Flask app

## Troubleshooting

### Arduino Not Detected

- Check USB connection
- Verify correct port in `.env` (use `ls /dev/tty*` on Linux/Mac or Device Manager on Windows)
- Ensure pyserial is installed: `pip install pyserial`

### IMU Sensor Not Working

- Verify wiring connections
- Check I2C address (default 0x68)
- Test with Arduino Serial Monitor
- Ensure sensor libraries are installed

### No Data in Dashboard

- Start monitoring via `/api/monitoring/start`
- Wait for sensor readings to accumulate
- Check Arduino Serial Monitor for data transmission
- Verify database file is being created

## Development

### Running in Development Mode

```bash
export FLASK_ENV=development
python app.py
```

### Database Management

```bash
# Reset database
rm laundriuno.db

# Restart app to recreate tables
python app.py
```

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## Acknowledgments

- Flask framework for the web application
- Adafruit for MPU6050 Arduino libraries
- SQLAlchemy for database management
