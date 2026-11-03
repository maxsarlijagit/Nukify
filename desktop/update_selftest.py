# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline frozen-build check of version discovery and the update dialog."""
import json
import sys
from pathlib import Path
from updates import installed_version, select_release, RELEASES


def run(window, app, output):
    report = {'passed': False, 'network_used': False, 'installer_started': False}
    try:
        window.live_toggle.setChecked(False)
        current = installed_version()
        manifest = json.loads((Path(sys.executable).parent / 'release.json').read_text())
        assert current == manifest['app']
        assert current in window.windowTitle()
        assert not window.updates.schedule.isActive()
        tag = 'v99.0.0'
        fixture = dict(tag_name=tag, name='Update QA', body='Changelog fixture: update checks and EXR layers.',
            draft=False, prerelease=True, published_at='2026-11-03T00:00:00Z',
            html_url=RELEASES + '/tag/' + tag, assets=[dict(name='Nukify-Setup-99.0.0.exe',
            state='uploaded', size=100, digest='sha256:' + 'a' * 64,
            browser_download_url=RELEASES + '/download/' + tag + '/Nukify-Setup-99.0.0.exe')])
        release = select_release([fixture], current)
        assert release['version'] == '99.0.0'
        assert select_release([fixture], current, False) is None
        window.updates.show_release(release)
        app.processEvents()
        dialog = window.updates.dialog
        assert 'Changelog fixture' in dialog.notes.toPlainText()
        assert dialog.primary.isEnabled()
        dialog.grab().save(str(Path(output).with_suffix('.png')))
        dialog.reject()
        assert window.updates.cancelled.is_set()
        report.update(passed=True, version=current, frozen=bool(getattr(sys, 'frozen', False)),
                      changelog=True, beta_channel=True, deferred_install=True)
    except Exception as exc:
        report['error'] = str(exc)
    Path(output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    window.dirty = False
    window.close()
    app.exit(0 if report['passed'] else 1)
