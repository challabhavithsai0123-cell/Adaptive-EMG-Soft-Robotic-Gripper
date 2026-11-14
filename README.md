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

## Implementation details and limitations

The current controller generates a **synthetic** EMG-like waveform in the SOFA animation loop; it does not acquire live sEMG from electrodes or an EMG amplifier. The signal uses a 20 Hz carrier with staged amplitude levels and added noise. A 100 ms RMS window is used to estimate activity, followed by threshold-based LOW / MEDIUM / HIGH classification with hysteresis.

The pressure command mapping in the simulation is:

| Classified state | Pressure command |
|---|---:|
| LOW | 0.00 |
| MEDIUM | 0.25 |
| HIGH | 0.40 |

The SOFA scene contains a three-finger PneuNet model and a virtual object. Experiment logging records time, RMS, classified state, pressure command, grip state and virtual cube position.

**Interpretation:** this is a simulation proof of concept for the signal-processing-to-actuation pipeline. The pressure values are simulation commands, not calibrated pneumatic pressures. No physical soft gripper, pneumatic supply, electrode interface or live EMG acquisition is claimed by this repository.

### Next validation steps

1. Replace the synthetic waveform with recorded or live EMG after adding an isolated, appropriately conditioned acquisition interface.
2. Establish subject/session-separated calibration and thresholds rather than relying on fixed synthetic-signal levels.
3. Validate pressure-to-finger deformation in SOFA and document solver settings and material assumptions.
4. Compare grasp outcomes across repeatable object sizes and masses.
5. Only describe a physical prototype after hardware and pneumatic tests have been completed and documented.

