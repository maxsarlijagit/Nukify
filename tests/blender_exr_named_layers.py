"""Real Read -> compositor -> float pixels test, after exr_named_layers.py --fixture."""
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'desktop'))
import numpy as np
from model import blank,new_node
from worker import live_render

out=root/'validation/exr'
g=blank();g.update(width=8,height=8)
n=new_node(g,'Read');n['params']['path']=str(out/'named_layers.exr')
for layer,expected in [('Image',[2.,.4,.1,.5]),('Basecolor',[.7,.8,.9,1.])]:
    n['params']['layer']=layer
    result=live_render(dict(graph=g,target=n['id'],frame=1,proxy=1,key='named-'+layer,cache=str(out)))
    pixels=np.fromfile(result['raw'],np.float32).reshape(8,8,4)
    np.testing.assert_allclose(pixels,np.broadcast_to(expected,pixels.shape),atol=1e-5)
print('EXR_NAMED_LAYERS_RENDER_OK')
