"""
NEURAL-RMF configuration.
Edit this file to match your EEG setup before running the pipeline.
"""

# ── EEG channels ───────────────────────────────────────────────────────────────
# List the channel names exactly as they appear in your EDF/LSL stream.
# Minimum: 4 channels in the frontal-temporal region.
# Recommended for wearable use: ["F7", "T7", "F8", "T8"]
eeg_channels: list[str] = ["F7", "T7", "F8", "T8"]

# ── Sampling rate (Hz) ─────────────────────────────────────────────────────────
# CHB-MIT recordings: 256 Hz
# Siena recordings:   512 Hz
# Adjust to match your hardware.
fs: int = 256

# ── Monitoring mode ────────────────────────────────────────────────────────────
# "saved" → read from a local EDF file (set edf_path below)
# "live"  → receive data from an LSL stream (set lsl_stream_name below)
monitoring: str = "saved"

# Path to EDF file (used when monitoring == "saved")
edf_path: str = "data/example_eeg.edf"

# LSL stream name (used when monitoring == "live")
# Find this name with: pylsl.resolve_streams()
lsl_stream_name: str = "EEG"

# ── Calibration ────────────────────────────────────────────────────────────────
# Duration of interictal baseline used to calibrate the field (minutes).
# Must precede any seizure onset in the recording.
calib_min: int = 8

# ── Field parameters ───────────────────────────────────────────────────────────
# These are the validated parameters from the CHB-MIT and Siena datasets.
# Change only if you have a specific reason to do so.
n_nodes: int = 50           # number of field nodes (BA-m3 graph)
omega_std: float = 0.20     # initial frequency spread
top_k: int = 10             # nodes updated per exposure
n_expose: int = 10          # exposures per calibration window
alpha_learn: float = 0.15   # learning rate
calib_offset: list = [1.5, 0.0, 0.0]  # PCA centroid offset
omega_scale: float = 1.5    # omega rescaling factor

# ── Alert thresholds ───────────────────────────────────────────────────────────
# thr_max:  P80 of calibration novelty_max (computed automatically at runtime)
# thr_col_abs: absolute threshold for novelty_collective (Siena-validated)
thr_col_abs: float = 0.70

# ── Anti-ictal forcing (optional, experimental) ────────────────────────────────
# See docs/anti_ictal.md for details.
# Setting this to True enables oscillatory forcing when the alert state is FRONTERA.
anti_ictal_forcing: bool = False
forcing_amplitude: float = 0.02     # sweet spot — individual calibration recommended
forcing_trigger_state: str = "FRONTERA"  # "FRONTERA" or "OPUESTO"
