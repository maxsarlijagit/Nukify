# SPDX-License-Identifier: GPL-3.0-or-later
"""Executable QA for A/B prefetch and dependency-aware cache reuse."""
import json,time,tempfile,sys
from pathlib import Path
from PySide6.QtCore import QTimer
from model import blank,new_node
from animation import set_key
from live_engine import fingerprint

def run(w,app,report):
    temp=Path(tempfile.mkdtemp(prefix='nukify-workflow-qa-'));engine=w.project['blender']
    w.app_data=temp;w.recovery_path=temp/'recovery.nukify';w.pause();w.live_timer.stop();w.engine.stop();w.engine_b.stop()
    w.engine.cache=temp/'a';w.engine.cache.mkdir();w.engine_b.cache=temp/'b';w.engine_b.cache.mkdir()
    g=blank();g.update(width=320,height=180,last=6,blender=engine)
    source=new_node(g,'Constant',0,-150);a=new_node(g,'Color',-150,0);b=new_node(g,'Color',150,0)
    a['inputs']['Image']=source['id'];b['inputs']['Image']=source['id'];b['params']['exposure']=-1
    set_key(a,'exposure',1,0);set_key(a,'exposure',6,1);g['viewer']=a['id'];g['viewer_b']=b['id']
    w.project=g;w.sync();w.live_timer.stop();w.request_live()
    state={'stage':'initial','errors':[],'executable':sys.executable,'engine':engine};start=time.perf_counter()
    timer=QTimer(w);timer.setInterval(20)
    def finish(error=None):
        if state.get('finished'):return
        state['finished']=True;timer.stop();w.cache_scan.stop()
        if error:state['errors'].append(str(error))
        w.pause();w.live_timer.stop();w.engine.stop();w.engine_b.stop()
        state['passed']=not state['errors'];state['seconds']=time.perf_counter()-start
        w.grab().save(str(Path(report).with_suffix('.png')));Path(report).write_text(json.dumps(state,indent=2),encoding='utf-8')
        w.dirty=False;app.exit(0 if state['passed'] else 1)
    w.engine.failed.connect(finish);w.engine_b.failed.connect(finish)
    def poll():
        try:
            if time.perf_counter()-start>120:finish('Timeout');return
            if state['stage']=='initial' and not w.waiting_frame and w.viewer.reference is not None:
                state['stage']='warming';w.cache_range()
            elif state['stage']=='warming' and not w.warming and not w.engine.busy and not w.engine_b.busy:
                for branch,target,worker in [('A',a['id'],w.engine),('B',b['id'],w.engine_b)]:
                    assert all(worker.cached(fingerprint(g,target,f,w.proxy.currentData())) for f in range(1,7)),branch
                assert all(w.cache_strip.marks.get(f)=={'A','B'} for f in range(1,7))
                state['prefetched_a']=state['prefetched_b']=6
                old1=fingerprint(g,a['id'],1,w.proxy.currentData());old6=fingerprint(g,a['id'],6,w.proxy.currentData())
                bkeys=[fingerprint(g,b['id'],f,w.proxy.currentData()) for f in range(1,7)]
                set_key(a,'exposure',6,2)
                assert old1==fingerprint(g,a['id'],1,w.proxy.currentData())
                assert old6!=fingerprint(g,a['id'],6,w.proxy.currentData())
                assert bkeys==[fingerprint(g,b['id'],f,w.proxy.currentData()) for f in range(1,7)]
                state['unchanged_frames_retained']=True;state['jobs_before']=[w.engine.jobs_sent,w.engine_b.jobs_sent]
                state['stage']='cache_hit';w.invalidate_live();w.request_live()
            elif state['stage']=='cache_hit' and not w.waiting_frame and not w.engine.busy and not w.engine_b.busy:
                state['jobs_after']=[w.engine.jobs_sent,w.engine_b.jobs_sent]
                assert state['jobs_before']==state['jobs_after']
                w.pinned_properties=a['id'];w.properties(a);w.viewer.overlays.setChecked(True);w.viewer.sample_size.setCurrentIndex(1)
                state['zero_extra_renders']=True;finish()
        except Exception as exc:finish(str(exc))
    timer.timeout.connect(poll);timer.start();w.workflow_test_timer=timer
