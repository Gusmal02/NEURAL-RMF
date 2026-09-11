"""
run_pipeline.py — NEURAL-RMF entry point.

Usage
-----
# Saved EDF file:
python run_pipeline.py --monitoring saved --edf data/example_eeg.edf

# Live LSL stream:
python run_pipeline.py --monitoring live --lsl-stream EEG

The pipeline:
  1. Reads config.py for field and alert parameters.
  2. Calibrates the encoder and field on the first `calib_min` minutes.
  3. Runs a sliding 2-second window and prints the alert state per window.
  4. Writes results/results.json on completion.
"""

from __future__ import annotations
import argparse
import json
import time
from pathlib import Path

import numpy as np

import config
from core.eeg_encoder import EEGEncoder
from core.field_engine import build_field, measure_window
from core.alert_system import AlertSystem


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_edf(path: str, channels: list[str], fs_expected: int):
    """Return (data, fs) where data is ndarray (n_ch, n_samples)."""
    import pyedflib
    f = pyedflib.EdfReader(path)
    labels = f.getSignalLabels()
    fs = int(f.getSampleFrequency(0))
    idx = [i for i, l in enumerate(labels) if l.strip() in channels]
    if not idx:
        raise ValueError(f"None of {channels} found in {path}. Available: {labels}")
    data = np.array([f.readSignal(i) for i in idx])
    f._close()
    return data, fs


def _iter_edf(edf_path: str, channels: list[str], fs: int, win_sec: float, stride_sec: float):
    """Yield overlapping windows from an EDF file."""
    data, actual_fs = _load_edf(edf_path, channels, fs)
    win_samp    = int(win_sec    * actual_fs)
    stride_samp = int(stride_sec * actual_fs)
    n_samples   = data.shape[1]
    start = 0
    while start + win_samp <= n_samples:
        yield data[:, start:start + win_samp], actual_fs
        start += stride_samp


def _iter_lsl(stream_name: str, channels: list[str], fs: int, win_sec: float):
    """Yield windows from a live LSL stream (blocking)."""
    import pylsl
    streams = pylsl.resolve_stream("name", stream_name)
    if not streams:
        raise RuntimeError(f"No LSL stream named '{stream_name}' found.")
    inlet = pylsl.StreamInlet(streams[0])
    info  = inlet.info()
    actual_fs = int(info.nominal_srate())
    win_samp  = int(win_sec * actual_fs)
    buf: list = []

    while True:
        chunk, _ = inlet.pull_chunk(max_samples=win_samp)
        if chunk:
            buf.extend(chunk)
        if len(buf) >= win_samp:
            win = np.array(buf[:win_samp]).T  # (n_ch, n_samples)
            buf = buf[win_samp:]
            yield win[:len(channels)], actual_fs


# ── calibration ───────────────────────────────────────────────────────────────

def _calibrate(windows_iter, calib_wins: int, enc: EEGEncoder):
    calib_windows = []
    for win, fs in windows_iter:
        calib_windows.append(win)
        if len(calib_windows) >= calib_wins:
            break
    enc.fit(calib_windows)
    return calib_windows


# ── main pipeline ─────────────────────────────────────────────────────────────

def run(monitoring: str, edf_path: str = None, lsl_stream: str = None):
    win_sec    = 2.0
    stride_sec = win_sec  # non-overlapping; reduce for higher resolution

    fs      = config.fs
    calib_wins = int(config.calib_min * 60 / win_sec)

    enc   = EEGEncoder(
        fs=fs,
        win_sec=win_sec,
        calib_offset=config.calib_offset,
        omega_scale=config.omega_scale,
    )
    field  = build_field(seed=42)
    alert  = None  # built after calibration

    results = []
    win_idx = 0
    calib_phase = True
    calib_buffer = []
    calib_novelties = []

    print(f"[NEURAL-RMF] monitoring={monitoring}  channels={config.eeg_channels}")
    print(f"[NEURAL-RMF] calibrating for {config.calib_min} min ({calib_wins} windows)…")

    if monitoring == "saved":
        path = edf_path or config.edf_path
        source = _iter_edf(path, config.eeg_channels, fs, win_sec, stride_sec)
    elif monitoring == "live":
        name = lsl_stream or config.lsl_stream_name
        source = _iter_lsl(name, config.eeg_channels, fs, win_sec)
    else:
        raise ValueError(f"Unknown monitoring mode: {monitoring!r}")

    for win, actual_fs in source:
        if calib_phase:
            calib_buffer.append(win)
            if len(calib_buffer) >= calib_wins:
                enc.fit(calib_buffer)
                # warm up field with calibration omegas
                for cw in calib_buffer:
                    omega = enc.encode(cw)
                    m = measure_window(field, omega)
                    calib_novelties.append(m["nov_collective"])
                alert = AlertSystem(
                    thr_col_abs=config.thr_col_abs,
                    calib_novelties=calib_novelties,
                )
                calib_phase = False
                print(f"[NEURAL-RMF] calibration done. "
                      f"thr_amarillo={alert.thr_amarillo:.3f}  "
                      f"thr_col_abs={config.thr_col_abs:.2f}")
            continue

        omega   = enc.encode(win)
        metrics = measure_window(field, omega)
        state   = alert.update(metrics)

        win_idx += 1
        t_min = round(win_idx * win_sec / 60.0, 2)

        row = dict(
            t_min=t_min,
            nov_max=state.nov_max,
            nov_collective=state.nov_collective,
            state=state.state,
            alert_level=state.alert_level,
            lead_minutes=state.lead_minutes,
        )
        results.append(row)

        marker = ""
        if state.alert_level == "warn":
            marker = "  ⚠  FRONTERA"
        elif state.alert_level == "critical":
            marker = "  🔴  OPUESTO — ALERT"

        print(f"  t={t_min:6.1f} min | "
              f"nov_max={state.nov_max:.3f} | "
              f"nov_col={state.nov_collective:.3f} | "
              f"{state.state}{marker}")

    # save results
    out_path = Path("results") / "results.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\n[NEURAL-RMF] done. {len(results)} windows processed. "
          f"Results → {out_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NEURAL-RMF pipeline")
    parser.add_argument("--monitoring", choices=["saved", "live"], default=config.monitoring)
    parser.add_argument("--edf",        default=config.edf_path,        help="Path to EDF file")
    parser.add_argument("--lsl-stream", default=config.lsl_stream_name, help="LSL stream name")
    args = parser.parse_args()

    run(
        monitoring=args.monitoring,
        edf_path=args.edf,
        lsl_stream=args.lsl_stream,
    )
