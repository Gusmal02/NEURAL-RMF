import sys
import os
from pathlib import Path

def _load_field_engine():
    _dir = Path(__file__).parent
    if sys.platform.startswith("win"):
        candidates = list(_dir.glob("field_engine*.pyd"))
    else:
        candidates = list(_dir.glob("field_engine*.so"))

    if candidates:
        import importlib.util
        spec = importlib.util.spec_from_file_location("field_engine", candidates[0])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    # Fallback: pure Python implementation (no compiled binary available)
    from . import field_engine as _py_fe
    return _py_fe

_fe = _load_field_engine()

build_field      = _fe.build_field
calibrate_field  = _fe.calibrate_field
sense            = _fe.sense
forget_step      = _fe.forget_step
