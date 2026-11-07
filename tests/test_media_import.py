# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from media_import import read_paths
from model import sequence_path
from app import Window, STYLE
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication


class MediaTests(unittest.TestCase):
    def test_sequence_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = ['plate.1001.exr', 'plate.1003.exr', 'plate.01.exr',
                     'logo2026.png', 'still.jpg', 'clip.mp4', 'notes.txt']
            paths = [root / name for name in names]
            for path in paths:
                path.touch()
            expected = [str(root / 'plate.####.exr')] + [str(p) for p in paths[2:5]]
            self.assertEqual(read_paths(paths + paths), expected)
            self.assertEqual(read_paths([paths[1]]), expected[:1])
            self.assertEqual(sequence_path(expected[0], 1003), str(paths[1]))
            self.assertEqual(read_paths([root, root / 'missing.png']), [])


class DropTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
        cls.app.setFont(QFont('Segoe UI', 9))
        cls.app.setStyle('Fusion')
        cls.app.setStyleSheet(STYLE)

    def test_viewport_drop_position_selection_undo_redo(self):
        window = Window()
        window.live_toggle.setChecked(False)
        window.live_timer.stop()
        window.engine.stop()
        try:
            window.show()
            self.app.processEvents()
            with tempfile.TemporaryDirectory() as directory:
                paths = [Path(directory) / name for name in ('shot.0001.png', 'shot.0002.png', 'logo.png')]
                for path in paths:
                    path.touch()
                before = copy.deepcopy(window.project)
                mime = QMimeData()
                mime.setUrls([QUrl.fromLocalFile(str(p)) for p in paths])
                graph = window.graph
                graph.scale(1.3, 1.3)
                point = QPoint(110, 80)
                expected = graph.mapToScene(point)
                for event in (QDragEnterEvent(point, Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier),
                              QDragMoveEvent(point, Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier),
                              QDropEvent(QPointF(point), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)):
                    QApplication.sendEvent(graph.viewport(), event)
                    self.assertTrue(event.isAccepted())
                created = window.project['nodes'][len(before['nodes']):]
                self.assertEqual(len(created), 2)
                self.assertEqual((created[0]['x'], created[0]['y']), (expected.x(), expected.y()))
                self.assertTrue(created[0]['params']['path'].endswith('shot.####.png'))
                self.assertEqual(len(graph.selected_nodes()), 2)
                self.assertTrue(window.dirty)
                self.assertEqual(len(window.history), 1)
                window.undo()
                self.assertEqual(window.project, before)
                window.redo()
                self.assertEqual(window.project['nodes'][-2:], created)
                invalid = QMimeData()
                invalid.setUrls([QUrl('https://example.com/image.png')])
                event = QDragEnterEvent(point, Qt.CopyAction, invalid, Qt.LeftButton, Qt.NoModifier)
                QApplication.sendEvent(graph.viewport(), event)
                self.assertFalse(event.isAccepted())
                count = len(window.history)
                self.assertFalse(graph.import_media([str(Path(directory) / 'missing.png')], expected))
                self.assertEqual(len(window.history), count)
                for width, height in ((1024, 768), (1440, 940)):
                    window.resize(width, height)
                    self.app.processEvents()
                    self.assertEqual(window.width(), width)
                    output = Path(__file__).resolve().parents[1] / 'validation'
                    output.mkdir(exist_ok=True)
                    window.grab().save(str(output / f'media-drop-{width}.png'))
        finally:
            window.dirty = False
            window.close()
            window.deleteLater()


if __name__ == '__main__':
    unittest.main()
