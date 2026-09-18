"""NEURAL-RMF — Detección pre-ictal de epilepsia por Campo de Memoria Resonante."""

from .api import (
    calibrate,
    detect,
    run_edf,
    plot_semaforo,
    CalibratedModel,
    ResultadoDeteccion,
)
from .edf import read_edf, list_channels, DIADEMA_CHANNELS
from .semaforo import calibrar_umbral, Semaforo
from .validator import (
    Validator,
    AlertaRegistrada,
    ReporteValidacion,
    confirmar_alerta,
    reporte,
    exportar,
)
from .streaming import StreamMonitor, EventoStream
from .stimulus_gate import StimulusGate, EventoEstimulo

__version__ = "0.1.0"
__all__ = [
    # Detección
    "calibrate",
    "detect",
    "plot_semaforo",
    "CalibratedModel",
    "ResultadoDeteccion",
    # EDF
    "read_edf",
    "list_channels",
    "DIADEMA_CHANNELS",
    # Semáforo
    "calibrar_umbral",
    "Semaforo",
    # Validación clínica
    "Validator",
    "AlertaRegistrada",
    "ReporteValidacion",
    "confirmar_alerta",
    "reporte",
    "exportar",
    # Monitoreo en tiempo real
    "StreamMonitor",
    "EventoStream",
    # Estímulo cerrado
    "StimulusGate",
    "EventoEstimulo",
]
