# SPDX-License-Identifier: GPL-3.0-or-later
from i18n import tr
import time
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QComboBox, QSpinBox, QSlider
from live_engine import LiveEngine, fingerprint
from ui_theme import FlowLayout,icon


class LiveMixin:
    def setup_live(self, layout, timeline, root, data):
        self.engine = LiveEngine(root, data / 'live-cache', self)
        self.engine_b = LiveEngine(root, data / 'live-cache-b', self)
        self.engine_b.ready.connect(self.live_b_ready)
        self.engine_b.failed.connect(self.live_error)
        self.expected_b=None
        import json
        try:budget=int(json.loads((data/'cache-settings.json').read_text())['disk_mb'])*1024**2
        except (OSError,ValueError,KeyError):budget=1024**3
        self.engine.budget=self.engine_b.budget=max(64*1024**2,budget)//2
        self.engine.ready.connect(self.live_ready)
        self.engine.failed.connect(self.live_error)
        self.engine.message.connect(self.log.appendPlainText)
        self.log.setMaximumBlockCount(250)
        self.expected_key = None
        self.playing = False
        self.waiting_frame = False
        self.warming = False
        self.warm_frames = []
        self.display_times = []
        self.live_timer = QTimer(self)
        self.live_timer.setSingleShot(True)
        self.live_timer.setInterval(140)
        self.live_timer.timeout.connect(self.request_live)
        self.play_timer = QTimer(self)
        self.play_timer.setTimerType(Qt.PreciseTimer)
        self.play_timer.setSingleShot(True)
        self.play_timer.timeout.connect(self.play_tick)
        row = FlowLayout()
        self.live_toggle = QPushButton(tr('Live ON'))
        self.live_toggle.setCheckable(True)
        self.live_toggle.setChecked(True)
        self.live_toggle.toggled.connect(self.toggle_live)
        row.addWidget(self.live_toggle)
        row.addWidget(QLabel(tr('Proxy')))
        self.proxy = QComboBox()
        for label, value in [('Full', 1), ('1/2', 2), ('1/4', 4)]:
            self.proxy.addItem(label, value)
        self.proxy.setCurrentIndex(1)
        self.proxy.currentIndexChanged.connect(self.invalidate_live)
        row.addWidget(self.proxy)
        self.cache_button = QPushButton(tr('Cache range'))
        self.cache_button.clicked.connect(self.cache_range)
        row.addWidget(self.cache_button)
        self.live_state = QLabel(tr('Iniciando motor...'))
        from PySide6.QtWidgets import QSizePolicy
        self.live_state.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed)
        row.addWidget(self.live_state, 1)
        layout.insertLayout(1, row)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(self.project['first'], self.project['last'])
        self.slider.setValue(self.project['frame'])
        self.slider.valueChanged.connect(self.frame.setValue)
        layout.addWidget(self.slider)
        from cache_strip import CacheStrip
        self.cache_strip=CacheStrip();self.cache_strip.seek.connect(self.jump);layout.addWidget(self.cache_strip)
        self.cache_scan=QTimer(self);self.cache_scan.setInterval(25);self.cache_scan.timeout.connect(self.scan_cache_marks)
        for label, callback in [('|<', lambda: self.jump(self.project['first'])),
                                ('<', lambda: self.jump(self.project['frame'] - 1))]:
            b = QPushButton(tr(label))
            b.setMaximumWidth(34)
            b.clicked.connect(callback)
            timeline.addWidget(b)
        self.play_button = QPushButton(tr('Play'))
        self.play_button.clicked.connect(self.toggle_play)
        timeline.addWidget(self.play_button)
        for label, callback in [('>', lambda: self.jump(self.project['frame'] + 1)),
                                ('>|', lambda: self.jump(self.project['last']))]:
            b = QPushButton(tr(label))
            b.setMaximumWidth(34)
            b.clicked.connect(callback)
            timeline.addWidget(b)
        self.fps = QSpinBox()
        self.fps.setRange(1, 60)
        self.fps.setValue(24)
        self.fps.setSuffix(' fps')
        timeline.addWidget(self.fps)
        self.loop = QPushButton(tr('Loop'))
        self.loop.setCheckable(True)
        self.loop.setChecked(True)
        timeline.addWidget(self.loop)
        QTimer.singleShot(200, self, lambda: self.request_live() if self.live_toggle.isChecked() else None)

    def toggle_live(self, enabled):
        self.live_toggle.setText(tr('Live ON') if enabled else tr('Live OFF'))
        self.live_timer.stop()
        if enabled:
            self.request_live()
        else:
            self.pause()
            self.expected_b=None
            self.engine_b.stop()
            self.warming = False
            self.warm_frames = []
            self.expected_key = None
            self.engine.pending = None

    def invalidate_live(self, *_):
        if not hasattr(self, 'engine'):
            return
        self.expected_key = None
        self.expected_b = None
        self.reset_cache_marks()
        self.warming = False
        self.warm_frames = []
        self.engine.pending = None
        self.slider.blockSignals(True)
        self.slider.setRange(self.project['first'], max(self.project['first'], self.project['last']))
        self.slider.setValue(self.project['frame'])
        self.slider.blockSignals(False)
        if self.live_toggle.isChecked() and not self.process:
            self.live_timer.start()

    def request_live(self):
        self.live_timer.stop()
        if self.process:
            return
        target = self.project.get('viewer')
        if not target:
            self.live_state.setText(tr('Selecciona un nodo y pulsa 1'))
            return
        try:
            frame = self.project['frame']
            self.expected_key = fingerprint(self.project, target, frame, self.proxy.currentData())
            self.waiting_frame = True
            self.request_time = time.perf_counter()
            self.live_state.setText(tr('Buffering {0}...').format(frame) if self.playing else tr('Actualizando {0}...').format(target))
            self.engine.request(self.project, target, frame, self.proxy.currentData())
        except (ValueError, OSError, KeyError) as exc:
            self.live_error(str(exc))

    def live_ready(self, info):
        self.mark_cached(info,'A')
        if self.warming:
            QTimer.singleShot(0,self.warm_next);return
        if info['key'] == self.expected_key:
            target_b=self.project.get('viewer_b')
            if target_b and not getattr(self,'accepting_pair',False):
                self.pending_a=info
                try:
                    self.expected_b=fingerprint(self.project,target_b,info['frame'],self.proxy.currentData())
                    self.engine_b.request(self.project,target_b,info['frame'],self.proxy.currentData())
                except (ValueError,OSError,KeyError) as exc:self.live_error(str(exc))
                return
            try:
                self.viewer.load_float(info)
            except (ValueError, OSError) as exc:
                self.live_error(str(exc))
                return
            self.waiting_frame = False
            self.viewer_label.setText(tr('VIEWER A / {0} / frame {1} / {2} x {3}').format(info['target'], info['frame'], info['width'], info['height']))
            now = time.perf_counter()
            self.display_times = (self.display_times + [now])[-24:]
            measured = (len(self.display_times)-1)/(now-self.display_times[0]) if len(self.display_times)>1 else 0
            status = 'cache' if info.get('cached') else f"Blender {info.get('ms', 0):.0f} ms"
            self.live_state.setText(status + (f' / {measured:.1f} fps' if self.playing else ' / live'))
            if self.playing:
                self.play_timer.start(max(1, round(1000 / self.fps.value() - (time.perf_counter()-self.request_time)*1000)))
        if self.warming:
            QTimer.singleShot(0, self.warm_next)
        elif not info.get('cached'):
            self.engine.prune()

    def live_b_ready(self, info):
        self.mark_cached(info,'B')
        if self.warming:
            QTimer.singleShot(0,self.warm_next);return
        if info['key']!=self.expected_b or self.pending_a['key']!=self.expected_key:return
        import numpy as np
        try:self.viewer.reference=np.fromfile(info['raw'],np.float32).reshape(info['height'],info['width'],4)
        except (OSError,ValueError) as exc:self.live_error(str(exc));return
        self.viewer.reference_label.setText(tr('B: {0} / frame {1}').format(info['target'], info['frame']))
        self.accepting_pair=True
        try:self.live_ready(self.pending_a)
        finally:self.accepting_pair=False
        self.engine_b.prune()

    def live_error(self, message):
        self.pause()
        self.warming = False
        self.warm_frames = []
        self.waiting_frame = False
        self.live_state.setText('Error: ' + message)
        self.viewer_label.setText(tr('VIEWER / imagen anterior · error de evaluacion'))
        self.log.appendPlainText('LIVE ERROR: ' + message)

    def pause(self):
        self.playing = False
        if hasattr(self, 'play_timer'):
            self.play_timer.stop()
            self.play_button.setText(tr('Play'))
            self.play_button.setIcon(icon('play'))

    def toggle_play(self):
        if self.playing:
            self.pause()
            return
        if self.project['last'] <= self.project['first']:
            self.live_state.setText(tr('Playback: define First y Last (al menos dos cuadros)'))
            return
        if self.process:
            return
        self.warming = False
        self.warm_frames = []
        self.display_times = []
        self.playing = True
        self.play_button.setText(tr('Pause'))
        self.play_button.setIcon(icon('pause'))
        self.request_live()

    def play_tick(self):
        if not self.playing:
            return
        frame = self.project['frame'] + getattr(self, 'play_direction', 1)
        if frame > self.project['last'] or frame < self.project['first']:
            if not self.loop.isChecked():
                self.pause()
                return
            frame = self.project['first'] if getattr(self, 'play_direction', 1) > 0 else self.project['last']
        self.frame.blockSignals(True)
        self.frame.setValue(frame)
        self.frame.blockSignals(False)
        self.project['frame'] = frame
        self.slider.blockSignals(True)
        self.slider.setValue(frame)
        self.slider.blockSignals(False)
        self.request_live()

    def jump(self, frame):
        self.pause()
        self.frame.setValue(max(self.project['first'], min(self.project['last'], frame)))

    def cache_range(self):
        if self.process:self.live_state.setText(tr('Espera o cancela la exportacion antes de preparar cache'));return
        self.pause()
        self.live_timer.stop()
        self.warming=False;self.warm_frames=[]
        frames=list(range(self.project['first'], self.project['last'] + 1))
        if not frames:self.live_state.setText(tr('Cache: el rango First/Last esta invertido'));return
        if len(frames) > 1000:
            self.live_state.setText(tr('Cache range: maximo 1000 cuadros por tanda'))
            self.warm_frames = []
            return
        branches=[('A',self.project.get('viewer'),self.engine)]
        if self.project.get('viewer_b'):branches.append(('B',self.project['viewer_b'],self.engine_b))
        size=max(1,self.project['width']//self.proxy.currentData())*max(1,self.project['height']//self.proxy.currentData())*16*len(frames)
        if any(size>getattr(engine,'budget',512*1024**2) for _,_,engine in branches):
            self.live_state.setText(tr('Rango excede el presupuesto: aumenta cache o usa un proxy menor.'));return
        if not branches[0][1]:self.live_state.setText(tr('Asigna Viewer A antes de preparar cache'));return
        self.expected_key=self.expected_b=None
        self.warm_frames=[(label,target,frame) for frame in frames for label,target,_ in branches]
        self.warming = True
        self.warm_next()

    def warm_next(self):
        if not self.warming or self.process:
            return
        if self.engine.busy or self.engine_b.busy:
            return
        try:
            while self.warm_frames:
                branch,target,frame = self.warm_frames.pop(0)
                engine=self.engine if branch=='A' else self.engine_b
                key = fingerprint(self.project, target, frame, self.proxy.currentData())
                if engine.cached(key):
                    from pathlib import Path
                    Path(engine.cached(key)['raw']).touch()
                    self.cache_strip.marks.setdefault(frame,set()).add(branch)
                    continue
                self.live_state.setText(tr('Cache {0}: frame {1} / {2}').format(branch, frame, self.project["last"]))
                engine.request(self.project, target, frame, self.proxy.currentData())
                return
            self.warming = False
            self.engine.prune()
            self.engine_b.prune();self.cache_strip.update()
            self.request_live()
            self.live_state.setText(tr('Rango cacheado. Play listo.'))
        except (ValueError, OSError, KeyError) as exc:
            self.live_error(str(exc))

    def reset_cache_marks(self):
        if not hasattr(self,'cache_strip'):return
        self.cache_strip.first=self.project['first'];self.cache_strip.last=self.project['last'];self.cache_strip.marks={};self.cache_strip.update()
        self.scan_frame=self.project['first'];self.cache_scan.start()

    def mark_cached(self,info,branch):
        target=self.project.get('viewer' if branch=='A' else 'viewer_b')
        if info.get('target')!=target:return
        try:
            if info['key']!=fingerprint(self.project,target,info['frame'],self.proxy.currentData()):return
        except (ValueError,OSError,KeyError):return
        self.cache_strip.marks.setdefault(info['frame'],set()).add(branch);self.cache_strip.update()

    def scan_cache_marks(self):
        # Bound each UI tick; never evaluate a whole long sequence in one event.
        if self.playing:return
        try:
            for _ in range(4):
                frame=self.scan_frame
                if frame>min(self.project['last'],self.project['first']+999):self.cache_scan.stop();break
                for branch,target,engine in [('A',self.project.get('viewer'),self.engine),('B',self.project.get('viewer_b'),self.engine_b)]:
                    if target and engine.cached(fingerprint(self.project,target,frame,self.proxy.currentData())):self.cache_strip.marks.setdefault(frame,set()).add(branch)
                self.scan_frame+=1
            self.cache_strip.update()
        except (ValueError,OSError,KeyError):self.cache_scan.stop()
