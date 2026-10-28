import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from runtime import engine_path


class RuntimeTests(unittest.TestCase):
    def test_frozen_ignores_external_override(self):
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', r'C:\Apps\Nukify\Nukify.exe'), patch.dict(os.environ, {'NUKIFY_BLENDER': r'G:\unavailable.exe'}):
            self.assertEqual(Path(engine_path()), Path(r'C:\Apps\Nukify\engine\blender.exe'))

    def test_source_allows_development_engine(self):
        with patch.object(sys, 'frozen', False, create=True), patch.dict(os.environ, {'NUKIFY_BLENDER': r'C:\test\blender.exe'}):
            self.assertEqual(engine_path(), r'C:\test\blender.exe')
