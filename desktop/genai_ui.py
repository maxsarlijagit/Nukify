# SPDX-License-Identifier: GPL-3.0-or-later
"""GENAI workspace: model-aware forms, explicit cost review and versioned media."""
from i18n import tr
import copy
import json
import os
from pathlib import Path
import threading
import time
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices
from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QSplitter, QScrollArea, QLabel, QPushButton, QLineEdit, QPlainTextEdit, QComboBox,
    QDoubleSpinBox, QCheckBox, QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QProgressBar, QTabWidget, QSizePolicy)
from genai import (FalClient, JobStore, CATEGORIES, input_schema, field_schema,
                   validate, fingerprint, now)
from genai_jobs import JobRunner, input_signature
from genai_media import VIDEO, sequence, ffmpeg_path
from ui_theme import decorate


class Task(QThread):
    result = Signal(object)
    error = Signal(str)
    progress = Signal(object)

    def __init__(self, action, parent):
        super().__init__(parent)
        self.action = action
        self.stop = threading.Event()

    def run(self):
        try:
            self.result.emit(self.action(self))
        except Exception as exc:
            # Exceptions from HTTP transports may contain signed upload URLs.
            message = str(exc) if isinstance(exc, ValueError) else 'La operación falló. Revisá conexión, clave y configuración.'
            self.error.emit(message)


