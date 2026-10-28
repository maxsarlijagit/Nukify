# SPDX-License-Identifier: GPL-3.0-or-later
import sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
job=json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_text(encoding='utf-8'))
try:
    if job['task']=='track':
        from tracking import analyze
        result=analyze(job,lambda info:print('@@PROGRESS '+json.dumps(info),flush=True))
    else:
        import bpy
        image=bpy.data.images.load(job['path'],check_existing=False)
        bpy.context.scene.use_nodes=True
        n=bpy.context.scene.node_tree.nodes.new('CompositorNodeImage');n.image=image
        crypto=bpy.context.scene.node_tree.nodes.new('CompositorNodeCryptomatteV2');crypto.source='IMAGE';crypto.image=image
        result=dict(ok=True,width=image.size[0],height=image.size[1],type=image.type,
                    outputs=[s.name for s in n.outputs],colorspace=image.colorspace_settings.name,
                    alpha=image.alpha_mode,crypto_layers=[item.identifier for item in crypto.bl_rna.properties['layer_name'].enum_items])
        if Path(job['path']).suffix.lower()=='.exr':
            from exr_bridge import call
            result['exr']=call('inspect',path=job['path'])
except Exception as exc:
    traceback.print_exc();result=dict(ok=False,error=str(exc))
Path(job['result']).write_text(json.dumps(result,indent=2),encoding='utf-8')
print('@@RESULT '+json.dumps(result),flush=True)
