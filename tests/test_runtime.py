import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from runtime import engine_path, ocio_path, worker_python


class RuntimeTests(unittest.TestCase):
    def test_frozen_ignores_external_override(self):
        with patch.object(sys, 'platform', 'win32'), patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', str(Path('/Apps/Nukify/Nukify.exe').resolve())), patch.dict(os.environ, {'NUKIFY_BLENDER': r'G:\unavailable.exe'}):
            self.assertEqual(Path(engine_path()), Path('/Apps/Nukify/engine/blender.exe').resolve())

    def test_source_allows_development_engine(self):
        with patch.object(sys, 'frozen', False, create=True), patch.dict(os.environ, {'NUKIFY_BLENDER': r'C:\test\blender.exe'}):
            self.assertEqual(engine_path(), r'C:\test\blender.exe')

    def test_mac_bundle_ignores_override(self):
        with patch.object(sys, 'platform', 'darwin'), patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', str(Path('/Applications/Nukify.app/Contents/MacOS/Nukify').resolve())), patch.dict(os.environ, {'NUKIFY_BLENDER': '/external/blender'}):
            self.assertEqual(Path(engine_path()), Path('/Applications/Nukify.app/Contents/Resources/engine/Blender.app/Contents/MacOS/Blender').resolve())

    def test_mac_worker_and_color_resources(self):
        engine = '/Apps/Blender.app/Contents/MacOS/Blender'
        with patch.object(sys, 'platform', 'darwin'):
            self.assertEqual(worker_python(engine), Path('/Apps/Blender.app/Contents/Resources/4.5/python/bin/python3.11'))
            self.assertEqual(ocio_path(engine), Path('/Apps/Blender.app/Contents/Resources/4.5/datafiles/colormanagement/config.ocio'))