class GenAIWindow(QDialog):
    def __init__(self, owner, root, data):
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle(tr('Nukify · GENAI Studio'))
        self.resize(1220, 860)
        self.setMinimumSize(900, 650)
        self.store = JobStore(Path(data) / 'genai')
        self.models = json.loads((Path(root) / 'assets/genai/catalog.json').read_text(encoding='utf-8'))['models']
        self.task = None
        self.quote = None
        self.controls = {}
        self.frames = []
        self.play_index = 0
        self.preview_timer = QTimer(self)
        self.preview_timer.setInterval(83)
        self.preview_timer.timeout.connect(self.next_frame)
        layout = QVBoxLayout(self)
        title = QLabel(tr('GENAI  /  fal.ai'))
        title.setStyleSheet('font-size:20px;font-weight:700;color:#e6a34b')
        layout.addWidget(title)
        subtitle = QLabel(tr('Crear → seguir el proceso → revisar versiones → incorporar a composición'))
        layout.addWidget(subtitle)
        split = QSplitter(Qt.Horizontal)
        layout.addWidget(split, 1)
        left = QWidget(); left_layout = QVBoxLayout(left)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(left)
        scroll.setMinimumWidth(330)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_container = QWidget(); left_outer = QVBoxLayout(left_container)
        left_outer.setContentsMargins(0, 0, 0, 0); left_outer.addWidget(scroll, 1)
        split.addWidget(left_container)
        self.settings_tabs = QTabWidget(); left_layout.addWidget(self.settings_tabs)
        create = QWidget(); form_layout = QVBoxLayout(create)
        self.settings_tabs.addTab(create, tr('Crear'))
        connection = QWidget(); connection_form = QFormLayout(connection)
        self.settings_tabs.addTab(connection, tr('Conexión'))
        self.key = QLineEdit(); self.key.setEchoMode(QLineEdit.Password)
        self.key.setPlaceholderText(tr('Clave de sesión; vacío usa FAL_KEY'))
        self.key.setToolTip(tr('Solo memoria. No se guarda en proyectos, preferencias ni historial.'))
        connection_form.addRow(tr('API key propia'), self.key)
        key_note = QLabel(tr('La clave se usa en esta sesión. Para próximos inicios configurá FAL_KEY en tu entorno.'))
        key_note.setWordWrap(True); connection_form.addRow(key_note)
        dashboard = QPushButton(tr('Abrir claves de fal.ai')); dashboard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://fal.ai/dashboard/keys')))
        connection_form.addRow(dashboard)
        self.ffmpeg = QLineEdit(); self.ffmpeg.setPlaceholderText(tr('FFmpeg en PATH o ruta al ejecutable'))
        connection_form.addRow(tr('FFmpeg'), self.ffmpeg)
        ffchoose = QPushButton(tr('Elegir FFmpeg')); ffchoose.clicked.connect(self.choose_ffmpeg); connection_form.addRow(ffchoose)
        info = QLabel(tr('Los proxies de video y la importación como secuencia requieren FFmpeg. Los originales se conservan siempre.'))
        info.setWordWrap(True); connection_form.addRow(info)
        self.category = QComboBox()
        for key, label in CATEGORIES.items(): self.category.addItem(tr(label), key)
        form_layout.addWidget(self.category)
        self.model = QComboBox(); self.model.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.model.setMinimumContentsLength(20); form_layout.addWidget(self.model)
        self.search = QLineEdit(); self.search.setPlaceholderText(tr('Buscar modelos en fal.ai…'))
        searchrow = QHBoxLayout(); searchrow.addWidget(self.search)
        self.search_button = QPushButton(tr('Buscar')); searchrow.addWidget(self.search_button)
        form_layout.addLayout(searchrow)
        self.model_note = QLabel(tr('Destacados verificados · 28 oct 2026. La búsqueda consulta el catálogo actual.'))
        self.model_note.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.model_note.setWordWrap(True); form_layout.addWidget(self.model_note)
        modelrow = QHBoxLayout()
        self.schema_button = QPushButton(tr('Actualizar schema')); modelrow.addWidget(self.schema_button)
        docs = QPushButton(tr('Ficha del modelo')); docs.clicked.connect(self.open_model_docs); modelrow.addWidget(docs)
        form_layout.addLayout(modelrow)
        self.asset = QLineEdit('shot-001'); self.asset.setPlaceholderText(tr('Nombre del asset / shot'))
        form_layout.addWidget(QLabel(tr('ASSET / VERSIONES'))); form_layout.addWidget(self.asset)
        self.prompt = QPlainTextEdit(); self.prompt.setPlaceholderText(tr('Describí el resultado y qué debe conservarse…')); self.prompt.setMaximumHeight(100)
        form_layout.addWidget(self.prompt)
        self.fields_host = QWidget(); self.fields = QFormLayout(self.fields_host)
        self.fields.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.fields.setRowWrapPolicy(QFormLayout.WrapLongRows)
        form_layout.addWidget(self.fields_host)
        advanced_toggle = QPushButton(tr('Opciones avanzadas')); advanced_toggle.setCheckable(True)
        form_layout.addWidget(advanced_toggle)
        self.advanced_host = QWidget(); self.advanced_fields = QFormLayout(self.advanced_host)
        self.advanced_fields.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.advanced_host.hide(); advanced_toggle.toggled.connect(self.advanced_host.setVisible)
        form_layout.addWidget(self.advanced_host)
        proxies = QFormLayout()
        self.send_proxy = QComboBox(); self.receive_proxy = QComboBox()
        for combo in (self.send_proxy, self.receive_proxy):
            for label, size in [('Original', 0), ('Proxy 512', 512), ('Proxy 1024', 1024), ('Proxy 1920', 1920)]:
                combo.addItem(label, size)
        self.receive_proxy.setCurrentIndex(2)
        proxies.addRow(tr('Medio a enviar'), self.send_proxy); proxies.addRow(tr('Proxy recibido'), self.receive_proxy)
        form_layout.addLayout(proxies)
        note = QLabel(tr('Proxy = máximo del lado largo; no aumenta resolución. El proxy recibido se crea localmente y no reduce el cobro de fal.'))
        note.setWordWrap(True); form_layout.addWidget(note)
        self.units = QDoubleSpinBox(); self.units.setDecimals(3); self.units.setRange(.001, 100000); self.units.setValue(1)
        self.units.setToolTip(tr('Cantidad de unidades facturables del modelo. Ajustar por duración, resolución y cantidad según su ficha.'))
        unitrow = QFormLayout(); unitrow.addRow(tr('Unidades (manual)'), self.units); left_outer.addLayout(unitrow)
        self.estimate_button = QPushButton(tr('Calcular costo')); decorate(self.estimate_button, 'tools'); left_outer.addWidget(self.estimate_button)
        self.cost = QLabel(tr('Costo sin calcular')); self.cost.setWordWrap(True); left_outer.addWidget(self.cost)
        self.generate = QPushButton(tr('Revisar y generar')); self.generate.setProperty('primary', True)
        self.generate.setStyleSheet('QPushButton:disabled {background:#393939;border-color:#494949;color:#888888}')
        self.generate.setEnabled(False); left_outer.addWidget(self.generate)
        form_layout.addStretch()
        right = QWidget(); rl = QVBoxLayout(right); split.addWidget(right)
        rl.addWidget(QLabel(tr('BIBLIOTECA  /  VERSIONES LOCALES')))
        self.jobs = QListWidget(); self.jobs.setMaximumHeight(160); rl.addWidget(self.jobs)
        self.outputs = QComboBox(); rl.addWidget(self.outputs)
        reuse = QPushButton(tr('Reutilizar parámetros de esta versión')); reuse.clicked.connect(self.reuse_selected); rl.addWidget(reuse)
        self.preview = QLabel(tr('Los resultados aparecerán aquí al completar la generación'))
        self.preview.setAlignment(Qt.AlignCenter); self.preview.setWordWrap(True)
        self.preview.setMinimumSize(250, 180); self.preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.preview.setStyleSheet('background:#202020;border:1px solid #454545;border-radius:6px;color:#a5a5a5')
        rl.addWidget(self.preview, 1)
        actions = QHBoxLayout()
        self.play = QPushButton(tr('Play proxy')); self.play.clicked.connect(self.toggle_play); actions.addWidget(self.play)
        self.open_file = QPushButton(tr('Abrir original')); self.open_file.clicked.connect(self.open_original); actions.addWidget(self.open_file)
        self.import_button = QPushButton(tr('Usar en graph')); self.import_button.clicked.connect(self.import_selected); actions.addWidget(self.import_button)
        rl.addLayout(actions)
        prepare_proxy = QPushButton(tr('Preparar proxy local de esta versión'))
        prepare_proxy.clicked.connect(self.prepare_selected_proxy); rl.addWidget(prepare_proxy)
        self.details = QLabel(tr('Elegí una versión para ver sus parámetros y estado')); self.details.setWordWrap(True); rl.addWidget(self.details)
        self.logs = QPlainTextEdit(); self.logs.setReadOnly(True); self.logs.setMaximumHeight(130); rl.addWidget(self.logs)
        self.progress = QProgressBar(); self.progress.setRange(0, 1); self.progress.setValue(0); rl.addWidget(self.progress)
        controls = QHBoxLayout()
        self.resume_button = QPushButton(tr('Reanudar seguimiento')); self.resume_button.clicked.connect(self.resume_selected); controls.addWidget(self.resume_button)
        self.stop_button = QPushButton(tr('Pausar seguimiento')); self.stop_button.clicked.connect(self.pause_tracking); controls.addWidget(self.stop_button)
        self.cancel_button = QPushButton(tr('Cancelar en fal')); self.cancel_button.clicked.connect(self.cancel_selected); controls.addWidget(self.cancel_button)
        rl.addLayout(controls)
        self.status = QLabel(tr('Listo · no se envían medios hasta confirmar una generación')); self.status.setWordWrap(True); layout.addWidget(self.status)
        split.setSizes([460, 720])
        self.category.currentIndexChanged.connect(self.populate_models)
        self.model.currentIndexChanged.connect(self.model_changed)
        self.search_button.clicked.connect(self.search_models)
        self.schema_button.clicked.connect(self.refresh_schema)
        self.estimate_button.clicked.connect(self.estimate)
        self.generate.clicked.connect(self.submit)
        self.jobs.currentItemChanged.connect(self.select_job)
        self.outputs.currentIndexChanged.connect(self.show_output)
        for field in (self.key, self.ffmpeg, self.asset): field.textChanged.connect(self.invalidate)
        self.prompt.textChanged.connect(self.invalidate)
        self.units.valueChanged.connect(self.invalidate)
        self.send_proxy.currentIndexChanged.connect(self.invalidate)
        self.receive_proxy.currentIndexChanged.connect(self.invalidate)
        self.populate_models(); self.refresh_jobs()

    def client(self):
        return FalClient(self.key.text() or os.environ.get('FAL_KEY', ''))

    def busy(self):
        return self.task is not None and self.task.isRunning()

    def invalidate(self, *args):
        self.quote = None; self.generate.setEnabled(False); self.cost.setText(tr('Costo sin calcular · parámetros modificados'))

    def run_task(self, action, done):
        if self.busy():
            return self.status.setText(tr('Esperá a que termine la operación actual'))
        task = Task(action, self); self.task = task
        self.progress.setRange(0, 0)
        for button in (self.generate, self.estimate_button, self.search_button, self.schema_button): button.setEnabled(False)
        task.result.connect(done)
        task.error.connect(lambda message: self.status.setText(tr(message)))
        task.progress.connect(self.job_progress)
        task.finished.connect(self.task_finished)
        task.start()

    def task_finished(self):
        self.progress.setRange(0, 1); self.progress.setValue(1)
        for button in (self.estimate_button, self.search_button, self.schema_button): button.setEnabled(True)
        self.generate.setEnabled(self.quote is not None)

    def populate_models(self):
        self.model.blockSignals(True); self.model.clear()
        for item in self.models:
            if item['category'] == self.category.currentData():
                self.model.addItem(item.get('name', item['endpoint_id']), item)
        self.model.blockSignals(False); self.model_changed()

    def model_changed(self):
        self.invalidate()
        while self.fields.rowCount(): self.fields.removeRow(0)
        while self.advanced_fields.rowCount(): self.advanced_fields.removeRow(0)
        self.controls = {}
        item = self.model.currentData()
        if not item or not item.get('schema'):
            self.model_note.setText(tr('Actualizá el schema del modelo antes de generar')); return
        document = item['schema']; schema = input_schema(document)
        self.model.setToolTip(item['endpoint_id'])
        self.model_note.setText(item['endpoint_id'].replace('/', '/ ') + tr(' · schema de fal'))
        common = ['image_url', 'image_urls', 'start_image_url', 'end_image_url', 'video_url', 'video_urls',
                  'resolution', 'quality', 'image_size', 'duration', 'aspect_ratio', 'num_images', 'output_format', 'seed']
        properties = schema.get('properties', {})
        names = [n for n in common if n in properties] + [n for n in properties if n not in common]
        for name in names:
            raw = properties[name]
            if name in ('prompt', 'sync_mode'): continue
            field = field_schema(raw, document)
            default = raw.get('default', field.get('default'))
            required = name in schema.get('required', [])
            enum = field.get('enum')
            if enum:
                control = QComboBox()
                if not required and default is None: control.addItem(tr('Predeterminado'), None)
                for value in enum: control.addItem(str(value), value)
                if default is not None: control.setCurrentIndex(max(0, control.findData(default)))
                control.currentIndexChanged.connect(self.invalidate)
            elif field.get('type') == 'boolean':
                control = QCheckBox(); control.setChecked(bool(default)); control.toggled.connect(self.invalidate)
            else:
                control = QLineEdit()
                if default is not None:
                    control.setText(json.dumps(default) if field.get('type') in ('array', 'object') else str(default))
                control.setPlaceholderText('JSON' if field.get('type') in ('array', 'object') else (tr('Requerido') if required else tr('Opcional')))
                control.textChanged.connect(self.invalidate)
            control.setToolTip(raw.get('description', name))
            self.controls[name] = (control, field)
            target_form = self.fields if name in common or required else self.advanced_fields
            label = name.replace('_', ' ').title() + (' *' if required else '')
            if name.endswith(('_url', '_urls')) and isinstance(control, QLineEdit):
                container = QWidget(); row = QHBoxLayout(container); row.setContentsMargins(0, 0, 0, 0)
                row.addWidget(control); browse = QPushButton(tr('…')); browse.setMaximumWidth(35)
                browse.setToolTip(tr('Seleccionar medios locales; se suben solo al confirmar'))
                browse.clicked.connect(lambda _, n=name: self.choose_media(n)); row.addWidget(browse)
                target_form.addRow(label, container)
            else: target_form.addRow(label, control)

    def choose_media(self, name):
        paths, _ = QFileDialog.getOpenFileNames(self, tr('Medios de entrada'), '', 'Medios (*.png *.jpg *.jpeg *.webp *.mp4 *.mov *.mkv *.webm *.avi)')
        if paths:
            self.controls[name][0].setText(json.dumps(['local:' + p for p in paths]) if name.endswith('_urls') else 'local:' + paths[0])

    def choose_ffmpeg(self):
        path, _ = QFileDialog.getOpenFileName(self, tr('FFmpeg'), '', 'Ejecutable (*.exe)')
        if path: self.ffmpeg.setText(path)

    def spec(self):
        item = self.model.currentData()
        if not item or not item.get('schema'): raise ValueError('Cargá el schema del modelo')
        payload = {'prompt': self.prompt.toPlainText().strip()}
        if not payload['prompt']: raise ValueError('Escribí un prompt')
        for name, (control, schema) in self.controls.items():
            if isinstance(control, QComboBox): value = control.currentData()
            elif isinstance(control, QCheckBox): value = control.isChecked()
            else:
                value = control.text().strip()
                if not value: continue
                if schema.get('type') in ('integer', 'number', 'array', 'object'): value = json.loads(value)
            if value is not None: payload[name] = value
        category = self.category.currentData()
        if category in ('image-to-image', 'image-to-video') and not any(payload.get(k) for k in ('image_url', 'image_urls', 'start_image_url')):
            raise ValueError('Elegí al menos una imagen de entrada')
        if category == 'video-to-video' and not any(payload.get(k) for k in ('video_url', 'video_urls')):
            raise ValueError('Elegí un video de entrada')
        validate(payload, input_schema(item['schema']), item['schema'])
        signatures = input_signature(payload)
        if any(Path(p).suffix.lower() in VIDEO for p in signatures) and self.send_proxy.currentData():
            ffmpeg_path(self.ffmpeg.text().strip())
        return dict(endpoint=item['endpoint_id'], category=category, schema=item['schema'], payload=payload,
                    asset=self.asset.text().strip() or 'shot', project=str(self.owner.filename or 'Sin guardar'),
                    send_proxy=self.send_proxy.currentData(), receive_proxy=self.receive_proxy.currentData(),
                    ffmpeg=self.ffmpeg.text().strip(), input_signature=signatures, units=self.units.value())

    def estimate(self):
        try:
            spec = self.spec(); client = self.client()
            if not client.key: raise ValueError('Configurá tu API key en Conexión o FAL_KEY')
        except (ValueError, OSError) as exc: return self.status.setText(tr(str(exc)))
        self.status.setText(tr('Consultando precio; no se envían medios ni se genera contenido'))
        def done(quote):
            try:
                if fingerprint(self.spec()) != fingerprint(spec): return
            except (ValueError, OSError): return
            self.quote = dict(quote, spec_hash=fingerprint(spec), received=time.time())
            self.cost.setText(tr('Estimado: {0:.4f} {1} · {2:g} × {3:g} / {4}\nBase por unidades manuales. No ajusta calidad/duración automáticamente: revisá la ficha. No es un tope de gasto ni el cobro final.').format(quote['total_cost'], quote['currency'], quote['units'], quote['unit_price'], quote['unit']))
            self.status.setText(tr('Precio consultado. Revisá unidades y parámetros antes de confirmar.'))
        self.run_task(lambda _: client.estimate(spec['endpoint'], spec['units']), done)

    def submit(self):
        try:
            spec = self.spec()
            if not self.quote or self.quote['spec_hash'] != fingerprint(spec) or time.time() - self.quote['received'] > 300:
                raise ValueError('Calculá el costo nuevamente: parámetros cambiados o cotización vencida')
            quote = copy.deepcopy(self.quote); client = self.client()
        except (ValueError, OSError) as exc: return self.status.setText(tr(str(exc)))
        text = tr('Modelo: {0}\nEstimado: {1:.4f} {2}\nBase: {3:g} unidades de {4}. Puede variar con calidad/duración.\nArchivos locales a subir: {5}\nProxy de entrada: {6}\nSe enviarán el prompt y los medios elegidos a fal.ai usando tu cuenta.\nConfirmo que revisé las unidades facturables y autorizo este trabajo pago.').format(
            spec['endpoint'], quote['total_cost'], quote['currency'], quote['units'], quote['unit'], len(spec['input_signature']), self.send_proxy.currentText())
        if QMessageBox.question(self, tr('Confirmar envío y costo'), text, QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self.invalidate()
        self.run_task(lambda task: JobRunner(client, self.store, task.progress.emit, task.stop).start(spec, quote), self.job_done)

    def search_models(self):
        category, query = self.category.currentData(), self.search.text().strip()
        client = self.client()
        def done(response):
            found = []
            for row in response.get('models', []):
                meta = row.get('metadata') or {}
                if meta.get('category') != category: continue
                endpoint = row['endpoint_id']
                found.append(endpoint)
                if not any(m['endpoint_id'] == endpoint for m in self.models):
                    self.models.append(dict(endpoint_id=endpoint, name=meta.get('display_name', endpoint), category=category))
            if self.category.currentData() != category: return
            self.model.blockSignals(True); self.model.clear()
            for endpoint in found:
                item = next(m for m in self.models if m['endpoint_id'] == endpoint)
                self.model.addItem(item.get('name', endpoint), item)
            self.model.blockSignals(False); self.model_changed()
            self.status.setText(tr('{0} modelos encontrados (máximo 30). Trending no garantiza calidad; consultá la ficha.').format(len(found)))
        self.run_task(lambda _: client.search(category, query), done)

    def refresh_schema(self):
        item = self.model.currentData()
        if not item: return
        endpoint = item['endpoint_id']
        client = self.client()
        def done(schema):
            input_schema(schema)
            for model in self.models:
                if model['endpoint_id'] == endpoint: model['schema'] = schema
            # Qt item data is copied; repopulate to ensure updated schema is used.
            self.populate_models()
            for index in range(self.model.count()):
                if self.model.itemData(index)['endpoint_id'] == endpoint: self.model.setCurrentIndex(index); break
            self.model_changed(); self.status.setText(tr('Schema actualizado desde fal.ai'))
        self.run_task(lambda _: client.schema(endpoint), done)

    def open_model_docs(self):
        if self.model.currentData(): QDesktopServices.openUrl(QUrl('https://fal.ai/models/' + self.model.currentData()['endpoint_id']))

    def reuse_selected(self):
        job = self.selected_job()
        if not job: return
        spec = job['spec']
        if not any(m['endpoint_id'] == spec['endpoint'] for m in self.models):
            self.models.append(dict(endpoint_id=spec['endpoint'], name=spec['endpoint'],
                                    category=spec['category'], schema=spec['schema']))
        self.category.setCurrentIndex(self.category.findData(spec['category']))
        for index in range(self.model.count()):
            if self.model.itemData(index)['endpoint_id'] == spec['endpoint']:
                self.model.setCurrentIndex(index); break
        self.model_changed(); self.asset.setText(spec['asset']); self.prompt.setPlainText(spec['payload']['prompt'])
        for name, value in spec['payload'].items():
            if name not in self.controls: continue
            control, schema = self.controls[name]
            if isinstance(control, QComboBox): control.setCurrentIndex(control.findData(value))
            elif isinstance(control, QCheckBox): control.setChecked(bool(value))
            else: control.setText(json.dumps(value) if isinstance(value, (dict, list)) else str(value))
        self.send_proxy.setCurrentIndex(self.send_proxy.findData(spec['send_proxy']))
        self.receive_proxy.setCurrentIndex(self.receive_proxy.findData(spec['receive_proxy']))
        self.units.setValue(spec['units']); self.invalidate()
        self.status.setText(tr('Parámetros recuperados. Calculá el costo para crear una nueva versión.'))

    def refresh_jobs(self, selected_id=None):
        old = self.selected_job()
        selected_id = selected_id or (old['id'] if old else None)
        self.jobs.clear()
        for job in self.store.list():
            cost = job['estimate']
            row = QListWidgetItem(f"{job['spec']['asset']} · v{job['version']:04d}  |  {job['state']}  |  ≈ {cost['total_cost']:.4f} {cost['currency']}")
            row.setData(Qt.UserRole, job); self.jobs.addItem(row)
            if job['id'] == selected_id: self.jobs.setCurrentItem(row)
        if self.jobs.currentRow() < 0 and self.jobs.count(): self.jobs.setCurrentRow(0)

    def selected_job(self):
        row = self.jobs.currentItem()
        return row.data(Qt.UserRole) if row else None

    def select_job(self, *args):
        self.preview_timer.stop(); self.outputs.clear()
        job = self.selected_job()
        if not job: return
        for index, output in enumerate(job.get('outputs', [])):
            self.outputs.addItem(f'Resultado {index + 1} · {Path(output["original"]).name}', output)
        self.details.setText(tr('{0} · {1}\nRequest: {2}\nProyecto: {3}\nPrompt: {4}').format(job['spec']['endpoint'], job['state'], job.get('remote', {}).get('request_id', 'sin confirmar'), job['spec'].get('project', ''), job['spec']['payload'].get('prompt', '')[:180]))
        self.logs.setPlainText('\n'.join(e['at'][11:19] + '  ' + e['message'] for e in job.get('events', [])[-30:]))
        self.show_output()

    def job_progress(self, job):
        self.status.setText(tr('v{0:04d} · {1} · {2}').format(job['version'], job['state'], job['events'][-1]['message']))
        self.refresh_jobs(job['id'])
        if job.get('live_logs'): self.logs.appendPlainText('\n'.join(job['live_logs']))

    def job_done(self, job):
        self.refresh_jobs(job['id']); self.status.setText(tr('Trabajo: ') + job['state'])

    def resume_selected(self):
        job = self.selected_job()
        if not job or not job.get('remote'): return self.status.setText(tr('Sin request ID recuperable'))
        if job['state'] == 'READY': return self.status.setText(tr('Los resultados ya están guardados'))
        client = self.client()
        self.run_task(lambda task: JobRunner(client, self.store, task.progress.emit, task.stop).resume(job), self.job_done)

    def pause_tracking(self):
        if self.busy():
            self.task.stop.set(); self.status.setText(tr('Pausando al terminar la operación actual. El trabajo remoto puede continuar y cobrar.'))

    def cancel_selected(self):
        job = self.selected_job()
        if not job or not job.get('remote', {}).get('cancel_url'): return
        if self.busy(): return self.status.setText(tr('Pausá primero el seguimiento y esperá a que termine la operación actual'))
        if QMessageBox.question(self, tr('Cancelar en fal'), tr('Solicitar cancelación remota. Si ya está ejecutándose puede no cancelarse y generar cargos.'),
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes: return
        def done(result):
            job['events'].append(dict(at=now(), message='Cancelación solicitada. Reanudar seguimiento para confirmar el estado.'))
            self.store.save(job); self.job_done(job)
        client = self.client()
        self.run_task(lambda _: client.queue_request(job['remote']['cancel_url'], 'PUT'), done)

    def show_output(self, *args):
        self.preview_timer.stop(); self.frames = []
        output = self.outputs.currentData()
        if not output:
            self.preview.clear(); self.preview.setText(tr('Sin resultados descargados para esta versión')); return
        if output.get('preview'):
            self.frames = sorted(Path(output['preview']['first_file']).parent.glob('frame_*.jpg'))
            self.play_index = 0
            if self.frames: return self.show_image(self.frames[0])
        path = output.get('proxy') or output['original']
        if Path(path).suffix.lower() in VIDEO:
            self.preview.clear(); self.preview.setText(tr('Video guardado. Abrí el original o configurá FFmpeg para preparar una secuencia.')); return
        self.show_image(path)

    def show_image(self, path):
        pixmap = QPixmap(str(path))
        self.preview.setPixmap(pixmap.scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def toggle_play(self):
        if self.preview_timer.isActive(): self.preview_timer.stop()
        elif self.frames: self.preview_timer.start()

    def next_frame(self):
        if self.frames:
            self.play_index = (self.play_index + 1) % len(self.frames); self.show_image(self.frames[self.play_index])

    def open_original(self):
        if self.outputs.currentData(): QDesktopServices.openUrl(QUrl.fromLocalFile(self.outputs.currentData()['original']))

    def import_selected(self):
        output, job = self.outputs.currentData(), self.selected_job()
        if not output or not job: return
        original = output['original']
        project = self.owner.project
        def done(result):
            if self.owner.project is not project:
                return self.status.setText(tr('Cambió el proyecto; volvé a elegir Usar en graph'))
            self.owner.import_genai_result(result['path'], job, output, result.get('frames'))
            self.status.setText(tr('Nodo Read agregado al proyecto; original conservado'))
        if Path(original).suffix.lower() in VIDEO:
            directory = Path(original).parent / (Path(original).stem + '_frames')
            ffmpeg = self.ffmpeg.text().strip()
            self.run_task(lambda _: sequence(original, directory, ffmpeg), done)
        else: done({'path': original})

    def prepare_selected_proxy(self):
        from genai_media import proxy
        job, output = self.selected_job(), self.outputs.currentData()
        if not job or not output: return
        index = self.outputs.currentIndex()
        ffmpeg, size = self.ffmpeg.text().strip(), self.receive_proxy.currentData()
        def work(_):
            directory = Path(job['directory']) / f'receive_{index}'
            path = proxy(output['original'], directory, size, ffmpeg)
            output['proxy'] = path
            if Path(path).suffix.lower() in VIDEO:
                output['preview'] = sequence(path, directory / 'playback', ffmpeg, True)
            output.pop('proxy_error', None)
            job['outputs'][index] = output; self.store.save(job)
            return job
        self.run_task(work, self.job_done)

    def closeEvent(self, event):
        self.preview_timer.stop()
        if self.busy():
            self.status.setText(tr('Pausá el seguimiento y esperá la operación actual antes de cerrar.')); event.ignore()
        else: event.accept()
