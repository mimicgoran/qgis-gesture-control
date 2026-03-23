# QGIS Gesture Control

Hand gesture based control system for QGIS navigation using Python.  This project explores hand gesture based interaction as an alternative way to control QGIS navigation, with a focus on accessibility and experimental GIS workflows. Make sure your webcam is connected and QGIS is open.

## Features

- Pointer control
- Dwell click
- Pan and zoom
- Gesture based interaction

  ## How it works

The system uses MediaPipe for hand tracking and OpenCV for video processing. 
Recognized gestures are translated into mouse actions using PyAutoGUI to control QGIS navigation.

Supported interactions include:
- Pointer movement using index finger
- Dwell based clicking
- Pan using closed fist
- Zoom using two hand distance

  ## Gesture Controls

- Open hand → Navigation mode
- Index finger → Pointer control
- Closed fist → Pan
- Two open hands → Zoom in or zoom out based on the distance between hands

## Installation

pip install -r requirements.txt

## Usage

Run the application:

python -m src.qgis_gesture_control.main
