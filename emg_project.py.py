import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d

# ============================================================
# 1. BASIC SETTINGS
# ============================================================

fs = 2000                  # Sampling frequency: 2000 Hz
duration = 10              # Signal duration: 10 seconds
t = np.arange(0, duration, 1 / fs)

# Fixed random seed so the same EMG is generated every time
rng = np.random.default_rng(42)


# ============================================================
# 2. DEFINE MUSCLE ACTIVATION LEVEL
# ============================================================

# 0–2 s       -> LOW
# 2–5 s       -> MEDIUM
# 5–6.5 s     -> LOW
# 6.5–9 s     -> HIGH
# 9–10 s      -> LOW

activation = np.zeros_like(t)

activation[(t >= 0) & (t < 2)] = 0.10
activation[(t >= 2) & (t < 5)] = 0.38
activation[(t >= 5) & (t < 6.5)] = 0.10
activation[(t >= 6.5) & (t < 9)] = 0.80
activation[(t >= 9) & (t <= 10)] = 0.08


# ============================================================
# 3. GENERATE SYNTHETIC RAW EMG
# ============================================================

# Several frequency components to make the signal
# look more like a noisy EMG waveform.

emg_component = (
    0.55 * np.sin(2 * np.pi * 80 * t)
    + 0.30 * np.sin(2 * np.pi * 125 * t)
    + 0.18 * np.sin(2 * np.pi * 180 * t)
)

# Random electrical/muscle noise
noise = rng.normal(0, 1, len(t))

# Combine EMG components and noise
raw_emg = activation * (emg_component + 0.65 * noise)

# Small baseline noise even when muscle is relaxed
raw_emg += rng.normal(0, 0.035, len(t))


# ============================================================
# 4. RECTIFICATION
# ============================================================

# Full-wave rectification
# Negative values become positive.

rectified_emg = np.abs(raw_emg)


# ============================================================
# 5. RMS ENVELOPE
# ============================================================

# RMS window = 100 ms
rms_window = int(0.100 * fs)

# RMS calculation
squared_signal = rectified_emg ** 2

rms_envelope = np.sqrt(
    uniform_filter1d(
        squared_signal,
        size=rms_window,
        mode="nearest"
    )
)


# ============================================================
# 6. EMG CLASSIFICATION THRESHOLDS
# ============================================================

LOW_MEDIUM_CUTOFF = 0.15
MEDIUM_HIGH_CUTOFF = 0.55

# Classification
emg_class = np.full(len(t), "LOW", dtype=object)

emg_class[
    (rms_envelope >= LOW_MEDIUM_CUTOFF)
    & (rms_envelope < MEDIUM_HIGH_CUTOFF)
] = "MEDIUM"

emg_class[rms_envelope >= MEDIUM_HIGH_CUTOFF] = "HIGH"


# ============================================================
# 7. PRESSURE MAPPING
# ============================================================

LOW_PRESSURE = 5
MEDIUM_PRESSURE = 25
HIGH_PRESSURE = 45

pressure = np.zeros_like(t)

pressure[emg_class == "LOW"] = LOW_PRESSURE
pressure[emg_class == "MEDIUM"] = MEDIUM_PRESSURE
pressure[emg_class == "HIGH"] = HIGH_PRESSURE


# ============================================================
# 8. CREATE THE COMPLETE FIGURE
# ============================================================

fig, axes = plt.subplots(
    3,
    1,
    figsize=(14, 12),
    sharex=True,
    gridspec_kw={"height_ratios": [1, 1, 1.15]}
)

fig.suptitle(
    "EMG Signal Processing & Pneumatic Pressure Mapping",
    fontsize=18,
    fontweight="bold"
)


# ============================================================
# 9. TOP GRAPH — RAW EMG
# ============================================================

axes[0].plot(
    t,
    raw_emg,
    linewidth=0.5,
    color="darkslategray",
    label="Raw Synthetic sEMG"
)

axes[0].set_ylabel(
    "Amplitude [mV]",
    fontsize=12,
    fontweight="bold"
)

axes[0].set_title(
    "Synthetic Surface EMG Signal",
    fontsize=13
)

