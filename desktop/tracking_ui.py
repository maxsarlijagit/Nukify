# SPDX-License-Identifier: GPL-3.0-or-later
from i18n import tr
import copy,ctypes,json,sys,uuid
from pathlib import Path
from PySide6.QtCore import QProcess,QProcessEnvironment
from PySide6.QtWidgets import QDialog,QVBoxLayout,QPlainTextEdit,QComboBox,QPushButton,QTableWidget,QTableWidgetItem,QLabel
from model import new_node,sequence_path
from animation import parameters


class TrackingUI:
    def tracking_report_dialog(self,node):
        report=node.get('last_tracking_attempt') or node.get('tracking_report')
        if not report:self.statusBar().showMessage(tr('Todavia no hay un analisis'));return
        dialog=QDialog(self);dialog.setWindowTitle(tr('Tracking: confianza y perdidas'));layout=QVBoxLayout(dialog)
        layout.addWidget(QLabel('Analisis completo' if report.get('complete',True) else 'Analisis incompleto: las curvas anteriores se conservaron. Corregi el frame perdido y reanaliza.'))
        rows={int(f):dict(record,status='MANUAL' if record.get('manual') else 'TRACK') for f,record in report.get('records',{}).items()}
        for failure in report.get('failures',[]):rows[failure['frame']]=dict(status='PERDIDO: '+failure['error'])
        frames=sorted(rows);table=QTableWidget(len(frames),4);table.setHorizontalHeaderLabels(['Frame','Estado','Confianza','Error FB px'])
        for row,frame in enumerate(frames):
            record=rows[frame]
            for col,value in enumerate((frame,record['status'],record.get('confidence',''),record.get('fb_error',''))):table.setItem(row,col,QTableWidgetItem(str(value)))
        table.cellDoubleClicked.connect(lambda row,col:(self.jump(frames[row]),dialog.accept()))
        layout.addWidget(table);dialog.resize(780,450);dialog.exec()

    def edit_tracking_correction(self,node):
        frame=self.project['frame'];report=node.get('last_tracking_attempt') or node.get('tracking_report',{});record=report.get('records',{}).get(str(frame),report.get('records',{}).get(frame,{}))
        points=node['params'].get('manual_points',{}).get(str(frame))
        if points is None:
            if node['kind']=='PlanarTracker':points=record.get('corners',parameters(node,frame,self.project)['corners'])
            elif record.get('points'):points=[[x/report['width'],1-y/report['height']] for x,y in record['points']]
            else:points=node['params']['tracks']
        self.checkpoint();node['params']['correction_points']=copy.deepcopy(points);self.changed();self.edit_shape(node,'correction_points',True)

    def store_tracking_correction(self,node):
        import math
        points=node['params']['correction_points'];count=4 if node['kind']=='PlanarTracker' else len(node['params']['tracks'])
        if count not in (1,2,4) or len(points)!=count or any(len(p)!=2 or any(not math.isfinite(v) or not 0<=v<=1 for v in p) for p in points):self.error('Correccion requiere '+str(count)+' puntos normalizados dentro de la imagen');return
        self.checkpoint();frame=self.project['frame'];node['params']['manual_points'][str(frame)]=copy.deepcopy(points)
        if frame==round(node['params']['reference']):
            key='corners' if node['kind']=='PlanarTracker' else 'tracks';node['params'][key]=copy.deepcopy(points)
            if key in node.get('animation',{}):
                from animation import set_key
                set_key(node,key,frame,points)
        self.changed();self.statusBar().showMessage('Correccion guardada en frame '+str(frame)+'. Analiza de nuevo para aplicarla al movimiento.')

    def remove_tracking_correction(self,node):
        key=str(self.project['frame'])
        if key in node['params']['manual_points']:self.checkpoint();node['params']['manual_points'].pop(key);self.changed()

    def task_start(self,job,callback):
        if getattr(self,'task_process',None):self.error('Hay un analisis activo. Espera o cancela.');return
        directory=self.app_data/'analysis';directory.mkdir(exist_ok=True)
        token=uuid.uuid4().hex;job['result']=str(directory/(token+'-result.json'))
        path=directory/(token+'.json');path.write_text(json.dumps(job),encoding='utf-8')
        process=QProcess(self);self.task_process=process
        env=QProcessEnvironment.systemEnvironment()
        for k in ('PYTHONHOME','PYTHONPATH','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH'):env.remove(k)
        process.setProcessEnvironment(env);process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyReadStandardOutput.connect(lambda:self.log.appendPlainText(bytes(process.readAllStandardOutput()).decode('utf-8',errors='replace').rstrip()))
        def finish(code,status):
            self.task_process=None
            try:
                result=json.loads(Path(job['result']).read_text(encoding='utf-8'))
                if not result.get('ok'):raise ValueError(result.get('error','Analisis fallido'))
                callback(result)
            except (OSError,ValueError) as exc:self.statusBar().showMessage('Analisis sin aplicar: '+str(exc));self.log.appendPlainText(str(exc))
            process.deleteLater()
        process.finished.connect(finish)
        def failed(error):
            if error==QProcess.FailedToStart:
                self.task_process=None;process.deleteLater();self.error('No se pudo iniciar el motor de analisis')
        process.errorOccurred.connect(failed)
        frozen=sys.platform=='win32' and getattr(sys,'frozen',False)
        if frozen:ctypes.windll.kernel32.SetDllDirectoryW(None)
        try:
            process.start(self.project['blender'],['-b','--factory-startup','--threads','4','--python-exit-code','1','--python',str(self.app_root/'desktop/task_worker.py'),'--',str(path)])
            process.waitForStarted(5000)
        finally:
            if frozen:ctypes.windll.kernel32.SetDllDirectoryW(str(self.app_root))
        self.statusBar().showMessage(tr('Analizando en segundo plano... Diagnostico muestra el progreso.'))

    def cancel_tracking(self):
        if getattr(self,'task_process',None):self.task_process.kill()

    def start_tracking(self,node,direction='both'):
        p=parameters(node,round(node['params']['reference']),self.project);path=p.get('tracking_path','')
        if not path:
            src=next((n for n in self.project['nodes'] if n['id']==node['inputs'].get('Image')),None)
            if src and src['kind']=='Read':path=src['params']['path']
        if not path:self.error('Defini tracking_path o conecta un Read directo para analizar.');return
        job=dict(task='track',kind=node['kind'],path=path,reference=round(p['reference']),first=self.project['first'],last=self.project['last'],tracks=p.get('tracks',[]),corners=p.get('corners',[]))
        job.update(manual_points=p.get('manual_points',{}),exclude_polygon=p.get('exclude_polygon',[]),allow_partial=True)
        if direction=='forward':job['first']=job['reference']
        elif direction=='backward':job['last']=job['reference']
        for key in ('pattern_size','pyramid_levels','max_fb_error','max_step'):job[key]=p.get(key,{'pattern_size':31,'pyramid_levels':4,'max_fb_error':1.,'max_step':64.}[key])
        original=copy.deepcopy(node);project=self.project
        def apply(result):
            current=next((n for n in self.project['nodes'] if n['id']==original['id']),None)
            if self.project is not project or current!=original:
                self.statusBar().showMessage(tr('Resultado conservado en analysis; el nodo cambio durante el tracking.'));return
            if (result['width'],result['height'])!=(self.project['width'],self.project['height']):
                self.error('El formato del proyecto debe coincidir con el plate: '+str(result['width'])+' x '+str(result['height']));return
            previous=node.get('tracking_report',{})
            if not result.get('complete',True):
                self.checkpoint();node['last_tracking_attempt']=result;self.dirty=True;self.statusBar().showMessage(tr('Tracking perdido: curvas anteriores conservadas. Abri Confianza / perdidas para corregir.'));return
            if previous.get('reference')==result['reference'] and previous.get('path')==result['path']:
                for key,curve in result['animation'].items():
                    retained=[entry for entry in node.get('animation',{}).get(key,{}).get('keys',[]) if not job['first']<=entry[0]<=job['last']]
                    curve['keys']=sorted(retained+curve['keys'])
                retained={k:v for k,v in previous.get('records',{}).items() if not job['first']<=int(k)<=job['last']}
                result['records']={**retained,**result['records']}
            self.checkpoint();node.setdefault('animation',{}).update(result['animation']);node['tracking_report']=result;node.pop('last_tracking_attempt',None)
            if node['kind']=='PlanarTracker':node['tracking_reference_corners']=copy.deepcopy(job['corners'])
            self.changed();self.properties(node);self.statusBar().showMessage('Tracking aplicado: '+str(len(result['records']))+' cuadros')
        self.task_start(job,apply)

    def bake_tracking(self,node):
        if not node.get('tracking_report'):self.error('Primero analiza el rango.');return
        self.checkpoint();kind='CornerPin' if node['kind']=='PlanarTracker' else 'Transform'
        created=new_node(self.project,kind,node['x']+190,node['y'])
        created['animation']=copy.deepcopy(node['animation'])
        if kind=='Transform' and node['params'].get('mode')=='stabilize':
            import math
            for f,record in node['tracking_report']['records'].items():
                frame=int(f);p=parameters(node,frame);angle=-math.radians(p['rotation']);scale=1/p['scale']
                values=dict(x=-scale*(math.cos(angle)*p['x']-math.sin(angle)*p['y']),y=-scale*(math.sin(angle)*p['x']+math.cos(angle)*p['y']),scale=scale,rotation=-p['rotation'])
                from animation import set_key
                for k,v in values.items():set_key(created,k,frame,v)
        if kind=='CornerPin':
            from geometry import planar_output
            for entry in created['animation']['corners']['keys']:
                entry[1]=planar_output(entry[1],node.get('tracking_reference_corners',node['params']['corners']),node['params'].get('mode','cornerpin'))
        created['inputs']=copy.deepcopy(node['inputs'])
        self.graph.rebuild();self.graph.items_by_id[created['id']].setSelected(True);self.changed()

    def inspect_media(self,node):
        path=sequence_path(node['params']['path'],self.project['frame'])
        def show(result):
            dialog=QDialog(self);dialog.setWindowTitle(tr('Canales y metadata de imagen'));layout=QVBoxLayout(dialog)
            text=QPlainTextEdit(json.dumps(result,indent=2));text.setReadOnly(True);layout.addWidget(text)
            combo=QComboBox();layout.addWidget(combo)
            metadata=result.get('exr',{}).get('metadata',{})
            if node['kind']=='Read':
                channels=result.get('exr',{}).get('channels',[])
                choices=list(dict.fromkeys(result['outputs']+channels+[c.rsplit('.',1)[0] for c in channels if '.' in c]))
                combo.addItems(choices)
            else:
                for key,value in metadata.items():
                    if key.startswith('cryptomatte/') and key.endswith('/manifest'):
                        layer=metadata.get(key.rsplit('/',1)[0]+'/name','')
                        for name in json.loads(value):combo.addItem(layer+' / '+name,(layer,name))
            def apply():
                if not combo.count():return
                if node['kind']=='Read':self.parameter(node,'layer',combo.currentText())
                else:
                    layer,name=combo.currentData();self.parameter(node,'layer',layer);self.parameter(node,'matte_id',name)
                self.properties(node);dialog.accept()
            button=QPushButton(tr('Usar seleccion'));button.clicked.connect(apply);layout.addWidget(button)
            dialog.resize(650,500);dialog.exec()
        self.task_start(dict(task='inspect',path=path),show)

    def link_tracking(self,node):
        dialog=QDialog(self);dialog.setWindowTitle(tr('Enlazar movimiento'));layout=QVBoxLayout(dialog);combo=QComboBox()
        kinds=('CornerPin',) if node['kind']=='PlanarTracker' else ('Transform','Roto')
        for n in self.project['nodes']:
            if n['kind'] in kinds:combo.addItem(n['id'],n['id'])
        layout.addWidget(combo)
        def link():
            target=next((n for n in self.project['nodes'] if n['id']==combo.currentData()),None)
            if target:
                self.checkpoint();target['animation_link']=node['id'];self.changed();dialog.accept()
        button=QPushButton(tr('Enlazar'));button.clicked.connect(link);layout.addWidget(button);dialog.exec()
