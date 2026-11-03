import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu
from update_ui import UpdateController
from test_updates import release
import updates


class TestWindow(QMainWindow):
    allow_close = False
    def closeEvent(self, event):
        if self.allow_close: event.accept()
        else: event.ignore()


class UpdateUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.window = TestWindow()
        self.menu = QMenu(self.window)
        self.controller = UpdateController(self.window, self.directory.name, self.menu)
        self.controller.version = '0.10.1'

    def tearDown(self):
        self.controller.stop()
        self.window.allow_close = True
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.directory.cleanup()

    def settle(self):
        deadline = time.monotonic() + 3
        while self.controller.busy and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.01)
        self.assertFalse(self.controller.busy)

    def test_check_dialog_skip_and_manual_override(self):
        with patch('updates.fetch_releases', return_value=[release()]) as fetch:
            self.controller.check(True); self.settle()
            self.assertIn('EXR fixes', self.controller.dialog.notes.toPlainText())
            self.assertFalse(self.controller.dialog.notes.openExternalLinks())
            self.controller.skip()
            self.assertEqual(self.controller.settings['skipped'], '0.11.0')
            self.controller.check()
            self.assertEqual(fetch.call_count, 1)
            self.controller.check(True); self.settle()
            self.assertTrue(self.controller.dialog.isVisible())

    def test_network_failure_and_disabled_automatic(self):
        self.controller.settings['automatic'] = False
        with patch('updates.fetch_releases', side_effect=TimeoutError('offline')) as fetch:
            self.controller.check()
            fetch.assert_not_called()
            self.controller.check(True); self.settle()
            self.assertIn('offline', self.window.statusBar().currentMessage())
            self.assertTrue(self.controller.check_action.isEnabled())

    def test_rejected_close_never_launches_installer(self):
        self.controller.show_release(updates.select_release([release()], '0.10.1'))
        self.controller.installer = 'fixture.exe'
        with patch('updates.verify_installer', return_value=Path('fixture.exe')), patch('update_ui.subprocess.Popen') as launch:
            self.controller.activate(); self.settle()
            launch.assert_not_called()

    def test_download_requires_separate_install_click(self):
        selected = updates.select_release([release()], '0.10.1')
        self.controller.show_release(selected)
        with patch('updates.download_installer', return_value='fixture.exe'), patch('update_ui.subprocess.Popen') as launch:
            self.controller.activate(); self.settle()
            self.assertEqual(self.controller.installer, 'fixture.exe')
            self.assertTrue(self.controller.dialog.primary.isEnabled())
            launch.assert_not_called()
        self.controller.dialog.reject()
        self.assertTrue(self.controller.cancelled.is_set())

    def test_tampered_download_never_launches(self):
        self.controller.show_release(updates.select_release([release()], '0.10.1'))
        self.controller.installer = 'fixture.exe'
        with patch('updates.verify_installer', side_effect=ValueError('SHA256 mismatch')), patch('update_ui.subprocess.Popen') as launch:
            self.controller.activate(); self.settle()
            launch.assert_not_called()
            self.assertIn('SHA256', self.controller.dialog.status.text())

    def test_confirmed_close_launches_and_failure_recovers(self):
        self.controller.show_release(updates.select_release([release()], '0.10.1'))
        self.controller.installer = 'fixture.exe'
        self.window.allow_close = True
        with patch('update_ui.subprocess.Popen') as launch:
            self.controller.launch_installer()
            launch.assert_called_once_with(['fixture.exe', '/NORESTART'], close_fds=True)
        with patch('update_ui.subprocess.Popen', side_effect=OSError('cannot launch')):
            self.controller.launch_installer()
            self.assertTrue(self.window.isVisible())
            self.assertFalse(self.controller.closed)


if __name__ == '__main__':
    unittest.main()
