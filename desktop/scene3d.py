# SPDX-License-Identifier: GPL-3.0-or-later
"""Owned render scenes. Descriptors are evaluated at each graph frame."""
import math
import bpy
from mathutils import Vector


def cleanup():
    for scene in list(bpy.data.scenes):
        if scene.name.startswith('NK3D_'):
            objects=list(scene.objects)
            bpy.data.scenes.remove(scene)
            for obj in objects:
                if obj.users==0:bpy.data.objects.remove(obj)
    for collection in (bpy.data.meshes,bpy.data.materials,bpy.data.cameras,bpy.data.lights,bpy.data.worlds):
        for item in list(collection):
            if item.name.startswith('NK3D_') and item.users==0:collection.remove(item)


def render_node(builder, descriptor, camera, params):
    g=builder.graph
    scene=bpy.data.scenes.new('NK3D_Scene')
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=max(1,int(params['samples']))
    scene.render.resolution_x=g['width'];scene.render.resolution_y=g['height'];scene.render.resolution_percentage=100
    scene.render.film_transparent=True
    world=bpy.data.worlds.new('NK3D_World');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=max(0,descriptor['params']['ambient'])
    scene.world=world
    def place(obj,p):
        obj.location=[p[k] for k in ('x','y','z')]
        obj.rotation_euler=[math.radians(p[k]) for k in ('rx','ry','rz')]
        obj.scale=(p.get('scale',1.),)*3;scene.collection.objects.link(obj)
    p=camera['params'];data=bpy.data.cameras.new('NK3D_Camera')
    if p['lens']<=0 or p['near']<=0 or p['far']<=p['near']:raise ValueError('Camera: lens/near > 0 y far > near')
    data.lens=p['lens'];data.clip_start=p['near'];data.clip_end=p['far']
    obj=bpy.data.objects.new('NK3D_Camera',data);place(obj,p);scene.camera=obj
    for desc in descriptor['inputs'].values():
        projection=desc if desc['kind']=='Project3D' else None
        if projection:desc=projection['inputs']['Object']
        p=desc['params'];kind=desc['kind']
        if kind=='Light':
            data=bpy.data.lights.new('NK3D_Light','AREA');data.energy=max(0,p['energy']);data.shape='DISK';data.size=max(.001,p['size'])
            obj=bpy.data.objects.new('NK3D_Light',data);place(obj,p)
            obj.rotation_euler=(Vector((0,0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
            obj.rotation_euler.rotate_axis('X',math.radians(p['rx']));obj.rotation_euler.rotate_axis('Y',math.radians(p['ry']));obj.rotation_euler.rotate_axis('Z',math.radians(p['rz']))
            continue
        import bmesh
        mesh=bpy.data.meshes.new('NK3D_Mesh');bm=bmesh.new()
        primitive='plane' if kind=='Card' else p['primitive']
        if primitive=='cube':bmesh.ops.create_cube(bm,size=2)
        elif primitive=='sphere':bmesh.ops.create_uvsphere(bm,u_segments=32,v_segments=16,radius=1)
        else:bmesh.ops.create_grid(bm,x_segments=1,y_segments=1,size=1)
        bm.to_mesh(mesh);bm.free()
        obj=bpy.data.objects.new('NK3D_'+kind,mesh);place(obj,p)
        mat=bpy.data.materials.new('NK3D_Material');mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(*[p[c] for c in 'rgb'],1)
        texture=projection['params']['texture_path'] if projection else p.get('texture_path')
        if texture:
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(texture,check_existing=True)
            coords=mat.node_tree.nodes.new('ShaderNodeTexCoord')
            if projection:
                cp=projection['inputs']['Camera']['params'];cd=bpy.data.cameras.new('NK3D_Projector');cd.lens=cp['lens']
                projector=bpy.data.objects.new('NK3D_Projector',cd);place(projector,cp)
                uv=mesh.uv_layers.new(name='Projection');modifier=obj.modifiers.new('Projection','UV_PROJECT')
                modifier.uv_layer=uv.name;modifier.projectors[0].object=projector
                modifier.aspect_x=g['width'];modifier.aspect_y=g['height']
                mat.node_tree.links.new(coords.outputs['UV'],tex.inputs['Vector']);tex.extension='CLIP'
            else:mat.node_tree.links.new(coords.outputs['Generated'],tex.inputs['Vector'])
            mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
            mat.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
        obj.data.materials.append(mat)
    layer=scene.view_layers[0];layer.use_pass_z=True;layer.use_pass_normal=True
    n=builder.node('RLayers');n.scene=scene
    return n.outputs[params['pass_name']]
