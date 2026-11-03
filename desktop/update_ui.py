# SPDX-License-Identifier: GPL-3.0-or-later
"""Nonblocking update checks; installer execution always requires a user click."""
import queue
import subprocess
import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QPushButton, QProgressBar
from i18n import tr
import updates


class UpdateDialog(QDialog):
    def __init__(self, parent, current, release):
        super().__init__(parent)
        self.setWindowTitle(tr('Actualización de Nukify'))
        self.resize(640, 480)
        self.setMinimumSize(400, 320)
        layout = QVBoxLayout(self)
        title = QLabel(f'Nukify {current} → {release["version"]}' + (' (beta)' if release['prerelease'] else ''))
        title.setTextFormat(Qt.PlainText)
        layout.addWidget(title)
        self.notes = QTextBrowser()
        self.notes.setOpenLinks(False)
        self.notes.setOpenExternalLinks(False)
        # Plain text prevents remote images, HTML or release text from executing.
        self.notes.setPlainText(release['notes'] or tr('Esta versión no incluye notas de cambios.'))
        layout.addWidget(self.notes)
        self.status = QLabel(tr('Descargá la actualización y guardá tu proyecto antes de instalar.'))
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.PlainText)
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.hide()
        layout.addWidget(self.progress)
        buttons = QHBoxLayout()
        self.web = QPushButton(tr('Ver en GitHub'))
        self.web.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(release['url'])))
        self.skip = QPushButton(tr('Omitir esta versión'))
        self.later = QPushButton(tr('Más tarde'))
        self.primary = QPushButton(tr('Descargar actualización'))
        self.primary.setProperty('primary', True)
        for button in (self.web, self.skip, self.later, self.primary):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.later.clicked.connect(self.reject)


