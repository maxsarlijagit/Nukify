"""Exercise real UI signals, automatic invalidation and cached playback."""
import json
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import sys
import tempfile
import time
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'desktop'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from app import Window
app = QApplication([])
w = Window()
w.engine.cache = Path(tempfile.mkdtemp(prefix='nukify-ui-test-'))
w.project['last'] = 12
w.last.setValue(12)
state = {'stage': 'initial', 'frames': [], 'start': time.perf_counter()}
errors = []

def fail(message):
    print('UI_FAILURE', message, state, w.log.toPlainText(), flush=True)
    errors.append(message)
    w.pause()
    w.engine.stop()
    app.quit()

def ready(info):
    if state['stage'] == 'initial' and info['key'] == w.expected_key:
        state['stage'] = 'edit'
        state['old'] = info['key']
        # No preview/evaluate call. Parameter change must schedule pinned Merge.
        w.parameter(w.project['nodes'][2], 'exposure', .75)
    elif state['stage'] == 'edit' and info['key'] == w.expected_key:
        assert info['key'] != state['old']
        assert info['target'] == 'Merge1'
        state['stage'] = 'warming-requested'
        def begin_warm():
            state['stage'] = 'warming'
            w.cache_range()
        QTimer.singleShot(0, begin_warm)
    elif state['stage'] == 'play' and info['key'] == w.expected_key:
        state['frames'].append((info['frame'], time.perf_counter(), info['cached']))
        if len(state['frames']) >= 36:
            frames = state['frames']
            fps = (len(frames)-1)/(frames[-1][1]-frames[0][1])
            assert all(f[2] for f in frames)
            assert set(f[0] for f in frames) == set(range(1,13))
            assert 20 < fps < 28, fps
            state['fps'] = fps
            state['worker_starts'] = w.engine.starts
            assert w.engine.starts == 1
            w.pause()
            w.engine.stop()
            app.quit()

def poll():
    if state['stage'] == 'warming' and not w.warming and not w.engine.busy:
        state['stage'] = 'play'
        w.toggle_play()

w.engine.ready.connect(ready)
w.engine.failed.connect(fail)
poller = QTimer()
poller.timeout.connect(poll)
poller.start(25)
QTimer.singleShot(30000, lambda: fail('timeout'))
app.exec()
assert not errors, errors
assert state['stage'] == 'play' and 'fps' in state, state
report = {k:v for k,v in state.items() if k not in ('old','frames','start')}
(root/'validation'/'live-ui.json').write_text(json.dumps(report, indent=2))
print('LIVE_UI_OK', report)
