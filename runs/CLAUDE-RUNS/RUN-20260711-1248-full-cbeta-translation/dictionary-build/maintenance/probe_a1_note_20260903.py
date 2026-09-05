#!/usr/bin/env python3
"""Probe: t_1793c3514a69 s1 Note (the missed vague site) + context."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "a1_eng", HERE / "a1_transform_20260903.py")
eng = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eng)

by_id = eng.clone_state()
note = str(by_id["t_1793c3514a69"]["Senses"][0].get("Note") or "")
print(f"Note ({len(note)} chars):\n{note}")
