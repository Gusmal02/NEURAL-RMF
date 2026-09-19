"""API pública de NEURAL-RMF.

Funciones exportadas:
    calibrate(edf_path, calib_minutes, channels) -> CalibratedModel
    detect(model, edf_path) -> ResultadoDeteccion
    plot_semaforo(resultado, save, show)
"""

from __future__ import annotations
import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
import pickle
import io

from .edf import read_edf, DIADEMA_CHANNELS
from .encoder import EEGEncoder
from .semaforo import calibrar_umbral, Semaforo
from ._core import build_field, calibrate_field, sense, forget_step


_FIELD_N     = 50
_FIELD_K     = 2.0
_FIELD_SEED  = 42
_OMEGA_STD   = 0.20
_N_EXPOSE    = 10
_FORGET_GAMMA = 0.003
_WIN_SEC     = 30.0
_STRIDE_SEC  = 30.0


@dataclass
class ResultadoDeteccion:
    novelty_por_minuto:  List[float]
    alerta_minuto:       Optional[int]
    lead_time_min:       Optional[float]
    semaforo:            str           # 'verde' | 'naranja' | 'rojo'
    umbral_calibrado:    float
    canales_usados:      List[str]
    nov_collective:      List[float]
    slope_r:             List[float]
    r_field_series:      List[float] = field(default_factory=list)


@dataclass
class CalibratedModel:
    encoder:    EEGEncoder
    field:      object           # campo RMF binario (devuelto por build_field)
    umbral:     float
    channels:   List[str]
    fs:         float
    calib_novs: List[float]      # novelty minuto a minuto de calibración
    _field_bytes: bytes = field(default=b"", repr=False)  # snapshot serializado


# ---------------------------------------------------------------------------
def calibrate(
    edf_path: str,
    calib_minutes: float = 8.0,
    channels: Optional[List[str]] = None,
) -> CalibratedModel:
    """
    Lee los primeros `calib_minutes` minutos de `edf_path` y calibra el campo.

    Devuelve un CalibratedModel listo para pasar a detect().
    """
    if channels is None:
        channels = DIADEMA_CHANNELS

    signal, fs, names = read_edf(edf_path, channels)
    n_calib = int(calib_minutes * 60 * fs)
    signal_calib = signal[:, :n_calib]

    win_samples  = int(_WIN_SEC * fs)
    stride_samples = int(_STRIDE_SEC * fs)

    windows_calib = _sliding_windows(signal_calib, win_samples, stride_samples)
    if len(windows_calib) < 4:
        raise ValueError(
            f"Solo {len(windows_calib)} ventanas de calibración — "
            f"necesitas al menos 4 (aumento calib_minutes o usa un EDF más largo)."
        )

    encoder = EEGEncoder()
    encoder.fit(windows_calib, fs)

    omegas_calib = np.array([encoder.transform(w) for w in windows_calib], dtype=np.float32)

    rmf = build_field(N=_FIELD_N, K=_FIELD_K, omega_std=_OMEGA_STD, seed=_FIELD_SEED)
    calibrate_field(rmf, omegas_calib, n_expose=_N_EXPOSE)

    novs_calib = [float(1.0 - sense(rmf, o, update_dynamics=False)["max_res"]) for o in omegas_calib]
    umbral = calibrar_umbral(novs_calib, percentil=80)

    return CalibratedModel(
        encoder=encoder,
        field=rmf,
        umbral=umbral,
        channels=names,
        fs=float(fs),
        calib_novs=novs_calib,
    )


