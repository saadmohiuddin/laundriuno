from datetime import datetime, timedelta
from models import Machine, MachineSession
from sqlalchemy import func

class AnalyticsService:
    """Service for analyzing machine usage and making recommendations"""
    
    @staticmethod
    def get_machine_status(machine_id=None):
        """Get current status of machines"""
        if machine_id:
            machines = Machine.query.filter_by(id=machine_id).all()
        else:
            machines = Machine.query.all()
        
        result = []
        for machine in machines:
            result.append({
                'id': machine.id,
                'name': machine.name,
                'is_running': machine.is_running,
                'last_status_change': machine.last_status_change.isoformat() if machine.last_status_change else None
            })
        
        return result
    
    @staticmethod
    def get_available_machines():
        """Get list of currently available (not running) machines"""
        machines = Machine.query.filter_by(is_running=False).all()
        return [{'id': m.id, 'name': m.name} for m in machines]
    
    @staticmethod
    def get_machine_history(machine_id, days=7):
        """Get usage history for a specific machine"""
        start_date = datetime.utcnow() - timedelta(days=days)
        sessions = MachineSession.query.filter(
            MachineSession.machine_id == machine_id,
            MachineSession.start_time >= start_date
        ).order_by(MachineSession.start_time.desc()).all()
        
        result = []
        for session in sessions:
            result.append({
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'duration': session.duration
            })
        
        return result
    
    @staticmethod
    def get_usage_statistics(days=7):
        """Get overall usage statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all completed sessions in the time period
        sessions = MachineSession.query.filter(
            MachineSession.start_time >= start_date,
            MachineSession.end_time.isnot(None)
        ).all()
        
        if not sessions:
            return {
                'total_sessions': 0,
                'average_duration': 0,
                'total_usage_time': 0,
                'busiest_hours': []
            }
        
        total_duration = sum(s.duration for s in sessions if s.duration)
        avg_duration = total_duration / len(sessions) if sessions else 0
        
        # Calculate busiest hours
        hour_counts = {}
        for session in sessions:
            hour = session.start_time.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        busiest_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_sessions': len(sessions),
            'average_duration': int(avg_duration),
            'total_usage_time': total_duration,
            'busiest_hours': [{'hour': h, 'count': c} for h, c in busiest_hours]
        }
    
    @staticmethod
    def get_best_times(days=7, target_hour_range=None):
        """
        Recommend best times to do laundry based on historical usage
        Returns hours with lowest usage
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all sessions in the time period
        sessions = MachineSession.query.filter(
            MachineSession.start_time >= start_date,
            MachineSession.end_time.isnot(None)
        ).all()
        
        if not sessions:
            return {
                'recommended_hours': list(range(0, 24)),
                'message': 'No historical data available. All times are equally good.'
            }
        
        # Count sessions by hour
        hour_counts = {}
        for hour in range(24):
            hour_counts[hour] = 0
        
        for session in sessions:
            hour = session.start_time.hour
            hour_counts[hour] += 1
        
        # Sort hours by usage (ascending)
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1])
        
        # Get top 5 least busy hours
        best_hours = [h for h, c in sorted_hours[:5]]
        
        # Format hour ranges for readability
        best_times = []
        for hour in sorted(best_hours):
            time_str = f"{hour:02d}:00 - {(hour+1)%24:02d}:00"
            best_times.append({
                'hour': hour,
                'time_range': time_str,
                'usage_count': hour_counts[hour]
            })
        
        return {
            'recommended_times': best_times,
            'message': f'These are the least busy times based on the last {days} days of data.'
        }
    
    @staticmethod
    def get_hourly_availability(days=7):
        """Get average machine availability by hour"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        sessions = MachineSession.query.filter(
            MachineSession.start_time >= start_date,
            MachineSession.end_time.isnot(None)
        ).all()
        
        total_machines = Machine.query.count()
        
        # Calculate usage by hour
        hour_usage = {hour: 0 for hour in range(24)}
        
        for session in sessions:
            hour = session.start_time.hour
            hour_usage[hour] += 1
        
        # Calculate average availability
        availability = []
        for hour in range(24):
            avg_used = hour_usage[hour] / days if days > 0 else 0
            avg_available = max(0, total_machines - avg_used)
            availability.append({
                'hour': hour,
                'time_range': f"{hour:02d}:00 - {(hour+1)%24:02d}:00",
                'avg_available': round(avg_available, 1),
                'avg_in_use': round(avg_used, 1)
            })
        
        return availability
