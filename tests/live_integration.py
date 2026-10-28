"""Real persistent Blender and latest-request-wins test, no GUI required."""
import json
import sys
import tempfile
from pathlib import Path
import numpy as np
from PySide6.QtCore import QCoreApplication, QTimer
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'desktop'))
from live_engine import LiveEngine
from model import demo
app = QCoreApplication([])
cache = Path(tempfile.mkdtemp(prefix='nukify-live-test-'))
engine = LiveEngine(root, cache)
g = demo(root / 'assets')
from runtime import engine_path
g['blender'] = engine_path()
results = []
errors = []

def fail(message):
    errors.append(message)
    engine.stop()
    app.quit()

def ready(info):
    results.append(info)
    if len(results) == 1:
        return
    if len(results) == 2:
        assert info['frame'] == 3, info
        QTimer.singleShot(0, lambda: engine.request(g, 'Merge1', 3, 2))
    if len(results) == 3:
        assert info['cached']
        assert engine.starts == 1, engine.starts
        assert engine.jobs_sent == 2, engine.jobs_sent
        first = np.fromfile(results[0]['raw'], dtype=np.float32)
        last = np.fromfile(results[1]['raw'], dtype=np.float32)
        assert first.size == 480*270*4
        assert np.max(np.abs(first-last)) > .01
        engine.stop()
        app.quit()

engine.ready.connect(ready)
engine.failed.connect(fail)
engine.message.connect(print)
engine.request(g, 'Merge1', 1, 2)
g['nodes'][2]['params']['exposure'] = .5
engine.request(g, 'Merge1', 2, 2)
g['nodes'][2]['params']['exposure'] = 1.
engine.request(g, 'Merge1', 3, 2)
QTimer.singleShot(30000, lambda: fail('timeout'))
app.exec()
assert not errors, errors
assert len(results) == 3, results
report = {'passed': True, 'worker_starts': engine.starts, 'jobs': engine.jobs_sent,
          'render_ms': [r.get('ms') for r in results[:2]], 'cache_hit': results[2]['cached']}
(root / 'validation' / 'live-engine.json').write_text(json.dumps(report, indent=2))
print('LIVE_INTEGRATION_OK', report)
