"""Run with Blender's bundled Python (OpenEXR worker ABI)."""
import sys
import tempfile
import unittest
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'desktop'))
from exr_io import OpenEXR, np, read_layer


def write_fixture(path,values):
    OpenEXR.File({'type':OpenEXR.scanlineimage},
                 {name:np.full((8,8),value,np.float32) for name,value in values.items()}).write(str(path))


class NamedLayersTests(unittest.TestCase):
    def read(self,values,layer='Image'):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.exr'
            write_fixture(path,values)
            return read_layer(path,layer)[0,0]

    def test_source_and_separate_alpha(self):
        values={'Source.red':2.,'Source.green':.4,'Source.blue':.1,'Alpha.red':.5,
                'Basecolor.red':.7,'Basecolor.green':.8,'Basecolor.blue':.9,'Depth.red':10.}
        np.testing.assert_allclose(self.read(values),[2.,.4,.1,.5])
        np.testing.assert_allclose(self.read(values,'Basecolor'),[.7,.8,.9,1.])
        np.testing.assert_allclose(self.read(values,'Depth.red'),[10.,10.,10.,1.])

    def test_root_and_explicit_layer_aliases(self):
        for suffixes in ('RGBA','rgba',('red','green','blue','alpha')):
            for prefix,layer in (('','Image'),('diffuse.','diffuse')):
                values={prefix+c:v for c,v in zip(suffixes,[2.,.4,.1,.5])}
                np.testing.assert_allclose(self.read(values,layer),[2.,.4,.1,.5])

    def test_opaque_and_nested_combined(self):
        np.testing.assert_allclose(self.read({'ViewLayer.Combined.'+c:v for c,v in zip('RGB',[2.,.4,.1])}),[2.,.4,.1,1.])

    def test_root_wins(self):
        values={c:v for c,v in zip('RGBA',[2.,.4,.1,.5])}
        values.update({'Source.'+c:9. for c in ('red','green','blue')})
        np.testing.assert_allclose(self.read(values),[2.,.4,.1,.5])

    def test_ambiguous_and_missing(self):
        values={prefix+'.'+c:1. for prefix in ('diffuse','specular') for c in 'RGB'}
        with self.assertRaisesRegex(ValueError,'seleccionar una capa'):
            self.read(values)
        with self.assertRaisesRegex(ValueError,'no disponible'):
            self.read(values,'missing')
        with self.assertRaisesRegex(ValueError,'seleccionar una capa'):
            self.read({'Source.red':1.})


if __name__=='__main__':
    if '--fixture' in sys.argv:
        out=root/'validation/exr';out.mkdir(parents=True,exist_ok=True)
        write_fixture(out/'named_layers.exr',{'Source.red':2.,'Source.green':.4,'Source.blue':.1,
                      'Alpha.red':.5,'Basecolor.red':.7,'Basecolor.green':.8,'Basecolor.blue':.9})
    else:
        unittest.main()
