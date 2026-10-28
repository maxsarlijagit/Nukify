# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import re
from pathlib import Path
from registry import INPUTS, DEFAULTS, MASKS, TYPES, SOCKET_TYPES
from animation import parameters, upstream_frame


def blank():
    return dict(version=2, nodes=[], viewer=None, width=960, height=540, frame=1,
                first=1, last=1, output='', blender='', ocio='')


def migrate(graph):
    g = copy.deepcopy(graph)
    if g.get('version') not in (1,2): raise ValueError('Version de proyecto no compatible')
    g['version'] = 2
    g.setdefault('ocio','')
    for n in g['nodes']:
        if n['kind'] not in INPUTS: raise ValueError('Nodo no compatible: '+n['kind'])
        n['params'] = dict(copy.deepcopy(DEFAULTS[n['kind']]), **n['params'])
    return g


def new_node(graph, kind, x=0, y=0):
    if kind not in INPUTS: raise ValueError('Unknown node type')
    used = {n['id'] for n in graph['nodes']}
    i = 1
    while f'{kind}{i}' in used: i += 1
    n = dict(id=f'{kind}{i}',kind=kind,x=x,y=y,params=copy.deepcopy(DEFAULTS[kind]),inputs={})
    graph['nodes'].append(n)
    return n


def sequence_path(path, frame):
    return re.sub(r'#+',lambda m: str(frame).zfill(len(m[0])),path)


def active_inputs(node, frame, graph=None):
    inputs = node['inputs']
    if node.get('disabled'):
        socket = 'B' if 'B' in INPUTS[node['kind']] else 'Image'
        return {socket: inputs[socket]} if socket in inputs else {}
    if node['kind'] == 'Switch':
        socket = 'A' if round(parameters(node,frame,graph)['which']) else 'B'
        return {socket: inputs[socket]} if socket in inputs else {}
    return inputs


def evaluation_order(graph, target, frame=None, check_files=True):
    nodes = {n['id']:n for n in graph['nodes']}
    if len(nodes)!=len(graph['nodes']): raise ValueError('Identificadores duplicados')
    done,pending,result = set(),set(),[]
    def visit(key,time):
        if key in pending: raise ValueError('La conexion crea un ciclo')
        if (key,time) in done: return
        if key not in nodes: raise ValueError('Falta el nodo '+key)
        n=nodes[key]; kind=n['kind']
        if kind not in INPUTS: raise ValueError('Tipo no soportado: '+kind)
        if kind=='Backdrop': raise ValueError('Backdrop no es una imagen')
        inputs=active_inputs(n,time,graph)
        required=[s for s in INPUTS[kind] if s not in ('Mask','Object2','Light')]
        if kind=='Switch': required=['A' if round(parameters(n,time,graph)['which']) else 'B']
        if n.get('disabled'): required=['B' if 'B' in INPUTS[kind] else 'Image']
        for socket in required:
            if not inputs.get(socket): raise ValueError(f'{key}: falta conectar {socket}')
        pending.add(key)
        for socket,source in inputs.items():
            if socket not in INPUTS[kind]: raise ValueError('Entrada invalida')
            visit(source,upstream_frame(n,time,graph))
            if TYPES.get(nodes[source]['kind'],'image') != SOCKET_TYPES.get(socket,'image'):
                raise ValueError('Tipo incompatible para '+socket)
            if socket=='Mask' and nodes[source]['kind'] not in MASKS:
                raise ValueError('Conecta una mascara a Mask; usa AlphaMask para extraer alpha')
        if kind in ('Read','Cryptomatte') and check_files:
            path=sequence_path(parameters(n,time)['path'],time)
            if not Path(path).is_file(): raise ValueError(f'{key}: archivo no encontrado: {path}')
        pending.remove(key);done.add((key,time));result.append((n,time))
    visit(target, graph['frame'] if frame is None else frame)
    return result


def ordered(graph,target,frame=None,check_files=True):
    return [n for n,t in evaluation_order(graph,target,frame,check_files)]


def connect(graph,source,target,socket):
    nodes={n['id']:n for n in graph['nodes']}
    if source==target: raise ValueError('Un nodo no puede conectarse a si mismo')
    if nodes[source]['kind'] in ('Write','Backdrop'): raise ValueError('Nodo sin salida')
    if socket not in INPUTS[nodes[target]['kind']]: raise ValueError('Entrada invalida')
    if TYPES.get(nodes[source]['kind'],'image') != SOCKET_TYPES.get(socket,'image'):raise ValueError('Tipo incompatible para '+socket)
    if socket=='Mask' and nodes[source]['kind'] not in MASKS: raise ValueError('Mask requiere mascara o AlphaMask')
    def upstream(key,seen):
        if key==target:return True
        if key in seen:return False
        seen.add(key)
        return any(upstream(k,seen) for k in nodes[key]['inputs'].values())
    if upstream(source,set()): raise ValueError('La conexion crea un ciclo')
    nodes[target]['inputs'][socket]=source


def demo(asset_dir):
    g = blank()
    bg = new_node(g, 'Read', -220, -220)
    bg['params']['path'] = str(Path(asset_dir) / 'background.png')
    fg = new_node(g, 'Read', 40, -220)
    fg['params']['path'] = str(Path(asset_dir) / 'foreground.png')
    if (Path(asset_dir) / 'sequence' / 'foreground_0001.png').is_file():
        fg['params']['path'] = str(Path(asset_dir) / 'sequence' / 'foreground_####.png')
        g['last'] = 48
    color = new_node(g, 'Color', 40, -100)
    color['inputs']['Image'] = fg['id']
    mask = new_node(g, 'Mask', 300, -100)
    merge = new_node(g, 'Merge', 40, 40)
    merge['inputs'] = {'B': bg['id'], 'A': color['id'], 'Mask': mask['id']}
    write = new_node(g, 'Write', 40, 180)
    write['inputs']['Image'] = merge['id']
    g['viewer'] = merge['id']
    return g
