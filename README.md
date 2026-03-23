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

## Development Notes

### Design Thinking

The project started as a sandbox experiment for gesture recognition, but the main goal quickly shifted toward evaluating whether hand gestures can realistically support everyday QGIS workflows.

Instead of introducing a large number of gestures, the system was intentionally limited to a small set of core interactions:

- pointer control  
- dwell click  
- navigation mode  
- pan  
- zoom  

The focus was on usability and reliability in a real GIS environment rather than feature complexity.

A configuration-driven approach was used so that parameters such as smoothing, dwell timing, and pan sensitivity could be tuned without modifying the core logic.

To accelerate development, the system initially relies on OS-level mouse control rather than a native QGIS plugin, allowing faster iteration and real-world validation.

---

### Challenges and Obstacles

The main challenge was not gesture detection itself, but achieving reliable behavior inside QGIS.

Key issues encountered:

- Gestures that worked in the sandbox did not always behave the same way in QGIS  
- Pan behavior was initially unstable due to cursor drift  
- QGIS tool context affected interaction reliability  
- Zoom required precise cursor positioning to work consistently  
- Temporary tracking loss caused interruptions in pan mode  
- Dwell timing required balancing responsiveness and accidental clicks  

The core difficulty was making the interaction feel natural within a desktop GIS workflow.

---

### Why Pinch Gesture Was Rejected

Pinch gesture was initially tested as a candidate for click and interaction control.

However, it proved unsuitable due to:

- high sensitivity to camera angle and hand orientation  
- inconsistent detection in real usage  
- physical strain during repeated use  
- conflicts with pointer interaction  
- poor performance for continuous actions  

Because of these limitations, pinch was removed in favor of more stable interaction patterns.

---

### Why Click Gesture Was Replaced with Dwell Click

Direct gesture-based clicking was also tested but showed several problems:

- unreliable detection of fast gesture transitions  
- frequent accidental clicks  
- physically tiring for repeated use  
- interference with other gesture modes  
- inconsistent timing behavior  

Dwell click was introduced as a more stable alternative.

It provided:

- better control  
- more predictable behavior  
- reduced physical effort  
- easier parameter tuning  

---

### What Was Tested

Testing focused on real QGIS workflows rather than sandbox-only behavior.

Scenarios included:

- pointer precision for UI elements and map features  
- dwell click timing and reliability  
- transitions between pointer, navigation, and pan  
- repeated pan cycles and stability  
- pan behavior with different active QGIS tools  
- zoom responsiveness and consistency  
- zoom behavior after pan  
- behavior when QGIS is opened without prior interaction  
- robustness during tracking loss  
- overall mode switching reliability  

---

### Key Design Decisions in Final Version

- Pan starts from screen center for consistent control  
- Middle mouse drag ensures tool-independent pan  
- Pan includes tolerance for short tracking loss  
- Pan exits immediately on open hand  
- Zoom repositions cursor to a reliable map area  
- Dwell click timing was reduced for responsiveness  
- Pointer smoothing balances precision and stability  
- Config-based tuning enables fast iteration  

---

### Why This Version Was Chosen

This version was selected because it provides the best balance between:

- stability  
- responsiveness  
- simplicity  
- practical usability  

Earlier versions either lacked stability or introduced unnecessary complexity.

The final approach focuses on a minimal set of robust gestures that work reliably in real QGIS interaction scenarios.

---

## Installation

```bash
pip install -r requirements.txt
