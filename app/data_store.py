"""
Data Store Module
Manages machine status data and history
"""
import threading
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataStore:
    """Store and manage laundry machine status data"""
    
    def __init__(self, num_machines=4):
        """
        Initialize data store
        
        Args:
            num_machines: Number of machines to track
        """
        self.num_machines = num_machines
        self.lock = threading.Lock()
        
        # Initialize machine data
        self.machines = {}
        for i in range(num_machines):
            self.machines[i] = {
                'id': i,
                'in_use': False,
                'last_updated': None,
                'last_state_change': None,
                'total_uses': 0,
                'total_time_used': 0  # in seconds
            }
        
        # History tracking
        self.history = {i: [] for i in range(num_machines)}
        self.max_history_entries = 100
    
    def update_machine_status(self, machine_id, in_use):
        """
        Update the status of a machine
        
        Args:
            machine_id: ID of the machine
            in_use: Boolean indicating if machine is in use
        """
        with self.lock:
            if machine_id not in self.machines:
                logger.warning(f"Invalid machine ID: {machine_id}")
                return
            
            machine = self.machines[machine_id]
            previous_status = machine['in_use']
            current_time = datetime.now()
            
            # Update status
            machine['in_use'] = in_use
            machine['last_updated'] = current_time
            
            # If status changed, record it
            if previous_status != in_use:
                machine['last_state_change'] = current_time
                
                # Track usage statistics
                if in_use:
                    # Machine started
                    machine['total_uses'] += 1
                    self._add_history_entry(machine_id, 'started', current_time)
                else:
                    # Machine finished
                    if machine['last_state_change']:
                        # Calculate duration
                        duration = (current_time - machine['last_state_change']).total_seconds()
                        machine['total_time_used'] += duration
                    self._add_history_entry(machine_id, 'finished', current_time)
                
                logger.info(f"Machine {machine_id} status changed to {'IN_USE' if in_use else 'FREE'}")
    
    def _add_history_entry(self, machine_id, event, timestamp):
        """Add entry to machine history"""
        entry = {
            'event': event,
            'timestamp': timestamp.isoformat(),
            'timestamp_display': timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.history[machine_id].append(entry)
        
        # Limit history size
        if len(self.history[machine_id]) > self.max_history_entries:
            self.history[machine_id] = self.history[machine_id][-self.max_history_entries:]
    
    def get_machine_status(self, machine_id):
        """
        Get status of a specific machine
        
        Args:
            machine_id: ID of the machine
            
        Returns:
            dict: Machine status or None if not found
        """
        with self.lock:
            if machine_id not in self.machines:
                return None
            
            machine = self.machines[machine_id].copy()
            
            # Convert datetime to string for JSON serialization
            if machine['last_updated']:
                machine['last_updated'] = machine['last_updated'].isoformat()
            if machine['last_state_change']:
                machine['last_state_change'] = machine['last_state_change'].isoformat()
            
            return machine
    
    def get_all_status(self):
        """
        Get status of all machines
        
        Returns:
            list: List of machine status dictionaries
        """
        with self.lock:
            result = []
            for machine_id in sorted(self.machines.keys()):
                machine = self.machines[machine_id].copy()
                
                # Convert datetime to string for JSON serialization
                if machine['last_updated']:
                    machine['last_updated'] = machine['last_updated'].isoformat()
                if machine['last_state_change']:
                    machine['last_state_change'] = machine['last_state_change'].isoformat()
                
                result.append(machine)
            
            return result
    
    def get_machine_history(self, machine_id, limit=50):
        """
        Get history for a specific machine
        
        Args:
            machine_id: ID of the machine
            limit: Maximum number of history entries to return
            
        Returns:
            list: List of history entries
        """
        with self.lock:
            if machine_id not in self.history:
                return []
            
            history = self.history[machine_id][-limit:]
            return history
    
    def get_statistics(self):
        """
        Get overall usage statistics
        
        Returns:
            dict: Statistics summary
        """
        with self.lock:
            total_uses = sum(m['total_uses'] for m in self.machines.values())
            total_time = sum(m['total_time_used'] for m in self.machines.values())
            machines_in_use = sum(1 for m in self.machines.values() if m['in_use'])
            
            # Calculate average time per use
            avg_time_per_use = total_time / total_uses if total_uses > 0 else 0
            
            return {
                'total_uses': total_uses,
                'total_time_hours': round(total_time / 3600, 2),
                'machines_in_use': machines_in_use,
                'machines_free': self.num_machines - machines_in_use,
                'avg_time_per_use_minutes': round(avg_time_per_use / 60, 2)
            }
