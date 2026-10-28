# SPDX-License-Identifier: GPL-3.0-or-later
"""OpenCV tracking with forward/backward rejection and explicit loss reports."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'vendor'))
os.environ.setdefault('OPENCV_IO_ENABLE_OPENEXR','1')
import cv2
import numpy as np
from model import sequence_path


def read_gray(path, frame):
    path=sequence_path(path,frame)
    image=cv2.imdecode(np.fromfile(path,np.uint8),cv2.IMREAD_UNCHANGED)
    if image is None:raise ValueError('No se pudo leer '+path)
    if image.ndim==3:image=cv2.cvtColor(image[...,:3],cv2.COLOR_BGR2GRAY)
    if image.dtype!=np.uint8:image=np.clip(image*255,0,255).astype(np.uint8)
    return image


def flow(a,b,points,settings=None):
    settings=settings or {}
    size=min(255,max(5,int(settings.get('pattern_size',31))))|1
    opts=dict(winSize=(size,size),maxLevel=min(8,max(0,int(settings.get('pyramid_levels',4)))),criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,.01))
    q,status,error=cv2.calcOpticalFlowPyrLK(a,b,points.reshape(-1,1,2),None,**opts)
    if q is None:raise ValueError('Tracking perdido: sin correspondencias')
    back,st2,_=cv2.calcOpticalFlowPyrLK(b,a,q,None,**opts)
    if back is None:raise ValueError('Tracking perdido: sin correspondencias inversas')
    distance=np.linalg.norm(back.reshape(-1,2)-points.reshape(-1,2),axis=1)
    valid=status.ravel().astype(bool)&st2.ravel().astype(bool)&(distance<float(settings.get('max_fb_error',1.)))&(error.ravel()<40.)
    valid &= np.linalg.norm(q.reshape(-1,2)-points.reshape(-1,2),axis=1)<float(settings.get('max_step',64.))
    return q.reshape(-1,2),valid,distance


def exclusion_mask(image,polygon):
    mask=np.full(image.shape,255,np.uint8)
    if polygon:
        pts=np.asarray(polygon,np.float32)
        if pts.ndim!=2 or pts.shape[1]!=2 or len(pts)<3 or not np.isfinite(pts).all():raise ValueError('Poligono de exclusion invalido')
        pts*=np.array([image.shape[1],image.shape[0]]);pts[:,1]=image.shape[0]-pts[:,1]
        cv2.fillPoly(mask,[pts.astype(np.int32)],0)
    return mask


def normalized_points(value,count,w,h):
    pts=np.asarray(value,np.float32)
    if pts.shape!=(count,2) or not np.isfinite(pts).all() or np.any(pts<0) or np.any(pts>1):raise ValueError('Correccion: cantidad o coordenadas invalidas')
    pts=pts*np.array([w,h],np.float32);pts[:,1]=h-pts[:,1]
    return pts


def similarity(initial,tracked):
    matrix=np.eye(3)
    if len(initial)==1:matrix[:2,2]=tracked[0]-initial[0]
    else:
        v=initial[1]-initial[0];u=tracked[1]-tracked[0]
        if np.linalg.norm(v)<2:raise ValueError('Los dos tracks estan demasiado cerca')
        a=float(np.dot(v,u)/np.dot(v,v));b=float((v[0]*u[1]-v[1]*u[0])/np.dot(v,v))
        matrix[:2,:2]=[[a,-b],[b,a]];matrix[:2,2]=tracked[0]-matrix[:2,:2]@initial[0]
    return matrix


def features(image,corners,excluded):
    mask=np.zeros_like(image);cv2.fillPoly(mask,[corners.astype(np.int32)],255);mask=cv2.bitwise_and(mask,excluded)
    points=cv2.goodFeaturesToTrack(image,maxCorners=300,qualityLevel=.01,minDistance=5,mask=mask)
    if points is None or len(points)<8:raise ValueError('Planar perdido: menos de ocho features')
    return points.reshape(-1,2)


def analyze(job,progress=lambda info:None):
    reference=job['reference'];first=job['first'];last=job['last']
    if not first<=reference<=last:raise ValueError('Referencia fuera del rango')
    image=read_gray(job['path'],reference);h,w=image.shape;planar=job['kind']=='PlanarTracker'
    excluded=exclusion_mask(image,job.get('exclude_polygon',[]));manual=job.get('manual_points',{})
    if planar:
        corners=normalized_points(job['corners'],4,w,h);points=features(image,corners,excluded)
    else:
        count=len(job['tracks'])
        if count not in (1,2):raise ValueError('Tracker2D: marcar uno o dos puntos')
        points=normalized_points(job['tracks'],count,w,h);corners=None
    initial=points.copy();records={reference:dict(matrix=np.eye(3).tolist(),confidence=1.,points=points.tolist(),manual=False)};failures=[]
    for frames in (range(reference+1,last+1),range(reference-1,first-1,-1)):
        previous=image;current=initial.copy();origin=initial.copy()
        for frame in frames:
            try:
                nxt=read_gray(job['path'],frame)
                if nxt.shape!=image.shape:raise ValueError('El formato cambia')
                correction=manual.get(str(frame),manual.get(frame))
                if correction is not None:
                    adjusted=normalized_points(correction,4 if planar else len(initial),w,h)
                    if planar:
                        matrix=cv2.getPerspectiveTransform(corners.astype(np.float32),adjusted.astype(np.float32))
                        current=features(nxt,adjusted,excluded)
                        origin=cv2.perspectiveTransform(current.reshape(-1,1,2),np.linalg.inv(matrix)).reshape(-1,2)
                    else:current=adjusted;matrix=similarity(initial,current)
                    confidence=1.;fb_error=0.
                else:
                    tracked,valid,fb=flow(previous,nxt,current,job)
                    xy=np.round(tracked).astype(np.int32);inside=(xy[:,0]>=0)&(xy[:,0]<w)&(xy[:,1]>=0)&(xy[:,1]<h)
                    valid &= inside
                    valid[inside] &= excluded[xy[inside,1],xy[inside,0]]>0
                    if planar:
                        tracked=tracked[valid];origin=origin[valid]
                        if len(tracked)<8:raise ValueError('Tracking perdido: menos de ocho features')
                        matrix,inliers=cv2.findHomography(origin,tracked,cv2.RANSAC,2.)
                        if matrix is None or inliers.sum()<6:raise ValueError('Planar perdido')
                        confidence=float(inliers.mean());current=tracked
                    else:
                        if not valid.all():raise ValueError('Track perdido; corregir puntos en este cuadro')
                        matrix=similarity(initial,tracked);current=tracked
                        confidence=float(np.clip(1-fb.max()/max(.0001,float(job.get('max_fb_error',1.))),0,1))
                    fb_error=float(fb.max())
                records[frame]=dict(matrix=matrix.tolist(),confidence=confidence,points=current.tolist(),manual=correction is not None,fb_error=fb_error)
                if planar:
                    dest=cv2.perspectiveTransform(corners.reshape(-1,1,2),matrix).reshape(-1,2)
                    records[frame]['corners']=[[float(x/w),float(1-y/h)] for x,y in dest]
                previous=nxt;progress(dict(frame=frame,confidence=confidence,manual=correction is not None))
            except (ValueError,np.linalg.LinAlgError,cv2.error) as exc:
                if not job.get('allow_partial'):raise ValueError(f'{exc} en frame {frame}') from exc
                failures.append(dict(frame=frame,error=str(exc)));progress(dict(frame=frame,lost=True,error=str(exc)));break
    if planar:records[reference]['corners']=job['corners']
    animation={}
    def put(key,frame,value):animation.setdefault(key,dict(interpolation='linear',keys=[]))['keys'].append([frame,value])
    for frame,r in sorted(records.items()):
        if planar:put('corners',frame,r['corners'])
        else:
            m=np.array(r['matrix']);center=np.array([w/2,h/2,1.]);dest=m@center
            put('x',frame,float(dest[0]-w/2));put('y',frame,float(h/2-dest[1]))
            put('scale',frame,float(np.hypot(m[0,0],m[1,0])))
            put('rotation',frame,float(-np.degrees(np.arctan2(m[1,0],m[0,0]))))
    return dict(ok=True,complete=not failures,failures=failures,animation=animation,records=records,width=w,height=h,reference=reference,path=job['path'],method='LK forward/backward + RANSAC homography' if planar else 'LK forward/backward + similarity')
