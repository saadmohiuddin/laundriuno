"""
Arduino Simulator for testing Laundriuno without hardware
This script simulates Arduino serial output to test the system
"""
import sys
import time
import random

def simulate_arduino():
    """Simulate Arduino sending machine status updates"""
    
    print("READY", flush=True)
    time.sleep(1)
    
    # Simulate 4 machines with random state changes
    num_machines = 4
    machine_states = [False] * num_machines
    
    print("Arduino Simulator Started - Simulating 4 machines")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        cycle = 0
        while True:
            cycle += 1
            print(f"\nCycle {cycle}:", file=sys.stderr)
            
            # Randomly change machine states
            for machine_id in range(num_machines):
                # 10% chance of state change each cycle
                if random.random() < 0.1:
                    machine_states[machine_id] = not machine_states[machine_id]
                    status = "IN_USE" if machine_states[machine_id] else "FREE"
                    message = f"MACHINE:{machine_id}:{status}"
                    print(message, flush=True)
                    print(f"  -> {message}", file=sys.stderr)
            
            # Wait before next cycle
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nSimulator stopped", file=sys.stderr)

if __name__ == '__main__':
    print("Laundriuno Arduino Simulator", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    simulate_arduino()
