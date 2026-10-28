# SPDX-License-Identifier: GPL-3.0-or-later
"""Executed by Blender's Python, never by the UI interpreter."""
import json
import sys
import time
import traceback
from pathlib import Path
import bpy

sys.path.insert(0, str(Path(__file__).parent))
from model import ordered, sequence_path


def build(graph, target, frame):
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()
    from scene3d import cleanup
    cleanup()
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 1
    for obj in scene.objects:
        if obj.type != 'CAMERA':
            obj.hide_render = True
    scene.render.resolution_x = graph['width']
    scene.render.resolution_y = graph['height']
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    try: scene.view_settings.view_transform = 'Standard'
    except TypeError: pass  # Custom OCIO config retains its valid default view.
    try: scene.view_settings.look = 'None'
    except TypeError: pass
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.frame_set(frame)
    from builder import Builder
    output = Builder(graph).compile(target, frame)
    composite = tree.nodes.new('CompositorNodeComposite')
    tree.links.new(output, composite.inputs[0])
    return scene, tree, output



def main():
    job = json.loads(Path(sys.argv[sys.argv.index('--') + 1]).read_text(encoding='utf-8'))
    graph = job['graph']
    out = Path(job['directory'])
    out.mkdir(parents=True, exist_ok=True)
    from delivery import frame_signature,completed,commit_frame,atomic_json
    (out/'result.json').unlink(missing_ok=True)
    for frame in job['frames']:
        signature=frame_signature(graph,job['target'],frame)
        if job['export'] and completed(out,frame,signature):
            print('NUKIFY_SKIP',frame,flush=True)
            continue
        import shutil
        if shutil.disk_usage(out).free < graph['width']*graph['height']*32+16*1024**2:raise OSError('Espacio insuficiente para renderizar el siguiente cuadro')
        frame_out=out/'.staging'/str(frame) if job['export'] else out
        frame_out.mkdir(parents=True,exist_ok=True)
        scene, tree, output = build(graph, job['target'], frame)
        if job.get('inspect'):
            scene3d=next((s for s in bpy.data.scenes if s.name.startswith('NK3D_')),None)
            if scene3d is None:raise ValueError('Selecciona una rama con RenderLayers')
            bpy.context.window.scene=scene3d
            bpy.ops.file.pack_all()
            bpy.ops.wm.save_as_mainfile(filepath=str(out/'inspection.blend'))
            atomic_json(out/'result.json',{'ok':True,'inspection':True})
            return
        if job['export']:
            write = tree.nodes.new('CompositorNodeOutputFile')
            write.base_path = str(frame_out)
            write.format.file_format = 'OPEN_EXR'
            write.format.color_depth = '32'
            write.format.color_mode = 'RGBA'
            write.file_slots[0].path = 'comp_'
            tree.links.new(output, write.inputs[0])
        scene.render.filepath = str(frame_out / f'preview_{frame:04d}.png')
        bpy.ops.render.render(write_still=True)
        target = next(n for n in graph['nodes'] if n['id']==job['target'])
        if job['export'] and target['kind']=='Write' and target['params'].get('preserve_exr'):
            from exr_bridge import call
            call('preserve',path=str(frame_out / f'comp_{frame:04d}.exr'),source=sequence_path(target['params']['preserve_exr'], frame),prefix=target['params'].get('output_layer',''))
        if job['export']:
            for name in (f'comp_{frame:04d}.exr',f'preview_{frame:04d}.png'):(frame_out/name).replace(out/name)
            commit_frame(out,frame,signature)
        atomic_json(out/'progress.json',{'last_completed':frame,'total':len(job['frames'])})
    if 'scene' in locals() or not (out/'composition.blend').exists():
        bpy.context.scene.render.filepath='//preview_'
        for node in bpy.context.scene.node_tree.nodes:
            if node.type=='OUTPUT_FILE':node.base_path='//renders'
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(out / 'composition.blend'))
    (out / 'result.json').write_text(json.dumps({'ok': True, 'frames': job['frames']}))
    print('NUKIFY_RENDER_OK', flush=True)


def live_render(job):
    import numpy as np
    start = time.perf_counter()
    # Release previous frames; persistent services must not grow per frame.
    bpy.context.scene.use_nodes = True
    bpy.context.scene.node_tree.nodes.clear()
    for image in list(bpy.data.images):
        if image.type not in ('RENDER_RESULT', 'COMPOSITING') and image.users == 0:
            bpy.data.images.remove(image)
    scene, tree, output = build(job['graph'], job['target'], job['frame'])
    built=time.perf_counter()
    scale = tree.nodes.new('CompositorNodeScale')
    scale.space = 'ABSOLUTE'
    scale.inputs['X'].default_value = max(1, job['graph']['width'] // job['proxy'])
    scale.inputs['Y'].default_value = max(1, job['graph']['height'] // job['proxy'])
    tree.links.new(output, scale.inputs['Image'])
    write = tree.nodes.new('CompositorNodeOutputFile')
    cache = Path(job['cache'])
    write.base_path = str(cache)
    write.format.file_format = 'OPEN_EXR'
    write.format.color_depth = '32'
    write.format.color_mode = 'RGBA'
    write.file_slots[0].path = job['key'] + '_'
    tree.links.new(scale.outputs[0], write.inputs[0])
    bpy.ops.render.render()
    rendered=time.perf_counter()
    exr = cache / (job['key'] + '_' + str(job['frame']).zfill(4) + '.exr')
    image = bpy.data.images.load(str(exr), check_existing=False)
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    raw = cache / (job['key'] + '.rgba')
    # Blender pixels are bottom-up. Store top-down scene-linear float RGBA.
    temporary=raw.with_suffix('.rgba.tmp')
    pixels.reshape(height, width, 4)[::-1].copy().tofile(str(temporary));temporary.replace(raw)
    bpy.data.images.remove(image)
    exr.unlink(missing_ok=True)
    result = {'ok': True, 'raw': str(raw), 'width': width, 'height': height,
              'ms': round((time.perf_counter() - start) * 1000, 1),
              'timings_ms':{'build':round((built-start)*1000,2),'render':round((rendered-built)*1000,2),'readback':round((time.perf_counter()-rendered)*1000,2)}}
    from delivery import atomic_json
    atomic_json(raw.with_suffix('.json'),result)
    return result


def serve():
    print('@@NUKIFY ' + json.dumps({'status': 'ready'}), flush=True)
    for line in sys.stdin:
        try:
            result = live_render(json.loads(line))
        except Exception as exc:
            traceback.print_exc()
            result = {'ok': False, 'error': str(exc)}
        print('@@NUKIFY ' + json.dumps(result), flush=True)


if __name__ == '__main__':
    if '--serve' in sys.argv:
        serve()
    else:
        main()