axes[0].grid(
    True,
    linestyle="--",
    alpha=0.6
)

axes[0].legend(
    loc="upper right"
)


# ============================================================
# 10. MIDDLE GRAPH — RECTIFIED EMG + RMS
# ============================================================

axes[1].plot(
    t,
    rectified_emg,
    linewidth=0.4,
    color="lightgray",
    label="Rectified EMG"
)

axes[1].plot(
    t,
    rms_envelope,
    linewidth=2,
    color="tab:blue",
    label="RMS Envelope (100 ms)"
)

# LOW/MEDIUM threshold
axes[1].axhline(
    LOW_MEDIUM_CUTOFF,
    linestyle="--",
    linewidth=1.5,
    color="tab:orange",
    label="Low/Med Cutoff (0.15 mV)"
)

# MEDIUM/HIGH threshold
axes[1].axhline(
    MEDIUM_HIGH_CUTOFF,
    linestyle="--",
    linewidth=1.5,
    color="tab:red",
    label="Med/High Cutoff (0.55 mV)"
)

axes[1].set_ylabel(
    "RMS Value [mV]",
    fontsize=12,
    fontweight="bold"
)

axes[1].set_title(
    "EMG Rectification, RMS Envelope & Classification Thresholds",
    fontsize=13
)

axes[1].grid(
    True,
    linestyle="--",
    alpha=0.6
)

axes[1].legend(
    loc="upper left"
)


# ============================================================
# 11. BOTTOM GRAPH — PRESSURE MAPPING
# ============================================================

axes[2].step(
    t,
    pressure,
    where="post",
    linewidth=3,
    color="tab:green",
    label="Mapped Pressure P(t)"
)

# Fill only below the pressure curve
axes[2].fill_between(
    t,
    0,
    pressure,
    step="post",
    alpha=0.15,
    color="tab:green"
)

axes[2].set_ylabel(
    "Pressure [kPa]",
    fontsize=12,
    fontweight="bold"
)

axes[2].set_xlabel(
    "Time [s]",
    fontsize=12,
    fontweight="bold"
)

axes[2].set_title(
    "EMG-to-Pneumatic Pressure Mapping",
    fontsize=13
)

# Make the pressure levels very clear
axes[2].set_ylim(0, 55)
axes[2].set_yticks([0, 5, 10, 20, 30, 40, 45, 50])

axes[2].set_yticks([0, 5, 25, 45, 50])

axes[2].grid(
    True,
    linestyle="--",
    alpha=0.6
)

axes[2].legend(
    loc="upper right"
)

# ============================================================
# 12. COMMON X-AXIS
# ============================================================

axes[2].set_xticks(
    np.arange(0, 11, 2)
)

plt.tight_layout(
    rect=[0, 0, 1, 0.95],
    h_pad=2.0
)


# ============================================================
# 13. SAVE THE COMPLETE GRAPH
# ============================================================

plt.savefig(
    "EMG_complete_project_graph.png",
    dpi=300,
    bbox_inches="tight"
)


# ============================================================
# 14. DISPLAY THE GRAPH
# ============================================================

plt.show()


# ============================================================
# 15. PRINT IMPORTANT INFORMATION
# ============================================================

print("\n========================================")
print("       EMG PROJECT SIMULATION")
print("========================================")

print("\nEMG Classification:")
print("----------------------------------------")
print("LOW       : RMS < 0.15 mV")
print("MEDIUM    : 0.15 <= RMS < 0.55 mV")
print("HIGH      : RMS >= 0.55 mV")

print("\nPressure Mapping:")
print("----------------------------------------")
print("LOW       -> 5 kPa")
print("MEDIUM    -> 25 kPa")
print("HIGH      -> 45 kPa")

print("\nSignal Timing:")
print("----------------------------------------")
print("0.0 – 2.0 s   : LOW")
print("2.0 – 5.0 s   : MEDIUM")
print("5.0 – 6.5 s   : LOW")
print("6.5 – 9.0 s   : HIGH")
print("9.0 – 10.0 s  : LOW")

print("\nGraph saved as:")
print("EMG_complete_project_graph.png")

print("========================================")