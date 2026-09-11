"""
EEGEncoder: transforms raw EEG windows into 3-D vectors (ω-space).

Pipeline:
    raw window (channels × samples)
    → 7 spectral/spatial features
    → StandardScaler normalization
    → 3-D projection via truncated SVD
    → unit-sphere rescaling

This file is shareable source.  The internal field engine is distributed
as a compiled binary (field_engine.pyd / field_engine.so).
"""

import numpy as np
from scipy.signal import welch
from scipy.stats import kurtosis
from sklearn.preprocessing import StandardScaler


# ── Feature extraction ────────────────────────────────────────────────────────

def _bandpower(win: np.ndarray, f_lo: float, f_hi: float, fs: int) -> float:
    """Mean power in a frequency band averaged across channels."""
    freqs, psd = welch(win, fs=fs, nperseg=min(256, win.shape[-1]))
    mask = (freqs >= f_lo) & (freqs <= f_hi)
    return float(psd[..., mask].mean())


def _coherence_mono(win: np.ndarray) -> float:
    """Mean absolute correlation between all channel pairs."""
    if win.shape[0] < 2:
        return 0.0
    cc = np.corrcoef(win)
    idx = np.triu_indices(win.shape[0], k=1)
    return float(np.abs(cc[idx]).mean())


def _kurtosis_mean(win: np.ndarray) -> float:
    return float(np.mean([kurtosis(win[c]) for c in range(win.shape[0])]))


def _sta_lta(win: np.ndarray, fs: int, sta_sec: float = 0.5, lta_sec: float = 5.0) -> float:
    """Short-term / long-term amplitude ratio (single-channel mean)."""
    sta = max(1, int(sta_sec * fs))
    lta = max(sta + 1, int(lta_sec * fs))
    amp = np.abs(win).mean(axis=0)
    n = len(amp)
    if n < lta:
        return 1.0
    sta_val = amp[-sta:].mean()
    lta_val = amp[-lta:].mean()
    return float(sta_val / (lta_val + 1e-8))


def extract_features(win: np.ndarray, fs: int) -> np.ndarray:
    """
    Parameters
    ----------
    win : ndarray, shape (n_channels, n_samples)
    fs  : sampling rate (Hz)

    Returns
    -------
    f : ndarray, shape (7,), dtype float32
        [delta, theta, beta, gamma, coherence_mono, kurtosis_mean, sta_lta]
    """
    f = np.array([
        _bandpower(win, 0.5,  4.0,  fs),
        _bandpower(win, 4.0,  8.0,  fs),
        _bandpower(win, 13.0, 30.0, fs),
        _bandpower(win, 30.0, 50.0, fs),
        _coherence_mono(win),
        _kurtosis_mean(win),
        _sta_lta(win, fs),
    ], dtype=np.float32)
    return np.nan_to_num(f, nan=0.0, posinf=0.0, neginf=0.0)


# ── Encoder ───────────────────────────────────────────────────────────────────

class EEGEncoder:
    """
    Fits a 3-D projection from EEG feature vectors.

    Usage
    -----
    enc = EEGEncoder(fs=256, win_sec=2, calib_offset=[1.5, 0, 0], omega_scale=1.5)
    enc.fit(calibration_windows)   # list/array of (n_ch, n_samples) windows
    omega = enc.encode(window)     # returns torch.Tensor shape (3,)
    """

    def __init__(
        self,
        fs: int = 256,
        win_sec: float = 2.0,
        calib_offset: list = None,
        omega_scale: float = 1.5,
    ):
        self.fs = fs
        self.win_sec = win_sec
        self.calib_offset = np.array(calib_offset or [1.5, 0.0, 0.0], dtype=np.float32)
        self.omega_scale = omega_scale
        self._fitted = False

    def fit(self, windows: list) -> "EEGEncoder":
        """
        Parameters
        ----------
        windows : list of ndarray, each shape (n_channels, n_samples)
            Interictal calibration windows (up to 240 used).
        """
        import torch
        feats = np.stack([extract_features(w, self.fs) for w in windows[:240]])
        self.sc = StandardScaler().fit(feats)
        Xs = self.sc.transform(feats)
        _, _, Vt = np.linalg.svd(Xs, full_matrices=False)
        self.Vt = Vt[:3].astype(np.float32)
        self._fitted = True
        return self

    def encode(self, win: np.ndarray):
        """
        Parameters
        ----------
        win : ndarray, shape (n_channels, n_samples)

        Returns
        -------
        omega : torch.Tensor, shape (3,)
        """
        import torch
        if not self._fitted:
            raise RuntimeError("Call fit() before encode().")
        f = extract_features(win, self.fs)
        Xs = self.sc.transform(f.reshape(1, -1))[0]
        v = self.Vt @ Xs + self.calib_offset
        v = v / (np.linalg.norm(v) + 1e-8)
        return torch.tensor(v * self.omega_scale, dtype=torch.float32)
