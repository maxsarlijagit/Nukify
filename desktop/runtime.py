# SPDX-License-Identifier: GPL-3.0-or-later
"""Installed builds always use their private compositor runtime."""
import os
import shutil
from pathlib import Path
import sys


def engine_path():
    if getattr(sys, 'frozen', False):
        return str(Path(sys.executable).resolve().parent / 'engine' / 'blender.exe')
    return os.environ.get('NUKIFY_BLENDER') or shutil.which('blender') or str(Path(__file__).resolve().parents[1]/'engine/blender.exe')
