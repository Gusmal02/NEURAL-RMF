"""Auditoría de falsas alarmas y validación clínica de alertas NEURAL-RMF."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class AlertaRegistrada:
    """Registro de una alerta emitida por el semáforo."""

    run_id: str
    t_alerta_min: float
    nivel: str                     # "naranja" | "rojo"
    novelty_max: float
    novelty_col: float
    confirmada: Optional[bool] = None   # True=TP, False=FP, None=sin revisión
    t_onset_real_min: Optional[float] = None
    lead_min: Optional[float] = None    # t_onset_real - t_alerta (>0 = anticipación)
    notas: str = ""


@dataclass
class ReporteValidacion:
    """Resultado agregado de la sesión de validación."""

    n_total: int = 0
    n_confirmadas: int = 0
    n_falsas: int = 0
    n_pendientes: int = 0
    tasa_fp: float = 0.0
    lead_medio_min: float = 0.0
    lead_min_min: float = 0.0
    lead_max_min: float = 0.0
    alertas: List[AlertaRegistrada] = field(default_factory=list)


class Validator:
    """Auditoría de alertas post-hoc para validación clínica.

    Flujo típico:
        val = Validator()
        val.registrar(alerta)
        val.confirmar_alerta("run_01", es_tp=True, t_onset_real=74.5)
        reporte = val.reporte()
        val.exportar("auditoria.json")
    """

    def __init__(self) -> None:
        self._alertas: List[AlertaRegistrada] = []

    # ------------------------------------------------------------------
    # Registro
    # ------------------------------------------------------------------

    def registrar(self, alerta: AlertaRegistrada) -> None:
        """Añade una alerta al registro de auditoría."""
        self._alertas.append(alerta)

    def registrar_desde_resultado(
        self,
        run_id: str,
        t_alerta_min: float,
        nivel: str,
        novelty_max: float,
        novelty_col: float,
    ) -> AlertaRegistrada:
        """Crea y registra una alerta desde los campos básicos del detector."""
        a = AlertaRegistrada(
            run_id=run_id,
            t_alerta_min=t_alerta_min,
            nivel=nivel,
            novelty_max=novelty_max,
            novelty_col=novelty_col,
        )
        self.registrar(a)
        return a

    # ------------------------------------------------------------------
    # Confirmación
    # ------------------------------------------------------------------

    def confirmar_alerta(
        self,
        run_id: str,
        es_tp: bool,
        t_onset_real_min: Optional[float] = None,
        notas: str = "",
    ) -> bool:
        """Marca una alerta como verdadero positivo o falso positivo.

        Args:
            run_id: Identificador del registro EDF.
            es_tp: True si hubo crisis real tras la alerta.
            t_onset_real_min: Minuto del onset ictal real (para calcular lead).
            notas: Observación clínica libre.

        Returns:
            True si se encontró y actualizó la alerta, False si no se halló.
        """
        for a in reversed(self._alertas):
            if a.run_id == run_id and a.confirmada is None:
                a.confirmada = es_tp
                a.notas = notas
                if t_onset_real_min is not None:
                    a.t_onset_real_min = t_onset_real_min
                    a.lead_min = t_onset_real_min - a.t_alerta_min
                return True
        return False

    def confirmar_todas_pendientes(
        self,
        run_id: str,
        es_tp: bool,
        t_onset_real_min: Optional[float] = None,
    ) -> int:
        """Confirma todas las alertas pendientes de un run_id. Devuelve el conteo."""
        n = 0
        for a in self._alertas:
            if a.run_id == run_id and a.confirmada is None:
                a.confirmada = es_tp
                if t_onset_real_min is not None:
                    a.t_onset_real_min = t_onset_real_min
                    a.lead_min = t_onset_real_min - a.t_alerta_min
                n += 1
        return n

    # ------------------------------------------------------------------
    # Reporte
    # ------------------------------------------------------------------

    def reporte(self) -> ReporteValidacion:
        """Calcula métricas agregadas de la auditoría actual."""
        r = ReporteValidacion(alertas=list(self._alertas))
        r.n_total = len(self._alertas)
        r.n_confirmadas = sum(1 for a in self._alertas if a.confirmada is True)
        r.n_falsas = sum(1 for a in self._alertas if a.confirmada is False)
        r.n_pendientes = sum(1 for a in self._alertas if a.confirmada is None)

        if r.n_total > 0:
            revisadas = r.n_confirmadas + r.n_falsas
            r.tasa_fp = r.n_falsas / revisadas if revisadas > 0 else 0.0

        leads = [
            a.lead_min
            for a in self._alertas
            if a.lead_min is not None and a.confirmada is True
        ]
        if leads:
            r.lead_medio_min = float(np.mean(leads))
            r.lead_min_min = float(np.min(leads))
            r.lead_max_min = float(np.max(leads))

        return r

    def resumen_texto(self) -> str:
        """Devuelve un resumen legible de la auditoría."""
        r = self.reporte()
        lines = [
            f"=== Auditoría NEURAL-RMF ===",
            f"Alertas registradas : {r.n_total}",
            f"  Confirmadas (TP)  : {r.n_confirmadas}",
            f"  Falsas (FP)       : {r.n_falsas}",
            f"  Pendientes        : {r.n_pendientes}",
            f"Tasa de falsas alarmas: {r.tasa_fp:.1%}",
        ]
        if r.lead_medio_min > 0:
            lines += [
                f"Lead medio (TP)   : {r.lead_medio_min:.1f} min",
                f"Lead rango        : [{r.lead_min_min:.1f}, {r.lead_max_min:.1f}] min",
            ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Exportación / importación
    # ------------------------------------------------------------------

    def exportar(self, ruta: str | Path) -> Path:
        """Guarda el registro completo en JSON.

        Args:
            ruta: Ruta de destino (.json).

        Returns:
            Path del archivo escrito.
        """
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "generado": datetime.now().isoformat(),
            "reporte": {
                "n_total": len(self._alertas),
                "n_confirmadas": sum(1 for a in self._alertas if a.confirmada is True),
                "n_falsas": sum(1 for a in self._alertas if a.confirmada is False),
                "n_pendientes": sum(1 for a in self._alertas if a.confirmada is None),
            },
            "alertas": [
                {
                    "run_id": a.run_id,
                    "t_alerta_min": a.t_alerta_min,
                    "nivel": a.nivel,
                    "novelty_max": a.novelty_max,
                    "novelty_col": a.novelty_col,
                    "confirmada": a.confirmada,
                    "t_onset_real_min": a.t_onset_real_min,
                    "lead_min": a.lead_min,
                    "notas": a.notas,
                }
                for a in self._alertas
            ],
        }

        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        return ruta

    @classmethod
    def desde_json(cls, ruta: str | Path) -> "Validator":
        """Carga un registro de auditoría previamente exportado."""
        ruta = Path(ruta)
        with open(ruta, encoding="utf-8") as f:
            payload = json.load(f)

        val = cls()
        for d in payload.get("alertas", []):
            val.registrar(
                AlertaRegistrada(
                    run_id=d["run_id"],
                    t_alerta_min=d["t_alerta_min"],
                    nivel=d["nivel"],
                    novelty_max=d["novelty_max"],
                    novelty_col=d["novelty_col"],
                    confirmada=d.get("confirmada"),
                    t_onset_real_min=d.get("t_onset_real_min"),
                    lead_min=d.get("lead_min"),
                    notas=d.get("notas", ""),
                )
            )
        return val


# ---------------------------------------------------------------------------
# Funciones de conveniencia
# ---------------------------------------------------------------------------

def confirmar_alerta(
    validator: Validator,
    run_id: str,
    es_tp: bool,
    t_onset_real_min: Optional[float] = None,
    notas: str = "",
) -> bool:
    """Atajo para `validator.confirmar_alerta()`."""
    return validator.confirmar_alerta(run_id, es_tp, t_onset_real_min, notas)


def reporte(validator: Validator) -> ReporteValidacion:
    """Atajo para `validator.reporte()`."""
    return validator.reporte()


def exportar(validator: Validator, ruta: str | Path) -> Path:
    """Atajo para `validator.exportar()`."""
    return validator.exportar(ruta)
