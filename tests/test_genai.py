import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'desktop'))
from genai import FalClient, JobStore, FalError, fingerprint, input_schema, validate, endpoint_id
from genai_jobs import JobRunner, input_signature
from genai_media import proxy
from PIL import Image

CATALOG = json.loads((ROOT / 'assets/genai/catalog.json').read_text(encoding='utf-8'))


class FakeFal:
    key = 'test-credential-not-persistent'
    def __init__(self):
        self.submits = 0
        self.uploads = []
        self.fail_submit = False
        self.fail_download = False
        self.remote_error = False
    def upload(self, path):
        self.uploads.append(path)
        return 'https://fal.media/input.png'
    def submit(self, endpoint, payload):
        self.submits += 1
        self.payload = payload
        if self.fail_submit: raise FalError('Disconnected')
        return dict(request_id='id-1', status_url='https://queue.fal.run/model/app/requests/id-1/status',
                    response_url='https://queue.fal.run/model/app/requests/id-1',
                    cancel_url='https://queue.fal.run/model/app/requests/id-1/cancel')
    def queue_request(self, url, method='GET'):
        if '/status' in url:
            return dict(status='COMPLETED', error='model error' if self.remote_error else None,
                        logs=[{'message': 'hello ' + self.key}])
        return {'images': [{'url': 'https://fal.media/output.png'}]}
    def download(self, url, target):
        if self.fail_download: raise OSError('offline')
        Image.new('RGB', (96, 64), '#ec9e46').save(target)


def spec():
    m = CATALOG['models'][0]
    return dict(endpoint=m['endpoint_id'], schema=m['schema'], category='text-to-image',
                asset='shot', payload={'prompt': 'A test image', 'resolution': '1K'}, input_signature={},
                send_proxy=0, receive_proxy=512, ffmpeg='', project='test', units=1)


def quote(s):
    return dict(total_cost=.1, currency='USD', spec_hash=fingerprint(s), received=time.time())


class GenAIContracts(unittest.TestCase):
    def test_all_cached_models_have_valid_default_payload(self):
        for m in CATALOG['models']:
            schema = input_schema(m['schema'])
            p = {k: copy.deepcopy(v['default']) for k, v in schema['properties'].items() if v.get('default') is not None}
            p['prompt'] = 'A production test fixture'
            for k in schema.get('required', []):
                if k == 'image_urls': p[k] = ['https://example.com/image.png']
                if k == 'video_url': p[k] = 'https://example.com/video.mp4'
            validate(p, schema, m['schema'])

    def test_invalid_settings_rejected(self):
        s = spec()
        for key, value in [('resolution', '16K'), ('num_images', 500), ('prompt', '')]:
            with self.assertRaises(ValueError):
                validate(dict(s['payload'], **{key: value}), input_schema(s['schema']), s['schema'])

    def test_endpoint_and_queue_reject_foreign_destinations(self):
        for value in ('https://evil.example/x', 'fal-ai/../x', 'fal-ai/x?token=1'):
            with self.assertRaises(ValueError): endpoint_id(value)
        with self.assertRaises(ValueError): FalClient('secret').queue_request('https://evil.example/requests/id')

    def test_cost_uses_provider_units(self):
        client = FalClient('secret')
        with patch.object(client, 'request', side_effect=[{'prices': [{'endpoint_id': 'x/y', 'unit': 'second', 'unit_price': .2}]},
                                                        {'total_cost': 1, 'currency': 'USD'}]) as call:
            result = client.estimate('x/y', 5)
            self.assertEqual(result['total_cost'], 1)
            self.assertEqual(call.call_args.args[2]['endpoints']['x/y']['unit_quantity'], 5)

    def test_no_key_never_sends_authenticated_request(self):
        client = FalClient()
        with patch.object(client.opener, 'open') as request:
            with self.assertRaises(ValueError): client.submit('x/y', {'prompt': 'test'})
            request.assert_not_called()


