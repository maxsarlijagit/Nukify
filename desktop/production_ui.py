# SPDX-License-Identifier: GPL-3.0-or-later
from i18n import tr
import copy
import json
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QWidget,QFormLayout,QLabel,QLineEdit,QPushButton,QDoubleSpinBox,
    QComboBox,QCheckBox,QHBoxLayout,QDialog,QVBoxLayout,QTableWidget,QTableWidgetItem,
    QDialogButtonBox,QFileDialog,QMessageBox,QGraphicsScene,QGraphicsView)
from PySide6.QtGui import QPainterPath,QPen,QColor
from registry import NODES,INPUTS,MASKS,DEFAULTS,TYPES,SOCKET_TYPES
from animation import parameters,set_key,value_at
from model import migrate
from shape_ui import ShapeUI
from tracking_ui import TrackingUI
from color_ui import ColorUI
from shortcuts import ShortcutUI
from delivery_ui import DeliveryUI
from ui_theme import FlowLayout,decorate,icon


class ProductionUI(ShapeUI, TrackingUI, ColorUI, ShortcutUI, DeliveryUI):
    def filter_properties(self,*args):
        if not hasattr(self,'scroll') or not self.scroll.widget():return
        form=self.scroll.widget().layout();query=self.property_search.text().strip().lower().replace('_',' ')
        for row in range(form.rowCount()):
            texts=[]
            for role in (QFormLayout.LabelRole,QFormLayout.FieldRole,QFormLayout.SpanningRole):
                item=form.itemAt(row,role)
                if item and item.widget():
                    widget=item.widget()
                    if isinstance(widget,(QLabel,QPushButton,QCheckBox)):texts.append(widget.text())
                    texts.extend(child.text() for child in widget.findChildren(QPushButton))
            form.setRowVisible(row,not query or query in ' '.join(texts).lower().replace('_',' '))
    def setup_production(self, root, data, tools):
        self.app_root,self.app_data=Path(root),Path(data)
        for category in dict.fromkeys(n['category'] for n in NODES.values()):
            from PySide6.QtWidgets import QMenu
            menu=QMenu(self)
            for kind,spec in NODES.items():
                if spec['category']==category:menu.addAction(kind,lambda k=kind:self.add(k))
            button=QPushButton(tr(category));button.setMenu(menu);decorate(button,{'Image':'image','Color':'color','Channel':'layers','Merge':'layers','Filter':'filter','Transform':'transform','Time':'loop','Draw':'draw','Keyer':'color','Tracking':'fit','Utilities':'tools','3D':'cube'}.get(category,'nodes'),category+' nodes');tools.addWidget(button)
        self.autosave_timer=QTimer(self);self.autosave_timer.setInterval(30000)
        self.autosave_timer.timeout.connect(self.autosave);self.autosave_timer.start()
        # One recovery per process; never overwrite another running session's backup.
        import os
        self.recovery_path=self.app_data/f'recovery-{os.getpid()}.nukify'
        self.viewer.canvas.owner=self
        controls=self.viewer.comparison_tools
        for title,callback in [('Layers / canales EXR',self.viewer_layers),('Intercambiar A / B',self.swap_viewers)]:
            button=QPushButton(tr(title));button.clicked.connect(callback);controls.addWidget(button)
            decorate(button,'layers' if title.startswith('Layers') else 'swap');button.setText(tr('Canales EXR') if title.startswith('Layers') else 'A / B')
            if title.startswith('Layers'):button.setToolTip(tr('Inspeccionar un Read EXR de la rama A. Usar seleccion cambia el pase del Read y afecta la composicion.'))
        self.load_shortcuts()
        self.context_tools=QWidget();self.context_row=FlowLayout();self.context_tools.setLayout(self.context_row)
        self.viewer.layout().insertWidget(2,self.context_tools);self.context_tools.hide()

    def autosave(self):
        if not self.dirty:return
        try:
            doc=copy.deepcopy(self.project);doc.pop('blender',None)
            temp=self.recovery_path.with_suffix('.tmp');temp.write_text(json.dumps(doc),encoding='utf-8');temp.replace(self.recovery_path)
        except OSError as exc:self.statusBar().showMessage('Autosave: '+str(exc))

    def swap_viewers(self):
        if not self.project.get('viewer') or not self.project.get('viewer_b'):self.statusBar().showMessage(tr('Asigna A y B con 1 y 2 antes de intercambiar'));return
        self.checkpoint();self.project['viewer'],self.project['viewer_b']=self.project['viewer_b'],self.project['viewer'];self.changed()

    def viewer_layers(self):
        from model import ordered
        from PySide6.QtWidgets import QInputDialog
        try:
            nodes=[n for n in ordered(self.project,self.project['viewer']) if n['kind']=='Read' and Path(n['params']['path']).suffix.lower()=='.exr']
            if not nodes:self.statusBar().showMessage(tr('La rama A no contiene un Read EXR'));return
            choice,ok=QInputDialog.getItem(self,tr('Layers / canales'),tr('Read de la rama A'),[n['id'] for n in nodes],0,False)
            if ok:self.inspect_media(next(n for n in nodes if n['id']==choice))
        except (ValueError,OSError,KeyError) as exc:self.error(str(exc))

    def recover(self):
        path,_=QFileDialog.getOpenFileName(self,tr('Recuperar autosave'),str(self.app_data),'Nukify (*.nukify)')
        if path and self.discard_ok():
            try:
                self.project=migrate(json.loads(Path(path).read_text(encoding='utf-8')));self.filename=None;self.history=[];self.future=[];self.sync()
            except (ValueError,KeyError,OSError) as exc:self.error(str(exc))

    def maximize_panel(self, panel):
        if getattr(self,'maximized_panel',None)==panel:
            self.viewer_panel.show();self.graph_panel.show();self.maximized_panel=None
        else:
            self.viewer_panel.setVisible(panel=='viewer');self.graph_panel.setVisible(panel=='graph');self.maximized_panel=panel

    def production_properties(self,node):
        self.context_toolbar(node)
        panel=QWidget();form=QFormLayout(panel)
        form.setRowWrapPolicy(QFormLayout.WrapLongRows);form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow);form.setSpacing(8)
        if not node:form.addRow(QLabel(tr('Selecciona un nodo para editarlo.')))
        else:
            form.addRow(QLabel(node['id']+' / '+node['kind']))
            pin=QCheckBox(tr('Fijar propiedades'));pin.setChecked(getattr(self,'pinned_properties',None)==node['id'])
            def toggle_pin(checked):
                self.pinned_properties=node['id'] if checked else None
                current=next((n for n in self.project['nodes'] if n['id']==self.selected),None)
                if not checked:self.properties(current)
            pin.toggled.connect(toggle_pin);form.addRow(pin)
            spec=NODES[node['kind']]
            try:values=parameters(node,self.project['frame'],self.project)
            except ValueError as exc:
                values=parameters(node,self.project['frame']);form.addRow(QLabel(str(exc)))
            if node['kind']=='Roto':self.roto_layers(form,node)
            for key,value in values.items():
                if key in ('shapes','shape_order','groups','manual_points','exclude_polygon','correction_points'):continue
                if key in ('points','tracks','corners'):
                    b=QPushButton(tr('Editar en Viewer / datos'))
                    b.clicked.connect(lambda _,n=node,k=key:self.edit_shape(n,k))
                    form.addRow(key,b)
                    if key!='tracks':
                        kb=QPushButton('Keyframe '+key+' en frame actual')
                        def key_shape(_, k=key):
                            self.checkpoint();set_key(node,k,self.project['frame'],parameters(node,self.project['frame'])[k]);self.changed()
                        kb.clicked.connect(key_shape);form.addRow(kb)
                    continue
                if key in spec['enums']:
                    control=QComboBox()
                    for option in spec['enums'][key]:control.addItem(str(option),option)
                    control.setCurrentIndex(max(0,control.findData(value)))
                    control.currentIndexChanged.connect(lambda _,c=control,k=key:self.parameter(node,k,c.currentData()))
                elif isinstance(value,bool):
                    control=QCheckBox();control.setChecked(value)
                    control.toggled.connect(lambda v,k=key:self.parameter(node,k,v))
                elif isinstance(value,(int,float)):
                    control=QDoubleSpinBox();control.setDecimals(4);control.setRange(-1000000,1000000);control.setSingleStep(.1)
                    bounds={'gamma':(.001,100),'scale':(.0001,1000),'shape_scale':(.0001,1000),'shape_opacity':(0,1),'motion_samples':(1,16),'shutter':(0,2),'blur_pre':(0,2048),'blur_post':(0,2048),'edge_kernel_radius':(0,100),'edge_kernel_tolerance':(0,1),'despill_balance':(0,1),'mix':(0,1),'size':(0,2048),'feather':(0,1024),'width':(1,16384),'height':(1,16384),'samples':(1,256),'fstop':(.001,1024)}
                    if key in bounds:control.setRange(*bounds[key])
                    if node['kind']=='Mask' and key in ('width','height'):control.setRange(.001,2)
                    control.setValue(value);control.setKeyboardTracking(False)
                    control.valueChanged.connect(lambda v,k=key:self.parameter(node,k,v))
                else:
                    control=QLineEdit(str(value));control.editingFinished.connect(lambda c=control,k=key:self.parameter(node,k,c.text()))
                if node.get('animation_link') and key in ('x','y','scale','rotation','corners'):control.setEnabled(False)
                if key in node.get('expressions',{}):control.setEnabled(False)
                row=QWidget();layout=QHBoxLayout(row);layout.setContentsMargins(0,0,0,0);layout.setSpacing(3);layout.addWidget(control)
                reset=QPushButton(tr('Reset'));decorate(reset,'reset','Restaurar valor por defecto y quitar curva y expresion. Undo revierte.',True)
                reset.setEnabled(not node.get('animation_link'))
                reset.clicked.connect(lambda _,k=key:self.reset_parameter(node,k));layout.addWidget(reset)
                if isinstance(value,(int,float)) and not isinstance(value,bool):
                    expression=QPushButton(tr('fx'));expression.setMaximumWidth(28);expression.setToolTip(tr('Expresion matematica o referencia a otro nodo'))
                    expression.clicked.connect(lambda _,k=key:self.expression_dialog(node,k));layout.addWidget(expression)
                    keybutton=QPushButton('◆' if key in node.get('animation',{}) else '◇');keybutton.setMaximumWidth(30);keybutton.setToolTip(tr('Curva y keyframes'))
                    decorate(keybutton,'key','Curva y keyframes',True)
                    if key in node.get('animation',{}):keybutton.setStyleSheet('background:#705534;border-color:#b99051;')
                    keybutton.clicked.connect(lambda _,k=key:self.curve_dialog(node,k));layout.addWidget(keybutton)
                label=QLabel(tr(key.replace('_',' ').capitalize()));label.setToolTip(key);form.addRow(label,row)
                if key in ('path','tracking_path','preserve_exr','texture_path'):
                    browse=QPushButton(tr('Elegir imagen / secuencia...'))
                    browse.clicked.connect(lambda _,c=control,k=key:self.browse_media(node,k,c));form.addRow(browse)
            for socket in INPUTS[node['kind']]:
                combo=QComboBox();combo.addItem(tr('(sin conectar)'),None)
                for n in self.project['nodes']:
                    if n['id']!=node['id'] and n['kind'] not in ('Write','Backdrop') and TYPES.get(n['kind'],'image')==SOCKET_TYPES.get(socket,'image') and (socket!='Mask' or n['kind'] in MASKS):combo.addItem(n['id'],n['id'])
                combo.setCurrentIndex(max(0,combo.findData(node['inputs'].get(socket))))
                combo.currentIndexChanged.connect(lambda _,c=combo,s=socket:self.input_changed(node,s,c.currentData()))
                form.addRow(socket,combo)
            if node['kind'] in ('Tracker2D','PlanarTracker'):
                b=QPushButton(tr('Quitar correccion de este frame'));b.clicked.connect(lambda:self.remove_tracking_correction(node));form.addRow(b)
                for label,callback in [('Confianza / perdidas',lambda:self.tracking_report_dialog(node)),('Corregir puntos en este frame',lambda:self.edit_tracking_correction(node)),('Guardar correccion manual',lambda:self.store_tracking_correction(node)),('Editar zona de exclusion',lambda:self.edit_shape(node,'exclude_polygon',True))]:
                    b=QPushButton(tr(label));b.clicked.connect(callback);form.addRow(b)
                for label,callback in [('Analizar rango',lambda:self.start_tracking(node)),('Cancelar tracking',self.cancel_tracking),('Crear Transform / CornerPin',lambda:self.bake_tracking(node)),('Enlazar a nodo...',lambda:self.link_tracking(node))]:
                    b=QPushButton(tr(label));b.clicked.connect(callback);form.addRow(b)
            if node['kind'] in ('Read','Cryptomatte'):
                b=QPushButton(tr('Inspeccionar EXR / canales'));b.clicked.connect(lambda:self.inspect_media(node));form.addRow(b)
            if node.get('animation_link'):
                form.addRow(QLabel('Enlazado a '+node['animation_link']))
                unlink=QPushButton(tr('Desenlazar animacion'))
                def detach():
                    self.checkpoint();node.pop('animation_link',None);self.changed();self.properties(node)
                unlink.clicked.connect(detach);form.addRow(unlink)
            b=QPushButton(tr('Ver este nodo [1]'));b.clicked.connect(lambda:self.preview(node['id']));form.addRow(b)
        old=self.scroll.takeWidget()
        if old:old.deleteLater()
        self.scroll.setWidget(panel)
        if hasattr(self,'property_search'):self.filter_properties()

    def reset_parameter(self,node,key):
        default=copy.deepcopy(DEFAULTS[node['kind']][key])
        if node.get('animation_link'):return
        if node['params'].get(key)==default and key not in node.get('animation',{}) and key not in node.get('expressions',{}):return
        self.checkpoint();node['params'][key]=default;node.get('animation',{}).pop(key,None)
        node.get('expressions',{}).pop(key,None)
        self.changed();self.properties(node)

    def expression_dialog(self,node,key):
        from PySide6.QtWidgets import QInputDialog
        text,ok=QInputDialog.getText(self,'Expresion: '+node['id']+'.'+key,tr('frame, value, pi, sin/cos/abs/min/max/sqrt/clamp y ref("Nodo", "parametro"). Vacio elimina.'),text=node.get('expressions',{}).get(key,''))
        if not ok:return
        try:
            proposed=copy.deepcopy(self.project);candidate=next(n for n in proposed['nodes'] if n['id']==node['id'])
            if text.strip():candidate.setdefault('expressions',{})[key]=text.strip()
            else:candidate.get('expressions',{}).pop(key,None)
            parameters(candidate,self.project['frame'],proposed)
            self.checkpoint();node['expressions']=candidate.get('expressions',{});self.changed();self.properties(node)
        except ValueError as exc:self.error(str(exc))

    def browse_media(self,node,key,control):
        path,_=QFileDialog.getOpenFileName(self,tr('Imagen o primer cuadro'),'','Images (*.png *.jpg *.jpeg *.exr *.tif *.tiff)')
        if path:
            import re
            file=Path(path);match=re.search(r'(\d+)$',file.stem)
            if match:
                prefix=file.stem[:match.start()];candidates=list(file.parent.glob(prefix+'*'+file.suffix))
                if len(candidates)>1:path=str(file.with_name(prefix+'#'*len(match[0])+file.suffix))
            control.setText(path);self.parameter(node,key,path)

    def curve_dialog(self,node,key):
        dialog=QDialog(self);dialog.setWindowTitle(node['id']+'.'+key);layout=QVBoxLayout(dialog)
        curve=copy.deepcopy(node.get('animation',{}).get(key,{'interpolation':'linear','keys':[]}))
        combo=QComboBox();combo.addItems(['constant','linear','smooth','bezier']);combo.setCurrentText(curve['interpolation']);layout.addWidget(combo)
        table=QTableWidget(0,4);table.setHorizontalHeaderLabels([tr(text) for text in ['Frame','Value','In slope','Out slope']]);layout.addWidget(table)
        for entry in curve['keys']:
            row=table.rowCount();table.insertRow(row)
            for col,v in enumerate((entry+[0.,0.])[:4]):table.setItem(row,col,QTableWidgetItem(str(v)))
        def add():
            row=table.rowCount();table.insertRow(row);table.setItem(row,0,QTableWidgetItem(str(self.project['frame'])));table.setItem(row,1,QTableWidgetItem(str(parameters(node,self.project['frame'])[key])))
            table.setItem(row,2,QTableWidgetItem('0'));table.setItem(row,3,QTableWidgetItem('0'))
        b=QPushButton(tr('Agregar clave en frame actual'));b.clicked.connect(add);layout.addWidget(b)
        delete=QPushButton(tr('Quitar fila seleccionada'));delete.clicked.connect(lambda:table.removeRow(table.currentRow()));layout.addWidget(delete)
        def read():
            keys=sorted([[float(table.item(r,c).text()) for c in range(4)] for r in range(table.rowCount())])
            if len({k[0] for k in keys})!=len(keys):raise ValueError('Frames duplicados')
            return {'interpolation':combo.currentText(),'keys':keys}
        from curve_editor import CurveView,add_curve_tools,validate_curve
        view=CurveView(table,combo,read);layout.addWidget(view)
        plot=view.plot
        table.itemChanged.connect(plot);combo.currentTextChanged.connect(plot);table.itemSelectionChanged.connect(plot);plot()
        add_curve_tools(self,layout,table,combo,read,plot)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);layout.addWidget(buttons);buttons.rejected.connect(dialog.reject)
        def save():
            try:c=validate_curve(read())
            except (ValueError,AttributeError) as exc:self.error(str(exc));return
            self.checkpoint()
            if c['keys']:node.setdefault('animation',{})[key]=c
            else:node.get('animation',{}).pop(key,None)
            self.changed();dialog.accept();self.properties(node)
        buttons.accepted.connect(save);dialog.resize(500,620);dialog.exec()

    def dope_sheet(self):
        dialog=QDialog(self);dialog.setWindowTitle(tr('Dope sheet'));layout=QVBoxLayout(dialog)
        table=QTableWidget(0,3);table.setHorizontalHeaderLabels([tr(text) for text in ['Nodo','Parametro','Frames']]);layout.addWidget(table)
        entries=[]
        for node in self.project['nodes']:
            for key,curve in node.get('animation',{}).items():
                row=table.rowCount();table.insertRow(row);entries.append((node,key))
                for col,value in enumerate([node['id'],key,', '.join(str(k[0]) for k in curve['keys'])]):table.setItem(row,col,QTableWidgetItem(value))
        def edit(row,column):
            node,key=entries[row]
            if isinstance(node['params'][key],(int,float)):dialog.accept();self.curve_dialog(node,key)
        table.cellDoubleClicked.connect(edit);dialog.resize(700,420);dialog.exec()

    def load_example(self,name):
        if not self.discard_ok():return
        from examples import example
        from runtime import engine_path
        output=self.project['output'];self.project=example(name,self.app_root/'assets')
        self.project.update(output=output,blender=engine_path());self.history=[];self.future=[];self.filename=None;self.sync()

    def context_toolbar(self,node):
        if not hasattr(self,'context_tools'):return
        if getattr(self,'shape_node',None) is not node:self.shape_node=None
        while self.context_row.count():
            item=self.context_row.takeAt(0)
            if item.widget():item.widget().deleteLater()
        self.context_tools.setVisible(bool(node and node['kind'] in ('Roto','Tracker2D','PlanarTracker','CornerPin')))
        if not node:return
        kind=node['kind']
        if kind not in ('Roto','Tracker2D','PlanarTracker','CornerPin'):return
        self.context_row.addWidget(QLabel(kind))
        key='points' if kind=='Roto' else 'tracks' if kind=='Tracker2D' else 'corners'
        actions=[('Editar en Viewer',lambda:self.edit_shape(node,key,True)),('Terminar herramienta',lambda:self.end_shape_tool())]
        if kind in ('Tracker2D','PlanarTracker'):
            actions += [('Track <',lambda:self.start_tracking(node,'backward')),('Track >',lambda:self.start_tracking(node,'forward')),('Stop',self.cancel_tracking)]
        else:
            def keyframe():
                self.checkpoint();set_key(node,key,self.project['frame'],parameters(node,self.project['frame'])[key]);self.changed()
            actions += [('Keyframe',keyframe)]
        for label,callback in actions:
            button=QPushButton(tr(label));button.clicked.connect(callback);self.context_row.addWidget(button)
        self.context_row.addStretch()

    def end_shape_tool(self):
        self.shape_node=None;self.shape_drag=None;self.viewer.canvas.viewport().update()