# ---------------------------------------------------------------------------
def detect(
    model: CalibratedModel,
    edf_path: str,
    crisis_minuto: Optional[int] = None,
) -> ResultadoDeteccion:
    """
    Aplica el modelo calibrado al EDF completo y devuelve ResultadoDeteccion.

    crisis_minuto: si se conoce el onset (para calcular lead_time), opcional.
    """
    signal, fs, names = read_edf(edf_path, model.channels)

    win_samples    = int(_WIN_SEC * model.fs)
    stride_samples = int(_STRIDE_SEC * model.fs)
    windows = _sliding_windows(signal, win_samples, stride_samples)

    semaforo = Semaforo(model.umbral, n_confirmacion=3)

    novelty_por_min: List[float] = []
    nov_collective:  List[float] = []
    slope_r:         List[float] = []
    r_history:       List[float] = []

    alerta_minuto: Optional[int] = None

    for idx, win in enumerate(windows):
        omega = model.encoder.transform(win)
        info  = sense(model.field, omega)
        forget_step(model.field, _FORGET_GAMMA)

        nov_max = float(1.0 - info["max_res"])
        nov_col = float(1.0 - info.get("mean_res", info["max_res"]))
        r       = float(info.get("r_field", 1.0))

        novelty_por_min.append(nov_max)
        nov_collective.append(nov_col)
        r_history.append(r)

        # slope(r) sobre ventana de 5 pasos
        if len(r_history) >= 3:
            w5 = r_history[-5:]
            sl = float(np.polyfit(range(len(w5)), w5, 1)[0])
        else:
            sl = 0.0
        slope_r.append(sl)

        estado = semaforo.actualizar(nov_max, r_field=r)
        minuto = idx  # 1 ventana = 30 s → 2 ventanas = 1 min

        if alerta_minuto is None and estado in ("naranja", "rojo"):
            alerta_minuto = minuto

    lead_time: Optional[float] = None
    if alerta_minuto is not None and crisis_minuto is not None:
        lead_time = (crisis_minuto - alerta_minuto) * (_STRIDE_SEC / 60.0)

    return ResultadoDeteccion(
        novelty_por_minuto=novelty_por_min,
        alerta_minuto=alerta_minuto,
        lead_time_min=lead_time,
        semaforo=semaforo.estado,
        umbral_calibrado=model.umbral,
        canales_usados=names,
        nov_collective=nov_collective,
        slope_r=slope_r,
        r_field_series=r_history,
    )


# ---------------------------------------------------------------------------
def run_edf(
    edf_path: str,
    channels: Optional[List[str]] = None,
    calib_minutes: float = 8.0,
) -> List[dict]:
    """
    Convenience wrapper: calibrate + detect in one call.

    Returns a list of dicts, one per 30-second window after calibration:
        {"t_min": float, "t_max": float, "novelty_max": float,
         "novelty_col": float, "estado": str, "umbral": float}
    """
    model = calibrate(edf_path, calib_minutes=calib_minutes, channels=channels)

    signal, fs, names = read_edf(edf_path, model.channels)

    win_samples    = int(_WIN_SEC * model.fs)
    stride_samples = int(_STRIDE_SEC * model.fs)
    n_calib        = int(calib_minutes * 60 * model.fs)

    all_windows = _sliding_windows(signal, win_samples, stride_samples)
    n_calib_wins = len(_sliding_windows(signal[:, :n_calib], win_samples, stride_samples))
    windows = all_windows[n_calib_wins:]

    semaforo = Semaforo(model.umbral, n_confirmacion=3)
    t_offset = n_calib_wins * _STRIDE_SEC

    results: List[dict] = []
    for idx, win in enumerate(windows):
        omega = model.encoder.transform(win)
        info  = sense(model.field, omega)
        forget_step(model.field, _FORGET_GAMMA)

        nov_max = float(1.0 - info["max_res"])
        nov_col = float(1.0 - info.get("mean_res", info["max_res"]))

        estado = semaforo.actualizar(nov_max, r_field=float(info.get("r_field", 1.0)))

        t_min = t_offset + idx * _STRIDE_SEC
        results.append({
            "t_min":       t_min,
            "t_max":       t_min + _WIN_SEC,
            "novelty_max": nov_max,
            "novelty_col": nov_col,
            "estado":      estado,
            "umbral":      model.umbral,
        })

    return results


# ---------------------------------------------------------------------------
def plot_semaforo(resultado: ResultadoDeteccion, save: Optional[str] = None, show: bool = True):
    """Delega en viz.plot_semaforo()."""
    from .viz import plot_semaforo as _plot
    _plot(resultado, save=save, show=show)


# ---------------------------------------------------------------------------
def _sliding_windows(signal: np.ndarray, win: int, stride: int) -> List[np.ndarray]:
    n = signal.shape[1]
    windows = []
    start = 0
    while start + win <= n:
        windows.append(signal[:, start:start + win])
        start += stride
    return windows
