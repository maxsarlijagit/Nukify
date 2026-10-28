# SPDX-License-Identifier: GPL-3.0-or-later
"""Packaged executable acceptance checks for S9/S10/S11 mechanisms."""
import json,tempfile,time,copy,sys
from pathlib import Path
from PySide6.QtCore import QTimer
from examples import example
from delivery import collect,resolve_media,atomic_json

def run(w,app,report):
    directory=Path(tempfile.mkdtemp(prefix='nukify-s9-11-'))
    w.app_data=directory;w.recovery_path=directory/'recovery.nukify'
    state={'stage':'pair1','errors':[],'executable':sys.executable,'engine':w.project['blender'],'directory':str(directory),'start':time.perf_counter()}
    w.pause();w.live_timer.stop();w.engine.stop();w.engine_b.stop()
    engine=w.project['blender'];w.project=example('Integracion 3D',w.app_root/'assets')
    w.project.update(width=96,height=72,blender=engine,output=str(directory/'renders'),last=2)
    w.engine.cache=directory/'cache-a';w.engine.cache.mkdir();w.engine_b.cache=directory/'cache-b';w.engine_b.cache.mkdir()
    w.sync();w.live_timer.stop();w.request_live()
    timer=QTimer(w);timer.setInterval(30)
    def finish(error=None):
        if state.get('finished'):return
        state['finished']=True;timer.stop()
        if error:state['errors'].append(str(error))
        w.pause();w.live_timer.stop();w.engine.stop();w.engine_b.stop()
        state['passed']=not state['errors'];state['seconds']=time.perf_counter()-state.pop('start')
        w.grab().save(str(Path(report).with_suffix('.png')))
        Path(report).write_text(json.dumps(state,indent=2),encoding='utf-8');w.dirty=False;app.exit(0 if state['passed'] else 1)
    w.engine.failed.connect(finish);w.engine_b.failed.connect(finish)
    def poll():
        try:
            if time.perf_counter()-state['start']>180:finish('Timeout');return
            stage=state['stage']
            if stage.startswith('pair') and w.viewer.current_info and w.viewer.current_info.get('frame')==(1 if stage=='pair1' else 2) and w.viewer.reference is not None and not w.waiting_frame:
                assert f"frame {w.project['frame']}" in w.viewer.reference_label.text()
                assert w.viewer.reference[:,:,3].max()>.9
                if stage=='pair1':
                    state['pair1']=True;state['stage']='pair2';w.frame.setValue(2)
                else:
                    state['pair2']=True;state['stage']='export';w.export()
            elif stage=='export' and w.process is None:
                job=copy.deepcopy(w.running_job);out=Path(job['directory'])
                assert (out/'result.json').is_file(),w.log.toPlainText()
                state['export_frames']=len(list(out.glob('comp_*.exr')))
                assert state['export_frames']==2
                state['first_mtime']=(out/'comp_0001.exr').stat().st_mtime_ns
                (out/'comp_0002.exr').write_bytes(b'interrupted')
                state['stage']='resume';w.engine.stop();w.engine_b.stop();w.live_timer.stop();w.run(job['target'],True,job)
            elif stage=='resume' and w.process is None:
                out=Path(w.running_job['directory']);assert (out/'result.json').is_file(),w.log.toPlainText()
                assert (out/'comp_0001.exr').stat().st_mtime_ns==state['first_mtime']
                assert (out/'comp_0002.exr').stat().st_size>100
                state['resume_verified']=True
                path=collect(w.project,directory/'package');moved=directory/'relocated';path.parent.rename(moved)
                portable=resolve_media(json.loads((moved/'project.nukify').read_text()),moved)
                portable['blender']=engine;portable['output']=str(directory/'queue-output')
                state['stage']='queue';w.live_timer.stop();w.engine.stop();w.engine_b.stop()
                # Two queued independent snapshots, last one uses relocated media.
                w.render_queue=[dict(graph=copy.deepcopy(portable),target='Write1',frames=[1],export=True,directory=str(directory/f'queued-{i}')) for i in (1,2)]
                w.queue_active=True;w.queue_next()
            elif stage=='queue' and not w.process and not w.queue_active:
                assert not w.render_queue
                assert all((directory/f'queued-{i}'/'result.json').exists() for i in (1,2))
                state['queue_jobs']=2;state['relocated_render']=True;finish()
        except Exception as exc:finish(str(exc))
    timer.timeout.connect(poll);timer.start();w.sprints_test_timer=timer
