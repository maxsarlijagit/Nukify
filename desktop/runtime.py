# SPDX-License-Identifier: GPL-3.0-or-later
"""Platform paths for the private compositor and its isolated Python."""
import os
import shutil
from pathlib import Path
import sys


def engine_path():
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).resolve().parent
        if sys.platform == 'darwin':
            return str(base.parent / 'Resources/engine/Blender.app/Contents/MacOS/Blender')
        return str(base / 'engine' / ('blender.exe' if sys.platform == 'win32' else 'blender'))
    configured = os.environ.get('NUKIFY_BLENDER') or shutil.which('blender')
    if configured:
        return configured
    if sys.platform == 'darwin':
        return '/Applications/Blender.app/Contents/MacOS/Blender'
    return str(Path(__file__).resolve().parents[1] / 'engine' / ('blender.exe' if sys.platform == 'win32' else 'blender'))


def engine_resources(executable):
    executable = Path(executable)
    if executable.parent.name == 'MacOS':
        return executable.parent.parent / 'Resources'
    return executable.parent


def ocio_path(executable):
    return engine_resources(executable) / '4.5/datafiles/colormanagement/config.ocio'


def worker_python(executable=None):
    """Blender reports its executable as sys.executable; never reuse the UI app."""
    executable = Path(executable or sys.executable)
    if executable.name.lower().startswith('python'):
        return executable
    directory = engine_resources(executable) / '4.5/python/bin'
    return directory / ('python.exe' if sys.platform == 'win32' else 'python3.11')
