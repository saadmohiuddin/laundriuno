from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Machine(db.Model):
    """Model for laundry machines"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    is_running = db.Column(db.Boolean, default=False)
    last_status_change = db.Column(db.DateTime, default=datetime.utcnow)
    
    sessions = db.relationship('MachineSession', backref='machine', lazy=True)
    
    def __repr__(self):
        return f'<Machine {self.name}>'

class MachineSession(db.Model):
    """Model for tracking machine usage sessions"""
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # duration in seconds
    
    def __repr__(self):
        return f'<MachineSession machine_id={self.machine_id} start={self.start_time}>'

class SensorReading(db.Model):
    """Model for storing sensor readings"""
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machine.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    acceleration_x = db.Column(db.Float)
    acceleration_y = db.Column(db.Float)
    acceleration_z = db.Column(db.Float)
    vibration_magnitude = db.Column(db.Float)
    
    def __repr__(self):
        return f'<SensorReading machine_id={self.machine_id} timestamp={self.timestamp}>'
