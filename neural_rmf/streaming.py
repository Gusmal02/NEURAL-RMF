"""Monitoreo clínico en tiempo real — StreamMonitor.

Consume ventanas de EEG de manera incremental, actualiza el semáforo
en cada ventana y puede disparar callbacks cuando el nivel cambia.

Uso mínimo::

    from neural_rmf import calibrate, StreamMonitor
    from neural_rmf.edf import read_edf

    data, fs = read_edf("paciente.edf")
    model = calibrate(data, fs)

    def on_alerta(nivel, resultado):
        print(f"[{nivel.upper()}] novelty={resultado.novelty_max:.3f}")

    monitor = StreamMonitor(model, on_alert=on_alerta)
    monitor.run(data, fs)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import numpy as np

from .api import CalibratedModel, ResultadoDeteccion, _sliding_windows


@dataclass
class EventoStream:
    """Registro de un evento emitido durante el stream."""

    t_min: float
    nivel: str          # "verde" | "naranja" | "rojo"
    novelty_max: float
    novelty_col: float
    r_field: float


class StreamMonitor:
    """Monitorea un registro EEG ventana por ventana y actualiza el semáforo.

    Args:
        model: Modelo calibrado devuelto por ``calibrate()``.
        on_alert: Callback opcional que se llama cuando el nivel es "naranja"
            o "rojo".  Firma: ``callback(nivel: str, resultado: ResultadoDeteccion)``.
        on_tick: Callback opcional que se llama en cada ventana.
            Firma: ``callback(t_min: float, resultado: ResultadoDeteccion)``.
        window_sec: Duración de cada ventana en segundos (default: 30).
        stride_sec: Paso entre ventanas en segundos (default: 30).
        simulated_realtime: Si True, introduce una pausa real entre ventanas
            para simular una adquisición en tiempo real.
    """

    def __init__(
        self,
        model: CalibratedModel,
        on_alert: Optional[Callable[[str, ResultadoDeteccion], None]] = None,
        on_tick: Optional[Callable[[float, ResultadoDeteccion], None]] = None,
        window_sec: float = 30.0,
        stride_sec: float = 30.0,
        simulated_realtime: bool = False,
    ) -> None:
        self.model = model
        self.on_alert = on_alert
        self.on_tick = on_tick
        self.window_sec = window_sec
        self.stride_sec = stride_sec
        self.simulated_realtime = simulated_realtime

        self._eventos: List[EventoStream] = []
        self._nivel_actual: str = "verde"

    # ------------------------------------------------------------------
    # Ejecución
    # ------------------------------------------------------------------

    def run(
        self,
        eeg: np.ndarray,
        fs: float,
        start_sec: float = 0.0,
    ) -> List[EventoStream]:
        """Procesa el array EEG completo ventana por ventana.

        Args:
            eeg: Array ``(n_canales, n_muestras)`` ya filtrado para los
                4 canales de la diadema.
            fs: Frecuencia de muestreo en Hz.
            start_sec: Offset temporal de la primera muestra (minutos
                mostrados en los eventos).

        Returns:
            Lista de eventos emitidos durante el stream.
        """
        self._eventos.clear()
        self._nivel_actual = "verde"

        win_samp = int(self.window_sec * fs)
        stride_samp = int(self.stride_sec * fs)
        n_samples = eeg.shape[1] if eeg.ndim == 2 else eeg.shape[0]

        start = 0
        while start + win_samp <= n_samples:
            ventana = eeg[:, start : start + win_samp] if eeg.ndim == 2 else eeg[start : start + win_samp]
            t_min = (start_sec + start / fs) / 60.0

            resultado = self._procesar_ventana(ventana, fs, t_min)

            if self.on_tick is not None:
                self.on_tick(t_min, resultado)

            if resultado.nivel in ("naranja", "rojo"):
                evento = EventoStream(
                    t_min=t_min,
                    nivel=resultado.nivel,
                    novelty_max=resultado.novelty_max,
                    novelty_col=resultado.novelty_col,
                    r_field=resultado.r_field,
                )
                self._eventos.append(evento)
                self._nivel_actual = resultado.nivel

                if self.on_alert is not None:
                    self.on_alert(resultado.nivel, resultado)
            else:
                self._nivel_actual = "verde"

            if self.simulated_realtime:
                time.sleep(self.stride_sec)

            start += stride_samp

        return list(self._eventos)

    def push_window(self, ventana: np.ndarray, fs: float, t_min: float) -> ResultadoDeteccion:
        """Procesa una única ventana EEG en modo push.

        Útil cuando las ventanas llegan de una fuente externa en tiempo real
        (tarjeta de adquisición, BLE, etc.).

        Args:
            ventana: Array ``(n_canales, n_muestras)`` de la ventana actual.
            fs: Frecuencia de muestreo.
            t_min: Tiempo en minutos desde el inicio de la grabación.

        Returns:
            ``ResultadoDeteccion`` para esta ventana.
        """
        resultado = self._procesar_ventana(ventana, fs, t_min)

        if resultado.nivel in ("naranja", "rojo"):
            evento = EventoStream(
                t_min=t_min,
                nivel=resultado.nivel,
                novelty_max=resultado.novelty_max,
                novelty_col=resultado.novelty_col,
                r_field=resultado.r_field,
            )
            self._eventos.append(evento)
            self._nivel_actual = resultado.nivel

            if self.on_alert is not None:
                self.on_alert(resultado.nivel, resultado)
        else:
            self._nivel_actual = "verde"

        if self.on_tick is not None:
            self.on_tick(t_min, resultado)

        return resultado

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    @property
    def nivel_actual(self) -> str:
        """Nivel del semáforo en la última ventana procesada."""
        return self._nivel_actual

    @property
    def eventos(self) -> List[EventoStream]:
        """Lista de eventos naranja/rojo registrados durante el stream."""
        return list(self._eventos)

    def reset(self) -> None:
        """Reinicia el historial de eventos y el nivel actual."""
        self._eventos.clear()
        self._nivel_actual = "verde"

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _procesar_ventana(
        self,
        ventana: np.ndarray,
        fs: float,
        t_min: float,
    ) -> ResultadoDeteccion:
        """Codifica la ventana y consulta el campo resonante."""
        enc = self.model.encoder
        omega = enc.transform(ventana, fs)

        field = self.model.field
        semaforo = self.model.semaforo
        thr = self.model.threshold

        from .semaforo import _novelty_max, _novelty_col, _r_field

        nov_max = _novelty_max(field, omega)
        nov_col = _novelty_col(field, omega)
        r_f = _r_field(field)

        nivel = semaforo.nivel(nov_max)

        # Confirmación naranja→rojo con slope(r)
        if nivel == "naranja":
            slope_r = _slope_r(field)
            if slope_r > 0:
                nivel = "rojo"

        return ResultadoDeteccion(
            t_min=t_min,
            novelty_max=nov_max,
            novelty_col=nov_col,
            r_field=r_f,
            nivel=nivel,
        )


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _slope_r(field) -> float:
    """Estima la pendiente de r(t) en las últimas muestras del campo.

    Devuelve un valor positivo si r está subiendo (correlaciona con
    silencio pre-ictal ordenado, confirmación naranja→rojo).
    """
    hist = getattr(field, "_r_history", None)
    if hist is None or len(hist) < 3:
        return 0.0
    arr = np.array(list(hist)[-20:], dtype=float)
    x = np.arange(len(arr))
    slope = float(np.polyfit(x, arr, 1)[0])
    return slope
