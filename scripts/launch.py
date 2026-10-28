# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nukify
nukify.register()


def setup():
    bpy.ops.nukify.workspace()
    bpy.ops.nukify.starter()
    return None


bpy.app.timers.register(setup, first_interval=1.0)
