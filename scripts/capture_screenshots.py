# SPDX-License-Identifier: GPL-3.0-or-later
"""Capture real Qt widgets rendering synthetic examples; no desktop/user data."""
import os,sys,tempfile,time
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtGui import QFontDatabase
from PySide6.QtCore import QTimer
from app import Window,STYLE
from examples import example
from runtime import engine_path
app=QApplication([]);QFontDatabase.addApplicationFont(str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/segoeui.ttf'));app.setStyle('Fusion');app.setStyleSheet(STYLE)
out=root/'docs/images';out.mkdir(parents=True,exist_ok=True)
w=Window();w.app_data=Path(tempfile.mkdtemp(prefix='nukify-screenshots-'));w.recovery_path=w.app_data/'recovery.nukify';w.show()
def scene(name,filename,kind):
    w.pause();w.project=example(name,root/'assets');w.project['blender']=engine_path();w.sync();w.live_timer.stop()
    w.viewer.source=None;w.request_live();deadline=time.monotonic()+45
    while (w.waiting_frame or w.viewer.source is None) and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
    assert w.viewer.source is not None and not w.waiting_frame,'Render timeout'
    w.resize(1440,940);w.workspace_preset('comp');n=next(n for n in w.project['nodes'] if n['kind']==kind);w.properties(n)
    for _ in range(10):app.processEvents()
    w.graph.fit();w.viewer.canvas.fit();app.processEvents()
    assert w.central.layout().itemAt(0).geometry().height()<100,'Header should remain compact'
    w.grab().save(str(out/filename));return n
scene('Composicion','compositing.png','Color')
n=scene('Curvas y roto','roto.png','Roto')
def capture_curve():
    from curve_editor import CurveView
    dialog=w.findChild(QDialog);dialog.resize(680,720);app.processEvents();dialog.findChild(CurveView).plot();app.processEvents();dialog.grab().save(str(out/'curve-editor.png'));dialog.reject()
QTimer.singleShot(150,capture_curve);w.curve_dialog(n,'shape_x')
w.dirty=False;w.close();print('Captured compositing, roto and curve editor')
