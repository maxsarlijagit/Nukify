# SPDX-License-Identifier: GPL-3.0-or-later
"""End-to-end executable QA, isolated from user projects and caches."""
import json,sys,time,tempfile
from pathlib import Path
from PySide6.QtCore import QTimer


def run(window,app,report_path):
    w=window;directory=Path(tempfile.mkdtemp(prefix='nukify-release-qa-'))
    w.engine.cache=directory/'cache';w.engine.cache.mkdir()
    w.project['last']=12;w.last.setValue(12)
    w.project['output']=str(directory/'renders');w.out.setText(w.project['output'])
    state={'stage':'initial','frames':[],'errors':[],'started':time.perf_counter(),
           'executable':sys.executable,'engine':w.project['blender'],'directory':str(directory)}
    timer=QTimer(w);timer.setInterval(20)
    deadline=QTimer(w);deadline.setSingleShot(True)
    def finish(error=None):
        if state.get('finished'):return
        state['finished']=True;timer.stop();deadline.stop()
        if error:state['errors'].append(str(error))
        state['passed']=not state['errors'];state['seconds']=time.perf_counter()-state['started'];state['worker_starts']=w.engine.starts
        state['log']=w.log.toPlainText();w.pause();w.live_timer.stop();w.engine.stop()
        w.grab().save(str(Path(report_path).with_suffix('.png')))
        Path(report_path).write_text(json.dumps({k:v for k,v in state.items() if k!='frames'},indent=2),encoding='utf-8')
        w.dirty=False;app.exit(0 if state['passed'] else 1)
    def ready(info):
        if info['key']!=w.expected_key:return
        if state['stage']=='crypto':
            import numpy as np
            pixels=np.fromfile(info['raw'],np.float32).reshape(info['height'],info['width'],4)
            if pixels[...,:3].max()<.9 or pixels[...,:3].min()!=0:finish('Cryptomatte invalido');return
            state['cryptomatte']=True;state['stage']='crypto-export-queued'
            def export_crypto():state['stage']='crypto-export';w.export()
            QTimer.singleShot(0,export_crypto);return
        if state['stage']=='initial':
            state['stage']='edit';state['old_key']=info['key']
            w.parameter(w.project['nodes'][2],'exposure',.75)
        elif state['stage']=='edit':
            if info['key']==state['old_key']:return
            state['auto_update']=True;state['stage']='warm-queued'
            def warm():state['stage']='warming';w.cache_range()
            QTimer.singleShot(0,warm)
        elif state['stage']=='playing':
            state['frames'].append((info['frame'],time.perf_counter(),info.get('cached')))
            if len(state['frames'])>=36:
                frames=state['frames'];state['fps']=(len(frames)-1)/(frames[-1][1]-frames[0][1])
                if set(f[0] for f in frames)!=set(range(1,13)) or not all(f[2] for f in frames):finish('Playback incompleto');return
                if not 20<state['fps']<28:finish('Playback fuera del objetivo 24 fps');return
                w.pause();state['stage']='export-queued'
                def export():
                    w.filename=str(directory/'test.nukify')
                    if not w.save_project():finish('No guardo proyecto');return
                    saved=json.loads(Path(w.filename).read_text());state['saved_without_engine']='blender' not in saved
                    w.project['last']=2;state['stage']='exporting';w.export()
                QTimer.singleShot(0,export)
    def poll():
        if state['stage']=='warming' and not w.warming and not w.engine.busy:state['stage']='playing';w.toggle_play()
        elif state['stage']=='exporting' and not w.process:
            outputs=list((directory/'renders').glob('render_*/comp_*.exr'))
            state['export_frames']=len(outputs)
            if len(outputs)!=2:finish('Exportacion incompleta');return
            state['stage']='tracking'
            plate=str(w.app_root/'assets/production/plate_####.png')
            common=dict(task='track',path=plate,reference=1,first=1,last=24)
            def tracked(result):
                state['tracking_frames']=len(result['records'])
                def planar(result):
                    state['planar_frames']=len(result['records'])
                    from examples import example
                    engine=w.project['blender'];w.project=example('EXR y Cryptomatte',w.app_root/'assets')
                    w.project.update(blender=engine,output=str(directory/'crypto-renders'))
                    w.sync();state['stage']='crypto';w.request_live()
                w.task_start(dict(common,kind='PlanarTracker',corners=[[.2,.2],[.8,.2],[.8,.8],[.2,.8]]),planar)
            w.task_start(dict(common,kind='Tracker2D',tracks=[[.4,.4],[.65,.65]]),tracked)
        elif state['stage']=='crypto-export' and not w.process:
            outputs=list((directory/'crypto-renders').glob('render_*/comp_*.exr'))
            if len(outputs)!=1:finish('Export Cryptomatte incompleto');return
            state['stage']='inspect-exr'
            def inspected(result):
                channels=result.get('exr',{}).get('channels',[])
                state['preserved_channels']=len(channels)
                if 'ViewLayer.Depth.Z' not in channels or 'Nukify.Matte.R' not in channels:finish('Canales no conservados');return
                finish()
            w.task_start(dict(task='inspect',path=str(outputs[0])),inspected)
    w.error=lambda message:finish(message)
    w.engine.ready.connect(ready);w.engine.failed.connect(finish)
    timer.timeout.connect(poll);timer.start();deadline.timeout.connect(lambda:finish('Timeout: '+state['stage']));deadline.start(60000)
    w._qa_timers=(timer,deadline)
