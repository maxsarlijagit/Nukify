import os,sys,tempfile,unittest
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'desktop'))
from PySide6.QtWidgets import QApplication,QFormLayout,QWidget,QLabel,QSizePolicy
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from unittest.mock import patch
from app import Window
from ui_theme import icon,FlowLayout

class DesktopUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.w=Window();self.w.live_toggle.setChecked(False);self.w.live_timer.stop();self.w.cache_scan.stop()
    def tearDown(self):self.w.dirty=False;self.w.close();self.w.deleteLater()
    def test_workspace_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp,patch('app.DATA',Path(tmp)):
            self.w.show();self.app.processEvents();self.w.workspace_preset('graph');self.app.processEvents()
            old=self.w.editor_split.sizes();self.w.save_workspace();self.w.workspace_preset('viewer');self.w.restore_workspace()
            self.assertEqual(self.w.editor_split.sizes(),old)
            (Path(tmp)/'workspace.json').write_text('{broken');self.w.restore_workspace()
    def test_parameter_filter_and_clear(self):
        node=next(n for n in self.w.project['nodes'] if n['id']=='Color1');self.w.properties(node)
        form=self.w.scroll.widget().layout();self.w.property_search.setText('exposure')
        visible=[r for r in range(form.rowCount()) if form.isRowVisible(r)]
        self.assertEqual(len(visible),1)
        self.assertEqual(form.itemAt(visible[0],QFormLayout.LabelRole).widget().text(),'Exposure')
        self.w.property_search.clear();self.assertTrue(all(form.isRowVisible(r) for r in range(form.rowCount())))
    def test_vector_icons_render_at_multiple_sizes(self):
        for size in (16,24,32,48):
            image=icon('save').pixmap(QSize(size,size)).toImage()
            self.assertFalse(image.isNull());self.assertEqual(image.pixelColor(0,0).alpha(),0)
            self.assertTrue(any(image.pixelColor(x,y).alpha()>0 for x in range(size) for y in range(size)))
            disabled=icon('save').pixmap(QSize(size,size),QIcon.Disabled).toImage()
            self.assertNotEqual(image,disabled)
    def test_wrapping_retains_status_labels(self):
        host=QWidget();flow=FlowLayout();host.setLayout(flow)
        label=QLabel('Motor listo');label.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed);flow.addWidget(label)
        host.resize(200,60);host.show();self.app.processEvents()
        self.assertGreater(label.width(),20);host.close()