class GenAIJobs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.store = JobStore(self.temp.name); self.client = FakeFal()
    def tearDown(self): self.temp.cleanup()

    def test_completed_job_downloads_and_versions_without_credentials(self):
        s = spec(); runner = JobRunner(self.client, self.store)
        a = runner.start(s, quote(s)); b = runner.start(s, quote(s))
        self.assertEqual((a['state'], b['version']), ('READY', 2))
        self.assertNotEqual(a['directory'], b['directory'])
        self.assertTrue(Path(a['outputs'][0]['original']).is_file())
        raw = (Path(a['directory']) / 'job.json').read_text()
        self.assertNotIn(self.client.key, raw)
        self.assertNotIn('live_logs', raw)
        self.assertEqual(len(a['outputs'][0]['sha256']), 64)

    def test_uncertain_submit_never_retries(self):
        self.client.fail_submit = True
        s = spec(); runner = JobRunner(self.client, self.store)
        job = runner.start(s, quote(s))
        self.assertEqual(job['state'], 'UNKNOWN')
        with self.assertRaises(ValueError): runner.resume(job)
        self.assertEqual(self.client.submits, 1)

    def test_failed_download_resume_does_not_submit_again(self):
        self.client.fail_download = True
        s = spec(); runner = JobRunner(self.client, self.store)
        job = runner.start(s, quote(s)); self.assertEqual(job['state'], 'PAUSED')
        self.client.fail_download = False
        job = JobRunner(self.client, JobStore(self.temp.name)).resume(self.store.list()[0])
        self.assertEqual(job['state'], 'READY'); self.assertEqual(self.client.submits, 1)

    def test_remote_completed_error_is_not_success(self):
        self.client.remote_error = True
        s = spec(); job = JobRunner(self.client, self.store).start(s, quote(s))
        self.assertEqual(job['state'], 'FAILED'); self.assertFalse(job['outputs'])

    def test_queue_progress_and_pause_preserve_remote_id(self):
        s = spec(); stop = threading.Event(); states = []
        def progress(job):
            states.append(job['state'])
            if job['state'] == 'IN_PROGRESS': stop.set()
        original = self.client.queue_request
        self.client.queue_request = lambda url, method='GET': {'status': 'IN_PROGRESS'}
        runner = JobRunner(self.client, self.store, progress, stop)
        job = runner.start(s, quote(s))
        self.assertEqual(job['state'], 'PAUSED')
        self.assertEqual(job['remote']['request_id'], 'id-1')
        self.assertIn('IN_PROGRESS', states)
        self.client.queue_request = original
        job = JobRunner(self.client, self.store).resume(job)
        self.assertEqual(job['state'], 'READY'); self.assertEqual(self.client.submits, 1)

    def test_invalid_result_image_does_not_become_ready(self):
        self.client.download = lambda url, target: Path(target).write_text('<html>Error</html>')
        s = spec(); job = JobRunner(self.client, self.store).start(s, quote(s))
        self.assertEqual(job['state'], 'PAUSED')
        self.assertFalse(job['outputs'])

    def test_expired_or_changed_quote_prevents_charge(self):
        s = spec(); q = quote(s); q['received'] -= 400
        with self.assertRaises(ValueError): JobRunner(self.client, self.store).start(s, q)
        q = quote(s); s['payload']['resolution'] = '4K'
        with self.assertRaises(ValueError): JobRunner(self.client, self.store).start(s, q)
        self.assertEqual(self.client.submits, 0)

    def test_local_media_changes_prevent_charge(self):
        p = Path(self.temp.name) / 'in.png'; Image.new('RGB', (10, 10)).save(p)
        s = spec(); s['payload']['image_urls'] = ['local:' + str(p)]
        s['input_signature'] = input_signature(s['payload']); q = quote(s)
        Image.new('RGB', (20, 20)).save(p)
        with self.assertRaises(ValueError): JobRunner(self.client, self.store).start(s, q)
        self.assertEqual(self.client.submits, 0)

    def test_proxy_upload_preserves_input_and_replaces_marker(self):
        p = Path(self.temp.name) / 'in.png'; Image.new('RGB', (1200, 800)).save(p)
        s = spec(); s['payload']['image_urls'] = ['local:' + str(p)]; s['send_proxy'] = 512
        s['input_signature'] = input_signature(s['payload'])
        job = JobRunner(self.client, self.store).start(s, quote(s))
        self.assertEqual(job['state'], 'READY')
        self.assertEqual(self.client.payload['image_urls'], ['https://fal.media/input.png'])
        with Image.open(p) as image: self.assertEqual(image.width, 1200)
        with Image.open(self.client.uploads[0]) as image: self.assertEqual(image.width, 512)

    def test_stop_before_submission(self):
        stop = threading.Event(); stop.set()
        s = spec(); job = JobRunner(self.client, self.store, stop=stop).start(s, quote(s))
        self.assertEqual(job['state'], 'STOPPED'); self.assertEqual(self.client.submits, 0)

    def test_no_proxy_does_not_alter_file(self):
        p = Path(self.temp.name) / 'original.png'; Image.new('RGB', (100, 60)).save(p)
        self.assertEqual(proxy(p, Path(self.temp.name) / 'proxy', 0), str(p))


class GenAIUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from app import Window
        from genai_ui import GenAIWindow
        self.temp = tempfile.TemporaryDirectory()
        self.owner = Window(); self.owner.live_toggle.setChecked(False)
        self.owner.live_timer.stop(); self.owner.cache_scan.stop()
        self.ui = GenAIWindow(self.owner, ROOT, self.temp.name)

    def tearDown(self):
        self.ui.close(); self.ui.deleteLater()
        self.owner.dirty = False; self.owner.close(); self.owner.deleteLater()
        self.app.processEvents(); self.temp.cleanup()

    def test_model_specific_controls_and_cost_invalidation(self):
        self.ui.prompt.setPlainText('A test image')
        self.assertIn('resolution', self.ui.spec()['payload'])
        self.ui.quote = {'total_cost': 1}; self.ui.generate.setEnabled(True)
        self.ui.controls['resolution'][0].setCurrentText('4K')
        self.assertIsNone(self.ui.quote); self.assertFalse(self.ui.generate.isEnabled())

    def test_image_edit_requires_input(self):
        self.ui.category.setCurrentIndex(1); self.ui.prompt.setPlainText('A test edit')
        with self.assertRaises(ValueError): self.ui.spec()

    def test_reuse_version_requires_new_quote(self):
        self.ui.prompt.setPlainText('A saved image prompt')
        s = self.ui.spec(); job = self.ui.store.create(s, quote(s))
        self.ui.refresh_jobs(job['id']); self.ui.prompt.setPlainText('Something else')
        self.ui.reuse_selected()
        self.assertEqual(self.ui.prompt.toPlainText(), 'A saved image prompt')
        self.assertIsNone(self.ui.quote)
        self.assertFalse(self.ui.generate.isEnabled())

    def test_import_adds_read_with_provenance_and_undo(self):
        from PIL import Image
        path = Path(self.temp.name) / 'out.png'; Image.new('RGB', (10, 10)).save(path)
        before = len(self.owner.project['nodes'])
        job = dict(id='local-job', version=1, spec={'endpoint': 'test/model'})
        self.owner.import_genai_result(str(path), job, {'original': str(path), 'sha256': 'test'})
        self.assertEqual(len(self.owner.project['nodes']), before + 1)
        self.assertEqual(self.owner.project['nodes'][-1]['genai']['job_id'], 'local-job')
        self.owner.undo(); self.assertEqual(len(self.owner.project['nodes']), before)

    def test_layout_at_1024_and_1440(self):
        for width in (1024, 1440):
            self.ui.resize(width, 820); self.ui.show(); self.app.processEvents()
            self.assertGreater(self.ui.preview.width(), 250)
            self.assertGreater(self.ui.generate.width(), 200)
