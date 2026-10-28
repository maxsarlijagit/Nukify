# SPDX-License-Identifier: GPL-3.0-or-later
from copy import deepcopy


def interpolate(a, b, t):
    if isinstance(a, list):
        if len(a) != len(b):
            raise ValueError('La topologia animada debe conservar el numero de puntos')
        return [interpolate(x,y,t) for x,y in zip(a,b)]
    if isinstance(a, bool) or not isinstance(a, (int,float)):
        return deepcopy(a)
    return a + (b-a)*t


def value_at(curve, frame):
    keys = sorted(curve['keys'], key=lambda k: k[0])
    if not keys:
        raise ValueError('Curva sin claves')
    if frame <= keys[0][0]: return deepcopy(keys[0][1])
    for a,b in zip(keys, keys[1:]):
        if frame <= b[0]:
            t = (frame-a[0]) / (b[0]-a[0])
            mode = curve.get('interpolation','linear')
            if mode == 'constant': t = 1. if frame == b[0] else 0.
            elif mode == 'smooth': t = t*t*(3-2*t)
            elif mode == 'bezier' and isinstance(a[1],(int,float)):
                span=b[0]-a[0];m0=a[3] if len(a)>3 else 0.;m1=b[2] if len(b)>2 else 0.
                return (2*t**3-3*t*t+1)*a[1]+(t**3-2*t*t+t)*span*m0+(-2*t**3+3*t*t)*b[1]+(t**3-t*t)*span*m1
            return interpolate(a[1],b[1],t)
    return deepcopy(keys[-1][1])


def parameters(node, frame, graph=None, seen=None):
    seen=set() if seen is None else set(seen)
    if node['id'] in seen:raise ValueError('Ciclo de enlaces o expresiones: '+node['id'])
    seen.add(node['id'])
    p = deepcopy(node['params'])
    for key, curve in node.get('animation',{}).items():
        p[key] = value_at(curve, frame)
    if graph is not None and node.get('animation_link'):
        source=next((n for n in graph['nodes'] if n['id']==node['animation_link']),None)
        if source is None:raise ValueError('Falta el tracker enlazado: '+node['animation_link'])
        values=parameters(source,frame,graph,seen)
        if source['kind']=='PlanarTracker':
            from geometry import planar_output
            values['corners']=planar_output(values['corners'],source.get('tracking_reference_corners',source['params']['corners']),values.get('mode','cornerpin'))
        if source['kind']=='Tracker2D' and values.get('mode')=='stabilize':
            import math
            a=-math.radians(values['rotation']);s=1/values['scale'];x=values['x'];y=values['y']
            values.update(x=-s*(math.cos(a)*x-math.sin(a)*y),y=-s*(math.sin(a)*x+math.cos(a)*y),scale=s,rotation=-values['rotation'])
        for key in ('x','y','scale','rotation','corners'):
            if key in p and key in values:p[key]=deepcopy(values[key])
    if graph is not None and node.get('expressions'):
        from expressions import evaluate
        def lookup(node_id,key):
            source=next((n for n in graph['nodes'] if n['id']==node_id),None)
            if source is None:raise ValueError('Referencia inexistente: '+node_id)
            values=parameters(source,frame,graph,seen)
            if key not in values or type(values[key]) not in (int,float):raise ValueError('Referencia no numerica: '+node_id+'.'+key)
            return values[key]
        for key,text in node['expressions'].items():
            if key not in p or type(p[key]) not in (int,float):raise ValueError('Expresion requiere parametro numerico: '+key)
            p[key]=evaluate(text,frame,p[key],lookup)
    return p

def render_parameters(node,frame,graph):
    p=parameters(node,frame,graph)
    if node['kind']=='Roto' and p.get('motion_samples',1)>1 and p.get('shutter',0)>0:
        count=max(1,min(16,round(p['motion_samples'])))
        p['_samples']=[parameters(node,frame+p['shutter']*((i+.5)/count-.5),graph) for i in range(count)]
        p['_sample_frames']=[frame+p['shutter']*((i+.5)/count-.5) for i in range(count)]
    return p


def set_key(node, key, frame, value, mode='linear'):
    curve = node.setdefault('animation',{}).setdefault(key, {'interpolation': mode, 'keys': []})
    old=next((k for k in curve['keys'] if k[0]==frame),[])
    curve['keys'] = sorted([k for k in curve['keys'] if k[0] != frame] + [[frame,deepcopy(value)]+old[2:]])


def upstream_frame(node, frame, graph=None):
    if node.get('disabled'): return frame
    p = parameters(node, frame,graph)
    if node['kind'] == 'FrameHold': return round(p['frame'])
    if node['kind'] == 'TimeOffset': return frame - round(p['offset'])
    if node['kind'] == 'TimeRemap': return round(p['source_frame'])
    return frame
