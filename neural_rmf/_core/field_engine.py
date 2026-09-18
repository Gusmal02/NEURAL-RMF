"""
Pure-Python fallback for the neural_rmf field engine.

Loaded automatically when the compiled binary is not present, such as
during a direct GitHub source installation.  Implements the same public
interface as the binary (build_field, calibrate_field, sense, forget_step)
using a simplified statistical approximation.
"""

from __future__ import annotations
import numpy as np


class _Field:
    def __init__(self, N: int, omega_std: float, seed: int):
        rng = np.random.default_rng(seed)
        self._N = N
        raw = rng.normal(0.0, omega_std, (N, 3)).astype(np.float32)
        norms = np.linalg.norm(raw, axis=1, keepdims=True)
        norms = np.where(norms < 1e-8, 1.0, norms)
        self._omega = raw / norms
        self._memory: list[np.ndarray] = []
        self._weights: list[float] = []
        self._r = float(rng.uniform(0.85, 0.95))


def build_field(
    N: int = 50,
    K: float = 2.0,
    omega_std: float = 0.20,
    seed: int = 42,
) -> _Field:
    return _Field(N=N, omega_std=omega_std, seed=seed)


def calibrate_field(
    field: _Field,
    omegas: np.ndarray,
    n_expose: int = 10,
) -> None:
    omegas = np.asarray(omegas, dtype=np.float32)
    for omega in omegas:
        norm = float(np.linalg.norm(omega))
        if norm < 1e-8:
            continue
        omega_n = omega / norm
        for _ in range(n_expose):
            field._memory.append(omega_n.copy())
            field._weights.append(1.0)

    if len(omegas) == 0:
        return
    centroid = np.mean(omegas, axis=0)
    nc = float(np.linalg.norm(centroid))
    if nc > 1e-8:
        centroid /= nc
        alpha = 0.15
        field._omega = (1.0 - alpha) * field._omega + alpha * centroid[np.newaxis, :]
        norms = np.linalg.norm(field._omega, axis=1, keepdims=True)
        norms = np.where(norms < 1e-8, 1.0, norms)
        field._omega /= norms


def sense(field: _Field, omega: np.ndarray) -> dict:
    omega = np.asarray(omega, dtype=np.float32)
    norm = float(np.linalg.norm(omega))
    if norm < 1e-8:
        return {"max_res": 0.5, "mean_res": 0.5, "r_field": field._r}
    omega_n = omega / norm

    node_cos = np.clip(field._omega @ omega_n, 0.0, 1.0)
    node_max = float(np.max(node_cos))
    node_mean = float(np.mean(node_cos))

    if field._memory:
        mem_arr = np.stack(field._memory)           # (M, 3)
        mem_cos = np.clip(mem_arr @ omega_n, 0.0, 1.0)
        w = np.asarray(field._weights, dtype=np.float32)
        mem_max = float(np.max(mem_cos))
        mem_mean = float(np.average(mem_cos, weights=w))
        max_res  = 0.7 * mem_max  + 0.3 * node_max
        mean_res = 0.7 * mem_mean + 0.3 * node_mean
    else:
        max_res  = node_max
        mean_res = node_mean

    return {"max_res": max_res, "mean_res": mean_res, "r_field": field._r}


def forget_step(field: _Field, gamma: float = 0.003) -> None:
    if not field._weights:
        return
    decay = 1.0 - gamma
    field._weights = [w * decay for w in field._weights]
    alive = [(m, w) for m, w in zip(field._memory, field._weights) if w >= 0.01]
    if alive:
        mems, wts = zip(*alive)
        field._memory  = list(mems)
        field._weights = list(wts)
    else:
        field._memory  = []
        field._weights = []
