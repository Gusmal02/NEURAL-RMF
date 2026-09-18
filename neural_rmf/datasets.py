"""Descarga de datasets de PhysioNet para NEURAL-RMF.

Funciones exportadas:
    download_chbmit(patient_id, dest_dir) -> list[Path]
    download_siena(patient_id, dest_dir) -> list[Path]
    list_chbmit_patients() -> list[str]
    list_siena_patients() -> list[str]
"""

from __future__ import annotations
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional

_CHBMIT_BASE = "https://physionet.org/files/chbmit/1.0.0"
_SIENA_BASE  = "https://physionet.org/files/siena-scalp-eeg/1.0.0"

_CHBMIT_PATIENTS = [f"chb{i:02d}" for i in range(1, 25)]  # chb01 … chb24
_SIENA_PATIENTS  = [f"PN{i:02d}" for i in range(0, 15)]   # PN00 … PN14


def list_chbmit_patients() -> List[str]:
    """Devuelve los IDs de pacientes disponibles en CHB-MIT."""
    return list(_CHBMIT_PATIENTS)


def list_siena_patients() -> List[str]:
    """Devuelve los IDs de pacientes disponibles en Siena Scalp EEG."""
    return list(_SIENA_PATIENTS)


def download_chbmit(
    patient_id: str,
    dest_dir: str = "data/chbmit",
    max_files: Optional[int] = None,
    verbose: bool = True,
) -> List[Path]:
    """
    Descarga los archivos EDF de un paciente de CHB-MIT desde PhysioNet.

    patient_id : e.g. "chb01"
    dest_dir   : directorio local donde guardar los archivos
    max_files  : límite de archivos a descargar (None = todos)
    verbose    : imprime progreso
    Devuelve   : lista de rutas a los archivos descargados
    """
    dest = Path(dest_dir) / patient_id
    dest.mkdir(parents=True, exist_ok=True)

    index_url = f"{_CHBMIT_BASE}/{patient_id}/{patient_id}-summary.txt"
    edf_urls = _fetch_chbmit_file_list(patient_id, index_url, verbose)

    if max_files is not None:
        edf_urls = edf_urls[:max_files]

    downloaded: List[Path] = []
    for url in edf_urls:
        fname = Path(url).name
        local = dest / fname
        if local.exists():
            if verbose:
                print(f"  [skip] {fname} ya existe")
            downloaded.append(local)
            continue
        if verbose:
            print(f"  [↓] {fname} …")
        try:
            urllib.request.urlretrieve(url, local)
            downloaded.append(local)
        except urllib.error.URLError as e:
            print(f"  [error] {fname}: {e}")
    return downloaded


def download_siena(
    patient_id: str,
    dest_dir: str = "data/siena",
    max_files: Optional[int] = None,
    verbose: bool = True,
) -> List[Path]:
    """
    Descarga los archivos EDF de un paciente de Siena Scalp EEG desde PhysioNet.

    patient_id : e.g. "PN00"
    dest_dir   : directorio local donde guardar los archivos
    max_files  : límite de archivos a descargar (None = todos)
    verbose    : imprime progreso
    Devuelve   : lista de rutas a los archivos descargados
    """
    dest = Path(dest_dir) / patient_id
    dest.mkdir(parents=True, exist_ok=True)

    edf_urls = _fetch_siena_file_list(patient_id, verbose)

    if max_files is not None:
        edf_urls = edf_urls[:max_files]

    downloaded: List[Path] = []
    for url in edf_urls:
        fname = Path(url).name
        local = dest / fname
        if local.exists():
            if verbose:
                print(f"  [skip] {fname} ya existe")
            downloaded.append(local)
            continue
        if verbose:
            print(f"  [↓] {fname} …")
        try:
            urllib.request.urlretrieve(url, local)
            downloaded.append(local)
        except urllib.error.URLError as e:
            print(f"  [error] {fname}: {e}")
    return downloaded


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _fetch_chbmit_file_list(patient_id: str, summary_url: str, verbose: bool) -> List[str]:
    """Parsea el summary.txt de CHB-MIT para extraer la lista de EDFs."""
    try:
        with urllib.request.urlopen(summary_url) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
    except urllib.error.URLError:
        if verbose:
            print(f"  [warn] no se pudo descargar el índice de {patient_id}; intentando listado directo")
        return _direct_edf_list(_CHBMIT_BASE, patient_id)

    edfs = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("File Name:"):
            fname = line.split(":", 1)[1].strip()
            if fname.endswith(".edf"):
                edfs.append(f"{_CHBMIT_BASE}/{patient_id}/{fname}")
    return edfs


def _fetch_siena_file_list(patient_id: str, verbose: bool) -> List[str]:
    """Construye URLs de EDFs de Siena a partir de la convención de nombres conocida."""
    base = f"{_SIENA_BASE}/{patient_id}"
    # Siena usa nombres como PN00_1.edf, PN00_2.edf, …
    # Intenta hasta el archivo 10 (la mayoría de pacientes tienen 1-5)
    edfs = []
    for i in range(1, 11):
        url = f"{base}/{patient_id}_{i}.edf"
        try:
            req = urllib.request.Request(url, method="HEAD")
            urllib.request.urlopen(req)
            edfs.append(url)
        except urllib.error.URLError:
            break
    if not edfs and verbose:
        print(f"  [warn] no se encontraron EDFs para {patient_id} en Siena")
    return edfs


def _direct_edf_list(base_url: str, patient_id: str) -> List[str]:
    """Fallback: construye lista de EDFs por convención de nombres CHB-MIT."""
    edfs = []
    for i in range(1, 42):
        url = f"{base_url}/{patient_id}/{patient_id}_{i:02d}.edf"
        try:
            req = urllib.request.Request(url, method="HEAD")
            urllib.request.urlopen(req)
            edfs.append(url)
        except urllib.error.URLError:
            continue
    return edfs
