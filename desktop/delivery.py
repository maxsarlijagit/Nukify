# SPDX-License-Identifier: GPL-3.0-or-later
"""Portable project collection and durable frame receipts."""
import copy
import hashlib
import json
import re
import shutil
from pathlib import Path

PATH_KEYS=('path','tracking_path','preserve_exr','texture_path')

def resolve_media(graph,base):
    g=copy.deepcopy(graph)
    for node in g['nodes']:
        for key in PATH_KEYS:
            value=node['params'].get(key)
            if value and not Path(value).is_absolute():node['params'][key]=str((Path(base)/value).resolve())
    if g.get('ocio') and not Path(g['ocio']).is_absolute():g['ocio']=str((Path(base)/g['ocio']).resolve())
    return g

def collect(graph,destination):
    dest=Path(destination)
    if dest.exists():raise ValueError('Elegí una carpeta nueva para el paquete.')
    g=copy.deepcopy(graph);g.pop('blender',None);g['output']=''
    # External OCIO dependencies may be absolute or use environment variables.
    if g.get('ocio'):raise ValueError('Paquete OCIO personalizado: recopila config/LUTs y sus dependencias antes de entregar. Coleccion automatica no soportada.')
    planned=[]
    for node in g['nodes']:
        for key in PATH_KEYS:
            value=node['params'].get(key)
            if not value:continue
            path=Path(value);pattern=re.escape(path.name);pattern=re.sub(r'(?:\\#)+',lambda m:r'\d{'+str(len(m[0])//2)+'}',pattern)
            matches=[p for p in path.parent.iterdir() if p.is_file() and re.fullmatch(pattern,p.name)] if '#' in path.name else [path]
            if not matches or any(not p.is_file() for p in matches):raise ValueError('Medio no encontrado: '+value)
            folder=Path('media')/hashlib.sha256(str(path.parent.resolve()).encode()).hexdigest()[:12]
            for source in matches:planned.append((source,folder/source.name))
            node['params'][key]=(folder/path.name).as_posix()
    dest.mkdir(parents=True)
    manifest={}
    for source,relative in planned:
        target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        manifest[relative.as_posix()]=hashlib.sha256(target.read_bytes()).hexdigest()
    (dest/'project.nukify').write_text(json.dumps(g,indent=2),encoding='utf-8')
    (dest/'media-sha256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return dest/'project.nukify'

def atomic_json(path,value):
    path=Path(path);temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2),encoding='utf-8');temp.replace(path)

def frame_signature(graph,target,frame):
    # Shared dependency fingerprint includes media stats and evaluated parameters.
    # Worker does not import Qt.
    from model import evaluation_order,sequence_path
    data={'graph':graph,'target':target,'frame':frame,'media':[]}
    for node,time in evaluation_order(graph,target,frame):
        for key in PATH_KEYS:
            value=node['params'].get(key)
            if value:
                p=Path(sequence_path(value,time));s=p.stat();data['media'].append((str(p),s.st_size,s.st_mtime_ns))
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()

def completed(out,frame,signature):
    out=Path(out)
    try:
        receipt=json.loads((out/f'frame_{frame:04d}.json').read_text())
        if receipt['signature']!=signature:return False
        return all(hashlib.sha256((out/name).read_bytes()).hexdigest()==digest for name,digest in receipt['files'].items())
    except (OSError,KeyError,ValueError):return False

def commit_frame(out,frame,signature):
    out=Path(out);names=[f'comp_{frame:04d}.exr',f'preview_{frame:04d}.png']
    atomic_json(out/f'frame_{frame:04d}.json',{'signature':signature,'files':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}})
