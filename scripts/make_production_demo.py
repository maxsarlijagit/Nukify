"""Generate reproducible local test media; these are not production footage."""
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop/vendor'))
import cv2,numpy as np
out=root/'assets/production';out.mkdir(exist_ok=True)
rng=np.random.default_rng(71);texture=rng.integers(30,180,(240,320,3),np.uint8)
texture=cv2.GaussianBlur(texture,(3,3),.7)
cv2.putText(texture,'NUKIFY TRACK',(30,120),cv2.FONT_HERSHEY_SIMPLEX,.7,(240,180,60),2)
for f in range(1,25):
    t=f-1;m=np.float32([[1,0,t],[0,1,t*.5]])
    plate=cv2.warpAffine(texture,m,(320,240),borderMode=cv2.BORDER_REFLECT)
    cv2.imencode('.png',plate)[1].tofile(str(out/f'plate_{f:04d}.png'))
    yy,xx=np.indices((240,320));radius=np.sqrt((xx-150-t)**2+(yy-120)**2)
    alpha=np.clip(42-radius,0,1)[...,None]
    chroma=(alpha*np.array([40,60,230])+(1-alpha)*np.array([25,190,20])).astype(np.uint8)
    cv2.imencode('.png',chroma)[1].tofile(str(out/f'chroma_{f:04d}.png'))
patch=np.zeros((240,320,4),np.uint8);patch[90:150,120:200]=[210,130,50,255]
cv2.putText(patch,'N',(140,135),cv2.FONT_HERSHEY_SIMPLEX,1.,(255,255,255,255),2)
cv2.imencode('.png',patch)[1].tofile(str(out/'insert.png'))
print('Production fixtures written')
