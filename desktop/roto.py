# SPDX-License-Identifier: GPL-3.0-or-later
"""Hierarchical shape transforms and sampled shutter integration."""
import math,sys
from pathlib import Path
import numpy as np
from animation import value_at
from shapes import sample_shape

def validate_groups(groups):
    if not isinstance(groups,list) or len(groups)>64:raise ValueError('Maximo 64 grupos de roto')
    lookup={}
    for g in groups:
        if not isinstance(g,dict) or not isinstance(g.get('id'),str) or not g['id'] or g['id'] in lookup:raise ValueError('Cada grupo requiere un id unico')
        for key in ('x','y','scale','rotation','opacity'):
            if key in g and (type(g[key]) not in (int,float) or not math.isfinite(g[key])):raise ValueError('Valor no numerico en grupo: '+key)
        if g.get('scale',1)<=0 or not 0<=g.get('opacity',1)<=1:raise ValueError('Grupo requiere escala positiva y opacity entre 0 y 1')
        lookup[g['id']]=g
    for g in groups:
        visited=set();current=g
        while current:
            if current['id'] in visited:raise ValueError('Ciclo de grupos de roto')
            visited.add(current['id']);parent=current.get('parent','')
            if parent and parent not in lookup:raise ValueError('Grupo padre inexistente: '+parent)
            current=lookup.get(parent)
    return lookup

def at_frame(data,frame):
    result=dict(data)
    for key,curve in data.get('animation',{}).items():result[key]=value_at(curve,frame)
    return result

def matrix(values,w,h,prefix=''):
    angle=math.radians(values.get(prefix+'rotation',0));scale=values.get(prefix+'scale',1)
    if not math.isfinite(scale) or scale<=0:raise ValueError('Escala roto debe ser positiva')
    c,s=math.cos(angle)*scale,math.sin(angle)*scale
    x,y=values.get(prefix+'x',0),values.get(prefix+'y',0)
    return np.array([[c,-s,x+w/2-c*w/2+s*h/2],[s,c,y+h/2-s*w/2-c*h/2],[0,0,1.]])

def shape_transform(shape,p,w,h,frame):
    groups=validate_groups(p.get('groups',[]));transform=matrix(shape,w,h,'shape_')
    enabled=shape.get('shape_enabled',True);opacity=shape.get('shape_opacity',1.)
    parent=shape.get('shape_group','')
    while parent:
        if parent not in groups:raise ValueError('La forma referencia un grupo inexistente: '+parent)
        group=at_frame(groups[parent],frame);transform=matrix(group,w,h)@transform
        enabled=enabled and group.get('enabled',True);opacity*=group.get('opacity',1.)
        parent=group.get('parent','')
    return matrix(p,w,h)@transform,enabled,max(0.,min(1.,opacity))

def transform_points(points,transform,w,h):
    result=[]
    for point in points:
        row=[]
        for i in range(0,len(point),2):
            xy=transform@np.array([point[i]*w,point[i+1]*h,1.]);row.extend([float(xy[0]/w),float(xy[1]/h)])
        result.append(row)
    return result

def raster(p,w,h,frame):
    sys.path.insert(0,str(Path(__file__).parent/'vendor'));import cv2
    mask=np.zeros((h,w),np.float32);ss=2
    for original in sorted(list(p.get('shapes',[]))+[p],key=lambda s:s.get('shape_order',0)):
        # Active shape has already been evaluated by parameters(); inactive layers carry curves.
        shape=at_frame(original,frame) if original is not p else dict(p)
        transform,enabled,opacity=shape_transform(shape,p,w,h,frame)
        if not enabled:continue
        pts=sample_shape(transform_points(shape['points'],transform,w,h))
        layer=np.zeros((h*ss,w*ss),np.float32)
        if len(pts)>=3:cv2.fillPoly(layer,[np.round(np.array(pts)*[w*ss,h*ss]).astype(np.int32)],1.)
        layer=cv2.resize(layer,(w,h),interpolation=cv2.INTER_AREA)
        if shape.get('feather',0)>0:layer=cv2.GaussianBlur(layer,(0,0),max(.01,shape['feather']))
        if shape.get('invert'):layer=1-layer
        layer*=opacity;op=shape.get('shape_operation','max')
        if op=='max':mask=np.maximum(mask,layer)
        elif op=='add':mask=np.clip(mask+layer,0,1)
        elif op=='subtract':mask=np.clip(mask-layer,0,1)
        elif op=='intersect':mask*=layer
        else:raise ValueError('Operacion de forma invalida: '+op)
    return mask

def render_mask(p,w,h,frame):
    if not p.get('_samples'):return raster(p,w,h,frame)
    result=np.zeros((h,w),np.float32)
    for sample,time in zip(p['_samples'],p['_sample_frames']):result+=raster(sample,w,h,time)/len(p['_samples'])
    return result
