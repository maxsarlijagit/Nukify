# SPDX-License-Identifier: GPL-3.0-or-later
"""Compile the versioned Nukify graph into Blender compositor operations."""
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from model import evaluation_order, active_inputs, sequence_path
from animation import parameters, upstream_frame,render_parameters
from registry import DEFAULTS


class Builder:
    def __init__(self, graph):
        self.graph = graph
        self.tree = bpy.context.scene.node_tree
        self.outputs = {}

    def node(self, kind):
        return self.tree.nodes.new('CompositorNode' + kind)

    def plug(self, value, socket):
        if hasattr(value, 'node'): self.tree.links.new(value, socket)
        else: socket.default_value = value

    def math(self, operation, a, b=0.):
        n = self.node('Math'); n.operation = operation
        self.plug(a,n.inputs[0]); self.plug(b,n.inputs[1])
        return n.outputs[0]

    def split(self, image):
        n = self.node('SepRGBA'); self.plug(image,n.inputs[0]); return list(n.outputs)

    def rgba(self, channels):
        n = self.node('CombRGBA')
        for v,s in zip(channels,n.inputs): self.plug(v,s)
        return n.outputs[0]

    def raster(self, pixels, name):
        h,w = pixels.shape[:2]
        image = bpy.data.images.new(name, width=w,height=h,alpha=True,float_buffer=True)
        image.colorspace_settings.name = 'Non-Color'
        image.alpha_mode = 'PREMUL'
        image.pixels.foreach_set(np.ascontiguousarray(pixels,dtype=np.float32).ravel())
        n = self.node('Image'); n.image = image
        return n.outputs[0]

    def compile(self, target, frame):
        for spec, time in evaluation_order(self.graph,target,frame):
            p = dict(DEFAULTS[spec['kind']], **render_parameters(spec,time,self.graph))
            if spec['kind']=='PlanarTracker':
                from geometry import planar_output
                p['corners']=planar_output(p['corners'],spec.get('tracking_reference_corners',spec['params']['corners']),p.get('mode','cornerpin'))
            inputs = {k:self.outputs[(v,upstream_frame(spec,time,self.graph))] for k,v in active_inputs(spec,time,self.graph).items()}
            if spec.get('disabled') or spec['kind']=='Switch': out = next(iter(inputs.values()))
            else: out = self.operation(spec['kind'],p,inputs,time)
            self.outputs[(spec['id'],time)] = out
            if hasattr(out,'node'):out.node.label = spec['id'] + f' @{time}'
        return self.outputs[(target,frame)]

    def operation(self, kind, p, ins, frame):
        if kind in ('Camera','Card','Geometry','Project3D','Light','Scene'):
            return dict(kind=kind,params=p,inputs=ins)
        if kind=='RenderLayers':
            from scene3d import render_node
            return render_node(self,ins['Scene'],ins['Camera'],p)
        image = ins.get('Image')
        if kind in ('Write','Dot','FrameHold','TimeOffset','TimeRemap'): return image
        if kind == 'Read':
            n = self.node('Image')
            n.image = bpy.data.images.load(sequence_path(p['path'],frame),check_existing=True)
            if p['colorspace'] != 'Auto': n.image.colorspace_settings.name = p['colorspace']
            if p['alpha'] != 'Auto': n.image.alpha_mode = p['alpha']
            if p['layer'] not in n.outputs:
                if Path(p['path']).suffix.lower()=='.exr':
                    from exr_bridge import call
                    return self.raster(call('read',path=sequence_path(p['path'],frame),layer=p['layer'])[::-1],p['layer'])
                raise ValueError('Canal/pase no disponible: '+p['layer']+'; disponibles: '+', '.join(s.name for s in n.outputs))
            return n.outputs[p['layer']]
        if kind == 'Constant':
            pixels=np.empty((self.graph['height'],self.graph['width'],4),np.float32)
            pixels[:]=[p[c] for c in 'rgba']
            return self.raster(pixels,'Constant')
        if kind == 'Color':
            n = self.node('Exposure'); self.plug(image,n.inputs[0]); n.inputs[1].default_value = p['exposure']; return n.outputs[0]
        if kind in ('Multiply','Add','Clamp','Invert','Grade','Shuffle','Copy','Premult','Unpremult','AlphaMask','LumaKey'):
            c = self.split(image if image is not None else ins['B'])
            if kind == 'AlphaMask': return c[3]
            if kind == 'Shuffle': c = [c['RGBA'.index(p[k])] if p[k] in 'RGBA' else float(p[k]) for k in 'rgba']
            elif kind == 'Copy': c['RGBA'.index(p['destination'])] = self.split(ins['A'])['RGBA'.index(p['source'])]
            elif kind == 'LumaKey':
                if p['high'] <= p['low']: raise ValueError('LumaKey requiere high > low')
                n = self.node('RGBToBW'); self.plug(image,n.inputs[0])
                a = self.math('DIVIDE',self.math('SUBTRACT',n.outputs[0],p['low']),p['high']-p['low'])
                c[3] = self.math('MINIMUM',1.,self.math('MAXIMUM',0.,a))
            else:
                for i in range(3):
                    if kind == 'Multiply': c[i] = self.math('MULTIPLY',c[i],p['value'])
                    elif kind == 'Add': c[i] = self.math('ADD',c[i],p['value'])
                    elif kind == 'Clamp': c[i] = self.math('MINIMUM',p['maximum'],self.math('MAXIMUM',p['minimum'],c[i]))
                    elif kind == 'Invert': c[i] = self.math('SUBTRACT',1.,c[i])
                    elif kind == 'Premult': c[i] = self.math('MULTIPLY',c[i],c[3])
                    elif kind == 'Unpremult': c[i] = self.math('DIVIDE',c[i],c[3])
                    elif kind == 'Grade':
                        if p['whitepoint']==p['blackpoint'] or p['gamma']<=0: raise ValueError('Grade: whitepoint != blackpoint y gamma > 0')
                        gain=p['gain']*p.get('gain_'+'rgb'[i],1.)
                        gamma=p['gamma']*p.get('gamma_'+'rgb'[i],1.)
                        offset=p['offset']+p.get('offset_'+'rgb'[i],0.)
                        if gamma<=0:raise ValueError('Gamma de canal debe ser positivo')
                        v = self.math('DIVIDE',self.math('SUBTRACT',c[i],p['blackpoint']),p['whitepoint']-p['blackpoint'])
                        v = self.math('ADD',self.math('MULTIPLY',v,gain-p['lift']),p['lift'])
                        v = self.math('ADD',self.math('MULTIPLY',v,p['multiply']),offset)
                        c[i] = self.math('MULTIPLY',self.math('SIGN',v),self.math('POWER',self.math('ABSOLUTE',v),1/gamma))
            return self.rgba(c)
        if kind == 'ColorCorrect':
            n = self.node('ColorCorrection'); self.plug(image,n.inputs[0])
            for k in p: setattr(n,k if '_' in k else 'master_'+k,p[k])
            return n.outputs[0]
        if kind == 'ColorSpace':
            n = self.node('ConvertColorSpace'); n.from_color_space=p['source']; n.to_color_space=p['destination']
            self.plug(image,n.inputs[0]); return n.outputs[0]
        if kind == 'Merge':
            fac = self.math('MULTIPLY',ins.get('Mask',1.),p['mix'])
            if p['operation']=='over':
                n = self.node('AlphaOver'); self.plug(fac,n.inputs[0]); self.plug(ins['B'],n.inputs[1]); self.plug(ins['A'],n.inputs[2]); return n.outputs[0]
            a,b = self.split(ins['A']),self.split(ins['B']); c=[]
            for x,y in zip(a,b):
                op = p['operation']
                v = self.math('ADD',x,y) if op=='plus' else self.math('MULTIPLY',x,y) if op=='multiply' else self.math('ABSOLUTE',self.math('SUBTRACT',x,y)) if op=='difference' else self.math('SUBTRACT',1.,self.math('MULTIPLY',self.math('SUBTRACT',1.,x),self.math('SUBTRACT',1.,y)))
                c.append(self.math('ADD',self.math('MULTIPLY',v,fac),self.math('MULTIPLY',y,self.math('SUBTRACT',1.,fac))))
            return self.rgba(c)
        if kind in ('Blur','EdgeBlur','DilateErode'):
            channels = self.split(image) if kind!='Blur' else None
            n = self.node('DilateErode' if kind=='DilateErode' else 'Blur')
            if kind=='DilateErode': n.mode='DISTANCE'; n.distance=round(p['distance'])
            else: n.filter_type='GAUSS'; n.size_x=n.size_y=round(p['size'])
            self.plug(channels[3] if channels else image,n.inputs[0])
            if channels:
                channels[3]=n.outputs[0]; return self.rgba(channels)
            return n.outputs[0]
        if kind in ('Transform','Tracker2D'):
            n = self.node('Transform'); self.plug(image,n.inputs[0])
            angle=math.radians(p['rotation']); scale=p['scale']; x=p['x'];y=p['y']
            if kind=='Tracker2D' and p['mode']=='stabilize':
                if scale==0: raise ValueError('Escala de tracking nula')
                angle=-angle;scale=1/scale;x,y=-scale*(math.cos(angle)*x-math.sin(angle)*y),-scale*(math.sin(angle)*x+math.cos(angle)*y)
            px=(p.get('pivot_x',.5)-.5)*self.graph['width'];py=(p.get('pivot_y',.5)-.5)*self.graph['height']
            n.inputs['X'].default_value=x+px-scale*(math.cos(angle)*px-math.sin(angle)*py)
            n.inputs['Y'].default_value=y+py-scale*(math.sin(angle)*px+math.cos(angle)*py)
            n.inputs['Angle'].default_value=angle;n.inputs['Scale'].default_value=scale
            return n.outputs[0]
        if kind in ('CornerPin','PlanarTracker'):
            n=self.node('CornerPin');self.plug(image,n.inputs[0])
            for socket,idx in [('Lower Left',0),('Lower Right',1),('Upper Right',2),('Upper Left',3)]:
                n.inputs[socket].default_value=p['corners'][idx]
            return n.outputs[0]
        if kind=='Reformat':
            n=self.node('Scale');n.space='ABSOLUTE';self.plug(image,n.inputs[0]);n.inputs[1].default_value=p['width'];n.inputs[2].default_value=p['height'];return n.outputs[0]
        if kind=='Crop':
            n=self.node('Crop');self.plug(image,n.inputs[0])
            n.inputs['X'].default_value=round(p['left']);n.inputs['Y'].default_value=round(p['bottom'])
            n.inputs['Width'].default_value=max(1,round(p['right']-p['left']))
            n.inputs['Height'].default_value=max(1,round(p['top']-p['bottom']))
            return n.outputs[0]
        if kind=='Mask':
            n=self.node('EllipseMask')
            for k in ('x','y','width','height'):setattr(n,'mask_'+k if k in ('width','height') else k,p[k])
            return n.outputs[0]
        if kind=='Roto':
            from roto import render_mask
            mask=render_mask(p,self.graph['width'],self.graph['height'],frame)
            return self.split(self.raster(np.repeat(mask[...,None],4,axis=2),'Roto'))[0]
        if kind=='MaskCombine':
            op={'max':'MAXIMUM','add':'ADD','subtract':'SUBTRACT','intersect':'MULTIPLY'}[p['operation']]
            return self.math('MINIMUM',1.,self.math('MAXIMUM',0.,self.math(op,ins['B'],ins['A'])))
        if kind=='ChromaKey':
            n=self.node('Keying');self.plug(image,n.inputs[0]);n.inputs[1].default_value=(p['r'],p['g'],p['b'],1.)
            for k in ('screen_balance','clip_black','clip_white'):setattr(n,k,p[k])
            n.despill_factor=p['despill']
            for key in ('blur_pre','blur_post','dilate_distance','feather_distance','edge_kernel_radius'):setattr(n,key,round(p[key]))
            n.edge_kernel_tolerance=p['edge_kernel_tolerance'];n.despill_balance=p['despill_balance']
            return n.outputs[p['output']]
        if kind=='Despill':
            n=self.node('ColorSpill');self.plug(image,n.inputs[0]);n.channel=p['channel'];n.inputs[1].default_value=p['factor'];return n.outputs[0]
        if kind=='ZDefocus':
            n=self.node('Defocus');n.use_zbuffer=True;n.use_preview=False;n.f_stop=p['fstop'];n.z_scale=p['zscale'];n.blur_max=p['maxblur']
            self.plug(image,n.inputs[0]);self.plug(ins['Depth'],n.inputs[1]);return n.outputs[0]
        if kind=='VectorBlur':
            n=self.node('VecBlur');n.samples=round(p['samples']);n.factor=p['factor']
            for key,s in zip(('Image','Depth','Vector'),n.inputs):self.plug(ins[key],s)
            return n.outputs[0]
        if kind=='Grain':
            rng=np.random.default_rng(round(p['seed'])+frame)
            h,w=self.graph['height'],self.graph['width']
            noise=rng.normal(0,p['amount'],(h,w,4)).astype(np.float32);noise[...,3]=0
            a,b=self.split(image),self.split(self.raster(noise,'Grain'))
            return self.rgba([self.math('ADD',a[i],b[i]) for i in range(3)]+[a[3]])
        if kind=='Regrain':
            a,b,c=self.split(image),self.split(ins['Plate']),self.split(ins['Clean'])
            return self.rgba([self.math('ADD',a[i],self.math('MULTIPLY',self.math('SUBTRACT',b[i],c[i]),p['amount'])) for i in range(3)]+[a[3]])
        if kind=='Cryptomatte':
            n=self.node('CryptomatteV2');n.source='IMAGE';n.image=bpy.data.images.load(sequence_path(p['path'],frame),check_existing=True)
            if not p['layer'] or not p['matte_id']: raise ValueError('Cryptomatte requiere layer y matte_id del EXR')
            n.layer_name=p['layer'];n.matte_id=p['matte_id'];return n.outputs['Matte']
        raise ValueError('Evaluator no disponible: '+kind)
