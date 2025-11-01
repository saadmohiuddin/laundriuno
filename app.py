"""
Main Flask Application for Laundriuno System

This is the entry point for the Laundriuno laundry machine monitoring system.
It initializes the Flask web server, database, and communication interfaces
(MQTT or Serial), and defines all REST API endpoints.

Architecture Overview:
    ┌─────────────────┐
    │  Flask Web App  │
    │    (this file)  │
    └────────┬────────┘
             │
      ┌──────┴───────┐
      │              │
    ┌─▼──┐      ┌───▼────┐
    │ DB │      │ MQTT/  │
    │    │      │ Serial │
    └────┘      └────────┘

Key Components:
    - Flask: Web framework for REST API and web interface
    - SQLAlchemy: Database ORM for data persistence
    - MQTT/Serial: Communication with Arduino sensors
    - Analytics: Data processing and recommendations

API Endpoints:
    Machine Status:
        GET  /api/machines
        GET  /api/machines/<id>
        GET  /api/machines/available
        GET  /api/machines/<id>/history
    
    Analytics:
        GET  /api/statistics
        GET  /api/best-times
        GET  /api/availability
    
    Monitoring Control:
        POST /api/monitoring/start
        POST /api/monitoring/stop
        GET  /api/monitoring/status
    
    Web Interface:
        GET  /

Dependencies:
    - Flask 3.0.0+
    - Flask-SQLAlchemy 3.1.1+
    - paho-mqtt 1.6.1+ (for MQTT mode)
    - pyserial 3.5+ (for Serial mode)

Configuration:
    All settings loaded from config.py, which reads from .env file.
    See .env.example for available configuration options.

Usage:
    Development:
        export FLASK_ENV=development
        python app.py
    
    Production:
        export FLASK_ENV=production
        gunicorn -w 4 -b 0.0.0.0:5000 app:app

Author: Laundriuno System
Version: 1.0.0
"""

from flask import Flask, jsonify, request, render_template
from config import Config
from models import db, Machine
from arduino_interface import ArduinoInterface
from mqtt_interface import MQTTInterface
from analytics import AnalyticsService
import os

# =============================================================================
# Flask Application Initialization
# =============================================================================

# Create Flask application instance
# __name__ helps Flask locate templates and static files
app = Flask(__name__)

# Load configuration from Config class
# Configuration includes database URI, MQTT settings, thresholds, etc.
app.config.from_object(Config)

# =============================================================================
# Database Initialization
# =============================================================================

# Initialize SQLAlchemy with Flask app
# This creates the database connection pool and session management
db.init_app(app)

# =============================================================================
# Communication Interface Initialization
# =============================================================================

# Initialize the appropriate communication interface based on configuration
# USE_MQTT flag determines whether to use MQTT broker or direct serial connection

if app.config['USE_MQTT']:
    # MQTT Mode: Use message broker for communication
    # Advantages: Wireless, scalable, supports multiple subscribers
    # Use case: Production deployments, multiple sensors, cloud integration
    interface = MQTTInterface(
        broker_host=app.config['MQTT_BROKER_HOST'],
        broker_port=app.config['MQTT_BROKER_PORT'],
        vibration_threshold=app.config['VIBRATION_THRESHOLD']
    )
    print(f"Initialized MQTT interface: {app.config['MQTT_BROKER_HOST']}:{app.config['MQTT_BROKER_PORT']}")
else:
    # Serial Mode: Direct USB/serial connection to Arduino
    # Advantages: Simple setup, no external dependencies
    # Use case: Development, testing, single sensor setups
    interface = ArduinoInterface(
        port=app.config['ARDUINO_PORT'],
        baud_rate=app.config['ARDUINO_BAUD_RATE'],
        vibration_threshold=app.config['VIBRATION_THRESHOLD']
    )
    print(f"Initialized Serial interface: {app.config['ARDUINO_PORT']} @ {app.config['ARDUINO_BAUD_RATE']} baud")

# =============================================================================
# Database Setup and Machine Initialization
# =============================================================================

# Create database tables and populate initial machine records
with app.app_context():
    # Create all database tables defined in models.py
    # This is idempotent - safe to run multiple times
    db.create_all()
    
    # Initialize machine records if database is empty
    # Each machine gets a unique ID and name
    if Machine.query.count() == 0:
        for i in range(1, app.config['NUM_MACHINES'] + 1):
            machine = Machine(name=f"Machine {i}")
            db.session.add(machine)
        db.session.commit()
        print(f"Created {app.config['NUM_MACHINES']} machines in database")

# =============================================================================
# Web Interface Routes
# =============================================================================

@app.route('/')
def index():
    """
    Serve the main web dashboard
    
    Renders the HTML template for the web-based user interface. The dashboard
    displays real-time machine status, usage statistics, and recommendations.
    
    URL: GET /
    
    Returns:
        HTML: Rendered index.html template
    
    Template Variables:
        None (dashboard loads data via JavaScript API calls)
    
    Example:
        Visit http://localhost:5000/ in web browser
    """
    return render_template('index.html')


# =============================================================================
# Machine Status API Endpoints
# =============================================================================

