# SPDX-License-Identifier: GPL-3.0-or-later
import numpy as np


def planar_output(corners,reference,mode):
    if mode=='cornerpin':return corners
    rows=[];values=[]
    for (x,y),(u,v) in zip(reference,corners):
        rows.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);values.extend([u,v])
    if np.linalg.matrix_rank(rows)<8:raise ValueError('Esquinas planares degeneradas')
    h=np.append(np.linalg.solve(rows,values),1.).reshape(3,3)
    if mode=='stabilize':h=np.linalg.inv(h)
    unit=np.array([[0,0,1],[1,0,1],[1,1,1],[0,1,1]],float)
    projected=unit@h.T
    if np.any(np.abs(projected[:,2])<1e-8):raise ValueError('Proyeccion planar singular')
    return (projected[:,:2]/projected[:,2:]).tolist()
