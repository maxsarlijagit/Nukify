import copy
import json
import os
from pathlib import Path
import string
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from i18n import read_language, save_language, set_language, tr
from translations import PAIRS
from PySide6.QtWidgets import QApplication, QPushButton, QDialogButtonBox, QComboBox, QDialog
from PySide6.QtCore import QTimer
from app import Window, ROOT
from genai_ui import GenAIWindow


class LanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def tearDown(self): set_language('en')

    def test_default_and_corrupt_preferences(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(read_language(tmp), 'en')
            for value in ('{broken', '[]', 'null', '{"language":"fr"}', '{"language":[]}'):
                (Path(tmp) / 'preferences.json').write_text(value)
                self.assertEqual(read_language(tmp), 'en')

    def test_roundtrip_preserves_other_preferences(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'preferences.json'
            path.write_text('{"theme":"dark"}')
            save_language(tmp, 'es')
            self.assertEqual(read_language(tmp), 'es')
            self.assertEqual(json.loads(path.read_text())['theme'], 'dark')
            save_language(tmp, 'en')
            self.assertEqual(read_language(tmp), 'en')
            with self.assertRaises(ValueError): save_language(tmp, 'fr')

    def test_templates_preserve_format_fields(self):
        formatter = string.Formatter()
        for source, translated in PAIRS:
            fields = lambda text: sorted((key, spec, conversion or '') for _, key, spec, conversion in formatter.parse(text) if key is not None)
            self.assertEqual(fields(source), fields(translated), source)

    def test_translation_does_not_touch_unknown_or_user_text(self):
        for language in ('en', 'es'):
            set_language(language)
            for value in ('Read1', 'fal-ai/flux/dev', 'My prompt: Guardar', 'C:/shots/Crear.png'):
                self.assertEqual(tr(value), value)
        set_language('en'); self.assertEqual(tr('Guardar'), 'Save')
        set_language('es'); self.assertEqual(tr('Output folder'), 'Carpeta de salida')

    def window(self, tmp, language):
        save_language(tmp, language)
        with patch('app.DATA', Path(tmp)): window = Window()
        window.live_toggle.setChecked(False); window.live_timer.stop(); window.cache_scan.stop()
        return window

    def dispose(self, window):
        window.dirty = False; window.close(); window.deleteLater()
        self.app.processEvents()

    def test_both_languages_main_genai_and_project_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            for lang, save, category, create in [('en', 'Save', 'Generate image', 'Create'), ('es', 'Guardar', 'Generar imagen', 'Crear')]:
                window = self.window(tmp, lang)
                before = copy.deepcopy(window.project)
                try:
                    self.assertIn(save, [b.text() for b in window.findChildren(QPushButton)])
                    self.assertEqual(window.property_tabs.tabText(0), 'Node' if lang == 'en' else 'Nodo')
                    panel = GenAIWindow(window, ROOT, Path(tmp))
                    self.assertEqual(panel.category.itemText(0), category)
                    self.assertEqual(panel.category.itemData(0), 'text-to-image')
                    self.assertEqual(panel.settings_tabs.tabText(0), create)
                    panel.prompt.setPlainText('Guardar la identidad, Create a scene')
                    self.assertEqual(panel.prompt.toPlainText(), 'Guardar la identidad, Create a scene')
                    self.assertEqual(window.project, before)
                    buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
                    self.assertEqual(buttons.button(QDialogButtonBox.Save).text().replace('&', ''), save)
                    panel.close(); panel.deleteLater()
                finally: self.dispose(window)

    def test_language_dialog_saves_for_next_launch_without_mutating_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            window = self.window(tmp, 'en'); before = copy.deepcopy(window.project)
            def choose():
                dialog = self.app.activeModalWidget()
                self.assertIsInstance(dialog, QDialog)
                combo = dialog.findChild(QComboBox, 'languageChoice')
                combo.setCurrentIndex(combo.findData('es'))
                dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Save).click()
            QTimer.singleShot(0, choose)
            from i18n import language_dialog
            language_dialog(window, tmp)
            self.assertEqual(read_language(tmp), 'es')
            self.assertEqual(tr('Guardar'), 'Save')
            self.assertEqual(window.project, before)
            self.dispose(window)
            window = self.window(tmp, 'es')
            self.assertEqual(tr('Guardar'), 'Guardar')
            self.dispose(window)
