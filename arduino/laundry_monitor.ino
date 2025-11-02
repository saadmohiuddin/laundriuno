/*
 * Laundriuno - Laundry Machine Monitor
 * 
 * This Arduino sketch monitors washing/drying machines using vibration sensors
 * and communicates machine status via serial connection to the Flask app.
 * 
 * Hardware:
 * - Arduino Uno/Nano
 * - SW-420 Vibration Sensors (or similar)
 * - Connect sensor digital outputs to pins 2-5 (supports up to 4 machines)
 */

// Pin definitions for up to 4 machines
const int MACHINE_PINS[] = {2, 3, 4, 5};
const int NUM_MACHINES = 4;

// Threshold for considering machine as "in use"
const int VIBRATION_THRESHOLD = 5;  // Number of vibrations in CHECK_INTERVAL
const unsigned long CHECK_INTERVAL = 5000;  // Check every 5 seconds

// Machine states
struct Machine {
  int pin;
  int vibrationCount;
  bool inUse;
  unsigned long lastCheckTime;
};

Machine machines[NUM_MACHINES];

void setup() {
  Serial.begin(9600);
  
  // Initialize machine pins and states
  for (int i = 0; i < NUM_MACHINES; i++) {
    machines[i].pin = MACHINE_PINS[i];
    machines[i].vibrationCount = 0;
    machines[i].inUse = false;
    machines[i].lastCheckTime = 0;
    pinMode(machines[i].pin, INPUT);
  }
  
  Serial.println("READY");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Count vibrations for each machine
  for (int i = 0; i < NUM_MACHINES; i++) {
    if (digitalRead(machines[i].pin) == HIGH) {
      machines[i].vibrationCount++;
      delay(50);  // Debounce
    }
  }
  
  // Check if it's time to evaluate machine status
  for (int i = 0; i < NUM_MACHINES; i++) {
    if (currentTime - machines[i].lastCheckTime >= CHECK_INTERVAL) {
      bool previousState = machines[i].inUse;
      
      // Determine if machine is in use based on vibration count
      machines[i].inUse = (machines[i].vibrationCount >= VIBRATION_THRESHOLD);
      
      // Report status change
      if (machines[i].inUse != previousState) {
        Serial.print("MACHINE:");
        Serial.print(i);
        Serial.print(":");
        Serial.println(machines[i].inUse ? "IN_USE" : "FREE");
      }
      
      // Reset for next interval
      machines[i].vibrationCount = 0;
      machines[i].lastCheckTime = currentTime;
    }
  }
  
  // Handle serial commands from Flask app
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "STATUS") {
      // Send status of all machines
      for (int i = 0; i < NUM_MACHINES; i++) {
        Serial.print("MACHINE:");
        Serial.print(i);
        Serial.print(":");
        Serial.println(machines[i].inUse ? "IN_USE" : "FREE");
      }
    } else if (command == "PING") {
      Serial.println("PONG");
    }
  }
  
  delay(100);
}
