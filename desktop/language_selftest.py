# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline packaged UI language check, using the caller's isolated profile."""
import json
from pathlib import Path
from PySide6.QtWidgets import QPushButton
from i18n import read_language, save_language


def run(window, app, output):
    report = {'passed': False}
    try:
        window.live_toggle.setChecked(False)
        language = read_language(window.app_data)
        expected = 'Save' if language == 'en' else 'Guardar'
        assert expected in [b.text() for b in window.findChildren(QPushButton)]
        assert window.findChild(QPushButton, 'languageButton') is not None
        window.open_genai()
        panel = window.genai_window
        assert panel.settings_tabs.tabText(0) == ('Create' if language == 'en' else 'Crear')
        assert panel.category.itemData(0) == 'text-to-image'
        save_language(window.app_data, language)
        assert read_language(window.app_data) == language
        report.update(passed=True, language=language, network_used=False)
        window.grab().save(str(Path(output).with_suffix('.png')))
    except Exception as exc:
        report['error'] = str(exc)
    Path(output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    window.dirty = False
    window.close()
    app.exit(0 if report['passed'] else 1)
