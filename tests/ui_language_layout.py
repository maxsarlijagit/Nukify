"""Capture real Qt controls in both languages using isolated preferences (no API calls)."""
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'desktop'))
from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtGui import QFontDatabase
from app import Window
from genai_ui import GenAIWindow
from i18n import save_language
from ui_theme import STYLE

app = QApplication([])
font = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/segoeui.ttf'
if font.exists(): QFontDatabase.addApplicationFont(str(font))
app.setStyle('Fusion'); app.setStyleSheet(STYLE)
output = ROOT / 'validation'; output.mkdir(exist_ok=True)
scale = os.environ.get('QT_SCALE_FACTOR', '1')
results = []
with tempfile.TemporaryDirectory() as tmp:
    for language in ('en', 'es'):
        save_language(tmp, language)
        with patch('app.DATA', Path(tmp)): window = Window()
        window.live_toggle.setChecked(False); window.live_timer.stop(); window.cache_scan.stop()
        window.properties(next(n for n in window.project['nodes'] if n['id'] == 'Color1'))
        window.show()
        panel = GenAIWindow(window, ROOT, Path(tmp))
        for width, height in [(1440, 940), (1024, 768)]:
            window.resize(width, height); window.workspace_preset('comp')
            for _ in range(5): app.processEvents()
            window.graph.fit(); app.processEvents()
            assert window.width() == width
            assert window.viewer.canvas.height() > 100
            button = window.findChild(QPushButton, 'languageButton')
            assert button.isVisible() and button.width() >= button.sizeHint().width()
            filename = output / f'language-{language}-{width}-scale{scale}.png'
            assert window.grab().save(str(filename))
            panel.resize(width, height); panel.show()
            for _ in range(5): app.processEvents()
            assert panel.width() == width
            assert panel.generate.isVisible() and panel.estimate_button.isVisible()
            assert panel.grab().save(str(output / f'language-genai-{language}-{width}-scale{scale}.png'))
            panel.hide()
            results.append({'language': language, 'width': width, 'scale': scale, 'viewer_height': window.viewer.canvas.height()})
        panel.close(); panel.deleteLater()
        window.dirty = False; window.close(); window.deleteLater(); app.processEvents()
(output / f'language-layout-scale{scale}.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results))
