"""
core/__init__.py
Re-exports the public API so users can do:
    from core.field_engine import build_field, measure_window
regardless of whether field_engine is a .pyd (Windows) or .so (Linux) binary.
"""
