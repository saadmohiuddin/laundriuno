# Laundriuno - Laundry Machine Monitor

A comprehensive IoT system that monitors washing and drying machines using Arduino sensors and provides a web-based dashboard via Flask for real-time status tracking.

## Features

- **Real-time Monitoring**: Track the status of multiple laundry machines simultaneously
- **Web Dashboard**: Beautiful, responsive web interface for viewing machine status
- **Arduino Interface**: Serial communication with Arduino for sensor data
- **Usage Statistics**: Track total uses, time spent, and availability
- **History Tracking**: Maintain history of machine usage events
- **RESTful API**: Complete REST API for integration with other systems

## Hardware Requirements

- Arduino Uno or Arduino Nano
- SW-420 or similar vibration sensors (one per machine)
- USB cable for Arduino connection
- Jumper wires

## Software Requirements

- Python 3.8+
- Flask
- pySerial
- Arduino IDE (for uploading sketch)

## Installation

### 1. Arduino Setup

1. Open Arduino IDE
2. Open `arduino/laundry_monitor.ino`
3. Connect your Arduino via USB
4. Select the correct board and port from Tools menu
5. Upload the sketch to Arduino
6. Connect vibration sensors to pins 2, 3, 4, 5 (for up to 4 machines)

### 2. Python Environment Setup

```bash
# Clone the repository
git clone https://github.com/saadmohiuddin/laundriuno.git
cd laundriuno

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Edit `config.env` to match your setup:

```bash
# Set the correct Arduino port
ARDUINO_PORT=/dev/ttyUSB0  # On Windows: COM3, COM4, etc.
ARDUINO_BAUD_RATE=9600

# Set a secure secret key for production
SECRET_KEY=your-secret-key-here
```

## Usage

### Starting the Application

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the Flask application
python main.py
```

The application will start on `http://localhost:5000`

### Web Interface

Open your browser and navigate to:
```
http://localhost:5000
```

You'll see:
- Real-time status of all machines
- Connection status with Arduino
- Usage statistics
- Individual machine details

### API Endpoints

#### Get All Machine Status
```bash
GET /api/status
```

Response:
```json
{
  "success": true,
  "connected": true,
  "machines": [
    {
      "id": 0,
      "in_use": false,
      "last_updated": "2025-11-01T20:00:00",
      "total_uses": 5,
      "total_time_used": 1800
    }
  ]
}
```

#### Get Single Machine Status
```bash
GET /api/machine/<id>
```

#### Get Machine History
```bash
GET /api/machine/<id>/history
```

#### Get Statistics
```bash
GET /api/stats
```

#### Arduino Connection Management
```bash
POST /api/arduino/connect
POST /api/arduino/disconnect
GET /api/arduino/status
```

## Hardware Wiring

### Vibration Sensor Connection

For each machine:
1. Connect sensor VCC to Arduino 5V
2. Connect sensor GND to Arduino GND
3. Connect sensor DO (Digital Out) to Arduino pins 2-5

Example for 4 machines:
- Machine 1 → Pin 2
- Machine 2 → Pin 3
- Machine 3 → Pin 4
- Machine 4 → Pin 5

## How It Works

1. **Sensor Detection**: Vibration sensors detect when machines are running
2. **Arduino Processing**: Arduino counts vibrations over 5-second intervals
3. **Serial Communication**: Arduino sends status updates to Flask via serial
4. **Data Storage**: Flask maintains current status and historical data
5. **Web Display**: Real-time dashboard shows current status and statistics

## Troubleshooting

### Arduino Not Connecting

1. Check the serial port in `config.env`
2. Verify Arduino is connected via USB
3. Ensure no other program is using the serial port
4. Check permissions: `sudo chmod 666 /dev/ttyUSB0` (Linux)

### Machines Not Detected

1. Test sensors individually with Arduino Serial Monitor
2. Adjust `VIBRATION_THRESHOLD` in Arduino code
3. Ensure sensors are properly mounted on machines
4. Check sensor wiring and power

### Web Interface Not Loading

1. Verify Flask is running: check terminal for errors
2. Check firewall settings
3. Try accessing via 127.0.0.1:5000 instead of localhost

## Development

### Project Structure

```
laundriuno/
├── main.py               # Main Flask application
├── app/
│   ├── __init__.py       # Package initialization
│   ├── arduino_interface.py  # Arduino serial communication
│   └── data_store.py     # Data storage and management
├── arduino/
│   └── laundry_monitor.ino   # Arduino sketch
├── templates/
│   └── index.html        # Web dashboard
├── static/               # Static files (CSS, JS, images)
├── requirements.txt      # Python dependencies
├── config.env           # Configuration file
└── README.md            # This file
```

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-flask

# Run tests (when implemented)
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this project for any purpose.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Future Enhancements

- [ ] Mobile app integration
- [ ] Email/SMS notifications when machines are free
- [ ] Machine reservation system
- [ ] Historical usage analytics and charts
- [ ] Support for more sensor types (current sensors, smart plugs)
- [ ] Multi-location support
- [ ] User authentication and profiles

## Credits

Developed for monitoring laundry facilities to help users find the best times to do laundry