class UpdateController(QObject):
    def __init__(self, window, directory, menu):
        super().__init__(window)
        self.window, self.directory = window, Path(directory)
        self.version = updates.installed_version()
        self.settings = updates.read_settings(directory)
        self.events = queue.Queue()
        self.busy = False
        self.cancelled = threading.Event()
        self.dialog = None
        self.closed = False
        self.manual = False
        self.available = None
        self.installer = None
        submenu = menu.addMenu(tr('Actualizaciones'))
        submenu.addAction('Nukify ' + (self.version or '?')).setEnabled(False)
        self.check_action = submenu.addAction(tr('Buscar actualizaciones'), lambda: self.check(True))
        self.auto_action = submenu.addAction(tr('Buscar automáticamente'))
        self.auto_action.setCheckable(True)
        self.auto_action.setChecked(self.settings['automatic'])
        self.auto_action.toggled.connect(lambda value: self.preference('automatic', value))
        self.beta_action = submenu.addAction(tr('Incluir versiones beta'))
        self.beta_action.setCheckable(True)
        self.beta_action.setChecked(self.settings['include_beta'])
        self.beta_action.toggled.connect(lambda value: self.preference('include_beta', value))
        self.poll = QTimer(self)
        self.poll.setInterval(100)
        self.poll.timeout.connect(self.drain)
        self.poll.start()
        self.schedule = QTimer(self)
        self.schedule.setInterval(3600000)
        self.schedule.timeout.connect(self.check)

    def start(self):
        self.schedule.start()
        QTimer.singleShot(3000, self.check)

    def persist(self):
        try:
            updates.save_settings(self.directory, self.settings)
        except OSError:
            self.window.statusBar().showMessage(tr('No se pudieron guardar las preferencias de actualización.'), 10000)

    def preference(self, key, value):
        self.settings[key] = value
        if key == 'include_beta':
            self.settings['last_check'] = 0
        self.persist()

    def work(self, task, operation):
        self.busy = True
        self.check_action.setEnabled(False)
        self.cancelled = threading.Event()
        def run():
            try:
                self.events.put((task, operation()))
            except Exception as exc:
                self.events.put(('error', (task, str(exc))))
        threading.Thread(target=run, daemon=True, name='Nukify updates').start()

    def check(self, manual=False):
        if self.closed or self.busy:
            return
        if self.dialog and self.dialog.isVisible():
            if manual:
                self.dialog.raise_()
            return
        if not manual and not updates.check_due(self.settings):
            return
        self.manual = manual
        if not self.version:
            if manual:
                self.window.statusBar().showMessage(tr('No se pudo identificar la versión instalada.'), 10000)
            return
        self.settings['last_check'] = int(time.time())
        self.persist()
        if manual:
            self.window.statusBar().showMessage(tr('Buscando actualizaciones…'))
        beta = self.settings['include_beta']
        self.work('check', lambda: updates.select_release(updates.fetch_releases(), self.version, beta))

    def drain(self):
        while not self.events.empty():
            task, value = self.events.get_nowait()
            if self.closed:
                continue
            if task == 'progress':
                if self.dialog:
                    self.dialog.progress.setValue(value)
                continue
            self.busy = False
            self.check_action.setEnabled(True)
            if task == 'check':
                if value and (self.manual or value['version'] != self.settings['skipped']):
                    self.show_release(value)
                elif self.manual:
                    self.window.statusBar().showMessage(tr('No hay una actualización compatible disponible en este canal.'), 15000)
            elif task == 'download':
                self.installer = value
                if self.dialog:
                    self.dialog.primary.setText(tr('Instalar y cerrar Nukify'))
                    self.dialog.primary.setEnabled(True)
                    self.dialog.status.setText(tr('Descarga verificada. Al instalar se comprobarán los cambios sin guardar.'))
            elif task == 'verify':
                self.dialog.primary.setEnabled(True)
                if not self.cancelled.is_set():
                    self.launch_installer()
            elif task == 'error':
                operation, message = value
                if operation in ('download', 'verify') and self.dialog:
                    self.dialog.status.setText(tr('No se pudo descargar la actualización:') + ' ' + message)
                    self.dialog.primary.setEnabled(True)
                elif self.manual:
                    self.window.statusBar().showMessage(tr('No se pudo consultar GitHub:') + ' ' + message, 15000)

    def show_release(self, release):
        self.available, self.installer = release, None
        if self.dialog:
            self.dialog.deleteLater()
        self.dialog = UpdateDialog(self.window, self.version, release)
        self.dialog.primary.clicked.connect(self.activate)
        self.dialog.skip.clicked.connect(self.skip)
        self.dialog.finished.connect(lambda _: self.cancelled.set())
        self.dialog.show()

    def skip(self):
        self.settings['skipped'] = self.available['version']
        self.persist()
        self.dialog.reject()

    def activate(self):
        if self.busy:
            return
        if self.installer:
            self.dialog.primary.setEnabled(False)
            self.work('verify', lambda: updates.verify_installer(self.installer, self.available))
            return
        self.dialog.primary.setEnabled(False)
        self.dialog.progress.show()
        self.dialog.progress.setValue(0)
        self.dialog.status.setText(tr('Descargando actualización…'))
        release = self.available
        self.work('download', lambda: updates.download_installer(release, self.directory / 'updates',
                  self.cancelled, lambda value: self.events.put(('progress', value))))

    def launch_installer(self):
        app = QApplication.instance()
        quit_on_close = app.quitOnLastWindowClosed()
        app.setQuitOnLastWindowClosed(False)
        try:
            # closeEvent preserves the existing save/cancel and active-job guards.
            if self.window.close():
                subprocess.Popen([self.installer, '/NORESTART'], close_fds=True)
                app.quit()
        except OSError as exc:
            self.closed = False
            self.poll.start()
            self.window.show()
            self.dialog.show()
            self.dialog.status.setText(tr('No se pudo iniciar el instalador:') + ' ' + str(exc))
        finally:
            app.setQuitOnLastWindowClosed(quit_on_close)

    def stop(self):
        self.closed = True
        self.cancelled.set()
        self.schedule.stop()
        self.poll.stop()
