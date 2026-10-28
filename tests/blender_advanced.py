import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
import numpy as np
from model import blank,new_node
from animation import set_key,render_parameters
from worker import live_render
from roto import render_mask
cache=root/'validation/advanced-render';cache.mkdir(exist_ok=True)
g=blank();g.update(width=100,height=100)
src=new_node(g,'Constant');src['expressions']={'r':'frame / 10'}
def pixels(target,frame,key):
    info=live_render(dict(graph=g,target=target,frame=frame,proxy=1,key=key,cache=str(cache)))
    return np.fromfile(info['raw'],np.float32).reshape(100,100,4)
np.testing.assert_allclose(pixels(src['id'],3,'expression')[50,50,0],.3,atol=1e-5)
r=new_node(g,'Roto');r['params'].update(points=[[.4,.4],[.5,.4],[.5,.5],[.4,.5]],shape_group='moving',groups=[{'id':'moving','x':10}],motion_samples=8,shutter=1)
set_key(r,'shape_x',1,-20);set_key(r,'shape_x',3,20)
expected=render_mask(render_parameters(r,2,g),100,100,2)
np.testing.assert_allclose(pixels(r['id'],2,'roto')[...,0],expected[::-1],atol=1e-5)
k=new_node(g,'ChromaKey');k['inputs']['Image']=src['id'];k['params'].update(blur_pre=2,blur_post=2,dilate_distance=1,feather_distance=1)
for output in ('Image','Matte','Edges'):
    k['params']['output']=output;assert np.isfinite(pixels(k['id'],1,output)).all()
(root/'validation/advanced-render.json').write_text(json.dumps({'passed':True,'expression_pixel':.3,'roto_shutter_group_pixels':True,'key_outputs':['Image','Matte','Edges']}))
print('ADVANCED_RENDER_OK')
