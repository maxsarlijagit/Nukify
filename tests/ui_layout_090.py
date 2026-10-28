"""Render the actual Qt interface at desktop/laptop sizes and check containment."""
import sys,os,json
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
(root/'validation').mkdir(exist_ok=True)
from PySide6.QtWidgets import QApplication,QPushButton
from PySide6.QtCore import QPoint
from app import Window,STYLE
from examples import example
app=QApplication([])
from PySide6.QtGui import QFontDatabase
QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
app.setStyle('Fusion');app.setStyleSheet(STYLE)
w=Window();w.live_toggle.setChecked(False);w.live_timer.stop();w.cache_scan.stop()
w.project=example('Curvas y roto',root/'assets');w.sync();w.live_timer.stop()
import time
w.live_toggle.setChecked(True);w.request_live();deadline=time.monotonic()+30
while w.viewer.source is None and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
assert w.viewer.source is not None,'Example did not render'
w.live_toggle.setChecked(False)
n=next(n for n in w.project['nodes'] if n['kind']=='Roto');w.properties(n)
w.show();results=[]
suffix='-scale'+os.environ['QT_SCALE_FACTOR'] if 'QT_SCALE_FACTOR' in os.environ else ''
for width,height in [(1440,940),(1280,800),(1024,768)]:
    w.resize(width,height);w.workspace_preset('comp')
    for _ in range(10):app.processEvents()
    w.graph.fit();app.processEvents()
    w.grab().save(str(root/f'validation/ui-090-{width}{suffix}.png'))
    results.append(dict(requested=[width,height],actual=[w.width(),w.height()],device_pixel_ratio=w.devicePixelRatioF(),viewer=[w.viewer.canvas.width(),w.viewer.canvas.height()],graph=[w.graph.width(),w.graph.height()]))
    assert w.width()==width,(width,w.width())
    assert w.viewer.canvas.height()>100
    for layout in [w.viewer.layout().itemAt(0).layout(),w.viewer.layout().itemAt(1).layout()]:
        for i in range(layout.count()):
            item=layout.itemAt(i)
            if item.widget() and item.widget().isVisible():assert item.geometry().right()<=layout.geometry().right()+1
w.dirty=False;w.close()
(root/f'validation/ui-090-layout{suffix}.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
