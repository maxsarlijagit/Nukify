"""Real Cycles RGBA/pass/animation and persistent scene isolation regression."""
import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
import bpy,numpy as np
from examples import example
from worker import live_render
from model import new_node
cache=root/'validation/3d';cache.mkdir(parents=True,exist_ok=True)
g=example('Integracion 3D',root/'assets');g.update(width=96,height=72)
render=next(n for n in g['nodes'] if n['kind']=='RenderLayers');render['params']['samples']=4
images=[];reports=[]
for frame in (1,12,1):
    info=live_render(dict(graph=g,target=render['id'],frame=frame,proxy=1,key=f'render{len(images)}',cache=str(cache)))
    pixels=np.fromfile(info['raw'],np.float32).reshape(72,96,4);images.append(pixels)
    assert np.isfinite(pixels).all()
    assert pixels[:,:,3].max()>.99 and pixels[:,:,3].min()==0
    assert np.count_nonzero(pixels[:,:,3])>100
    assert len([s for s in bpy.data.scenes if s.name.startswith('NK3D_')])==1
    reports.append({'frame':frame,'ms':info['ms'],'covered_pixels':int(np.count_nonzero(pixels[:,:,3]))})
assert np.abs(images[0]-images[1]).max()>.1
np.testing.assert_allclose(images[0],images[2],atol=1e-5)
projection=new_node(g,'Project3D');projection['params']['texture_path']=str(root/'assets/production/insert.png')
projection['inputs']={'Object':'Geometry1','Camera':'Camera1'}
next(n for n in g['nodes'] if n['kind']=='Scene')['inputs']['Object']=projection['id']
info=live_render(dict(graph=g,target=render['id'],frame=1,proxy=1,key='projection',cache=str(cache)))
projected=np.fromfile(info['raw'],np.float32).reshape(72,96,4)
assert np.abs(projected-images[0]).max()>.1
reports.append({'projection':True,'ms':info['ms']})
for pass_name in ('Depth','Normal','Alpha'):
    render['params']['pass_name']=pass_name
    info=live_render(dict(graph=g,target=render['id'],frame=1,proxy=1,key=pass_name,cache=str(cache)))
    pixels=np.fromfile(info['raw'],np.float32);assert np.isfinite(pixels).all()
    reports.append({'pass':pass_name,'ms':info['ms']})
(cache/'report.json').write_text(json.dumps(reports,indent=2))
print('THREE_D_OK',reports)
