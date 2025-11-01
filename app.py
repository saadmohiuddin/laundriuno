from flask import Flask, jsonify, request, render_template
from config import Config
from models import db, Machine
from arduino_interface import ArduinoInterface
from analytics import AnalyticsService
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize Arduino interface
arduino = ArduinoInterface(
    port=app.config['ARDUINO_PORT'],
    baud_rate=app.config['ARDUINO_BAUD_RATE'],
    vibration_threshold=app.config['VIBRATION_THRESHOLD'],
    idle_timeout=app.config['IDLE_TIMEOUT']
)

# Initialize database and machines
with app.app_context():
    db.create_all()
    
    # Create machines if they don't exist
    if Machine.query.count() == 0:
        for i in range(1, app.config['NUM_MACHINES'] + 1):
            machine = Machine(name=f"Machine {i}")
            db.session.add(machine)
        db.session.commit()
        print(f"Created {app.config['NUM_MACHINES']} machines")

# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/machines', methods=['GET'])
def get_machines():
    """Get status of all machines"""
    status = AnalyticsService.get_machine_status()
    return jsonify(status)

@app.route('/api/machines/<int:machine_id>', methods=['GET'])
def get_machine(machine_id):
    """Get status of a specific machine"""
    status = AnalyticsService.get_machine_status(machine_id)
    if not status:
        return jsonify({'error': 'Machine not found'}), 404
    return jsonify(status[0])

@app.route('/api/machines/available', methods=['GET'])
def get_available():
    """Get list of available machines"""
    available = AnalyticsService.get_available_machines()
    return jsonify({
        'count': len(available),
        'machines': available
    })

@app.route('/api/machines/<int:machine_id>/history', methods=['GET'])
def get_machine_history(machine_id):
    """Get usage history for a specific machine"""
    days = request.args.get('days', default=7, type=int)
    history = AnalyticsService.get_machine_history(machine_id, days)
    return jsonify({
        'machine_id': machine_id,
        'days': days,
        'sessions': history
    })

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get overall usage statistics"""
    days = request.args.get('days', default=7, type=int)
    stats = AnalyticsService.get_usage_statistics(days)
    return jsonify(stats)

@app.route('/api/best-times', methods=['GET'])
def get_best_times():
    """Get recommended best times to do laundry"""
    days = request.args.get('days', default=7, type=int)
    best_times = AnalyticsService.get_best_times(days)
    return jsonify(best_times)

@app.route('/api/availability', methods=['GET'])
def get_availability():
    """Get hourly availability forecast"""
    days = request.args.get('days', default=7, type=int)
    availability = AnalyticsService.get_hourly_availability(days)
    return jsonify(availability)

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start Arduino monitoring"""
    if arduino.start_monitoring(app):
        return jsonify({'status': 'success', 'message': 'Monitoring started'})
    return jsonify({'status': 'error', 'message': 'Failed to start monitoring'}), 500

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop Arduino monitoring"""
    arduino.stop_monitoring()
    return jsonify({'status': 'success', 'message': 'Monitoring stopped'})

@app.route('/api/monitoring/status', methods=['GET'])
def monitoring_status():
    """Get monitoring status"""
    return jsonify({
        'running': arduino.running,
        'port': arduino.port
    })

if __name__ == '__main__':
    # Note: In production, monitoring should be started automatically
    # or via a separate process/service
    app.run(debug=True, host='0.0.0.0', port=5000)
