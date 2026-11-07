# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit single-part, flat EXR contract. Never silently drop extra parts."""
import sys
sys.dont_write_bytecode = True  # Preserve the signed macOS bundle.
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'vendor'))
import OpenEXR
import numpy as np


def load(path):
    file=OpenEXR.File(str(path),separate_channels=True)
    if len(file.parts)!=1:raise ValueError('EXR multipart no soportado; separar las partes antes de importar')
    if file.header()['type'] in (OpenEXR.deepscanline,OpenEXR.deeptile):raise ValueError('Deep EXR no soportado')
    if any(c.xSampling!=1 or c.ySampling!=1 for c in file.channels().values()):raise ValueError('Canales EXR subsampled no soportados')
    return file


def inspect(path):
    file=load(path);header=file.header()
    return dict(channels=list(file.channels()),dataWindow=[x.tolist() for x in header['dataWindow']],
                displayWindow=[x.tolist() for x in header['displayWindow']],
                metadata={k:str(v) for k,v in header.items() if k!='channels'})


def layer_channels(channels,layer):
    """Resolve RGB aliases without mixing components from unrelated passes."""
    aliases=(('R','r','red'),('G','g','green'),('B','b','blue'),('A','a','alpha'))
    def rgba(prefix):
        return [next((prefix+c for c in names if prefix+c in channels),None) for names in aliases]
    if layer in channels:
        return [layer]*3+[None]
    if layer in ('Image','rgba','RGBA'):
        names=rgba('')
        if all(names[:3]):return names
        layers=sorted({name.rsplit('.',1)[0] for name in channels if '.' in name})
        candidates={name:rgba(name+'.') for name in layers}
        candidates={name:names for name,names in candidates.items() if all(names[:3])}
        # Prefer conventional beauty names; never choose Basecolor alphabetically.
        for preferred in ('image','rgba','combined','beauty','source'):
            matches=[name for name in candidates if name.rsplit('.',1)[-1].lower()==preferred]
            if len(matches)==1:
                names=candidates[matches[0]]
                break
            if len(matches)>1:break
        else:
            if len(candidates)==1:names=next(iter(candidates.values()))
        if not all(names[:3]):
            raise ValueError('EXR: seleccionar una capa RGB en Read.layer; disponibles: '+', '.join(candidates))
        if names[3] is None:
            names[3]=rgba('')[3] or next((name for name in ('Alpha.A','Alpha.alpha','Alpha.red','Alpha.R') if name in channels),None)
        return names
    names=rgba(layer+'.')
    if not all(names[:3]):
        raise ValueError('Canal/capa no disponible: '+layer+'; '+', '.join(channels))
    return names


def read_layer(path,layer):
    file=load(path);channels=file.channels();header=file.header()
    names=layer_channels(channels,layer)
    shape=next(iter(channels.values())).pixels.shape
    values=[]
    for i,name in enumerate(names):
        if name in channels:values.append(channels[name].pixels.astype(np.float32))
        elif i==3:values.append(np.ones(shape,np.float32))
        else:raise ValueError('Canal no disponible: '+name+'; '+', '.join(channels))
    cropped=np.stack(values,axis=2)
    dmin,dmax=header['dataWindow'];smin,smax=header['displayWindow']
    w,h=(smax-smin+1).tolist();x,y=(dmin-smin).tolist()
    if x<0 or y<0 or x+shape[1]>w or y+shape[0]>h:raise ValueError('EXR overscan fuera de displayWindow: reformatear explicitamente antes de importar')
    pixels=np.zeros((h,w,4),np.float32);pixels[y:y+shape[0],x:x+shape[1]]=cropped
    return pixels


def preserve_channels(render_path,source_path,prefix=''):
    """Replace named RGBA in a copy of the original header/channels, atomically."""
    source=load(source_path);render=load(render_path)
    header=dict(source.header());channels=dict(source.channels());smin,smax=header['displayWindow']
    shape=next(iter(render.channels().values())).pixels.shape
    if tuple((smax-smin+1)[::-1])!=shape:raise ValueError('Write: formato render y displayWindow del EXR fuente no coinciden')
    dmin,dmax=header['dataWindow'];x,y=(dmin-smin).tolist();w,h=(dmax-dmin+1).tolist()
    if x<0 or y<0 or x+w>shape[1] or y+h>shape[0]:raise ValueError('Write: overscan no soportado')
    for c in 'RGBA':
        name=(prefix+'.' if prefix else '')+c
        channels[name]=np.ascontiguousarray(render.channels()[c].pixels[y:y+h,x:x+w])
    temp=Path(render_path).with_suffix('.preserve.exr')
    OpenEXR.File(header,channels).write(str(temp));temp.replace(render_path)


if __name__=='__main__':
    import json
    job=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    result={}
    if job['task']=='read':np.save(job['pixels'],read_layer(job['path'],job['layer']))
    elif job['task']=='inspect':result=inspect(job['path'])
    elif job['task']=='preserve':preserve_channels(job['path'],job['source'],job.get('prefix',''))
    else:raise ValueError('EXR task no valido')
    Path(job['result']).write_text(json.dumps(result),encoding='utf-8')
