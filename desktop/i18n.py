# SPDX-License-Identifier: GPL-3.0-or-later
"""UI-only translation. Project keys, prompts and provider schemas stay unchanged.

Language is selected once per application session. Preferences apply on the next
launch so changing language never interrupts a render or discards editor state.
"""
import json
import os
from pathlib import Path
from translations import PAIRS

LANGUAGES = {'en': 'English', 'es': 'Español'}
_language = 'en'
_catalog = {source: (english, source) for source, english in PAIRS}
for _spanish, _english in PAIRS:
    _catalog.setdefault(_english, (_english, _spanish))


def read_language(directory):
    try:
        value = json.loads((Path(directory) / 'preferences.json').read_text(encoding='utf-8')).get('language')
        return value if value in LANGUAGES else 'en'
    except (OSError, ValueError, AttributeError, TypeError):
        return 'en'


def save_language(directory, language):
    if language not in LANGUAGES:
        raise ValueError('Unsupported UI language')
    path = Path(directory) / 'preferences.json'
    try:
        preferences = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(preferences, dict): preferences = {}
    except (OSError, ValueError):
        preferences = {}
    preferences['language'] = language
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(preferences, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def set_language(language):
    global _language
    _language = language if language in LANGUAGES else 'en'


def tr(source):
    pair = _catalog.get(source)
    return pair[0 if _language == 'en' else 1] if pair else source


def install_qt_translator(app):
    """Translate Qt standard dialog buttons independently of the Windows locale."""
    from PySide6.QtCore import QTranslator
    class DialogTranslator(QTranslator):
        def translate(self, context, source, disambiguation=None, n=-1):
            if context in ('QPlatformTheme', 'QDialogButtonBox', 'QMessageBox'):
                plain = source.replace('&', '')
                return tr(plain) if plain in _catalog else ''
            return ''
    previous = getattr(app, '_nukify_translator', None)
    if previous: app.removeTranslator(previous)
    app._nukify_translator = DialogTranslator(app)
    app.installTranslator(app._nukify_translator)


def language_dialog(parent, directory):
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox, QMessageBox
    dialog = QDialog(parent)
    dialog.setWindowTitle(tr('Idioma de la interfaz'))
    layout = QVBoxLayout(dialog)
    combo = QComboBox()
    combo.setObjectName('languageChoice')
    combo.setAccessibleName(tr('Idioma de la interfaz'))
    for code, name in LANGUAGES.items(): combo.addItem(name, code)
    combo.setCurrentIndex(combo.findData(read_language(directory)))
    layout.addWidget(combo)
    note = QLabel(tr('El idioma se aplica al volver a abrir Nukify. Guardá tu proyecto antes de cerrar.'))
    note.setWordWrap(True); layout.addWidget(note)
    buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
    layout.addWidget(buttons)
    buttons.rejected.connect(dialog.reject)
    def save():
        try: save_language(directory, combo.currentData())
        except OSError as exc:
            QMessageBox.warning(dialog, 'Nukify', tr('No se pudo guardar el idioma: {0}').format(exc))
            return
        parent.statusBar().showMessage(tr('Idioma guardado. Se aplicará al volver a abrir Nukify.'), 10000)
        dialog.accept()
    buttons.accepted.connect(save)
    dialog.resize(420, 160)
    dialog.exec()
