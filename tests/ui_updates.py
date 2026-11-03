"""Actual app/update dialog layout and save/render guards; never installs anything."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'desktop'))
from PySide6.QtCore import QPoint
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QMessageBox
from app import Window, STYLE
from i18n import save_language
from test_updates import release
import updates

application = QApplication([])
QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
application.setStyle('Fusion')
application.setStyleSheet(STYLE)
out = root / 'validation/updates'
out.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as directory, patch('app.DATA', Path(directory)):
    save_language(directory, 'es')
    window = Window()
    window.live_toggle.setChecked(False)
    window.live_timer.stop()
    window.cache_scan.stop()
    window.show()
    controller = window.updates
    fixture = release()
    fixture['body'] = '# Novedades\n\n- Comprobación automática de versiones en GitHub.\n- Changelog antes de actualizar.\n- Corrección de lectura de capas EXR.\n\nValidación visual con una release simulada.'
    controller.show_release(updates.select_release([fixture], '0.10.1'))
    for width, height in ((1024, 768), (1440, 940)):
        window.resize(width, height)
        controller.dialog.move(window.pos() + QPoint(30, 60))
        for _ in range(10): application.processEvents()
        assert window.width() == width, (width, window.width())
        for button in (controller.dialog.primary, controller.dialog.later, controller.dialog.skip, controller.dialog.web):
            assert controller.dialog.rect().contains(button.geometry())
        window.grab().save(str(out / f'window-{width}.png'))
        controller.dialog.grab().save(str(out / f'dialog-{width}.png'))
    controller.installer = 'fixture.exe'
    with patch('update_ui.subprocess.Popen') as launch:
        window.dirty = True
        with patch('app.QMessageBox.question', return_value=QMessageBox.Cancel):
            controller.launch_installer()
            launch.assert_not_called()
        with patch('app.QMessageBox.question', return_value=QMessageBox.Save), patch.object(window, 'save_project', return_value=False):
            controller.launch_installer()
            launch.assert_not_called()
        window.dirty = False
        window.process = object()
        with patch('app.QMessageBox.information'):
            controller.launch_installer()
            launch.assert_not_called()
        window.process = None
    controller.dialog.close()
    window.close()
print('UPDATE_LAYOUT_AND_CLOSE_GUARDS_OK')
