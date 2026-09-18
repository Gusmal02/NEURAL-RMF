# NEURAL-RMF

**Real-time EEG pre-ictal detection for epilepsy monitoring.**

NEURAL-RMF is a Python library that provides a lightweight, field-based approach to detecting the pre-ictal state in scalp EEG recordings. It is designed for integration in clinical monitoring systems, wearable devices, and research pipelines.

---

## Key capabilities

- **Pre-ictal detection** — alerts up to ~90 minutes before seizure onset on validated datasets (CHB-MIT, Siena Scalp EEG).
- **Minimal electrode setup** — 4 frontal-temporal channels (F7, T7, F8, T8), compatible with diadem-style hardware.
- **Three-level alert** — `verde` / `naranja` / `rojo` based on a domain-calibrated threshold (no global constants).
- **Intra-session calibration** — calibrates from the first 8 minutes of the same recording; no cross-patient training required.
- **Streaming-ready** — processes 30-second windows sequentially; designed for LSL and EDF-based pipelines.

---

## Installation

```bash
pip install neural-rmf
```

> **Note:** The package ships a pre-compiled binary extension. Python ≥ 3.9 is required.  
> Optional live-stream support: `pip install neural-rmf[live]`

---

## Quick start

```python
from neural_rmf import run_edf

# Run on an EDF file — calibrates on the first 8 minutes, then streams
results = run_edf("patient01.edf", channels=["F7", "T7", "F8", "T8"])

for window in results:
    print(window["t_min"], window["estado"])   # verde / naranja / rojo
```

---

## API overview

| Function / Class | Purpose |
|---|---|
| `run_edf(path, channels)` | Process a full EDF file end-to-end |
| `build_field()` | Create a resonant field (default parameters) |
| `calibrate_field(field, omegas)` | Expose the field to baseline patterns |
| `sense(field, omega)` | Query novelty and coherence metrics |
| `Semaforo(umbral)` | Three-level alert state machine |
| `calibrar_umbral(novelty_list)` | Compute the P80 domain threshold |
| `EEGEncoder(fs, channels)` | Extract ω-space features from an EEG window |

Full API reference: see module docstrings.

---

## Validated results

| Dataset | Detection rate | Mean lead time |
|---|---|---|
| CHB-MIT Scalp EEG (pediatric, 4 ch) | 100 % | 74.5 min |
| Siena Scalp EEG (adult, 4 ch) | 97 % | 89.5 min |

False-alarm rate ≤ 0.5 % / hour at the `rojo` level.

---

## Requirements

- Python ≥ 3.9
- numpy, scipy, scikit-learn, torch, pyedflib, networkx, psutil

---

## License

Proprietary. All rights reserved.
