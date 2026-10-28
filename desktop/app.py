# SPDX-License-Identifier: GPL-3.0-or-later
"""Nukify desktop: vertical graph, Blender compositor backend."""
import copy
import ctypes
import json
import os
from pathlib import Path
import sys
import uuid

from PySide6.QtCore import Qt, QPointF, QProcess, QProcessEnvironment, QTimer,QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QPixmap, QAction, QKeySequence, QIcon,QPainterPathStroker
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QPushButton, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsSimpleTextItem,
    QFormLayout, QLineEdit, QDoubleSpinBox, QSpinBox, QFileDialog, QMessageBox,
    QComboBox, QScrollArea, QPlainTextEdit, QMenu,QSizePolicy)

from model import INPUTS, blank, demo, new_node, ordered, connect
from viewer import FloatViewer
from live_ui import LiveMixin
from runtime import engine_path
from graph_tools import GraphInteraction
from production_ui import ProductionUI
from registry import NODES, CATEGORY_COLORS
from animation import parameters, set_key
from model import migrate
from ui_theme import STYLE,FlowLayout,decorate,icon

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
DATA = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Nukify'
COLORS = {k:CATEGORY_COLORS[v['category']] for k,v in NODES.items()}


class Port(QGraphicsEllipseItem):
    def boundingRect(self):return QRectF(-9,-9,18,18)
    def shape(self):
        path=QPainterPath();path.addEllipse(self.boundingRect());return path
    def __init__(self, node, socket, x, y):
        super().__init__(-5, -5, 10, 10, node)
        self.node, self.socket = node, socket
        self.setPos(x, y)
        self.setBrush(QColor('#d2d9df'))
        self.setPen(QPen(QColor('#111820'), 1))
        self.setZValue(3)
        self.setToolTip(socket or 'Output: click, then an input')

    def mousePressEvent(self, event):
        self.node.graph.port_clicked(self)
        event.accept()


class Cable(QGraphicsPathItem):
    def shape(self):
        stroke=QPainterPathStroker();stroke.setWidth(12);return stroke.createStroke(self.path())
    def boundingRect(self):return self.shape().boundingRect()

class Node(QGraphicsRectItem):
    def paint(self,painter,option,widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor('#3b3b3b' if self.isSelected() else '#303030'))
        painter.setPen(QPen(QColor('#e6a34b' if self.isSelected() else '#151515'),2 if self.isSelected() else 1))
        painter.drawRoundedRect(self.rect(),5,5)
        if self.data['kind']!='Backdrop':
            painter.setPen(QPen(QColor(COLORS[self.data['kind']]),3));painter.drawLine(QPointF(6,3),QPointF(144,3))
    def __init__(self, graph, data):
        super().__init__(0, 0, 150, 42)
        self.graph, self.data = graph, data
        self.setBrush(QColor('#2b3038'))
        self.setPen(QPen(QColor(COLORS[data['kind']]), 2))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        if data['kind'] == 'Backdrop':
            self.setRect(0, 0, data['params']['width'], data['params']['height'])
            self.setZValue(-5)
            self.setBrush(QColor('#242d36'))
        if data.get('disabled'):
            self.setOpacity(.45)
        label = QGraphicsSimpleTextItem(data['params'].get('label', data['id']), self)
        label.setBrush(QColor('#e4e8ed'))
        label.setPos(12, 13)
        self.inputs = {}
        sockets = INPUTS[data['kind']]
        for i, socket in enumerate(sockets):
            x = 150 * (i + 1) / (len(sockets) + 1)
            self.inputs[socket] = Port(self, socket, x, 0)
            tag = QGraphicsSimpleTextItem(socket, self)
            tag.setBrush(QColor('#8c99a8'))
            tag.setScale(.75)
            tag.setPos(x - 7, -21)
        self.output = Port(self, None, 75, 42) if data['kind'] not in ('Write', 'Backdrop') else None
        self.setPos(data['x'], data['y'])

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.data['x'], self.data['y'] = value.x(), value.y()
            self.graph.update_edges()
            if not self.graph.loading:
                self.graph.owner.dirty = True
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)


