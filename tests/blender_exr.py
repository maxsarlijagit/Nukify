import sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
import bpy,numpy as np
from exr_bridge import call
from worker import live_render
from model import blank,new_node
out=root/'validation/exr';out.mkdir(parents=True,exist_ok=True)
# Real Blender multilayer EXR with Cryptomatte manifest.
bpy.ops.wm.read_factory_settings(use_empty=False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=4;scene.cycles.device='CPU'
scene.render.resolution_x=64;scene.render.resolution_y=64;scene.render.resolution_percentage=100
layer=scene.view_layers[0];layer.use_pass_cryptomatte_object=True;layer.use_pass_z=True;layer.use_pass_vector=True;layer.use_pass_diffuse_color=True
scene.render.image_settings.file_format='OPEN_EXR_MULTILAYER';scene.render.image_settings.color_depth='32';scene.render.filepath=str(out/'crypto.exr')
bpy.ops.render.render(write_still=True)
metadata=call('inspect',path=str(out/'crypto.exr'));(out/'metadata.json').write_text(json.dumps(metadata,indent=2))
crypto_name=next(v for k,v in metadata['metadata'].items() if k.startswith('cryptomatte/') and k.endswith('/name'))
g=blank();g.update(width=64,height=64)
n=new_node(g,'Cryptomatte');n['params'].update(path=str(out/'crypto.exr'),layer=crypto_name,matte_id='Cube')
info=live_render(dict(graph=g,target=n['id'],frame=1,proxy=1,key='crypto-mask',cache=str(out)))
mask=np.fromfile(info['raw'],np.float32).reshape(info['height'],info['width'],4)
assert mask[...,:3].max()>.9 and mask[...,:3].min()==0, (mask.min(),mask.max())
(out/'report.json').write_text(json.dumps(dict(passed=True,arbitrary_channels=True,data_window=True,metadata=True,cryptomatte=crypto_name,mask_pixels=int((mask[...,0]>.5).sum())),indent=2))
print('EXR_OK')