@app.route('/api/machines', methods=['GET'])
def get_machines():
    """
    Get current status of all machines
    
    Returns a list of all machines with their current running status and
    last status change time. This is the primary endpoint for checking
    which machines are available.
    
    URL: GET /api/machines
    
    Returns:
        JSON: Array of machine objects
        
    Response Format:
        [
            {
                "id": 1,
                "name": "Machine 1",
                "is_running": false,
                "last_status_change": "2024-11-01T10:30:00"
            },
            ...
        ]
    
    Status Codes:
        200: Success
    
    Example:
        curl http://localhost:5000/api/machines
    """
    status = AnalyticsService.get_machine_status()
    return jsonify(status)


@app.route('/api/machines/<int:machine_id>', methods=['GET'])
def get_machine(machine_id):
    """
    Get status of a specific machine
    
    Returns detailed information about a single machine identified by its ID.
    
    URL: GET /api/machines/<machine_id>
    
    Parameters:
        machine_id (int): Unique machine identifier (1, 2, 3, ...)
    
    Returns:
        JSON: Machine object or error message
        
    Response Format (Success):
        {
            "id": 1,
            "name": "Machine 1",
            "is_running": true,
            "last_status_change": "2024-11-01T10:30:00"
        }
    
    Response Format (Error):
        {
            "error": "Machine not found"
        }
    
    Status Codes:
        200: Success
        404: Machine not found
    
    Example:
        curl http://localhost:5000/api/machines/1
    """
    status = AnalyticsService.get_machine_status(machine_id)
    if not status:
        return jsonify({'error': 'Machine not found'}), 404
    return jsonify(status[0])


@app.route('/api/machines/available', methods=['GET'])
def get_available():
    """
    Get list of currently available (idle) machines
    
    Returns only the machines that are not currently running, along with
    a count of available machines. Useful for quickly finding free machines.
    
    URL: GET /api/machines/available
    
    Returns:
        JSON: Object containing count and list of available machines
        
    Response Format:
        {
            "count": 2,
            "machines": [
                {"id": 1, "name": "Machine 1"},
                {"id": 3, "name": "Machine 3"}
            ]
        }
    
    Status Codes:
        200: Success
    
    Example:
        curl http://localhost:5000/api/machines/available
    """
    available = AnalyticsService.get_available_machines()
    return jsonify({
        'count': len(available),
        'machines': available
    })


@app.route('/api/machines/<int:machine_id>/history', methods=['GET'])
def get_machine_history(machine_id):
    """
    Get usage history for a specific machine
    
    Returns a chronological list of usage sessions for a machine over a
    specified time period. Each session includes start time, end time,
    and duration.
    
    URL: GET /api/machines/<machine_id>/history?days=<days>
    
    Parameters:
        machine_id (int): Machine identifier (path parameter)
        days (int): Number of days to look back (query parameter, default: 7)
    
    Returns:
        JSON: Object containing machine ID, time period, and session list
        
    Response Format:
        {
            "machine_id": 1,
            "days": 7,
            "sessions": [
                {
                    "start_time": "2024-11-01T10:00:00",
                    "end_time": "2024-11-01T10:45:00",
                    "duration": 2700
                },
                ...
            ]
        }
    
    Status Codes:
        200: Success
    
    Example:
        curl http://localhost:5000/api/machines/1/history?days=7
    """
    days = request.args.get('days', default=7, type=int)
    history = AnalyticsService.get_machine_history(machine_id, days)
    return jsonify({
        'machine_id': machine_id,
        'days': days,
        'sessions': history
    })


# =============================================================================
# Analytics API Endpoints
# =============================================================================

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """
    Get overall usage statistics
    
    Returns aggregate statistics about machine usage over a specified time
    period, including total sessions, average duration, total usage time,
    and busiest hours.
    
    URL: GET /api/statistics?days=<days>
    
    Parameters:
        days (int): Number of days to analyze (query parameter, default: 7)
    
    Returns:
        JSON: Statistics object
        
    Response Format:
        {
            "total_sessions": 85,
            "average_duration": 3600,
            "total_usage_time": 306000,
            "busiest_hours": [
                {"hour": 8, "count": 15},
                {"hour": 18, "count": 12},
                ...
            ]
        }
    
    Status Codes:
        200: Success
    
    Example:
        curl http://localhost:5000/api/statistics?days=7
    """
    days = request.args.get('days', default=7, type=int)
    stats = AnalyticsService.get_usage_statistics(days)
    return jsonify(stats)


@app.route('/api/best-times', methods=['GET'])
def get_best_times():
    """
    Get recommended best times to do laundry
    
    Analyzes historical usage patterns to identify the least busy time slots.
    Returns the top 5 recommended hours based on lowest usage frequency.
    
    URL: GET /api/best-times?days=<days>
    
    Parameters:
        days (int): Number of days to analyze (query parameter, default: 7)
    
    Returns:
        JSON: Object containing recommendations and message
        
    Response Format:
        {
            "recommended_times": [
                {
                    "hour": 3,
                    "time_range": "03:00 - 04:00",
                    "usage_count": 0
                },
                ...
            ],
            "message": "These are the least busy times based on the last 7 days of data."
        }
    
    Status Codes:
        200: Success
    
    Example:
        curl http://localhost:5000/api/best-times?days=7
    """
    days = request.args.get('days', default=7, type=int)
    best_times = AnalyticsService.get_best_times(days)
    return jsonify(best_times)


