# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline packaged-app smoke test. Synthetic media, no provider requests."""
import json
from pathlib import Path
import tempfile
import urllib.request
from PIL import Image
from genai import JobStore
from genai_media import proxy
from genai_ui import GenAIWindow


def run(window, app, report):
    from app import ROOT
    result = {'passed': False, 'synthetic_fixture': True, 'paid_inference': False, 'network_attempts': 0}
    original_open = urllib.request.OpenerDirector.open
    dialog = None
    def blocked(*args, **kwargs):
        result['network_attempts'] += 1
        raise RuntimeError('Network disabled in packaged GENAI smoke test')
    urllib.request.OpenerDirector.open = blocked
    window.live_toggle.setChecked(False)
    window.pause(); window.live_timer.stop(); window.cache_scan.stop()
    window.engine.stop(); window.engine_b.stop()
    try:
        with tempfile.TemporaryDirectory(prefix='nukify-genai-smoke-') as temporary:
            root = Path(temporary)
            dialog = GenAIWindow(window, ROOT, root)
            dialog.prompt.setPlainText('Synthetic offline packaging fixture; not an AI generation.')
            spec = dialog.spec()
            assert len(dialog.models) >= 11
            result['catalog_models'] = len(dialog.models)
            store = JobStore(root / 'genai')
            estimate = {'total_cost': 0, 'currency': 'USD', 'source': 'synthetic offline fixture'}
            job = store.create(spec, estimate)
            source = Path(job['directory']) / 'original.png'
            Image.new('RGB', (800, 450), '#dc9947').save(source)
            received = proxy(source, Path(job['directory']) / 'receive', 512)
            with Image.open(received) as im:
                assert im.size == (512, 288)
            import hashlib
            output = {'original': str(source), 'proxy': received, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
            job['state'] = 'READY'; job['outputs'] = [output]; store.save(job)
            dialog.refresh_jobs(job['id'])
            dialog.resize(1024, 800); dialog.show(); app.processEvents()
            assert dialog.outputs.count() == 1 and not dialog.preview.pixmap().isNull()
            before = len(window.project['nodes'])
            dialog.import_selected()
            assert len(window.project['nodes']) == before + 1
            assert window.project['nodes'][-1]['genai']['job_id'] == job['id']
            window.undo()
            assert len(window.project['nodes']) == before
            dialog.reuse_selected()
            assert dialog.quote is None and not dialog.generate.isEnabled()
            second = store.create(spec, estimate)
            assert second['version'] == 2
            result.update(panel_opens=True, proxy_pillow=True, library=True, import_undo=True, versioning=True)
            target = Path(report); target.parent.mkdir(parents=True, exist_ok=True)
            dialog.grab().save(str(target.with_suffix('.png')))
            dialog.close(); dialog.deleteLater(); dialog = None
            assert result['network_attempts'] == 0
            result['passed'] = True
    except Exception as exc:
        result['error'] = str(exc)
    finally:
        urllib.request.OpenerDirector.open = original_open
        if dialog:
            dialog.close(); dialog.deleteLater()
        window.dirty = False
        window.live_timer.stop(); window.engine.stop(); window.engine_b.stop()
        target = Path(report); target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2), encoding='utf-8')
        app.exit(0 if result['passed'] else 1)
