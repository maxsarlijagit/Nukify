import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
import numpy as np
from exr_io import OpenEXR,load,read_layer,preserve_channels,inspect
out=root/'validation/exr';out.mkdir(parents=True,exist_ok=True)
# Explicit dataWindow, HDR and arbitrary layers roundtrip.
shape=(32,32);channels={c:np.full(shape,v,np.float32) for c,v in zip('RGBA',[2.,.4,.1,.5])}
channels['depth.Z']=np.full(shape,10.,np.float32)
channels['diffuse.R']=np.full(shape,.2,np.float32);channels['diffuse.G']=np.full(shape,.3,np.float32);channels['diffuse.B']=np.full(shape,.4,np.float32)
header={'type':OpenEXR.scanlineimage,'compression':OpenEXR.ZIP_COMPRESSION,'dataWindow':(np.array([4,8],np.int32),np.array([35,39],np.int32)), 'displayWindow':(np.array([0,0],np.int32),np.array([63,63],np.int32)),'test:metadata':'preserved'}
OpenEXR.File(header,channels).write(str(out/'source.exr'))
pixels=read_layer(out/'source.exr','diffuse');assert pixels.shape==(64,64,4)
np.testing.assert_allclose(pixels[9,5],[.2,.3,.4,1.])
OpenEXR.File({'type':OpenEXR.scanlineimage},{c:np.full((64,64),v,np.float32) for c,v in zip('RGBA',[4.,.8,.2,.5])}).write(str(out/'result.exr'))
preserve_channels(out/'result.exr',out/'source.exr')
check=load(out/'result.exr');assert check.header()['test:metadata']=='preserved'
np.testing.assert_array_equal(check.channels()['depth.Z'].pixels,channels['depth.Z'].pixels)
np.testing.assert_array_equal(check.channels()['diffuse.R'].pixels,channels['diffuse.R'].pixels)
np.testing.assert_allclose(check.channels()['R'].pixels,4.)

print('EXR_ROUNDTRIP_OK')
