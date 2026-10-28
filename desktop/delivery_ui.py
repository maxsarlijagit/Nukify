# SPDX-License-Identifier: GPL-3.0-or-later
from i18n import tr
import copy
import json
import uuid
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFileDialog,QDialog,QVBoxLayout,QListWidget,QPushButton,QInputDialog
from delivery import collect,atomic_json


class DeliveryUI:
    def inspect_3d(self):
        target=self.project.get('viewer')
        if not target:return
        job=dict(graph=copy.deepcopy(self.project),target=target,frames=[self.project['frame']],export=False,inspect=True,directory=str(self.app_data/('inspect-'+uuid.uuid4().hex[:8])))
        self.pause();self.live_timer.stop();self.engine.stop();self.engine_b.stop()
        self.run(target,False,job)

    def collect_project(self):
        parent=QFileDialog.getExistingDirectory(self,tr('Carpeta donde crear el paquete'))
        if not parent:return
        try:
            path=collect(self.project,Path(parent)/('Nukify-project-'+uuid.uuid4().hex[:8]))
            self.statusBar().showMessage('Proyecto portable: '+str(path))
        except Exception as exc:self.error(str(exc))

    def resume_render(self):
        path,_=QFileDialog.getOpenFileName(self,tr('Reanudar job.json'),'','Render (job.json)')
        if not path:return
        try:
            job=json.loads(Path(path).read_text(encoding='utf-8'))
            job['directory']=str(Path(path).parent)
            job['graph']['blender']=self.project['blender']
            self.pause();self.live_timer.stop();self.engine.stop();self.engine_b.stop()
            self.run(job['target'],True,job)
        except Exception as exc:self.error(str(exc))

    def queue_dialog(self):
        queue_path=self.app_data/'render-queue.json'
        if not hasattr(self,'render_queue'):
            try:self.render_queue=json.loads(queue_path.read_text())
            except (OSError,ValueError):self.render_queue=[]
        dialog=QDialog(self);dialog.setWindowTitle(tr('Render queue'));layout=QVBoxLayout(dialog);listing=QListWidget();layout.addWidget(listing)
        def refresh():
            listing.clear()
            for job in self.render_queue:listing.addItem(f"{job['target']} | {job['frames'][0]}-{job['frames'][-1]} | {job['directory']}")
            atomic_json(queue_path,self.render_queue)
        def add():
            writes=[n['id'] for n in self.project['nodes'] if n['kind']=='Write']
            target=self.selected if self.selected in writes else (writes[0] if len(writes)==1 else None)
            if not target or not self.project['output']:self.error('Selecciona Write y configura Output.');return
            frames=list(range(self.project['first'],self.project['last']+1))
            if not frames:self.error('Rango invertido');return
            self.render_queue.append(dict(graph=copy.deepcopy(self.project),target=target,frames=frames,export=True,directory=str(Path(self.project['output'])/('queue_'+uuid.uuid4().hex[:12]))));refresh()
        def remove():
            row=listing.currentRow()
            if row>=0 and not getattr(self,'queue_active',False):self.render_queue.pop(row);refresh()
        def start():
            if self.process:self.error('Hay un render activo');return
            dialog.accept();self.queue_active=True;self.queue_next()
        for title,callback in [('Agregar proyecto actual',add),('Quitar seleccionado',remove),('Iniciar / reanudar cola',start)]:
            button=QPushButton(tr(title));button.clicked.connect(callback);layout.addWidget(button)
        refresh();dialog.resize(760,320);dialog.exec()

    def queue_next(self):
        if not getattr(self,'queue_active',False) or not self.render_queue:
            self.queue_active=False;return
        job=copy.deepcopy(self.render_queue[0]);job['graph']['blender']=self.project['blender']
        self.pause();self.live_timer.stop();self.engine.stop();self.engine_b.stop()
        self.run(job['target'],True,job)

    def cache_settings(self):
        mb,ok=QInputDialog.getInt(self,tr('Cache de disco'),tr('Presupuesto total A+B en MB'),int(getattr(self.engine,'budget',512*1024**2)*2/1024**2),64,65536)
        if ok:
            self.engine.budget=self.engine_b.budget=mb*1024**2//2
            atomic_json(self.app_data/'cache-settings.json',{'disk_mb':mb})
            self.engine.prune();self.engine_b.prune()

    def preview_b(self):
        if self.selected:
            from registry import TYPES
            if next(n for n in self.project['nodes'] if n['id']==self.selected)['kind'] in TYPES:self.error('B requiere una imagen renderizada');return
            self.project['viewer_b']=self.selected;self.dirty=True;self.invalidate_live()

    def clear_b(self):
        self.project.pop('viewer_b',None);self.engine_b.stop();self.viewer.reference=None;self.viewer.reference_label.setText(tr('B: sin asignar'));self.dirty=True;self.invalidate_live()
