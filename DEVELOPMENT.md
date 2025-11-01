# Development Guide

## Quick Start for Development

### Without Arduino Hardware

You can develop and test the system without Arduino hardware:

1. **Run the Flask app** (it will run without Arduino):
   ```bash
   source venv/bin/activate
   python main.py
   ```

2. **Run the test suite**:
   ```bash
   python test_app.py
   ```

3. **Use the simulator** (optional - for testing the interface):
   ```bash
   python simulator.py
   ```

### With Arduino Hardware

1. **Upload Arduino sketch**:
   - Open `arduino/laundry_monitor.ino` in Arduino IDE
   - Connect Arduino via USB
   - Upload to board

2. **Find Arduino port**:
   - Linux/Mac: `ls /dev/tty*` (usually `/dev/ttyUSB0` or `/dev/ttyACM0`)
   - Windows: Check Device Manager (usually `COM3`, `COM4`, etc.)

3. **Update configuration**:
   Edit `config.env` and set the correct port:
   ```
   ARDUINO_PORT=/dev/ttyUSB0
   ```

4. **Run the application**:
   ```bash
   ./run.sh
   ```

## API Testing

### Using curl

```bash
# Get all machine status
curl http://localhost:5000/api/status

# Get specific machine
curl http://localhost:5000/api/machine/0

# Get statistics
curl http://localhost:5000/api/stats

# Get machine history
curl http://localhost:5000/api/history/0

# Check Arduino connection
curl http://localhost:5000/api/arduino/status
```

### Using Python requests

```python
import requests

# Get status
response = requests.get('http://localhost:5000/api/status')
print(response.json())

# Get stats
response = requests.get('http://localhost:5000/api/stats')
print(response.json())
```

## Testing Arduino Communication

### Monitor Serial Output

Use Arduino IDE Serial Monitor or `screen`:

```bash
# Linux/Mac
screen /dev/ttyUSB0 9600

# Or use minicom
minicom -D /dev/ttyUSB0 -b 9600
```

### Send Commands to Arduino

From Serial Monitor or terminal, send:
- `STATUS` - Request current status of all machines
- `PING` - Test connection (should respond with `PONG`)

## Project Structure Details

### `main.py`
- Flask application entry point
- Defines all API routes
- Manages Arduino connection lifecycle

### `app/arduino_interface.py`
- Handles serial communication
- Background thread for reading data
- Message parsing and protocol handling

### `app/data_store.py`
- In-memory data storage
- Thread-safe operations
- Statistics and history tracking

### `arduino/laundry_monitor.ino`
- Arduino firmware
- Sensor reading and debouncing
- Serial protocol implementation

### `templates/index.html`
- Single-page web dashboard
- Auto-refresh functionality
- Responsive design

## Customization

### Change Number of Machines

1. In `arduino/laundry_monitor.ino`:
   ```cpp
   const int NUM_MACHINES = 4;  // Change this
   const int MACHINE_PINS[] = {2, 3, 4, 5};  // Add/remove pins
   ```

2. In `app/data_store.py`:
   ```python
   DataStore(num_machines=4)  # Change this
   ```

### Adjust Vibration Sensitivity

In `arduino/laundry_monitor.ino`:
```cpp
const int VIBRATION_THRESHOLD = 5;  // Increase for less sensitive
const unsigned long CHECK_INTERVAL = 5000;  // Check interval in ms
```

### Change Update Frequency

In `templates/index.html`:
```javascript
// Auto-refresh every 5 seconds
updateInterval = setInterval(fetchData, 5000);  // Change 5000 to desired ms
```

## Troubleshooting

### Port Permission Denied (Linux)

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Or temporarily change permissions
sudo chmod 666 /dev/ttyUSB0
```

### Arduino Not Responding

1. Check if port is correct: `ls -l /dev/ttyUSB*`
2. Close other programs using the port
3. Press reset button on Arduino
4. Check baud rate matches (9600)

### Web Interface Not Updating

1. Check browser console for errors (F12)
2. Verify Flask app is running
3. Check network tab for failed API calls
4. Clear browser cache

## Building for Production

### Using Gunicorn (Linux/Mac)

```bash
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Using Waitress (Windows)

```bash
pip install waitress

# Run with waitress
waitress-serve --host=0.0.0.0 --port=5000 main:app
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t laundriuno .
docker run -p 5000:5000 --device=/dev/ttyUSB0 laundriuno
```

## Adding Features

### Email Notifications

1. Install: `pip install flask-mail`
2. Configure SMTP settings in `config.env`
3. Send email when machine becomes free

### Database Storage

1. Install: `pip install sqlalchemy`
2. Replace `DataStore` with SQLAlchemy models
3. Persist history to database

### WebSocket Support

1. Install: `pip install flask-socketio`
2. Push updates to clients in real-time
3. Remove polling, use event-driven updates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit pull request

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions
- Comment complex logic

## License

MIT License - See LICENSE file for details
