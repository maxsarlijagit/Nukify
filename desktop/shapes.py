# SPDX-License-Identifier: GPL-3.0-or-later
def sample_shape(points, steps=16):
    """Points [x,y,in_x,in_y,out_x,out_y], normalized bottom-left coordinates."""
    if len(points)<3: return points
    result=[]
    for i,a in enumerate(points):
        b=points[(i+1)%len(points)]
        p0=a[:2];p1=a[4:6] if len(a)>=6 else p0
        p3=b[:2];p2=b[2:4] if len(b)>=6 else p3
        for j in range(steps):
            t=j/steps;u=1-t
            result.append([u**3*p0[k]+3*u*u*t*p1[k]+3*u*t*t*p2[k]+t**3*p3[k] for k in (0,1)])
    return result
