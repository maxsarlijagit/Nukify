# SPDX-License-Identifier: GPL-3.0-or-later
"""Float Viewer controls are display-only; they never alter the Blender graph."""
import numpy as np
from collections import OrderedDict
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QImage, QPixmap, QColor, QBrush, QPainter,QPen
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QDoubleSpinBox, QSlider, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem)


def display_pixels(source, channel='RGB', exposure=0., gamma=1., transform='sRGB', checker=True, ocio_processor=None):
    data = np.nan_to_num(source, nan=0., posinf=65504., neginf=-65504.)
    if channel == 'A':
        rgb = np.repeat(np.clip(data[..., 3:4], 0, 1), 3, axis=2)
    else:
        rgb = data[..., :3].copy()
        if checker and channel == 'RGB':
            alpha = data[..., 3:4]
            rgb = np.divide(rgb, alpha, out=np.zeros_like(rgb), where=np.abs(alpha)>1e-8)
        if channel in ('R', 'G', 'B'):
            rgb = np.repeat(rgb[..., 'RGB'.index(channel):'RGB'.index(channel)+1], 3, axis=2)
        elif channel == 'Y':
            rgb = np.repeat(np.sum(rgb * [0.2126, 0.7152, 0.0722], axis=2, keepdims=True), 3, axis=2)
        rgb *= 2. ** exposure
        if transform == 'OCIO':
            if ocio_processor is None: raise ValueError('Configura OCIO en Color management')
            rgb = np.ascontiguousarray(rgb, dtype=np.float32)
            ocio_processor.applyRGB(rgb)
        elif transform == 'sRGB':
            rgb = np.where(rgb <= .0031308, rgb * 12.92, 1.055 * np.maximum(rgb, 0) ** (1 / 2.4) - .055)
        rgb = np.maximum(rgb, 0) ** (1 / max(.01, gamma))
        if channel == 'Matte':
            rgb[..., 0] = .5 * rgb[..., 0] + .5 * (1 - np.clip(data[..., 3], 0, 1))
        if checker and channel == 'RGB':
            yy, xx = np.indices(data.shape[:2])
            bg = (.12 + .08 * ((xx // 16 + yy // 16) % 2))[..., None]
            alpha = np.clip(data[..., 3:4], 0, 1)
            rgb = rgb * alpha + bg * (1 - alpha)
    return np.ascontiguousarray(np.clip(rgb * 255 + .5, 0, 255).astype(np.uint8))


class Canvas(QGraphicsView):
    sample = Signal(str)
    zoomed = Signal(str)
    channel = Signal(str)
    play = Signal()

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.item = QGraphicsPixmapItem()
        self.scene().addItem(self.item)
        self.setBackgroundBrush(QBrush(QColor('#101318')))
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.setMinimumSize(320, 150)
        self.fit_mode = True
        self.pixels = None
        self.format_overlay=False;self.sample_radius=0

    def image(self, rgb, source):
        self.pixels = source
        h, w, _ = rgb.shape
        qimage = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888).copy()
        self.item.setPixmap(QPixmap.fromImage(qimage))
        self.scene().setSceneRect(QRectF(0, 0, w, h))
        if self.fit_mode:
            self.fit()

    def fit(self):
        self.fit_mode = True
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        self.zoomed.emit(f'{self.transform().m11()*100:.0f}%')

    def actual(self):
        self.fit_mode = False
        self.resetTransform()
        self.zoomed.emit('100%')

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        if .02 < self.transform().m11() * factor < 32:
            self.fit_mode = False
            self.scale(factor, factor)
            self.zoomed.emit(f'{self.transform().m11()*100:.0f}%')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fit_mode:
            self.fit()

    def drawForeground(self, painter, rect):
        if self.format_overlay and self.pixels is not None:
            h,w=self.pixels.shape[:2];painter.save();pen=QPen(QColor('#e6bd76'));pen.setCosmetic(True);painter.setPen(pen)
            painter.drawRect(QRectF(0,0,w,h));pen.setStyle(Qt.DashLine);painter.setPen(pen)
            painter.drawRect(QRectF(w*.05,h*.05,w*.9,h*.9));painter.restore()
        if hasattr(self, 'owner'): self.owner.draw_shapes(painter, self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._pan = event.position().toPoint(); event.accept(); return
        if hasattr(self, 'owner') and self.owner.shape_event('press', event, self):
            event.accept(); return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._pan = None; event.accept(); return
        if hasattr(self, 'owner') and self.owner.shape_event('release', event, self):
            event.accept(); return
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, '_pan', None) is not None:
            pos=event.position().toPoint();d=pos-self._pan;self._pan=pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()-d.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value()-d.y());return
        if hasattr(self, 'owner') and self.owner.shape_event('move', event, self):
            return
        if self.pixels is not None:
            p = self.mapToScene(event.position().toPoint())
            x, y = int(np.floor(p.x())), int(np.floor(p.y()))
            h, w, _ = self.pixels.shape
            if 0 <= x < w and 0 <= y < h:
                r=self.sample_radius;region=self.pixels[max(0,y-r):min(h,y+r+1),max(0,x-r):min(w,x+r+1)]
                rgba=region.mean(axis=(0,1));luma=float(np.dot(rgba[:3],[.2126,.7152,.0722]))
                full=getattr(getattr(self,'owner',None),'project',{})
                sx=full.get('width',w)/w;sy=full.get('height',h)/h
                self.sample.emit(f'x {int(x*sx)}  y {int((h-1-y)*sy)} | RGBA linear '+ '  '.join(f'{v:.5g}' for v in rgba)+f' | Y {luma:.5g} | {region.shape[1]}x{region.shape[0]} proxy px')
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        text = event.text().upper()
        if text in ('R', 'G', 'B', 'A', 'Y'):
            self.channel.emit(text)
        elif event.key() == Qt.Key_F:
            self.fit()
        elif event.key() == Qt.Key_Space and hasattr(self, 'owner'):
            self.owner.maximize_panel('viewer')
        elif event.key() == Qt.Key_Escape and hasattr(self, 'owner'):
            self.owner.shape_event('cancel', event, self)
        elif event.key() in (Qt.Key_J, Qt.Key_K, Qt.Key_L) and hasattr(self, 'owner'):
            self.owner.pause()
            if event.key() != Qt.Key_K:
                self.owner.play_direction = -1 if event.key() == Qt.Key_J else 1
                self.owner.toggle_play()
        elif event.key() in (Qt.Key_Left, Qt.Key_Right) and hasattr(self, 'owner'):
            self.owner.jump(self.owner.project['frame'] + (-1 if event.key()==Qt.Key_Left else 1))
        else:
            super().keyPressEvent(event)


class FloatViewer(QWidget):
    play_requested = Signal()
    def __init__(self):
        super().__init__()
        self.source = None
        self.reference = None
        self.current_info = None
        self.buffers = OrderedDict()
        self.display_cache = OrderedDict()
        self.cache_bytes = 0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        from ui_theme import FlowLayout,decorate
        toolbar = FlowLayout()
        self.channels = QComboBox()
        self.channels.addItems(['RGB', 'R', 'G', 'B', 'A', 'Y', 'Matte'])
        self.channels.setToolTip('Canales RGBA / luminancia / overlay de matte')
        toolbar.addWidget(QLabel('rgba'))
        toolbar.addWidget(self.channels)
        self.transform = QComboBox()
        self.transform.addItems(['sRGB', 'Linear', 'OCIO'])
        self.transform.setToolTip('Transformacion de visualizacion; no modifica Write')
        toolbar.addWidget(self.transform)
        self.exposure = QDoubleSpinBox()
        self.exposure.setRange(-20, 20)
        self.exposure.setSingleStep(.25)
        self.exposure.setPrefix('Exp ')
        self.exposure.setToolTip('Exposicion del Viewer en stops; independiente de la composicion')
        toolbar.addWidget(self.exposure)
        self.gamma = QDoubleSpinBox()
        self.gamma.setRange(.1, 5)
        self.gamma.setValue(1)
        self.gamma.setSingleStep(.1)
        self.gamma.setPrefix('Gamma ')
        toolbar.addWidget(self.gamma)
        self.checker = QPushButton('Checker')
        self.checker.setCheckable(True)
        self.checker.setChecked(True)
        toolbar.addWidget(self.checker)
        fit, actual = QPushButton('Fit'), QPushButton('1:1')
        toolbar.addWidget(fit)
        toolbar.addWidget(actual)
        self.zoom = QLabel('100%')
        toolbar.addWidget(self.zoom)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        comparison = FlowLayout()
        self.comparison_tools=comparison
        capture = QPushButton('Capturar B')
        capture.setToolTip('Congela el cuadro actual como referencia B')
        capture.clicked.connect(self.capture)
        comparison.addWidget(capture)
        self.compare = QComboBox()
        self.compare.addItems(['A', 'B', 'Wipe', 'Difference'])
        comparison.addWidget(self.compare)
        self.wipe = QSlider(Qt.Horizontal)
        self.wipe.setRange(0, 100)
        self.wipe.setValue(50)
        self.wipe.setMaximumWidth(140)
        self.wipe.setToolTip('Posicion del wipe A/B')
        comparison.addWidget(self.wipe)
        self.reference_label = QLabel('B: sin captura')
        from PySide6.QtWidgets import QSizePolicy
        self.reference_label.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed)
        comparison.addWidget(self.reference_label)
        self.sample_size=QComboBox();self.sample_size.addItems(['Pixel','3 x 3','9 x 9']);self.sample_size.setToolTip('Promedio de muestras scene-linear, antes del display')
        comparison.addWidget(self.sample_size)
        self.overlays=QPushButton('Formato');self.overlays.setCheckable(True);self.overlays.setToolTip('Limite de formato y margen del 5%; no representa dataWindow EXR');comparison.addWidget(self.overlays)
        comparison.addStretch()
        reset = QPushButton('Reset view')
        reset.clicked.connect(self.reset)
        for button,name in [(capture,'layers'),(fit,'fit'),(actual,'viewer'),(reset,'reset'),(self.checker,'image'),(self.overlays,'fit')]:decorate(button,name)
        comparison.addWidget(reset)
        layout.addLayout(comparison)
        self.canvas = Canvas()
        self.sample_size.currentIndexChanged.connect(lambda i:setattr(self.canvas,'sample_radius',[0,1,4][i]))
        def toggle_overlay(enabled):self.canvas.format_overlay=enabled;self.canvas.viewport().update()
        self.overlays.toggled.connect(toggle_overlay)
        self.canvas.channel.connect(lambda c: self.channels.setCurrentText('RGB' if self.channels.currentText() == c else c))
        self.canvas.play.connect(self.play_requested)
        self.canvas.zoomed.connect(self.zoom.setText)
        self.probe = QLabel('RGBA float · zoom con rueda · boton medio para pan')
        self.canvas.sample.connect(self.probe.setText)
        self.probe.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed)
        self.canvas.sample.connect(self.probe.setToolTip)
        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.probe)
        fit.clicked.connect(self.canvas.fit)
        actual.clicked.connect(self.canvas.actual)
        for combo in (self.channels, self.transform, self.compare):
            combo.currentIndexChanged.connect(self.refresh)
        for control in (self.exposure, self.gamma, self.wipe):
            control.valueChanged.connect(self.refresh)
        self.checker.toggled.connect(self.refresh)

    def load_float(self, info):
        self.current_info = info
        key = info['raw']
        if key not in self.buffers:
            pixels = np.fromfile(key, dtype=np.float32).reshape(info['height'], info['width'], 4)
            self.buffers[key] = pixels
            self.cache_bytes += pixels.nbytes
        self.buffers.move_to_end(key)
        self.source = self.buffers[key]
        while self.cache_bytes > 192 * 1024**2 and len(self.buffers) > 1:
            _, removed = self.buffers.popitem(last=False)
            self.cache_bytes -= removed.nbytes
        self.refresh()

    def capture(self):
        if self.source is not None:
            self.reference = self.source.copy()
            self.reference_label.setText(f"B: frame {self.current_info['frame']} (snapshot)")
            self.refresh()

    def reset(self):
        self.channels.setCurrentText('RGB')
        self.transform.setCurrentText('sRGB')
        self.exposure.setValue(0)
        self.gamma.setValue(1)
        self.compare.setCurrentText('A')
        self.canvas.fit()

    def refresh(self, *_):
        if self.source is None:
            return
        if self.transform.currentText() == 'OCIO' and getattr(self, 'ocio_processor', None) is None:
            self.probe.setText('Configura OCIO desde Color management'); return
        data = self.source
        if self.reference is not None and self.reference.shape == data.shape:
            mode = self.compare.currentText()
            if mode == 'B':
                data = self.reference
            elif mode == 'Difference':
                data = np.abs(data - self.reference)
                data[..., 3] = 1
            elif mode == 'Wipe':
                data = data.copy()
                cut = int(data.shape[1] * self.wipe.value() / 100)
                data[:, :cut] = self.reference[:, :cut]
        elif self.compare.currentText() != 'A':
            self.reference_label.setText('Capturar B con el mismo formato/proxy')
        cache_key = (self.current_info['raw'], self.channels.currentText(), self.exposure.value(),
                     self.gamma.value(), self.transform.currentText(), self.checker.isChecked())
        use_cache = self.compare.currentText() == 'A'
        rgb = self.display_cache.get(cache_key) if use_cache else None
        if rgb is None:
            rgb = display_pixels(data, self.channels.currentText(), self.exposure.value(),
                                 self.gamma.value(), self.transform.currentText(), self.checker.isChecked(), getattr(self, 'ocio_processor', None))
            if use_cache:
                self.display_cache[cache_key] = rgb
                while sum(a.nbytes for a in self.display_cache.values()) > 64 * 1024**2:
                    self.display_cache.popitem(last=False)
        elif use_cache:
            self.display_cache.move_to_end(cache_key)
        self.canvas.image(rgb, data)