class Graph(GraphInteraction, QGraphicsView):
    def __init__(self, owner):
        super().__init__()
        self.owner, self.items_by_id, self.edges, self.pending = owner, {}, [], None
        self.loading = False
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor('#181c22'))
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scene().selectionChanged.connect(self.selection)
        self.setMinimumHeight(150)

    def drawBackground(self,painter,rect):
        super().drawBackground(painter,rect)
        if self.transform().m11()<.35:return
        painter.setPen(QPen(QColor('#383838'),1))
        for x in range(int(rect.left())//24*24,int(rect.right())+24,24):
            for y in range(int(rect.top())//24*24,int(rect.bottom())+24,24):painter.drawPoint(QPointF(x,y))

    def rebuild(self):
        self.loading = True
        self._wire=None;self._preview=None;self._hover_port=None
        self.pending = None
        self.edges = []
        self.items_by_id = {}
        self.scene().clear()
        for data in self.owner.project['nodes']:
            item = Node(self, data)
            self.items_by_id[data['id']] = item
            self.scene().addItem(item)
        self.update_edges()
        self.loading = False

    def update_edges(self):
        for edge in self.edges:
            self.scene().removeItem(edge)
        self.edges = []
        for target in self.items_by_id.values():
            for socket, source_id in target.data['inputs'].items():
                source = self.items_by_id.get(source_id)
                if not source or not source.output:
                    continue
                a = source.output.scenePos()
                b = target.inputs[socket].scenePos()
                path = QPainterPath(a)
                offset = max(40, abs(b.y() - a.y()) * .5)
                path.cubicTo(a + QPointF(0, offset), b - QPointF(0, offset), b)
                edge = Cable(path)
                edge.setPen(QPen(QColor('#8195a7'), 2))
                edge.connection = (target.data['id'], socket)
                edge.setZValue(-1)
                self.scene().addItem(edge)
                self.edges.append(edge)

    def fit(self):
        self.fitInView(self.scene().itemsBoundingRect().adjusted(-80, -45, 80, 45), Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        if .15 < self.transform().m11() * factor < 4:
            self.scale(factor, factor)

    def port_clicked(self, port):
        if port.socket is None:
            self.pending = port.node.data['id']
            self.owner.statusBar().showMessage(f'{self.pending}: clic en una entrada superior para conectar')
        elif self.pending:
            try:
                before=copy.deepcopy(self.owner.project)
                connect(self.owner.project, self.pending, port.node.data['id'], port.socket)
                if before!=self.owner.project:self.owner.history.append(before);self.owner.future.clear();self.owner.changed()
                self.update_edges()
                self.owner.properties(port.node.data)
            except ValueError as exc:
                self.owner.error(str(exc))
            finally:
                self.pending = None

    def selection(self):
        if self.loading:
            return
        selected = [n for n in self.scene().selectedItems() if isinstance(n, Node)]
        if selected:
            self.owner.selected = selected[0].data['id']
            self.owner.properties(selected[0].data)
        else:
            self.owner.selected = None
            self.owner.properties(None)



class Window(ProductionUI, LiveMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Nukify 0.10.0 | Compositor Lab')
        self.setWindowIcon(QIcon(str(ROOT / 'assets' / 'nukify-logo.png')))
        self.resize(1440, 940)
        DATA.mkdir(parents=True, exist_ok=True)
        self.project = demo(ROOT / 'assets')
        self.project['blender'] = engine_path()
        self.project['output'] = str(Path.home() / 'Documents' / 'Nukify Renders')
        self.filename, self.selected, self.dirty = None, None, False
        self.history, self.future = [], []
        self.process = None
        self.running_job = None
        self.central = QWidget()
        self.setCentralWidget(self.central)
        layout = QVBoxLayout(self.central)
        layout.setContentsMargins(10, 8, 10, 8)
        bar = FlowLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap(str(ROOT / 'assets' / 'nukify-logo.png')).scaled(42, 42, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        bar.addWidget(logo)
        brand = QLabel('NUKIFY')
        brand.setStyleSheet('font-size:15px;font-weight:700;letter-spacing:2px;color:#e0b16b')
        bar.addWidget(brand)
        bar.addStretch()
        for label, callback in [('Demo', self.load_demo), ('Abrir', self.open_project),
                                ('Guardar', self.save_project), ('Asignar Viewer  [1]', self.preview_selected),
                                ('Exportar EXR', self.export)]:
            button = QPushButton(label)
            button.clicked.connect(callback)
            decorate(button,{'Demo':'image','Abrir':'open','Guardar':'save','Asignar Viewer  [1]':'viewer','Exportar EXR':'export'}[label])
            if label=='Exportar EXR':button.setProperty('primary',True)
            bar.addWidget(button)
        project_menu=QMenu(self)
        examples_menu=project_menu.addMenu('Ejemplos')
        for example_name in ['Composicion','Chroma y roto','Tracking 2D','Planar','EXR y Cryptomatte','Integracion 3D','Curvas y roto']:
            examples_menu.addAction(example_name,lambda _,name=example_name:self.load_example(name))
        for name,callback in [('Recuperar autosave',self.recover),('Color management',self.color_settings),('Shortcuts',self.shortcuts_dialog),('Curvas / Dope sheet',self.dope_sheet)]:
            project_menu.addAction(name,callback)
        project_button=QPushButton('Proyecto');project_button.setMenu(project_menu);bar.addWidget(project_button)
        decorate(project_button,'tools')
        genai_button = QPushButton('GENAI')
        decorate(genai_button, 'image', 'Generar y editar imágenes / videos con fal.ai')
        genai_button.clicked.connect(self.open_genai)
        bar.addWidget(genai_button)
        project_menu.addAction('Inspeccionar 3D en Blender',self.inspect_3d)
        for name,callback in [('Asignar Viewer B [2]',self.preview_b),('Desconectar B',self.clear_b),('Render queue',self.queue_dialog),('Reanudar render',self.resume_render),('Recopilar proyecto y medios',self.collect_project),('Presupuesto cache',self.cache_settings)]:project_menu.addAction(name,callback)
        layout.addLayout(bar)
        split = self.workspace_split = QSplitter(Qt.Horizontal)
        left = self.editor_split = QSplitter(Qt.Vertical)
        split.setChildrenCollapsible(False);left.setChildrenCollapsible(False)
        workspace_menu=QMenu(self)
        for title,mode in [('Composicion','comp'),('Viewer amplio','viewer'),('Nodos amplios','graph')]:workspace_menu.addAction(title,lambda _,m=mode:self.workspace_preset(m))
        workspace_menu.addSeparator();workspace_menu.addAction('Guardar distribucion',self.save_workspace)
        workspace=QPushButton('Espacio');workspace.setMenu(workspace_menu);decorate(workspace,'layers');bar.addWidget(workspace)
        viewer_panel = self.viewer_panel = QWidget()
        vl = QVBoxLayout(viewer_panel)
        vl.setContentsMargins(0, 0, 0, 0)
        self.viewer_label = QLabel('VIEWER  /  sin evaluar     |     Standard / sRGB')
        vl.addWidget(self.viewer_label)
        self.viewer = FloatViewer()
        vl.addWidget(self.viewer, 1)
        timeline = QHBoxLayout()
        timeline.addWidget(QLabel('FRAME'))
        self.frame = QSpinBox()
        self.frame.setRange(1, 1000000)
        self.frame.setValue(1)
        self.frame.valueChanged.connect(self.frame_changed)
        timeline.addWidget(self.frame)
        vl.addLayout(timeline)
        left.addWidget(viewer_panel)
        graph_panel = self.graph_panel = QWidget()
        gl = QVBoxLayout(graph_panel)
        gl.setContentsMargins(0, 0, 0, 0)
        tools = FlowLayout()
        tools.addWidget(QLabel('NODE GRAPH'))
        self.add_menu = QMenu(self)
        for kind in INPUTS:
            self.add_menu.addAction(kind, lambda k=kind: self.add(k))
        add = QPushButton('+ Nodo  [Tab]')
        add.setMenu(self.add_menu)
        decorate(add,'plus')
        tools.addWidget(add)
        fit = QPushButton('Encuadrar  [F]')
        fit.clicked.connect(lambda: self.graph.fit())
        decorate(fit,'fit')
        tools.addWidget(fit)
        tools.addStretch()
        gl.addLayout(tools)
        self.graph = Graph(self)
        graph_row=QHBoxLayout()
        palette=QWidget()
        categories=QVBoxLayout(palette);categories.setContentsMargins(0,0,4,0);categories.setSpacing(3)
        palette_scroll=QScrollArea();palette_scroll.setWidgetResizable(True);palette_scroll.setWidget(palette);palette_scroll.setFixedWidth(118);palette_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        graph_row.addWidget(palette_scroll);graph_row.addWidget(self.graph,1);gl.addLayout(graph_row,1)
        left.addWidget(graph_panel)
        left.setSizes([480, 380])
        split.addWidget(left)
        from PySide6.QtWidgets import QTabWidget
        right = QTabWidget();right.setMinimumWidth(290);right.setMaximumWidth(650)
        node_panel=QWidget();project_panel=QWidget();right.addTab(node_panel,icon('tools'),'Nodo');right.addTab(project_panel,icon('image'),'Proyecto')
        self.property_tabs=right
        node_layout=QVBoxLayout(node_panel);node_layout.setContentsMargins(6,6,6,6)
        self.property_search=QLineEdit();self.property_search.setPlaceholderText('Buscar parametro...');self.property_search.setClearButtonEnabled(True);self.property_search.setToolTip('Filtrar los controles del nodo seleccionado');node_layout.addWidget(self.property_search)
        self.property_search.textChanged.connect(self.filter_properties)
        rl = QVBoxLayout(project_panel)
        rl.setContentsMargins(12, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        node_layout.addWidget(self.scroll, 1)
        settings = QFormLayout()
        rl.addWidget(QLabel('PROJECT / FORMAT & RANGE'))
        self.width_box, self.height_box = QSpinBox(), QSpinBox()
        for key, control in [('width', self.width_box), ('height', self.height_box)]:
            control.setRange(16, 16384)
            control.setValue(self.project[key])
            control.valueChanged.connect(lambda v, k=key: self.setting(k, v))
            settings.addRow(key.title(), control)
        self.first, self.last = QSpinBox(), QSpinBox()
        for key, control in [('first', self.first), ('last', self.last)]:
            control.setRange(1, 1000000)
            control.setValue(self.project[key])
            control.valueChanged.connect(lambda v, k=key: self.setting(k, v))
            settings.addRow(key.title(), control)
        self.out = QLineEdit(self.project['output'])
        self.out.editingFinished.connect(lambda: self.setting('output', self.out.text()))
        settings.addRow('Output folder', self.out)
        rl.addLayout(settings)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(140)
        self.log.setPlaceholderText('Registro de Blender')
        self.log.hide()
        diagnostics = QPushButton('Diagnostico')
        diagnostics.setCheckable(True)
        diagnostics.toggled.connect(self.log.setVisible)
        rl.addWidget(diagnostics)
        rl.addWidget(self.log)
        cancel = QPushButton('Cancelar proceso')
        cancel.clicked.connect(self.cancel)
        rl.addWidget(cancel)
        rl.addStretch()
        split.addWidget(right)
        split.setSizes([1080, 340])
        layout.addWidget(split,1)
        self.setup_production(ROOT, DATA, categories)
        categories.addStretch()
        self.graph.rebuild()
        self.properties(None)
        self.setup_live(vl, timeline, ROOT, DATA)
        self.frame.setMaximumWidth(92);self.fps.setMaximumWidth(88)
        for b in viewer_panel.findChildren(QPushButton):
            names={'|<':'first','<':'prev','>':'next','>|':'last','Play':'play','Loop':'loop','Cache range':'layers','Live ON':'viewer'}
            if b.text() in names:decorate(b,names[b.text()],{'|<':'Primer frame','<':'Frame anterior','>':'Frame siguiente','>|':'Ultimo frame'}.get(b.text()),b.text() in ('|<','<','>','>|'))
        self.viewer_label.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed)
        self.restore_workspace()
        self.viewer.play_requested.connect(self.toggle_play)
        self.statusBar().showMessage('Live: edita parametros. 1 asigna el Viewer. Play reproduce; Cache range prepara el rango.')
        for shortcut, callback in [('Ctrl+S', self.save_project), ('Ctrl+Shift+S', self.save_as), ('Ctrl+O', self.open_project),
                                   ('Ctrl+Z', self.undo), ('Ctrl+Shift+Z', self.redo)]:
            action = QAction(self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            self.addAction(action)
        QTimer.singleShot(100, self.graph.fit)

    def workspace_preset(self,mode):
        self.viewer_panel.show();self.graph_panel.show();self.maximized_panel=None
        self.workspace_split.setSizes([max(500,self.width()-330),330])
        self.editor_split.setSizes({'comp':[600,300],'viewer':[750,150],'graph':[300,600]}[mode])

    def save_workspace(self):
        import base64
        payload={name:base64.b64encode(bytes(split.saveState())).decode() for name,split in [('main',self.workspace_split),('editors',self.editor_split)]}
        (DATA/'workspace.json').write_text(json.dumps(payload),encoding='utf-8');self.statusBar().showMessage('Distribucion guardada para la proxima apertura',4000)

    def restore_workspace(self):
        import base64
        try:
            payload=json.loads((DATA/'workspace.json').read_text(encoding='utf-8'))
            for name,split in [('main',self.workspace_split),('editors',self.editor_split)]:split.restoreState(base64.b64decode(payload[name],validate=True))
        except (OSError,ValueError,KeyError,TypeError):pass

    def checkpoint(self):
        self.history.append(copy.deepcopy(self.project))
        self.history = self.history[-60:]
        self.future.clear()

    def changed(self):
        self.dirty = True
        self.viewer_label.setText('VIEWER  /  cambios pendientes de evaluar     |     Standard / sRGB')
        self.invalidate_live()

    def setting(self, key, value):
        if self.project[key] != value:
            self.checkpoint()
            self.project[key] = value
            self.changed()

    def frame_changed(self, value):
        self.pause()
        self.project['frame'] = value
        property_id=getattr(self,'pinned_properties',None) or self.selected
        if property_id:
            node = next((n for n in self.project['nodes'] if n['id'] == property_id), None)
            if node and (node.get('animation') or node.get('expressions')): self.properties(node)
        self.invalidate_live()

    def sync(self,preserve_pin=False):
        if not preserve_pin:self.pinned_properties=None
        if hasattr(self, 'engine'):
            self.pause()
        self.selected = None
        for key, control in [('frame', self.frame), ('width', self.width_box), ('height', self.height_box),
                             ('first', self.first), ('last', self.last)]:
            control.blockSignals(True)
            control.setValue(self.project[key])
            control.blockSignals(False)
        self.project['blender'] = engine_path()
        self.restore_color()
        self.out.setText(self.project['output'])
        self.graph.rebuild()
        self.graph.fit()
        self.properties(None)
        self.changed()

    def undo(self):
        if self.history:
            self.future.append(copy.deepcopy(self.project))
            self.project = self.history.pop()
            self.sync(preserve_pin=True)

    def redo(self):
        if self.future:
            self.history.append(copy.deepcopy(self.project))
            self.project = self.future.pop()
            self.sync(preserve_pin=True)

    def properties(self, node):
        pinned=getattr(self,'pinned_properties',None)
        if pinned:
            resolved=next((n for n in self.project['nodes'] if n['id']==pinned),None)
            if resolved:node=resolved
            else:self.pinned_properties=None
        self.production_properties(node)

    def parameter(self, node, key, value):
        if parameters(node, self.project['frame'],self.project)[key] != value:
            self.checkpoint()
            if key in node.get('animation', {}):
                set_key(node, key, self.project['frame'], value)
            else:
                node['params'][key] = value
            self.changed()

    def input_changed(self, node, socket, source):
        before=copy.deepcopy(self.project)
        try:
            if source:
                connect(self.project, source, node['id'], socket)
            else:
                node['inputs'].pop(socket, None)
            if before!=self.project:self.history.append(before);self.future.clear()
            self.graph.update_edges()
            self.changed()
        except ValueError as exc:
            self.error(str(exc))
            QTimer.singleShot(0, lambda: self.properties(node))

    def add(self, kind):
        self.checkpoint()
        position = self.graph.mapToScene(self.graph.viewport().rect().center())
        node = new_node(self.project, kind, position.x(), position.y())
        self.graph.rebuild()
        self.graph.items_by_id[node['id']].setSelected(True)
        self.changed()

    def delete_selected(self):
        keys = {n.data['id'] for n in self.graph.scene().selectedItems() if isinstance(n, Node)}
        if not keys:
            return
        self.checkpoint()
        self.project['nodes'] = [n for n in self.project['nodes'] if n['id'] not in keys]
        for n in self.project['nodes']:
            n['inputs'] = {s: k for s, k in n['inputs'].items() if k not in keys}
        if self.project['viewer'] in keys:
            self.project['viewer'] = None
        if self.project.get('viewer_b') in keys:self.project.pop('viewer_b',None);self.engine_b.stop();self.viewer.reference=None
        self.sync()

    def discard_ok(self):
        if not self.dirty:
            return True
        result = QMessageBox.question(self, 'Proyecto modificado', 'Guardar cambios antes de continuar?',
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if result == QMessageBox.Save:
            return self.save_project()
        return result == QMessageBox.Discard

    def load_demo(self):
        if not self.discard_ok():
            return
        self.checkpoint()
        old = self.project
        self.project = demo(ROOT / 'assets')
        self.project['blender'], self.project['output'] = old['blender'], old['output']
        self.filename = None
        self.sync()

    def save_as(self):
        previous=self.filename;self.filename=None
        if not self.save_project():self.filename=previous

    def save_project(self):
        path = self.filename
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, 'Guardar proyecto', 'composition.nukify', 'Nukify (*.nukify)')
        if not path:
            return False
        try:
            target = Path(path)
            temp = target.with_suffix(target.suffix + '.tmp')
            document = copy.deepcopy(self.project)
            document.pop('blender', None)
            temp.write_text(json.dumps(document, indent=2), encoding='utf-8')
            temp.replace(target)
            self.filename, self.dirty = path, False
            self.statusBar().showMessage(f'Guardado: {path}')
            return True
        except Exception as exc:
            self.error(str(exc))
            return False

    def open_project(self):
        if not self.discard_ok():
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir proyecto', '', 'Nukify (*.nukify)')
        if not path:
            return
        try:
            project = json.loads(Path(path).read_text(encoding='utf-8'))
            if project.get('version') not in (1, 2) or not isinstance(project.get('nodes'), list):
                raise ValueError('Formato de proyecto no compatible')
            for node in project['nodes']:
                if node['kind'] not in INPUTS:
                    raise ValueError('Tipo de nodo no compatible')
            from delivery import resolve_media
            self.project, self.filename = migrate(resolve_media(project,Path(path).parent)), path
            self.history, self.future = [], []
            self.sync()
            self.dirty = False
        except Exception as exc:
            self.error(str(exc))

    def preview_selected(self):
        self.preview(self.selected or self.project['viewer'])

    def preview(self, target):
        if target:
            from registry import TYPES
            if next(n for n in self.project['nodes'] if n['id']==target)['kind'] in TYPES:
                self.error('Conecta la escena y camara a RenderLayers para verla.');return
            self.project['viewer'] = target
            self.dirty = True
            self.invalidate_live()
            self.request_live()
        else:
            self.error('Selecciona un nodo de imagen.')

    def export(self):
        writes = [n['id'] for n in self.project['nodes'] if n['kind'] == 'Write']
        if self.selected in writes:
            target = self.selected
        elif len(writes) == 1:
            target = writes[0]
        else:
            self.error('Selecciona el nodo Write que queres exportar.')
            return
        self.pause()
        self.live_timer.stop()
        self.warming = False
        self.warm_frames = []
        self.engine.stop();self.engine_b.stop()
        self.run(target, True)

    def run(self, target, export, resume_job=None):
        if self.process:
            self.error('Hay un proceso activo. Espera o cancela.')
            return
        try:
            executable = self.project['blender']
            if not Path(executable).is_file():
                raise ValueError('Falta el motor incluido. Reinstala Nukify para repararlo.')
            render_graph=resume_job['graph'] if resume_job else self.project
            frames = resume_job['frames'] if resume_job else (list(range(self.project['first'], self.project['last'] + 1)) if export else [self.project['frame']])
            if not frames:
                raise ValueError('El rango First/Last esta invertido.')
            for frame in frames:
                ordered(render_graph, target, frame)
            token = uuid.uuid4().hex[:12]
            root = Path(self.project['output']) if export else DATA / 'cache'
            if export and not resume_job and not self.project['output'].strip():
                raise ValueError('Configura la carpeta Output.')
            directory = Path(resume_job['directory']) if resume_job else root / ('render_' + token)
            directory.mkdir(parents=True,exist_ok=True)
            job = {'graph': copy.deepcopy(self.project), 'target': target, 'frames': frames,
                   'export': export, 'directory': str(directory.resolve())}
            if resume_job:job=copy.deepcopy(resume_job)
            (directory/'result.json').unlink(missing_ok=True)
            job_path = directory / 'job.json'
            job_path.write_text(json.dumps(job), encoding='utf-8')
            self.running_job = job
            self.log.clear()
            self.viewer_label.setText(f'VIEWER  /  evaluando {target} con Blender...')
            self.process = QProcess(self)
            environment = QProcessEnvironment.systemEnvironment()
            for key in ('PYTHONHOME', 'PYTHONPATH', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH'):
                environment.remove(key)
            if render_graph.get('ocio'): environment.insert('OCIO', render_graph['ocio'])
            else: environment.remove('OCIO')
            self.process.setProcessEnvironment(environment)
            self.process.setProcessChannelMode(QProcess.MergedChannels)
            self.process.readyReadStandardOutput.connect(self.read_log)
            self.process.finished.connect(self.finished)
            self.process.errorOccurred.connect(self.process_error)
            # Frozen Windows apps alter the DLL search path. Do not pass that
            # path to Blender, which ships its own Python and native libraries.
            frozen_windows = sys.platform == 'win32' and getattr(sys, 'frozen', False)
            if frozen_windows:
                ctypes.windll.kernel32.SetDllDirectoryW(None)
            try:
                self.process.start(executable, ['--background', '--factory-startup', '--threads', '4',
                    '--python-exit-code', '1', '--python', str(ROOT / 'desktop' / 'worker.py'), '--', str(job_path.resolve())])
                self.process.waitForStarted(5000)
            finally:
                if frozen_windows:
                    ctypes.windll.kernel32.SetDllDirectoryW(str(ROOT))
            self.statusBar().showMessage('Blender procesando · CPU · sin servicios externos')
        except Exception as exc:
            self.queue_active=False
            self.error(str(exc))

    def read_log(self):
        if self.process:
            text = bytes(self.process.readAllStandardOutput()).decode('utf-8', errors='replace')
            self.log.appendPlainText(text.rstrip())

    def process_error(self, error):
        if error == QProcess.FailedToStart:
            self.queue_active=False
            self.log.appendPlainText('ERROR: no se pudo iniciar Blender.')
            self.process.deleteLater()
            self.process = None
            self.viewer_label.setText('VIEWER  /  error al iniciar Blender')

    def finished(self, code, status):
        self.read_log()
        job = self.running_job
        directory = Path(job['directory'])
        (directory / 'blender.log').write_text(self.log.toPlainText(), encoding='utf-8')
        success = code == 0 and (directory / 'result.json').is_file()
        if success:
            if job.get('inspect'):
                import subprocess
                frozen_windows=sys.platform=='win32' and getattr(sys,'frozen',False)
                if frozen_windows:ctypes.windll.kernel32.SetDllDirectoryW(None)
                try:subprocess.Popen([job['graph']['blender'],str(directory/'inspection.blend')],env={k:v for k,v in os.environ.items() if k not in ('PYTHONHOME','PYTHONPATH','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH')})
                finally:
                    if frozen_windows:ctypes.windll.kernel32.SetDllDirectoryW(str(ROOT))
            self.dirty = True
            self.viewer_label.setText('VIEWER / exportacion terminada; Live actualiza la vista' if self.live_toggle.isChecked()
                                      else 'VIEWER / Live OFF · imagen anterior conservada')
            self.statusBar().showMessage(f"{'EXR exportado' if job['export'] else 'Evaluacion lista'}: {directory}")
        else:
            self.viewer_label.setText('VIEWER  /  render fallido o cancelado · revisar registro')
            self.statusBar().showMessage(f'Proceso sin resultado completo: {directory}')
        self.process.deleteLater()
        self.process = None
        if getattr(self,'queue_active',False):
            if success:
                from delivery import atomic_json
                self.render_queue.pop(0);atomic_json(self.app_data/'render-queue.json',self.render_queue)
                if self.render_queue:QTimer.singleShot(0,self.queue_next);return
            self.queue_active=False
        if self.live_toggle.isChecked():
            self.request_live()

    def cancel(self):
        self.queue_active=False
        self.pause()
        self.warming = False
        self.warm_frames = []
        self.live_timer.stop()
        self.engine.stop();self.engine_b.stop()
        self.cancel_tracking()
        if self.process:
            self.process.kill()

    def error(self, text):
        QMessageBox.warning(self, 'Nukify', text)

    def open_genai(self):
        from genai_ui import GenAIWindow
        if not getattr(self, 'genai_window', None):
            self.genai_window = GenAIWindow(self, ROOT, DATA)
        self.genai_window.show()
        self.genai_window.raise_()
        self.genai_window.activateWindow()

    def import_genai_result(self, path, job, output, frames=None):
        self.checkpoint()
        position = self.graph.mapToScene(self.graph.viewport().rect().center())
        node = new_node(self.project, 'Read', position.x(), position.y())
        node['params']['path'] = path
        node['genai'] = {'job_id': job['id'], 'version': job['version'],
                         'endpoint': job['spec']['endpoint'], 'original': output['original'],
                         'sha256': output['sha256'], 'frames': frames}
        self.project['viewer'] = node['id']
        if frames:
            self.project['first'], self.project['last'], self.project['frame'] = 1, frames, 1
            self.first.setValue(1); self.last.setValue(frames); self.frame.setValue(1)
        self.graph.rebuild()
        self.graph.items_by_id[node['id']].setSelected(True)
        self.changed()

    def closeEvent(self, event):
        if getattr(self, 'genai_window', None) and self.genai_window.busy():
            QMessageBox.information(self, 'GENAI activo', 'Pausá el seguimiento GENAI y esperá la operación actual antes de cerrar.')
            event.ignore()
        elif self.process:
            QMessageBox.information(self, 'Proceso activo', 'Cancela el proceso o espera a que termine antes de cerrar.')
            event.ignore()
        elif self.discard_ok():
            self.pause()
            self.live_timer.stop()
            self.engine.stop();self.engine_b.stop()
            self.cancel_tracking()
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    from PySide6.QtGui import QFontDatabase
    font_file = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/segoeui.ttf'
    if font_file.is_file(): QFontDatabase.addApplicationFont(str(font_file))
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    window = Window()
    window.show()
    if '--genai-test' in sys.argv:
        from genai_selftest import run
        QTimer.singleShot(0, lambda: run(window, app, sys.argv[sys.argv.index('--genai-test') + 1]))
    if '--self-test' in sys.argv:
        from selftest import run
        run(window, app, sys.argv[sys.argv.index('--self-test')+1])
    if '--sprints-test' in sys.argv:
        from sprints_test import run
        run(window, app, sys.argv[sys.argv.index('--sprints-test')+1])
    if '--workflow-test' in sys.argv:
        from workflow_test import run
        run(window, app, sys.argv[sys.argv.index('--workflow-test')+1])
    if '--advanced-test' in sys.argv:
        from advanced_test import run
        run(window, app, sys.argv[sys.argv.index('--advanced-test')+1])
    sys.exit(app.exec())