@app.route('/api/availability', methods=['GET'])
def get_availability():
    """
    Get hourly availability forecast
    
    Provides a 24-hour forecast of average machine availability based on
    historical patterns. Helps users plan when to do laundry.
    
    URL: GET /api/availability?days=<days>
    
    Parameters:
        days (int): Number of days to analyze (query parameter, default: 7)
    
    Returns:
        JSON: Array of hourly availability objects
        
    Response Format:
        [
            {
                "hour": 0,
                "time_range": "00:00 - 01:00",
                "avg_available": 3.8,
                "avg_in_use": 0.2
            },
            ...
        ]
    
    Status Codes:
        200: Success
    
    Example:
        curl http://localhost:5000/api/availability?days=7
    """
    days = request.args.get('days', default=7, type=int)
    availability = AnalyticsService.get_hourly_availability(days)
    return jsonify(availability)


# =============================================================================
# Monitoring Control API Endpoints
# =============================================================================

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """
    Start sensor monitoring
    
    Initiates the connection to sensors (MQTT or Serial) and begins processing
    incoming sensor data. This endpoint must be called before the system can
    detect machine states.
    
    URL: POST /api/monitoring/start
    
    Returns:
        JSON: Status message
        
    Response Format (Success):
        {
            "status": "success",
            "message": "Monitoring started"
        }
    
    Response Format (Error):
        {
            "status": "error",
            "message": "Failed to start monitoring"
        }
    
    Status Codes:
        200: Monitoring started successfully
        500: Failed to start monitoring
    
    Side Effects:
        - Connects to MQTT broker or serial port
        - Starts background thread for message processing
        - Begins updating machine states in database
    
    Example:
        curl -X POST http://localhost:5000/api/monitoring/start
    """
    if interface.start_monitoring(app):
        return jsonify({'status': 'success', 'message': 'Monitoring started'})
    return jsonify({'status': 'error', 'message': 'Failed to start monitoring'}), 500


@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """
    Stop sensor monitoring
    
    Stops the monitoring system and disconnects from sensors. Machine states
    will no longer be updated until monitoring is restarted.
    
    URL: POST /api/monitoring/stop
    
    Returns:
        JSON: Status message
        
    Response Format:
        {
            "status": "success",
            "message": "Monitoring stopped"
        }
    
    Status Codes:
        200: Success
    
    Side Effects:
        - Disconnects from MQTT broker or serial port
        - Stops background processing thread
        - Machine states frozen at last known values
    
    Example:
        curl -X POST http://localhost:5000/api/monitoring/stop
    """
    interface.stop_monitoring()
    return jsonify({'status': 'success', 'message': 'Monitoring stopped'})


@app.route('/api/monitoring/status', methods=['GET'])
def monitoring_status():
    """
    Get current monitoring status
    
    Returns information about the monitoring system state, including whether
    it's currently running and connection details.
    
    URL: GET /api/monitoring/status
    
    Returns:
        JSON: Status information object
        
    Response Format (MQTT mode):
        {
            "running": true,
            "mode": "mqtt",
            "broker": "localhost:1883"
        }
    
    Response Format (Serial mode):
        {
            "running": true,
            "mode": "serial",
            "port": "/dev/ttyUSB0"
        }
    
    Status Codes:
        200: Success
    
    Example:
        curl http://localhost:5000/api/monitoring/status
    """
    status_info = {
        'running': interface.running,
    }
    
    # Add mode-specific information
    if app.config['USE_MQTT']:
        status_info['mode'] = 'mqtt'
        status_info['broker'] = f"{app.config['MQTT_BROKER_HOST']}:{app.config['MQTT_BROKER_PORT']}"
    else:
        status_info['mode'] = 'serial'
        status_info['port'] = interface.port
    
    return jsonify(status_info)


# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == '__main__':
    """
    Main entry point when running app directly
    
    This block is executed only when the script is run directly (not imported).
    It starts the Flask development server with appropriate configuration.
    
    Configuration:
        - Debug mode: Enabled only in development environment
        - Host: 0.0.0.0 (accessible from network)
        - Port: 5000 (default Flask port)
    
    Production Note:
        For production deployment, use a production WSGI server instead:
        gunicorn -w 4 -b 0.0.0.0:5000 app:app
    
    Security Note:
        Debug mode is automatically disabled in production (when FLASK_ENV != 'development')
        to prevent security vulnerabilities.
    """
    # Determine debug mode based on environment
    # Debug mode enables:
    #   - Auto-reload on code changes
    #   - Detailed error pages with stack traces
    #   - Interactive debugger in browser
    # WARNING: Never enable debug mode in production!
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # Start Flask development server
    # host='0.0.0.0' makes server accessible from other machines on network
    # In production, this should be handled by a WSGI server like gunicorn
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)

