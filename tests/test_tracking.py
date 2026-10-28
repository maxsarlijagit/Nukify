import sys,unittest,tempfile,json
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
from tracking import analyze,cv2


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.directory=Path(tempfile.mkdtemp(prefix='nukify-tracking-'))
        rng=np.random.default_rng(42)
        self.base=rng.integers(0,256,(240,320),np.uint8)
        self.base=cv2.GaussianBlur(self.base,(3,3),.7)
        self.path=str(self.directory/'plate_####.png')

    def write(self,frame,image):
        cv2.imencode('.png',image)[1].tofile(str(self.directory/f'plate_{frame:04d}.png'))

    def test_translation_both_directions(self):
        for frame in range(1,10):
            t=frame-5;self.write(frame,cv2.warpAffine(self.base,np.float32([[1,0,t*2],[0,1,t]]),(320,240)))
        r=analyze(dict(kind='Tracker2D',path=self.path,reference=5,first=1,last=9,tracks=[[.4,.4],[.65,.65]]))
        xs=r['animation']['x']['keys'];ys=r['animation']['y']['keys']
        for f,v in xs:self.assertAlmostEqual(v,(f-5)*2,delta=.2)
        for f,v in ys:self.assertAlmostEqual(v,-(f-5),delta=.2)

    def test_planar_perspective(self):
        for frame in range(1,9):
            t=frame-1;m=np.array([[1+.001*t,.001*t,t],[.001*t,1.,.5*t],[.00001*t,.00002*t,1.]])
            self.write(frame,cv2.warpPerspective(self.base,m,(320,240)))
        corners=[[.2,.2],[.8,.2],[.8,.8],[.2,.8]]
        r=analyze(dict(kind='PlanarTracker',path=self.path,reference=1,first=1,last=8,corners=corners))
        got=np.array(r['records'][8]['matrix']);expected=np.array([[1.007,.007,7],[.007,1.,3.5],[.00007,.00014,1.]])
        pts=np.array([[[64.,48.]],[[256.,48.]],[[256.,192.]],[[64.,192.]]],np.float32)
        error=np.linalg.norm(cv2.perspectiveTransform(pts,got)-cv2.perspectiveTransform(pts,expected),axis=2)
        self.assertLess(float(error.max()),1.)

    def test_loss_is_not_success(self):
        self.write(1,self.base);self.write(2,np.zeros_like(self.base))
        with self.assertRaisesRegex(ValueError,'perdido'):
            analyze(dict(kind='Tracker2D',path=self.path,reference=1,first=1,last=2,tracks=[[.4,.4]]))

if __name__=='__main__':unittest.main()
