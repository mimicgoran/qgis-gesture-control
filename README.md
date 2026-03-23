# QGIS Gesture Control

A hand gesture based control system for QGIS navigation built with Python.

This project explores gesture based interaction as an alternative input method for GIS workflows, with a focus on usability, stability, and real-world testing inside QGIS. The application runs without displaying the live camera feed. While it is active, a small red REC indicator is visible in the system tray, signaling that the webcam is in use. The session can be closed at any time through the tray menu by selecting "End session".

Make sure your webcam lid is open and QGIS is running before starting the application. If QGIS is not open, nothing critical will happen, and some features will still work at the OS level.

---

## Features

- Pointer control using hand tracking  
- Dwell click for hands-free interaction  
- Pan using hand gestures  
- Zoom using two-hand distance  
- Gesture-based navigation mode switching  
- Config-based tuning for interaction behavior  

---

## How it works

The system uses MediaPipe for hand tracking and OpenCV for video processing. Recognized gestures are translated into mouse actions using PyAutoGUI to control QGIS navigation.

The current implementation operates at the OS level, allowing fast testing and validation of gesture behavior without requiring a native QGIS plugin.

---

## Supported Interactions

- Pointer movement using index finger  
- Dwell-based clicking  
- Pan using closed fist  
- Zoom using distance between two hands  

---

## Gesture Controls

- Open hand → Navigation mode  
- Index finger → Pointer control  
- Closed fist → Pan  
- Two open hands → Zoom in or zoom out based on hand distance  

---

## Installation

pip install -r requirements.txt

## Usage

Run the application:

python -m src.qgis_gesture_control.main
