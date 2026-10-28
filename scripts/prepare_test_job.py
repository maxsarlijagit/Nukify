import json
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'desktop'))
from model import demo
directory = root / 'validation' / 'render'
directory.mkdir(parents=True, exist_ok=True)
g = demo(root / 'assets')
job = {'graph': g, 'target': 'Write1', 'frames': [1, 2], 'export': True, 'directory': str(directory)}
(directory / 'job.json').write_text(json.dumps(job), encoding='utf-8')
