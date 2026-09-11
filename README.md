# NEURAL-RMF

AI-based EEG monitoring system for pre-ictal seizure prediction.

NEURAL-RMF uses a resonant memory field to detect gradual shifts in EEG dynamics
that precede seizures, generating multi-level alerts with substantial lead times.

---

## Performance

| Dataset | Detection rate | Mean lead time |
|---------|---------------|----------------|
| CHB-MIT (pediatric, 256 Hz) | 100 % | 74.5 min |
| Siena Scalp EEG (adult, 512 Hz) | 97 % | 89.5 min |

Detection is based on a single session calibration of 8 minutes of interictal EEG.

---

## Hardware

The system is validated on a **4-channel frontal-temporal configuration**:

| Channel | Position |
|---------|----------|
| F7 | Left frontal |
| T7 | Left temporal |
| F8 | Right frontal |
| T8 | Right temporal |

This 4-channel wearable setup (diadema) matches or outperforms full 23-channel clinical EEG
(95 % vs 74 % detection rate) for the tested populations.

The channel list is configurable in `config.py`.

---

## Alert semaphore

NEURAL-RMF outputs a continuous 3-state alert:

| State | Color | Meaning |
|-------|-------|---------|
| `CONOCIDO` | Green | Baseline interictal activity |
| `FRONTERA` | Orange | Approaching ictal territory — elevated vigilance |
| `OPUESTO` | Red | Clear pre-ictal signal — alert |

The FRONTERA threshold is calibrated automatically from the patient's own baseline (P80 of
calibration novelty). The OPUESTO threshold is an absolute value validated across both datasets.

Confirmation requires 3 consecutive windows in the elevated state before an alert is raised.

---

## Datasets

**CHB-MIT Scalp EEG Database**
Children's Hospital Boston — MIT (Physionet).
24 pediatric patients, 256 Hz, standard 23-channel 10-20 montage.
> Goldberger AL, et al. *PhysioBank, PhysioToolkit, and PhysioNet.*
> Circulation. 2000;101(23):e215–e220.

**Siena Scalp EEG Database**
University of Siena (Physionet).
14 adult patients, 512 Hz, standard 23-channel 10-20 montage.
> Detti P, et al. *EEG synchronization analysis for seizure prediction.*
> Entropy. 2020.

---

## Installation

```bash
pip install -r requirements.txt
```

For live EEG streaming (LSL), pylsl is required:

```bash
pip install pylsl
```

---

## Quick start

### Saved EDF file

```bash
python run_pipeline.py --monitoring saved --edf data/example_eeg.edf
```

### Live LSL stream

```bash
python run_pipeline.py --monitoring live --lsl-stream EEG
```

---

## Configuration

Edit `config.py` before running:

```python
# Channel names as they appear in your EDF/LSL stream
eeg_channels = ["F7", "T7", "F8", "T8"]

# Sampling rate (Hz) — 256 for CHB-MIT, 512 for Siena, match your hardware
fs = 256

# Monitoring mode: "saved" (EDF file) or "live" (LSL stream)
monitoring = "saved"

# Path to EDF file (used when monitoring == "saved")
edf_path = "data/example_eeg.edf"

# LSL stream name (used when monitoring == "live")
lsl_stream_name = "EEG"

# Calibration duration in minutes (interictal baseline)
calib_min = 8
```

---

## Output

Results are written to `results/results.json` after each run. Each entry contains:

| Field | Description |
|-------|-------------|
| `t_min` | Time in minutes since end of calibration |
| `nov_max` | Per-node novelty (primary alert metric) |
| `nov_collective` | Mean-resonance novelty (collective metric) |
| `state` | Current semaphore state |
| `alert_level` | `none` / `warn` / `critical` |
| `lead_minutes` | Minutes since first non-baseline window |

---

## Anti-ictal module (experimental)

NEURAL-RMF includes an optional oscillatory forcing module that attempts to deflect the
pre-ictal trajectory back toward the interictal baseline. It is **disabled by default** and
validated in simulation only.

See [`docs/anti_ictal.md`](docs/anti_ictal.md) for design details and simulation results.

---

## IP notice

The core signal-processing engine (`core/field_engine`) is distributed as a compiled
binary (`.pyd` on Windows, `.so` on Linux/macOS). Source is not included in this package.

All other modules — `config.py`, `core/eeg_encoder.py`, `core/alert_system.py`,
`run_pipeline.py` — are provided as readable Python source.

---

## Contact

Gustavo Alfonso Maldonado Vallejo · gustavo.a.maldonado.v@gmail.com
