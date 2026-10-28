"""Run with bundled Blender: verify pixels, not only node construction."""
import sys,json,traceback
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
import numpy as np
from model import blank,new_node
from worker import live_render
from registry import NODES
cache=root/'validation/nodes';cache.mkdir(parents=True,exist_ok=True)
results={}


def evaluate(kind,params=None):
    g=blank();g.update(width=64,height=64)
    src=new_node(g,'Constant');src['params'].update(r=.2,g=.4,b=.8,a=.5)
    n=new_node(g,kind)
    if params:n['params'].update(params)
    for socket in NODES[kind]['inputs']:
        if socket=='Mask':continue
        n['inputs'][socket]=src['id']
    info=live_render(dict(graph=g,target=n['id'],frame=1,proxy=1,key=kind,cache=str(cache)))
    pixels=np.fromfile(info['raw'],np.float32).reshape(64,64,4)
    assert np.isfinite(pixels).all(),kind
    return pixels[32,32]


expected={'Dot':[.2,.4,.8,.5],'Grade':[.2,.4,.8,.5],'Multiply':[.4,.8,1.6,.5],
          'Add':[.3,.5,.9,.5],'Premult':[.1,.2,.4,.5],'Unpremult':[.4,.8,1.6,.5],
          'Shuffle':[.8,.4,.2,.5],'Copy':[.2,.4,.8,.8],'FrameHold':[.2,.4,.8,.5]}
params={'Multiply':{'value':2},'Add':{'value':.1},'Shuffle':{'r':'B','b':'R'},'Copy':{'source':'B','destination':'A'},'Crop':{'right':64,'top':64},'Reformat':{'width':64,'height':64},'Roto':{'points':[[.1,.1],[.9,.1],[.9,.9],[.1,.9]]},'Grain':{'amount':0}}
for kind in NODES:
    if NODES[kind]['category']=='3D' or kind in ('Read','Cryptomatte','Backdrop'):continue
    try:
        px=evaluate(kind,params.get(kind))
        if kind in expected:np.testing.assert_allclose(px,expected[kind],atol=2e-5)
        results[kind]={'ok':True,'pixel':px.tolist()}
    except Exception as exc:results[kind]={'ok':False,'error':str(exc)};traceback.print_exc()
(root/'validation/node-results.json').write_text(json.dumps(results,indent=2))
assert all(v['ok'] for v in results.values()),{k:v for k,v in results.items() if not v['ok']}
print('NODES_OK',len(results))
