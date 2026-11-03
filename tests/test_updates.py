import hashlib
import io
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
import updates


def release(version='0.11.0', beta=False, content=b'installer fixture'):
    tag = 'v' + version
    name = f'Nukify-Setup-{version}.exe'
    return dict(tag_name=tag, name='Nukify ' + version, body='## Changes\n- EXR fixes\n- Update checks',
                prerelease=beta, draft=False, published_at='2026-11-03T00:00:00Z',
                html_url=updates.RELEASES + '/tag/' + tag,
                assets=[dict(name=name, state='uploaded', size=len(content),
                    digest='sha256:' + hashlib.sha256(content).hexdigest(),
                    browser_download_url=updates.RELEASES + '/download/' + tag + '/' + name)])


class UpdatesTests(unittest.TestCase):
    def test_semantic_order_and_channels(self):
        self.assertGreater(updates.version_key('0.10.1'), updates.version_key('0.9.9'))
        self.assertGreater(updates.version_key('1.0.0'), updates.version_key('1.0.0-rc.2'))
        self.assertGreater(updates.version_key('1.0.0-beta.10'), updates.version_key('1.0.0-beta.2'))
        items = [release('0.10.2'), release('0.11.0', True), release('0.9.0')]
        self.assertEqual(updates.select_release(items, '0.10.1')['version'], '0.11.0')
        self.assertEqual(updates.select_release(items, '0.10.1', False)['version'], '0.10.2')
        self.assertIsNone(updates.select_release(items, '0.11.0'))
        self.assertIsNone(updates.select_release([release('1.0.0-rc.1')], '0.10.1', False))

    def test_unpublished_untrusted_and_incomplete_releases(self):
        for change in ({'draft': True}, {'published_at': None}, {'tag_name': 'latest'},
                       {'html_url': 'https://example.com/release'}, {'assets': []}):
            item = release(); item.update(change)
            self.assertIsNone(updates.select_release([item], '0.10.1'))
        for change in ({'digest': None}, {'size': 0}, {'state': 'new'},
                       {'browser_download_url': 'https://example.com/malware.exe'},
                       {'name': '../../bad.exe'}):
            item = release(); item['assets'][0].update(change)
            self.assertIsNone(updates.select_release([item], '0.10.1'))

    def test_download_hash_size_and_cancel(self):
        data = b'installer fixture'
        selected = updates.select_release([release(content=data)], '0.10.1')
        with tempfile.TemporaryDirectory() as directory:
            with patch('updates.request', return_value=io.BytesIO(data)):
                path = updates.download_installer(selected, directory, threading.Event())
            self.assertEqual(Path(path).read_bytes(), data)
            for bad in (b'short', b'X' * len(data), data + b'extra'):
                with patch('updates.request', return_value=io.BytesIO(bad)):
                    with self.assertRaises(ValueError):
                        updates.download_installer(selected, directory, threading.Event())
                self.assertFalse(list(Path(directory).glob('*.part')))
                self.assertEqual(Path(path).read_bytes(), data)
            cancelled = threading.Event(); cancelled.set()
            with patch('updates.request', return_value=io.BytesIO(data)):
                with self.assertRaises(InterruptedError):
                    updates.download_installer(selected, directory, cancelled)
            self.assertFalse(list(Path(directory).glob('*.part')))

    def test_network_and_invalid_response(self):
        with patch('updates.request', side_effect=TimeoutError('offline')):
            with self.assertRaises(TimeoutError): updates.fetch_releases()
        for data in (b'bad json', b'{}'):
            with patch('updates.request', return_value=io.BytesIO(data)):
                with self.assertRaises(ValueError): updates.fetch_releases()

    def test_settings_and_rate_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = updates.read_settings(directory)
            self.assertTrue(updates.check_due(settings, 100000))
            settings.update(last_check=100000, skipped='0.11.0')
            updates.save_settings(directory, settings)
            self.assertEqual(updates.read_settings(directory), settings)
            self.assertFalse(updates.check_due(settings, 100001))
            self.assertTrue(updates.check_due(settings, 186400))
            settings['automatic'] = False
            self.assertFalse(updates.check_due(settings, 999999))
            (Path(directory) / 'updates.json').write_text('invalid')
            self.assertTrue(updates.read_settings(directory)['automatic'])

    def test_installed_manifest_and_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', str(Path(directory) / 'Nukify.exe')):
                self.assertIsNone(updates.installed_version())
                (Path(directory) / 'release.json').write_text(json.dumps({'app': '1.2.3'}))
                self.assertEqual(updates.installed_version(), '1.2.3')


if __name__ == '__main__':
    unittest.main()
