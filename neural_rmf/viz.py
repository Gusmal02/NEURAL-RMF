"""Visualización: curva de novelty + semáforo por minuto.

Uso:
    from neural_rmf import plot_semaforo
    plot_semaforo(resultado)       # muestra la figura
    plot_semaforo(resultado, save="figura.png")   # guarda sin mostrar
"""

from __future__ import annotations
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

_COLOR = {"verde": "#2ECC71", "naranja": "#F39C12", "rojo": "#E74C3C"}
_SEMAFORO_ORDER = ["verde", "naranja", "rojo"]


def plot_semaforo(resultado, save: str | None = None, show: bool = True):
    """
    Dibuja la curva de novelty_por_minuto coloreada por el semáforo.

    resultado : ResultadoDeteccion
    save      : ruta de archivo para guardar (PNG/PDF). Si es None, no guarda.
    show      : si True llama plt.show()
    """
    nov = np.asarray(resultado.novelty_por_minuto, dtype=float)
    minutos = np.arange(len(nov))
    thr = resultado.umbral_calibrado

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True,
                              gridspec_kw={"height_ratios": [3, 1]})

    ax = axes[0]
    ax.axhline(thr, color="gray", lw=1.2, ls="--", label=f"Umbral P80 = {thr:.3f}")

    # Pintar segmentos por color de semáforo
    for i, (m, n) in enumerate(zip(minutos, nov)):
        color = _color_for(n, thr, resultado, m)
        ax.bar(m, n, width=0.9, color=color, alpha=0.85, linewidth=0)

    if resultado.alerta_minuto is not None:
        ax.axvline(resultado.alerta_minuto, color="black", lw=1.5, ls=":",
                   label=f"Alerta naranja → min {resultado.alerta_minuto}")

    ax.set_ylabel("Novelty (1 − resonancia)")
    ax.set_title(
        f"NEURAL-RMF — Semáforo: {resultado.semaforo.upper()}  "
        f"| Lead time: {resultado.lead_time_min:.1f} min"
        if resultado.lead_time_min is not None
        else f"NEURAL-RMF — Semáforo: {resultado.semaforo.upper()}"
    )
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(nov.max() * 1.15, thr * 1.5))

    # Barra de semáforo inferior
    ax2 = axes[1]
    for i, m in enumerate(minutos):
        n = nov[i]
        c = _color_for(n, thr, resultado, m)
        ax2.bar(m, 1, width=0.9, color=c, linewidth=0)

    ax2.set_yticks([])
    ax2.set_xlabel("Minuto del registro")
    ax2.set_ylabel("Estado", fontsize=8)

    patches = [mpatches.Patch(color=_COLOR[s], label=s) for s in _SEMAFORO_ORDER]
    ax2.legend(handles=patches, loc="upper left", fontsize=8, ncol=3)

    plt.tight_layout()

    if save:
        fig.savefig(save, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def _color_for(novelty: float, thr: float, resultado, minuto: int) -> str:
    if novelty <= thr:
        return _COLOR["verde"]
    if resultado.alerta_minuto is not None and minuto >= resultado.alerta_minuto:
        return _COLOR.get(resultado.semaforo, _COLOR["naranja"])
    return _COLOR["naranja"]
