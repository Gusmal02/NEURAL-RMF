"""Lectura de archivos EDF y selección del diadema de 4 canales."""

import numpy as np
import pyedflib

DIADEMA_CHANNELS = ["F7", "T7", "F8", "T8"]

# Alias comunes en distintos datasets
_ALIAS = {
    "EEG F7": "F7", "EEG F7-REF": "F7", "EEG F7-LE": "F7",
    "EEG T7": "T7", "EEG T7-REF": "T7", "EEG T7-LE": "T7",
    "EEG T3": "T7",  # nombre antiguo del T7
    "EEG F8": "F8", "EEG F8-REF": "F8", "EEG F8-LE": "F8",
    "EEG T8": "T8", "EEG T8-REF": "T8", "EEG T8-LE": "T8",
    "EEG T4": "T8",  # nombre antiguo del T8
}


def read_edf(path: str, channels: list[str] | None = None) -> tuple[np.ndarray, float, list[str]]:
    """
    Lee un EDF y devuelve (señal, fs, nombres_canales).

    señal: (n_canales, n_muestras)  float32
    """
    if channels is None:
        channels = DIADEMA_CHANNELS

    with pyedflib.EdfReader(path) as f:
        all_labels = [f.getLabel(i) for i in range(f.signals_in_file)]
        fs_list    = [f.getSampleFrequency(i) for i in range(f.signals_in_file)]

        label_to_idx = {}
        for idx, raw in enumerate(all_labels):
            canonical = _ALIAS.get(raw, raw.strip())
            label_to_idx[canonical] = idx

        selected_idx = []
        selected_names = []
        for ch in channels:
            if ch in label_to_idx:
                selected_idx.append(label_to_idx[ch])
                selected_names.append(ch)
            else:
                raise ValueError(
                    f"Canal '{ch}' no encontrado en {path}. "
                    f"Disponibles: {list(label_to_idx.keys())}"
                )

        fs = fs_list[selected_idx[0]]
        signals = np.vstack([f.readSignal(i).astype(np.float32) for i in selected_idx])

    return signals, float(fs), selected_names


def list_channels(path: str) -> list[str]:
    """Devuelve los nombres de canal disponibles en el EDF."""
    with pyedflib.EdfReader(path) as f:
        return [f.getLabel(i) for i in range(f.signals_in_file)]
