import os,sys,json,tempfile
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from app import Window
from examples import example
app=QApplication([]);w=Window();w.live_toggle.setChecked(False);w.engine.stop()
state={'stage':'start','results':{},'error':None}
def fail(message):
    state['error']=str(message);w.cancel_tracking();app.quit()
w.error=fail
def start(name):
    previous=w.project;w.project=example(name,root/'assets');w.project.update(blender=previous['blender'],output=previous['output'])
    node=next(n for n in w.project['nodes'] if n['kind'] in ('Tracker2D','PlanarTracker'))
    state['kind']=node['kind'];state['node']=node;state['stage']='tracking';w.start_tracking(node)
def poll():
    if state['stage']=='start':start('Tracking 2D')
    elif state['stage']=='tracking' and not getattr(w,'task_process',None):
        node=state['node']
        if not node.get('tracking_report'):fail(w.log.toPlainText());return
        state['results'][node['kind']]=len(node['tracking_report']['records'])
        w.bake_tracking(node)
        assert len(w.project['nodes'])==6
        if state['kind']=='Tracker2D':start('Planar')
        else:state['stage']='done';app.quit()
timer=QTimer();timer.timeout.connect(poll);timer.start(30)
QTimer.singleShot(20000,lambda:fail('timeout'));app.exec()
assert not state['error'],state['error']
assert state['results']=={'Tracker2D':24,'PlanarTracker':24},state
(root/'validation/ui-tracking.json').write_text(json.dumps(state['results'],indent=2))
print('UI_TRACKING_OK',state['results'])
w.dirty=False;w.close()
