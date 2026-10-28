# SPDX-License-Identifier: GPL-3.0-or-later
"""Explicit single-part, flat EXR contract. Never silently drop extra parts."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'vendor'))
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


def read_layer(path,layer):
    file=load(path);channels=file.channels();header=file.header()
    if layer in ('Image','rgba','RGBA'):names=list('RGBA')
    elif layer in channels:names=[layer]*3+['1']
    else:names=[layer+'.'+c for c in 'RGBA']
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
