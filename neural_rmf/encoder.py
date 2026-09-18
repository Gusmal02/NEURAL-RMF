"""EEG → ω-space 3D.

Pipeline:
  señal (4ch, ventana 30s)
  → 7 features (bandpower ×4, coherencia, kurtosis, STA/LTA)
  → StandardScaler  (ajustado en calibración)
  → PCA 3D          (ajustado en calibración)
  → + CALIB_OFFSET [1.5, 0, 0]
  → normalize
  → ω ∈ ℝ³
"""

from __future__ import annotations
import numpy as np
from scipy.signal import welch
from scipy.stats import kurtosis
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

CALIB_OFFSET = np.array([1.5, 0.0, 0.0], dtype=np.float32)

# Bandas de frecuencia (Hz)
_BANDS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "beta":  (13.0, 30.0),
    "gamma": (30.0, 70.0),
}


def _bandpower(signal: np.ndarray, fs: float, fmin: float, fmax: float) -> float:
    freqs, psd = welch(signal, fs=fs, nperseg=min(256, len(signal)))
    idx = np.logical_and(freqs >= fmin, freqs <= fmax)
    _trapz = getattr(np, "trapezoid", None) or getattr(np, "trapz")
    return float(_trapz(psd[idx], freqs[idx]) + 1e-12)


def _extract_features(window: np.ndarray, fs: float) -> np.ndarray:
    """
    window: (4, n_muestras)  — F7, T7, F8, T8
    Devuelve vector de 7 features.
    """
    ch = window  # 4 canales

    # 4 bandpowers (media sobre los 4 canales)
    feats = []
    for band, (fmin, fmax) in _BANDS.items():
        bp = np.mean([_bandpower(ch[i], fs, fmin, fmax) for i in range(4)])
        feats.append(np.log1p(bp))

    # Coherencia inter-hemisférica izquierda-derecha (F7↔F8 + T7↔T8) / 2
    def _coherence(a, b):
        n = min(len(a), len(b))
        fa = np.fft.rfft(a[:n])
        fb = np.fft.rfft(b[:n])
        coh = np.abs(np.mean(fa * np.conj(fb))) / (
            np.sqrt(np.mean(np.abs(fa) ** 2) * np.mean(np.abs(fb) ** 2)) + 1e-12
        )
        return float(coh)

    coh = (_coherence(ch[0], ch[2]) + _coherence(ch[1], ch[3])) / 2.0
    feats.append(coh)

    # Kurtosis (media sobre canales)
    kurt = float(np.mean([kurtosis(ch[i]) for i in range(4)]))
    feats.append(kurt)

    # STA/LTA (short-term/long-term amplitude ratio)
    sta_len = int(fs * 0.5)
    lta_len = int(fs * 5.0)
    amp = np.abs(ch).mean(axis=0)
    sta = np.mean(amp[-sta_len:]) if sta_len > 0 else 1.0
    lta = np.mean(amp[-lta_len:]) if lta_len > 0 else 1.0
    feats.append(float(sta / (lta + 1e-12)))

    return np.array(feats, dtype=np.float32)


class EEGEncoder:
    """
    Ajusta scaler+PCA en calibración y proyecta ventanas a ω ∈ ℝ³.
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.pca    = PCA(n_components=3)
        self._fitted = False
        self.fs: float = 256.0

    # ------------------------------------------------------------------
    def fit(self, windows: list[np.ndarray], fs: float) -> "EEGEncoder":
        """
        windows: lista de arrays (4, n_muestras)
        """
        self.fs = fs
        X = np.vstack([self._features(w) for w in windows])
        self.scaler.fit(X)
        Xs = self.scaler.transform(X)
        self.pca.fit(Xs)
        self._fitted = True
        return self

    def transform(self, window: np.ndarray) -> np.ndarray:
        """Devuelve ω ∈ ℝ³ normalizado."""
        if not self._fitted:
            raise RuntimeError("Llama fit() antes de transform().")
        f = self._features(window).reshape(1, -1)
        fs = self.scaler.transform(f)
        pca3 = self.pca.transform(fs)[0].astype(np.float32)
        omega = pca3 + CALIB_OFFSET
        norm = np.linalg.norm(omega)
        if norm > 1e-9:
            omega = omega / norm
        return omega

    def _features(self, window: np.ndarray) -> np.ndarray:
        return _extract_features(window, self.fs)
