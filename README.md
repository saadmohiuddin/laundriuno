🏠 Home Appliance Status Monitor (HASM)

The Home Appliance Status Monitor (HASM) is an Internet of Things (IoT) project designed to track the operational status (On/Off) and door state (Open/Closed) of domestic appliances, specifically a washing machine and a dryer, using an ESP32 microcontroller, MQTT for communication, and a Flask web application for real-time visualization.

✨ Features

Real-Time Status: Instantly see if your washing machine or dryer is running.

Door State Monitoring: Track the door position (Open or Closed) to prevent unattended loads.

MQTT Broker Integration: Uses a standardized MQTT protocol for reliable, low-latency communication between the ESP32 and the web server.

Web Dashboard: A simple, responsive dashboard built with Flask provides the current status at a glance.

Scalable Architecture: Easily expandable to monitor other appliances.

🛠️ Prerequisites

Hardware

Component

Purpose

Notes

ESP32 Dev Board

Microcontroller/Wi-Fi connectivity

Any standard ESP32 or ESP8266 board will work.

Vibration Sensor

Detects when the machine is running

For On/Off status (e.g., SW-420 or similar). Alternatively, a current sensor (like a non-invasive SCT-013) can be used for more reliable power monitoring.

Magnetic Reed Switch

Door Open/Closed status

Placed on the appliance body and door.

Power Supply

To power the ESP32 unit.



Software & Services

MQTT Broker: A running instance of an MQTT broker (e.g., Mosquitto).

Python 3.x: Required for the Flask web application.

Arduino IDE or PlatformIO: For flashing the code onto the ESP32.
