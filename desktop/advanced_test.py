"""Packaged UI/worker pixel verification for expressions and sampled roto."""
import json,time,tempfile,sys
from pathlib import Path
import numpy as np
from PySide6.QtCore import QTimer
from model import blank,new_node
from animation import set_key,render_parameters

def run(w,app,report):
    temp=Path(tempfile.mkdtemp(prefix='nukify-advanced-'));engine=w.project['blender']
    w.app_data=temp;w.recovery_path=temp/'recovery.nukify';w.pause();w.live_timer.stop();w.engine.stop();w.engine_b.stop()
    w.engine.cache=temp/'cache';w.engine.cache.mkdir()
    g=blank();g.update(width=100,height=100,frame=2,last=3,blender=engine)
    c=new_node(g,'Constant');c['expressions']={'r':'frame / 10'}
    r=new_node(g,'Roto');r['params'].update(points=[[.4,.4],[.5,.4],[.5,.5],[.4,.5]],shape_group='Group',groups=[{'id':'Group','x':10}],motion_samples=8,shutter=1)
    set_key(r,'shape_x',1,-20);set_key(r,'shape_x',3,20)
    g['viewer']=c['id'];w.project=g;w.sync();w.proxy.setCurrentIndex(0);w.live_timer.stop();w.request_live()
    state={'stage':'expression','errors':[],'executable':sys.executable,'engine':engine};start=time.perf_counter()
    timer=QTimer(w);timer.setInterval(25)
    def finish(error=None):
        if state.get('finished'):return
        state['finished']=True;timer.stop();w.cache_scan.stop()
        if error:state['errors'].append(str(error))
        w.pause();w.live_timer.stop();w.engine.stop();w.engine_b.stop()
        state['passed']=not state['errors'];state['seconds']=time.perf_counter()-start
        w.grab().save(str(Path(report).with_suffix('.png')));Path(report).write_text(json.dumps(state,indent=2),encoding='utf-8')
        w.dirty=False;app.exit(0 if state['passed'] else 1)
    w.engine.failed.connect(finish)
    def poll():
        try:
            if time.perf_counter()-start>90:finish('Timeout');return
            if w.waiting_frame or w.engine.busy or w.viewer.source is None:return
            if state['stage']=='expression':
                np.testing.assert_allclose(w.viewer.source[50,50,0],.2,atol=1e-5);state['expression_pixel']=True
                c['expressions']['r']='frame / 5';state['stage']='edited';w.invalidate_live();w.request_live()
            elif state['stage']=='edited':
                np.testing.assert_allclose(w.viewer.source[50,50,0],.4,atol=1e-5);state['live_expression_edit']=True
                g['viewer']=r['id'];state['stage']='roto';w.invalidate_live();w.request_live()
            else:
                mask=w.viewer.source[...,0];ys,xs=np.where(mask>0)
                assert np.isfinite(mask).all() and mask.min()>=0 and mask.max()<=1
                assert xs.max()-xs.min()>18 and abs(float((mask.sum(axis=0)*np.arange(100)).sum()/mask.sum())-55)<2
                assert abs(float((mask.sum(axis=1)*np.arange(100)).sum()/mask.sum())-54)<2
                assert np.count_nonzero((mask>0)&(mask<1))>100
                state['roto_group_shutter_pixels']=True;finish()
        except Exception as exc:finish(str(exc))
    timer.timeout.connect(poll);timer.start();w.advanced_test_timer=timer
