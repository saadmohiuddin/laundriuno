"""
Laundriuno Flask Application
Main application file for laundry machine monitoring system
"""
import os
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from app.arduino_interface import ArduinoInterface
from app.data_store import DataStore
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get absolute paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / 'templates'
STATIC_DIR = BASE_DIR / 'static'

# Initialize Flask app
app = Flask(__name__, 
            template_folder=str(TEMPLATE_DIR),
            static_folder=str(STATIC_DIR))
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['ARDUINO_PORT'] = os.environ.get('ARDUINO_PORT', '/dev/ttyUSB0')
app.config['ARDUINO_BAUD_RATE'] = int(os.environ.get('ARDUINO_BAUD_RATE', 9600))

# Initialize components
data_store = DataStore()
arduino = ArduinoInterface(
    port=app.config['ARDUINO_PORT'],
    baud_rate=app.config['ARDUINO_BAUD_RATE'],
    data_store=data_store
)

@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current status of all machines"""
    try:
        status = data_store.get_all_status()
        return jsonify({
            'success': True,
            'machines': status,
            'connected': arduino.is_connected()
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/machine/<int:machine_id>')
def get_machine_status(machine_id):
    """Get status of a specific machine"""
    try:
        status = data_store.get_machine_status(machine_id)
        if status is None:
            return jsonify({
                'success': False,
                'error': 'Machine not found'
            }), 404
        
        return jsonify({
            'success': True,
            'machine': status
        })
    except Exception as e:
        logger.error(f"Error getting machine {machine_id} status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/history/<int:machine_id>')
def get_machine_history(machine_id):
    """Get usage history for a specific machine"""
    try:
        history = data_store.get_machine_history(machine_id)
        return jsonify({
            'success': True,
            'history': history
        })
    except Exception as e:
        logger.error(f"Error getting machine {machine_id} history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/arduino/connect', methods=['POST'])
def connect_arduino():
    """Manually trigger Arduino connection"""
    try:
        if arduino.connect():
            return jsonify({
                'success': True,
                'message': 'Connected to Arduino'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to Arduino'
            }), 500
    except Exception as e:
        logger.error(f"Error connecting to Arduino: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/arduino/disconnect', methods=['POST'])
def disconnect_arduino():
    """Disconnect from Arduino"""
    try:
        arduino.disconnect()
        return jsonify({
            'success': True,
            'message': 'Disconnected from Arduino'
        })
    except Exception as e:
        logger.error(f"Error disconnecting from Arduino: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/arduino/status')
def get_arduino_status():
    """Get Arduino connection status"""
    return jsonify({
        'success': True,
        'connected': arduino.is_connected(),
        'port': app.config['ARDUINO_PORT']
    })

@app.route('/api/stats')
def get_stats():
    """Get usage statistics"""
    try:
        stats = data_store.get_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.teardown_appcontext
def shutdown_arduino(exception=None):
    """Cleanup Arduino connection on shutdown"""
    arduino.disconnect()

if __name__ == '__main__':
    try:
        # Attempt to connect to Arduino on startup
        arduino.connect()
        logger.info("Starting Flask application...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        arduino.disconnect()
