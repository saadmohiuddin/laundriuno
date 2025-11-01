#!/usr/bin/env python3
"""
Laundriuno Demo Script
======================
This script demonstrates the core functionality of the Laundriuno system
by simulating machine usage and showing API responses.
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Machine, MachineSession, SensorReading
from analytics import AnalyticsService

def clear_database():
    """Clear all data from the database"""
    with app.app_context():
        SensorReading.query.delete()
        MachineSession.query.delete()
        db.session.commit()
        print("✓ Database cleared\n")

def generate_sample_data():
    """Generate sample usage data for demonstration"""
    print("Generating sample data...")
    
    with app.app_context():
        machines = Machine.query.all()
        
        # Generate data for the past 7 days
        now = datetime.now()
        
        session_count = 0
        for day in range(7):
            day_start = now - timedelta(days=day)
            
            # Generate 2-4 sessions per machine per day
            for machine in machines:
                num_sessions = random.randint(2, 4)
                
                for _ in range(num_sessions):
                    # Random start time during the day
                    hour = random.randint(6, 22)  # Between 6 AM and 10 PM
                    start_time = day_start.replace(hour=hour, minute=random.randint(0, 59))
                    
                    # Random duration between 30-90 minutes
                    duration = random.randint(1800, 5400)
                    end_time = start_time + timedelta(seconds=duration)
                    
                    session = MachineSession(
                        machine_id=machine.id,
                        start_time=start_time,
                        end_time=end_time,
                        duration=duration
                    )
                    db.session.add(session)
                    session_count += 1
                    
                    # Add some sensor readings
                    for i in range(5):
                        reading_time = start_time + timedelta(seconds=i * 300)
                        reading = SensorReading(
                            machine_id=machine.id,
                            timestamp=reading_time,
                            acceleration_x=random.uniform(-5000, 5000),
                            acceleration_y=random.uniform(-5000, 5000),
                            acceleration_z=random.uniform(-5000, 5000),
                            vibration_magnitude=random.uniform(3000, 8000)
                        )
                        db.session.add(reading)
        
        db.session.commit()
        print(f"✓ Generated {session_count} machine sessions with sensor data\n")

def display_machine_status():
    """Display current machine status"""
    print("=" * 60)
    print("CURRENT MACHINE STATUS")
    print("=" * 60)
    
    with app.app_context():
        status = AnalyticsService.get_machine_status()
        for machine in status:
            status_icon = "🟢" if not machine['is_running'] else "🔴"
            status_text = "Available" if not machine['is_running'] else "In Use"
            print(f"{status_icon} {machine['name']}: {status_text}")
        
        available = AnalyticsService.get_available_machines()
        print(f"\nTotal Available: {len(available)} machines")
    print()

def display_statistics():
    """Display usage statistics"""
    print("=" * 60)
    print("USAGE STATISTICS (Last 7 Days)")
    print("=" * 60)
    
    with app.app_context():
        stats = AnalyticsService.get_usage_statistics(7)
        
        print(f"Total Sessions: {stats['total_sessions']}")
        print(f"Average Duration: {stats['average_duration'] // 60} minutes")
        print(f"Total Usage Time: {stats['total_usage_time'] // 3600:.1f} hours")
        
        if stats['busiest_hours']:
            print("\nBusiest Hours:")
            for hour_data in stats['busiest_hours']:
                print(f"  {hour_data['hour']:02d}:00 - {hour_data['count']} sessions")
    print()

def display_best_times():
    """Display recommended best times"""
    print("=" * 60)
    print("RECOMMENDED TIMES TO DO LAUNDRY")
    print("=" * 60)
    
    with app.app_context():
        best_times = AnalyticsService.get_best_times(7)
        
        if 'recommended_times' in best_times:
            print("\n🌟 Best Times (Least Busy):\n")
            for time_slot in best_times['recommended_times']:
                print(f"  ⏰ {time_slot['time_range']} - {time_slot['usage_count']} average uses")
            
            if best_times.get('message'):
                print(f"\n💡 {best_times['message']}")
        else:
            print(f"\n{best_times.get('message', 'No data available')}")
    print()

def display_hourly_forecast():
    """Display hourly availability forecast"""
    print("=" * 60)
    print("HOURLY AVAILABILITY FORECAST")
    print("=" * 60)
    print()
    
    with app.app_context():
        availability = AnalyticsService.get_hourly_availability(7)
        
        # Show peak hours (6 AM - 11 PM)
        peak_hours = [h for h in availability if 6 <= h['hour'] <= 23]
        
        for hour_data in peak_hours:
            bar_length = int(hour_data['avg_available'] * 10)
            bar = "█" * bar_length
            print(f"{hour_data['time_range']}: {bar} {hour_data['avg_available']:.1f} avg available")
    print()

def display_machine_history(machine_id=1):
    """Display history for a specific machine"""
    print("=" * 60)
    print(f"MACHINE {machine_id} USAGE HISTORY (Last 3 Days)")
    print("=" * 60)
    
    with app.app_context():
        history = AnalyticsService.get_machine_history(machine_id, days=3)
        
        if not history:
            print("No usage history available")
        else:
            for i, session in enumerate(history[:10], 1):
                start = datetime.fromisoformat(session['start_time'])
                duration_min = session['duration'] // 60 if session['duration'] else 0
                print(f"{i}. {start.strftime('%Y-%m-%d %H:%M')} - Duration: {duration_min} min")
    print()

def main():
    """Main demo function"""
    print("\n" + "=" * 60)
    print("🧺 LAUNDRIUNO SYSTEM DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Ask user if they want to generate sample data
    print("This demo will showcase the Laundriuno system functionality.")
    response = input("Generate sample data? (y/n) [default: y]: ").strip().lower()
    
    if response in ['', 'y', 'yes']:
        clear_database()
        generate_sample_data()
    
    # Display all information
    display_machine_status()
    display_statistics()
    display_best_times()
    display_hourly_forecast()
    display_machine_history()
    
    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nTo start the web application, run:")
    print("  python app.py")
    print("\nThen visit: http://localhost:5000")
    print()
    print("To test the API endpoints, run:")
    print("  python test_simulator.py")
    print()

if __name__ == "__main__":
    main()
