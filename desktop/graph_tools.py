# SPDX-License-Identifier: GPL-3.0-or-later
from i18n import tr
import copy
import json
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainterPath, QPen, QColor, QKeySequence, QPainterPathStroker
from PySide6.QtWidgets import QApplication, QMenu, QDialog, QVBoxLayout, QLineEdit, QListWidget, QDialogButtonBox
from model import new_node, connect
from registry import NODES, INPUTS


class GraphInteraction:
    def search_nodes(self):
        dialog=QDialog(self);dialog.setWindowTitle(tr('Crear nodo'));layout=QVBoxLayout(dialog)
        search=QLineEdit();search.setPlaceholderText(tr('Buscar nodo...'));items=QListWidget()
        layout.addWidget(search);layout.addWidget(items)
        def update(text):
            items.clear()
            items.addItems([k for k in NODES if text.lower() in k.lower()]);items.setCurrentRow(0)
        update('');search.textChanged.connect(update)
        def create():
            if items.currentItem():self.owner.add(items.currentItem().text());dialog.accept()
        search.returnPressed.connect(create);items.itemDoubleClicked.connect(create)
        dialog.resize(360,420);dialog.exec()

    def selected_nodes(self):
        return [i for i in self.scene().selectedItems() if hasattr(i,'data') and isinstance(i.data,dict)]

    def copy_nodes(self):
        QApplication.clipboard().setText(json.dumps({'nukify_nodes':[i.data for i in self.selected_nodes()]}))

    def paste_nodes(self):
        before=None
        try:
            nodes=json.loads(QApplication.clipboard().text())['nukify_nodes']
            if not isinstance(nodes,list) or any(n['kind'] not in NODES for n in nodes):return
            before=copy.deepcopy(self.owner.project);mapping={};created=[]
            for src in nodes:
                n=new_node(self.owner.project,src['kind'],src['x']+45,src['y']+55)
                mapping[src['id']]=n['id'];created.append(n)
                for k in ('params','animation','disabled','expressions'):
                    if k in src:n[k]=copy.deepcopy(src[k])
            for src,n in zip(nodes,created):
                n['inputs']={k:mapping[v] for k,v in src['inputs'].items() if v in mapping}
                if src.get('animation_link'):n['animation_link']=mapping.get(src['animation_link'],src['animation_link'])
                if n.get('expressions'):
                    from expressions import remap_refs
                    n['expressions']={k:remap_refs(v,mapping) for k,v in n['expressions'].items()}
            self.owner.history.append(before);self.owner.future.clear();self.rebuild()
            for n in created:self.items_by_id[n['id']].setSelected(True)
            self.owner.changed()
        except (ValueError,KeyError,TypeError,SyntaxError,AttributeError):
            if before is not None:self.owner.project=before;self.rebuild()
            return

    def bypass(self):
        nodes=[i.data for i in self.selected_nodes() if 'Image' in INPUTS[i.data['kind']] or 'B' in INPUTS[i.data['kind']]]
        if not nodes:return
        self.owner.checkpoint()
        for n in nodes:n['disabled']=not n.get('disabled',False)
        self.rebuild();self.owner.changed()

    def contextMenuEvent(self,event):
        menu=QMenu(self);item=self.itemAt(event.pos())
        while item is not None and not hasattr(item,'data') and item.parentItem():item=item.parentItem()
        if item is not None and hasattr(item,'connection'):
            target,socket=item.connection
            def disconnect():
                self.owner.checkpoint();self.items_by_id[target].data['inputs'].pop(socket,None);self.update_edges();self.owner.changed()
            menu.addAction(tr('Desconectar'),disconnect)
        menu.addAction(tr('Crear nodo [Tab]'),self.search_nodes)
        menu.addAction(tr('Copiar'),self.copy_nodes);menu.addAction(tr('Pegar'),self.paste_nodes)
        menu.addAction(tr('Duplicar'),lambda:(self.copy_nodes(),self.paste_nodes()))
        menu.addAction(tr('Bypass [D]'),self.bypass);menu.addAction(tr('Eliminar'),self.owner.delete_selected)
        menu.addAction(tr('Encuadrar'),self.fit);menu.exec(event.globalPos())

    def mousePressEvent(self,event):
        if event.button()==Qt.MiddleButton:
            self._pan=event.position().toPoint();self.setCursor(Qt.ClosedHandCursor);event.accept();return
        if event.button()==Qt.LeftButton:
            item=self.itemAt(event.position().toPoint())
            if hasattr(item,'socket'):
                self._wire=item;self._wire_start=event.position().toPoint();event.accept();return
            node=item
            while node and not isinstance(getattr(node,'data',None),dict):node=node.parentItem()
            if node and event.modifiers() & Qt.ShiftModifier:
                node.setSelected(not node.isSelected());event.accept();return
            self._before=copy.deepcopy(self.owner.project)
        super().mousePressEvent(event)

    def mouseMoveEvent(self,event):
        if getattr(self,'_pan',None) is not None:
            pos=event.position().toPoint();delta=pos-self._pan;self._pan=pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()-delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value()-delta.y());event.accept();return
        if getattr(self,'_wire',None) is not None:
            if getattr(self,'_hover_port',None):self._hover_port.setBrush(QColor('#d2d9df'));self._hover_port=None
            candidate=self.itemAt(event.position().toPoint());color='#ffc46a'
            if hasattr(candidate,'socket') and candidate is not self._wire:
                source,dest=(self._wire,candidate) if self._wire.socket is None else (candidate,self._wire)
                if source.socket is None and dest.socket is not None:
                    try:connect(copy.deepcopy(self.owner.project),source.node.data['id'],dest.node.data['id'],dest.socket);color='#72d7a1'
                    except ValueError as exc:color='#ed7777';self.owner.statusBar().showMessage(str(exc))
                    candidate.setBrush(QColor(color));self._hover_port=candidate
            if getattr(self,'_preview',None):self.scene().removeItem(self._preview)
            path=QPainterPath(self._wire.scenePos());path.lineTo(self.mapToScene(event.position().toPoint()))
            self._preview=self.scene().addPath(path,QPen(QColor(color),2));self._preview.setZValue(-.5);event.accept();return
        super().mouseMoveEvent(event)
        self._insert=None
        selected=self.selected_nodes()
        if getattr(self,'_before',None) and len(selected)==1:
            node=selected[0];key=node.data['id']
            if 'Image' in INPUTS[node.data['kind']] and node.output is not None:
                center=node.sceneBoundingRect().center();stroke=QPainterPathStroker();stroke.setWidth(24/max(.01,self.transform().m11()))
                for edge in self.edges:
                    target,socket=edge.connection;source=self.items_by_id[target].data['inputs'][socket]
                    if key not in (target,source) and stroke.createStroke(edge.path()).contains(center):
                        self._insert=(key,source,target,socket);edge.setPen(QPen(QColor('#ffc46a'),3))
                        self.owner.statusBar().showMessage(tr('Soltar para insertar {0}: {1} → {2}.{3}').format(key, source, target, socket));break

    def mouseReleaseEvent(self,event):
        if event.button()==Qt.MiddleButton and getattr(self,'_pan',None) is not None:
            self._pan=None;self.unsetCursor();event.accept();return
        wire=getattr(self,'_wire',None)
        if wire is not None:
            if getattr(self,'_hover_port',None):self._hover_port.setBrush(QColor('#d2d9df'));self._hover_port=None
            self._wire=None
            if getattr(self,'_preview',None):self.scene().removeItem(self._preview);self._preview=None
            item=self.itemAt(event.position().toPoint())
            if hasattr(item,'socket') and item is not wire:
                source,dest=(wire,item) if wire.socket is None else (item,wire)
                if source.socket is None and dest.socket is not None:
                    before=copy.deepcopy(self.owner.project)
                    try:
                        connect(self.owner.project,source.node.data['id'],dest.node.data['id'],dest.socket)
                        if before!=self.owner.project:self.owner.history.append(before);self.owner.future.clear();self.update_edges();self.owner.changed()
                    except ValueError as exc:self.owner.statusBar().showMessage(str(exc))
            elif (event.position().toPoint()-self._wire_start).manhattanLength()<4:self.port_clicked(wire)
            event.accept();return
        super().mouseReleaseEvent(event)
        before=getattr(self,'_before',None);self._before=None
        insertion=getattr(self,'_insert',None);self._insert=None
        if before and insertion:
            key,source,target,socket=insertion
            proposed=copy.deepcopy(self.owner.project)
            try:
                connect(proposed,source,key,'Image');connect(proposed,key,target,socket)
                self.owner.project=proposed;self.owner.history.append(before);self.owner.future.clear()
                self.rebuild();self.items_by_id[key].setSelected(True);self.owner.changed();return
            except ValueError as exc:self.owner.statusBar().showMessage('Insercion cancelada: '+str(exc))
        if before and before!=self.owner.project:
            self.owner.history.append(before);self.owner.future.clear();self.owner.dirty=True

    def keyPressEvent(self,event):
        sequence=QKeySequence(event.keyCombination()).toString()
        from shortcuts import DEFAULTS
        command=next((k for k,v in getattr(self.owner,'graph_shortcuts',DEFAULTS).items() if v and v==sequence),None)
        if command:
            mapped=QKeySequence(DEFAULTS[command])[0]
            key=mapped.key();ctrl=bool(mapped.keyboardModifiers() & Qt.ControlModifier)
        elif event.key()==Qt.Key_Escape:key=event.key();ctrl=False
        else:super().keyPressEvent(event);return
        if key==Qt.Key_Escape:
            if getattr(self,'_hover_port',None):self._hover_port.setBrush(QColor('#d2d9df'));self._hover_port=None
            self.pending=None;self._wire=None;self._insert=None
            if getattr(self,'_preview',None):self.scene().removeItem(self._preview);self._preview=None
            if getattr(self,'_before',None):self.owner.project=self._before;self._before=None;self.rebuild()
        elif ctrl and key==Qt.Key_C:self.copy_nodes()
        elif ctrl and key==Qt.Key_V:self.paste_nodes()
        elif ctrl and key==Qt.Key_D:self.copy_nodes();self.paste_nodes()
        elif ctrl and key==Qt.Key_A:
            for n in self.items_by_id.values():n.setSelected(True)
        elif key==Qt.Key_D:self.bypass()
        elif key==Qt.Key_Tab:self.search_nodes()
        elif key==Qt.Key_1:self.owner.preview_selected()
        elif key==Qt.Key_2:self.owner.preview_b()
        elif key==Qt.Key_Delete:self.owner.delete_selected()
        elif key==Qt.Key_Home:self.fit()
        elif key==Qt.Key_F:
            selection=self.selected_nodes()
            if not selection:self.fit()
            else:
                bounds=selection[0].sceneBoundingRect()
                for n in selection[1:]:bounds=bounds.united(n.sceneBoundingRect())
                self.fitInView(bounds.adjusted(-70,-50,70,50),Qt.KeepAspectRatio)
        elif key==Qt.Key_Space:self.owner.maximize_panel('graph')
        else:super().keyPressEvent(event)
