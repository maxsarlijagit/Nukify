"""Run through Blender. Synthetic reproducible compositor benchmark, not playback."""
import sys,json,platform,os
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
import bpy
from model import blank,new_node
from worker import live_render
out=root/'validation/benchmark-070';out.mkdir(parents=True,exist_ok=True)
report={'engine':bpy.app.version_string,'processor':platform.processor(),'platform':platform.platform(),'logical_cpus':os.cpu_count(),'threads':4,'fixture':'Constant > Grade > Blur; full float RGBA output','measurements':[]}
for width,height in ((1920,1080),(3840,2160)):
    g=blank();g.update(width=width,height=height)
    c=new_node(g,'Constant');grade=new_node(g,'Grade');grade['inputs']['Image']=c['id'];grade['params']['gain']=1.2
    blur=new_node(g,'Blur');blur['inputs']['Image']=grade['id']
    for i in range(3):
        info=live_render(dict(graph=g,target=blur['id'],frame=1,proxy=1,key=f'{width}-{i}',cache=str(out)))
        report['measurements'].append({'width':width,'height':height,'iteration':i,'ms':info['ms'],'timings_ms':info['timings_ms'],'raw_bytes':Path(info['raw']).stat().st_size})
(out/'report.json').write_text(json.dumps(report,indent=2));print('BENCHMARK_OK',report)
