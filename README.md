# QGIS Gesture Control

A hand gesture based control system for QGIS navigation built with Python.

This project explores gesture based interaction as an alternative input method for GIS workflows, with a focus on usability, stability, and real-world testing inside QGIS.

Make sure your webcam is connected and QGIS is open before running the application.

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

```bash
pip install -r requirements.txt
