"""
alert_system.py — 3-state semaphore for pre-ictal alert.

States
------
CONOCIDO  (green)  : nov_collective < thr_amarillo  — baseline activity
FRONTERA  (orange) : thr_amarillo ≤ nov_collective < thr_col_abs — approaching ictal territory
OPUESTO   (red)    : nov_collective ≥ thr_col_abs   — clear pre-ictal signal

The orange/red thresholds are percentile-based (calibrated from the baseline
window) plus an absolute ceiling validated on CHB-MIT and Siena datasets.

This file is shareable source.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AlertState:
    state: str = "CONOCIDO"        # current 3-state label
    alert_level: str = "none"      # "none" | "warn" | "critical"
    nov_max: float = 0.0
    nov_collective: float = 0.0
    lead_minutes: Optional[float] = None  # minutes since first orange/red (if any)
    confirmation_windows: int = 0


class AlertSystem:
    """
    Parameters
    ----------
    thr_col_abs : float
        Absolute threshold for OPUESTO (validated: 0.70).
    calib_novelties : list[float]
        nov_collective values recorded during calibration.
        Used to set the FRONTERA threshold at P80 of the calibration distribution.
    confirm_windows : int
        Minimum consecutive windows at FRONTERA/OPUESTO before raising an alert.
    """

    def __init__(
        self,
        thr_col_abs: float = 0.70,
        calib_novelties: list = None,
        confirm_windows: int = 3,
        window_sec: float = 120.0,
    ):
        self.thr_col_abs = thr_col_abs
        self.confirm_windows = confirm_windows
        self.window_sec = window_sec  # seconds per monitoring window

        if calib_novelties:
            self.thr_amarillo = float(np.percentile(calib_novelties, 80))
        else:
            self.thr_amarillo = 0.40  # conservative default

        self._streak = 0          # consecutive non-CONOCIDO windows
        self._first_alert_win: Optional[int] = None
        self._win_count = 0

    def update(self, metrics: dict) -> AlertState:
        """
        Parameters
        ----------
        metrics : dict
            Output of field_engine.measure_window().

        Returns
        -------
        AlertState
        """
        self._win_count += 1
        nov_col = metrics["nov_collective"]
        nov_max = metrics["nov_max"]

        # composite index (v3): nov_norm × (1 + gradient_bonus)
        # gradient bonus is 0 without history — simple version here
        composite = nov_col

        # 3-state classification
        if composite >= self.thr_col_abs:
            state = "OPUESTO"
        elif composite >= self.thr_amarillo:
            state = "FRONTERA"
        else:
            state = "CONOCIDO"

        # confirmation streak
        if state != "CONOCIDO":
            self._streak += 1
            if self._first_alert_win is None:
                self._first_alert_win = self._win_count
        else:
            self._streak = 0
            self._first_alert_win = None

        # alert level
        if self._streak >= self.confirm_windows:
            alert_level = "critical" if state == "OPUESTO" else "warn"
        else:
            alert_level = "none"

        # lead time (minutes since first non-CONOCIDO window)
        lead = None
        if self._first_alert_win is not None:
            elapsed_wins = self._win_count - self._first_alert_win
            lead = round(elapsed_wins * self.window_sec / 60.0, 1)

        return AlertState(
            state=state,
            alert_level=alert_level,
            nov_max=round(nov_max, 4),
            nov_collective=round(nov_col, 4),
            lead_minutes=lead,
            confirmation_windows=self._streak,
        )

    def reset(self):
        """Reset streak counters (call between recordings)."""
        self._streak = 0
        self._first_alert_win = None
        self._win_count = 0
