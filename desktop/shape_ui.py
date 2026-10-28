# SPDX-License-Identifier: GPL-3.0-or-later
from i18n import tr
import copy
import json
from PySide6.QtCore import Qt,QPointF
from PySide6.QtGui import QPen,QColor,QPainterPath
from PySide6.QtWidgets import QDialog,QVBoxLayout,QPlainTextEdit,QDialogButtonBox,QPushButton,QLabel,QComboBox,QTreeWidget,QTreeWidgetItem,QTableWidget,QTableWidgetItem
from animation import parameters,set_key
from shapes import sample_shape


class ShapeUI:
    def roto_layers(self,form,node):
        from registry import DEFAULTS
        keys=('points','feather','invert','shape_name','shape_operation','shape_order','shape_group','shape_enabled','shape_opacity','shape_x','shape_y','shape_scale','shape_rotation')
        def current():
            data={k:copy.deepcopy(node['params'][k]) for k in keys}
            data['animation']={k:copy.deepcopy(c) for k,c in node.get('animation',{}).items() if k in keys}
            return data
        def activate(data):
            for k in keys:
                node['params'][k]=copy.deepcopy(data.get(k,DEFAULTS['Roto'][k]));node.get('animation',{}).pop(k,None)
            node.setdefault('animation',{}).update(copy.deepcopy(data.get('animation',{})))
        combo=QComboBox();combo.addItem(node['params']['shape_name']+' (activa)',None)
        for i,layer in enumerate(node['params']['shapes']):combo.addItem(layer['shape_name'],i)
        def select():
            i=combo.currentData()
            if i is None:return
            self.checkpoint();old=current();new=node['params']['shapes'][i];activate(new);node['params']['shapes'][i]=old
            self.shape_node=None;self.changed();self.properties(node)
        combo.activated.connect(select);form.addRow(tr('Capas'),combo)
        def add():
            self.checkpoint();old=current();node['params']['shapes'].append(old)
            order=max(s['shape_order'] for s in node['params']['shapes'])+1
            activate(dict(points=[],feather=0.,invert=False,shape_name=f'Shape{order+1}',shape_operation='max',shape_order=order))
            self.shape_node=None;self.changed();self.properties(node)
        button=QPushButton(tr('Nueva capa Bezier'));button.clicked.connect(add);form.addRow(button)
        def remove():
            self.checkpoint()
            if node['params']['shapes']:activate(node['params']['shapes'].pop())
            else:node['params']['points']=[];node.get('animation',{}).pop('points',None)
            self.shape_node=None;self.changed();self.properties(node)
        button=QPushButton(tr('Quitar capa activa'));button.clicked.connect(remove);form.addRow(button)
        tree=QTreeWidget();tree.setHeaderLabels(['Jerarquia de roto']);tree.setMaximumHeight(150)
        from roto import validate_groups
        try:
            groups=validate_groups(node['params'].get('groups',[]));items={key:QTreeWidgetItem([key]) for key in groups}
            for key,group in groups.items():
                parent=items.get(group.get('parent',''))
                if parent:parent.addChild(items[key])
                else:tree.addTopLevelItem(items[key])
            for layer in node['params']['shapes']+[node['params']]:
                item=QTreeWidgetItem([layer['shape_name']+(' (activa)' if layer is node['params'] else '')]);parent=items.get(layer.get('shape_group',''))
                if parent:parent.addChild(item)
                else:tree.addTopLevelItem(item)
            tree.expandAll();form.addRow(tree)
        except ValueError as exc:form.addRow(QLabel(str(exc)))
        button=QPushButton(tr('Editar grupos / transformaciones'));button.clicked.connect(lambda:self.roto_group_dialog(node));form.addRow(button)

    def roto_group_dialog(self,node):
        from roto import validate_groups,shape_transform
        dialog=QDialog(self);dialog.setWindowTitle(tr('Grupos de roto'));layout=QVBoxLayout(dialog)
        keys=['id','parent','x','y','scale','rotation','opacity','enabled'];table=QTableWidget(0,len(keys));table.setHorizontalHeaderLabels(keys);layout.addWidget(table)
        defaults=dict(id='Group',parent='',x=0,y=0,scale=1,rotation=0,opacity=1,enabled=True)
        def add(group=None):
            group=group if isinstance(group,dict) else dict(defaults,id='Group'+str(table.rowCount()+1));row=table.rowCount();table.insertRow(row)
            for col,key in enumerate(keys):table.setItem(row,col,QTableWidgetItem(str(group.get(key,defaults[key]))))
        for group in node['params']['groups']:add(group)
        for title,callback in [('Agregar grupo',add),('Eliminar fila',lambda:table.removeRow(table.currentRow()))]:
            b=QPushButton(tr(title));b.clicked.connect(callback);layout.addWidget(b)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);layout.addWidget(buttons);buttons.rejected.connect(dialog.reject)
        def save():
            try:
                groups=[];old={g['id']:g for g in node['params']['groups']}
                for row in range(table.rowCount()):
                    values=[table.item(row,col).text().strip() for col in range(len(keys))]
                    g=copy.deepcopy(old.get(values[0],{}));g.update(dict(zip(keys,values)));g.update({k:float(g[k]) for k in keys[2:7]});g['enabled']=values[7].lower()=='true';groups.append(g)
                validate_groups(groups);p=dict(node['params'],groups=groups)
                for layer in p['shapes']+[p]:shape_transform(layer,p,self.project['width'],self.project['height'],self.project['frame'])
                self.checkpoint();node['params']['groups']=groups;self.changed();self.properties(node);dialog.accept()
            except (ValueError,AttributeError,TypeError) as exc:self.error(str(exc))
        buttons.accepted.connect(save);dialog.resize(850,400);dialog.exec()

    def edit_shape(self,node,key,viewer_only=False):
        if node['kind'] in ('Tracker2D','PlanarTracker'):
            if key in ('tracks','corners'):self.jump(round(node['params']['reference']))
            plate=node['params'].get('tracking_path','')
            source=next((n['id'] for n in self.project['nodes'] if n['kind']=='Read' and n['params']['path']==plate),node['inputs'].get('Image'))
            if source:self.preview(source)
        self.shape_node=node;self.shape_key=key;self.shape_drag=None
        self.viewer.canvas.viewport().update()
        self.statusBar().showMessage(tr('Viewer: click agrega puntos; arrastrar mueve; Shift arrastra tangente; Escape termina. Coordenadas normalizadas.'))
        if viewer_only:return
        dialog=QDialog(self);dialog.setWindowTitle('Editar '+key);layout=QVBoxLayout(dialog)
        layout.addWidget(QLabel(tr('Editar puntos en Viewer o editar los datos JSON.\nRoto: [x,y,inX,inY,outX,outY], origen inferior izquierdo.')))
        text=QPlainTextEdit(json.dumps(parameters(node,self.project['frame'])[key],indent=2));layout.addWidget(text)
        button=QPushButton(tr('Usar herramientas del Viewer'));button.clicked.connect(dialog.reject);layout.addWidget(button)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);layout.addWidget(buttons);buttons.rejected.connect(dialog.reject)
        def save():
            try:
                points=json.loads(text.toPlainText())
                if not isinstance(points,list) or any(not isinstance(p,list) or len(p) not in (2,6) or not all(isinstance(v,(int,float)) for v in p) for p in points):raise ValueError('Lista de puntos invalida')
                if key=='corners' and len(points)!=4:raise ValueError('CornerPin requiere cuatro puntos')
                self.parameter(node,key,points);dialog.accept();self.viewer.canvas.viewport().update()
            except ValueError as exc:self.error(str(exc))
        buttons.accepted.connect(save);dialog.resize(430,440);dialog.exec()

    def shape_event(self,kind,event,canvas):
        node=getattr(self,'shape_node',None)
        if not node or node not in self.project['nodes'] or canvas.pixels is None:return False
        if kind=='cancel':self.shape_node=None;self.shape_drag=None;canvas.viewport().update();return True
        if event.button()!=Qt.LeftButton and kind!='move':return False
        h,w=canvas.pixels.shape[:2];q=canvas.mapToScene(event.position().toPoint());p=[q.x()/w,1-q.y()/h]
        if node['kind']=='Roto':
            from roto import shape_transform,transform_points
            import numpy as np
            values=parameters(node,self.project['frame'],self.project);fw,fh=self.project['width'],self.project['height']
            transform,_,_=shape_transform(values,values,fw,fh,self.project['frame']);p=transform_points([p],np.linalg.inv(transform),fw,fh)[0]
        key=self.shape_key;points=parameters(node,self.project['frame'])[key]
        if kind=='press':
            self.shape_before=copy.deepcopy(self.project)
            distances=[((pt[0]-p[0])*w)**2+((pt[1]-p[1])*h)**2 for pt in points]
            closest=min(range(len(points)),key=lambda i:distances[i]) if points else None
            radius=12/max(.01,canvas.transform().m11())
            if closest is not None and distances[closest]<radius**2:self.shape_drag=closest
            elif key!='corners':
                points.append(p+p+p if key=='points' else p);self.shape_drag=len(points)-1
            else:self.shape_drag=None
            self.shape_work=points;return True
        if kind=='move' and self.shape_drag is not None:
            points=self.shape_work;i=self.shape_drag;old=points[i]
            if len(old)==6 and event.modifiers() & Qt.ShiftModifier:
                points[i]=old[:2]+[2*old[0]-p[0],2*old[1]-p[1]]+p
            elif len(old)==6:
                dx,dy=p[0]-old[0],p[1]-old[1];points[i]=p+[old[2]+dx,old[3]+dy,old[4]+dx,old[5]+dy]
            else:points[i]=p
            canvas.viewport().update();return True
        if kind=='release':
            if self.shape_drag is not None:
                self.history.append(self.shape_before);self.future.clear()
                if key in node.get('animation',{}):set_key(node,key,self.project['frame'],self.shape_work)
                else:node['params'][key]=copy.deepcopy(self.shape_work)
                self.changed()
            self.shape_drag=None;canvas.viewport().update();return True
        return True

    def draw_shapes(self,painter,canvas):
        node=getattr(self,'shape_node',None)
        if not node or node not in self.project['nodes'] or canvas.pixels is None:return
        points=self.shape_work if getattr(self,'shape_drag',None) is not None else parameters(node,self.project['frame'])[self.shape_key]
        if node['kind']=='Roto':
            from roto import shape_transform,transform_points
            values=parameters(node,self.project['frame'],self.project);fw,fh=self.project['width'],self.project['height']
            transform,_,_=shape_transform(values,values,fw,fh,self.project['frame']);points=transform_points(points,transform,fw,fh)
        h,w=canvas.pixels.shape[:2];scale=max(.01,canvas.transform().m11())
        painter.setPen(QPen(QColor('#f7bc66'),1.5/scale))
        if self.shape_key!='tracks' and len(points)>1:
            sampled=sample_shape(points) if self.shape_key=='points' else points
            path=QPainterPath(QPointF(sampled[0][0]*w,(1-sampled[0][1])*h))
            for pt in sampled[1:]:path.lineTo(pt[0]*w,(1-pt[1])*h)
            path.closeSubpath();painter.drawPath(path)
        for p in points:
            painter.drawEllipse(QPointF(p[0]*w,(1-p[1])*h),4/scale,4/scale)
            if node['kind']=='Tracker2D' and self.shape_key in ('tracks','correction_points'):
                ratio=w/self.project['width'];size=node['params'].get('pattern_size',31)*ratio;search=node['params'].get('max_step',64)*ratio
                from PySide6.QtCore import QRectF
                painter.drawRect(QRectF(p[0]*w-size/2,(1-p[1])*h-size/2,size,size))
                painter.drawRect(QRectF(p[0]*w-search,(1-p[1])*h-search,2*search,2*search))
            if len(p)==6:
                for i in (2,4):
                    painter.drawLine(QPointF(p[0]*w,(1-p[1])*h),QPointF(p[i]*w,(1-p[i+1])*h))
                    painter.drawEllipse(QPointF(p[i]*w,(1-p[i+1])*h),2/scale,2/scale)
