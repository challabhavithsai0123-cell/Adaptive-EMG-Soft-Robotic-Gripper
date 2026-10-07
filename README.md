# Simulation of an EMG-Controlled Adaptive Soft Robotic Gripper Using SOFA

## Overview

This project presents a simulation-based proof of concept for an EMG-controlled adaptive soft robotic gripper.

A synthetic surface EMG (sEMG) signal is generated and processed using RMS analysis. The measured EMG intensity is classified into LOW, MEDIUM, and HIGH activity levels. These states are mapped to different pneumatic pressure commands to control a three-finger PneuNet soft robotic gripper simulated in SOFA.

The project demonstrates the complete control chain:

Synthetic EMG → RMS Processing → EMG Classification → Adaptive Pressure → PneuNet Actuation → Virtual Object Grasping

## Objectives

- Generate and process a synthetic EMG signal.
- Calculate RMS-based EMG intensity.
- Classify muscle activity into LOW, MEDIUM, and HIGH states.
- Map EMG activity to adaptive pneumatic pressure commands.
- Simulate a three-finger PneuNet gripper using SOFA.
- Demonstrate adaptive grasping of a virtual object.
- Record simulation data for analysis and visualization.

## System Architecture

```text
              Synthetic EMG Signal
                       │
                       ▼
                Rectification
                       │
                       ▼
                 RMS Calculation
                       │
                       ▼
              EMG State Classification
                 ┌─────┼─────┐
                 ▼     ▼     ▼
                LOW  MEDIUM  HIGH
                 │     │     │
                 ▼     ▼     ▼
               0.00   0.25   0.40
                 │     │     │
                 └─────┼─────┘
                       ▼
              PneuNet Pressure Control
                       │
                       ▼
             Three-Finger Soft Gripper
                       │
                       ▼
              Virtual Object Grasping