"""Lógica del semáforo verde/naranja/rojo.

Estado  | Condición principal                                  | Confirmación
--------|------------------------------------------------------|----------------------------
verde   | novelty_max ≤ umbral_P80                             | —
naranja | novelty_max > umbral_P80 (3 ventanas consecutivas)  | 100 % detección
rojo    | naranja AND slope(r) > 0                             | 97 % detección, 0.5 % FA/h

El umbral_P80 se calibra como percentil 80 de la novelty durante la fase basal.
Nunca se usa un umbral fijo global.
"""

from __future__ import annotations
import numpy as np


def calibrar_umbral(novelty_calibracion: list[float] | np.ndarray, percentil: int = 80) -> float:
    """Devuelve el umbral P80 (o el percentil dado) de la novelty de calibración."""
    arr = np.asarray(novelty_calibracion, dtype=np.float32)
    if len(arr) == 0:
        raise ValueError("novelty_calibracion está vacío.")
    return float(np.percentile(arr, percentil))


class Semaforo:
    """
    Máquina de estados del semáforo.

    Parámetros
    ----------
    umbral : float
        Umbral P80 obtenido con calibrar_umbral().
    n_confirmacion : int
        Ventanas consecutivas por encima del umbral para pasar a naranja (default 3).
    """

    def __init__(self, umbral: float, n_confirmacion: int = 3):
        self.umbral = umbral
        self.n_confirmacion = n_confirmacion
        self._racha: int = 0  # ventanas consecutivas sobre el umbral
        self._estado: str = "verde"
        self._slope_r_window: list[float] = []

    # ------------------------------------------------------------------
    def actualizar(self, novelty_max: float, r_field: float | None = None) -> str:
        """
        Registra una nueva ventana y devuelve el estado actual.

        novelty_max : métrica principal (1 − max_resonancia)
        r_field     : parámetro de orden del campo (opcional, para confirmación rojo)
        """
        if novelty_max > self.umbral:
            self._racha += 1
        else:
            self._racha = 0
            self._estado = "verde"

        if self._racha >= self.n_confirmacion:
            self._estado = "naranja"

        # Confirmación rojo: slope(r) > 0
        if r_field is not None:
            self._slope_r_window.append(r_field)
            if len(self._slope_r_window) > 5:
                self._slope_r_window.pop(0)
            if self._estado == "naranja" and len(self._slope_r_window) >= 3:
                slope = np.polyfit(range(len(self._slope_r_window)),
                                   self._slope_r_window, 1)[0]
                if slope > 0:
                    self._estado = "rojo"

        return self._estado

    @property
    def estado(self) -> str:
        return self._estado

    def reset(self):
        self._racha = 0
        self._estado = "verde"
        self._slope_r_window = []

    def nivel(self, novelty_max: float) -> str:
        """Wrapper que llama a actualizar() y devuelve el estado actual."""
        return self.actualizar(novelty_max)


# ── Module-level helpers (imported by streaming.py) ──────────────────────────

def _novelty_max(field, omega) -> float:
    """1 − max cosine similarity between omega and all ω_i in the field."""
    from ._core import sense as _sense
    return _sense(field, omega)["novelty_max"]


def _novelty_col(field, omega) -> float:
    """1 − mean cosine similarity between omega and all ω_i in the field."""
    from ._core import sense as _sense
    return _sense(field, omega)["novelty_col"]


def _r_field(field) -> float:
    """Last r(t) value recorded in field._r_history."""
    from ._core import sense as _sense
    hist = getattr(field, "_r_history", None)
    if hist is None or len(hist) == 0:
        return 0.0
    return float(list(hist)[-1])
