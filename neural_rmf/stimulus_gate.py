"""Puerta de estímulo cerrado — StimulusGate.

Envuelve un ``StreamMonitor`` y dispara un estímulo externo (auditivo o
transcraneal) cuando el semáforo alcanza el nivel configurado.

El módulo no depende de ningún SDK de hardware.  La integración real se
realiza a través del callback ``on_stimulus``, que el integrador conecta a
su propio driver (altavoces, BLE, USB, etc.).

Diseño clínico (E_ANTICICTAL):
    - Intervenir TEMPRANO es más efectivo que tarde: trigger en "naranja".
    - La amplitud tiene un punto óptimo individual (A ≈ 0.02 en la
      simulación); no es monótona — no aumentar sin calibración.
    - Cooldown obligatorio para evitar re-disparo inmediato.
    - El bucle cerrado lo cierra el dispositivo externo, no este módulo.

Uso mínimo::

    from neural_rmf import calibrate
    from neural_rmf.edf import read_edf
    from neural_rmf.stimulus_gate import StimulusGate

    data, fs = read_edf("paciente.edf")
    model = calibrate(data, fs)

    def mi_altavoz(tipo, intensidad, t_min):
        print(f"[{t_min:.1f} min] Estímulo {tipo} intensidad={intensidad:.3f}")

    gate = StimulusGate(model, on_stimulus=mi_altavoz)
    gate.run(data, fs)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import numpy as np

from .api import CalibratedModel, ResultadoDeteccion
from .streaming import EventoStream, StreamMonitor


# ---------------------------------------------------------------------------
# Tipos públicos
# ---------------------------------------------------------------------------

@dataclass
class EventoEstimulo:
    """Registro de un estímulo emitido por la puerta."""

    t_min: float
    tipo: str          # "auditory" | "transcranial" | personalizado
    intensidad: float
    nivel_trigger: str  # nivel del semáforo que disparó el estímulo
    novelty_max: float


# ---------------------------------------------------------------------------
# StimulusGate
# ---------------------------------------------------------------------------

class StimulusGate:
    """Puerta de estímulo cerrado sobre un registro EEG.

    Cuando el semáforo alcanza el nivel de trigger, dispara ``on_stimulus``
    con el tipo y la intensidad configurados.  Incluye un cooldown para evitar
    re-disparos rápidos.

    Args:
        model: Modelo calibrado devuelto por ``calibrate()``.
        on_stimulus: Callback de hardware.
            Firma: ``callback(tipo: str, intensidad: float, t_min: float)``.
            Se llama cada vez que se supera el umbral y el cooldown lo permite.
        trigger_nivel: Nivel mínimo que activa el estímulo.
            "naranja" (recomendado — intervención temprana) o "rojo".
        tipo: Tipo de estímulo a reportar al callback.  Valor libre; el
            hardware lo interpreta.  Convenios habituales: ``"auditory"``
            (ritmo auditivo), ``"transcranial"`` (estimulación transcraneal).
        intensidad: Intensidad del estímulo en unidades del dispositivo.
            0.0–1.0 normalizado.  Por defecto 0.02 (punto óptimo experimental).
        cooldown_min: Tiempo mínimo en minutos entre dos estímulos consecutivos.
            Evita re-disparo durante la misma ventana de alerta.
        window_sec: Duración de cada ventana EEG en segundos.
        stride_sec: Paso entre ventanas en segundos.
        on_alert: Callback adicional que se llama en cada ventana naranja/rojo,
            independientemente del cooldown (para monitoreo sin estímulo).
        on_tick: Callback opcional en cada ventana procesada.
    """

    def __init__(
        self,
        model: CalibratedModel,
        on_stimulus: Optional[Callable[[str, float, float], None]] = None,
        trigger_nivel: str = "naranja",
        tipo: str = "auditory",
        intensidad: float = 0.02,
        cooldown_min: float = 5.0,
        window_sec: float = 30.0,
        stride_sec: float = 30.0,
        on_alert: Optional[Callable[[str, ResultadoDeteccion], None]] = None,
        on_tick: Optional[Callable[[float, ResultadoDeteccion], None]] = None,
    ) -> None:
        if trigger_nivel not in ("naranja", "rojo"):
            raise ValueError("trigger_nivel debe ser 'naranja' o 'rojo'")
        if not (0.0 <= intensidad <= 1.0):
            raise ValueError("intensidad debe estar en [0.0, 1.0]")
        if cooldown_min < 0:
            raise ValueError("cooldown_min debe ser ≥ 0")

        self.model = model
        self.on_stimulus = on_stimulus
        self.trigger_nivel = trigger_nivel
        self.tipo = tipo
        self.intensidad = intensidad
        self.cooldown_min = cooldown_min

        self._estimulos: List[EventoEstimulo] = []
        self._ultimo_estimulo_min: Optional[float] = None

        # El StreamMonitor gestiona la lógica de ventanas y semáforo
        self._monitor = StreamMonitor(
            model=model,
            on_alert=self._on_alert_interna,
            on_tick=on_tick,
            window_sec=window_sec,
            stride_sec=stride_sec,
        )
        # Callback adicional del caller (monitoreo puro)
        self._on_alert_extra = on_alert

    # ------------------------------------------------------------------
    # Ejecución
    # ------------------------------------------------------------------

    def run(
        self,
        eeg: np.ndarray,
        fs: float,
        start_sec: float = 0.0,
    ) -> List[EventoEstimulo]:
        """Procesa el array EEG completo y dispara estímulos según el semáforo.

        Args:
            eeg: Array ``(n_canales, n_muestras)`` ya filtrado para los
                canales de la diadema.
            fs: Frecuencia de muestreo en Hz.
            start_sec: Offset temporal de la primera muestra.

        Returns:
            Lista de estímulos emitidos durante el stream.
        """
        self._estimulos.clear()
        self._ultimo_estimulo_min = None
        self._monitor.run(eeg, fs, start_sec)
        return list(self._estimulos)

    def push_window(
        self,
        ventana: np.ndarray,
        fs: float,
        t_min: float,
    ) -> ResultadoDeteccion:
        """Procesa una única ventana en modo push (hardware en tiempo real).

        Args:
            ventana: Array ``(n_canales, n_muestras)`` de la ventana actual.
            fs: Frecuencia de muestreo.
            t_min: Tiempo en minutos desde el inicio de la grabación.

        Returns:
            ``ResultadoDeteccion`` para esta ventana.
        """
        return self._monitor.push_window(ventana, fs, t_min)

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    @property
    def estimulos(self) -> List[EventoEstimulo]:
        """Lista de estímulos emitidos durante el stream."""
        return list(self._estimulos)

    @property
    def eventos(self) -> List[EventoStream]:
        """Lista de eventos naranja/rojo registrados por el monitor interno."""
        return self._monitor.eventos

    @property
    def nivel_actual(self) -> str:
        """Nivel del semáforo en la última ventana procesada."""
        return self._monitor.nivel_actual

    def reset(self) -> None:
        """Reinicia el historial de estímulos y el cooldown."""
        self._estimulos.clear()
        self._ultimo_estimulo_min = None
        self._monitor.reset()

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _on_alert_interna(self, nivel: str, resultado: ResultadoDeteccion) -> None:
        """Callback interno del StreamMonitor — decide si disparar el estímulo."""
        # Propagar al callback extra de monitoreo si existe
        if self._on_alert_extra is not None:
            self._on_alert_extra(nivel, resultado)

        # Verificar si el nivel alcanza el umbral de trigger
        if not self._nivel_alcanza_trigger(nivel):
            return

        t_min = resultado.t_min

        # Respetar el cooldown
        if self._ultimo_estimulo_min is not None:
            if t_min - self._ultimo_estimulo_min < self.cooldown_min:
                return

        # Disparar estímulo
        self._ultimo_estimulo_min = t_min
        evento = EventoEstimulo(
            t_min=t_min,
            tipo=self.tipo,
            intensidad=self.intensidad,
            nivel_trigger=nivel,
            novelty_max=resultado.novelty_max,
        )
        self._estimulos.append(evento)

        if self.on_stimulus is not None:
            self.on_stimulus(self.tipo, self.intensidad, t_min)

    def _nivel_alcanza_trigger(self, nivel: str) -> bool:
        """Devuelve True si `nivel` es igual o más severo que `trigger_nivel`."""
        _orden = {"verde": 0, "naranja": 1, "rojo": 2}
        return _orden.get(nivel, 0) >= _orden.get(self.trigger_nivel, 1)
