import unittest,sys
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'desktop'))
from color_ui import display_processor
from viewer import display_pixels

class ColorTests(unittest.TestCase):
    def test_ocio_display_and_alpha(self):
        from runtime import engine_path
        config=Path(engine_path()).parent/'4.5/datafiles/colormanagement/config.ocio'
        if not config.is_file():self.skipTest('Blender config fixture not available')
        processor=display_processor(str(config),'sRGB','Standard')
        source=np.array([[[.25,.25,.25,.5]]],np.float32);before=source.copy()
        a=display_pixels(source,transform='OCIO',ocio_processor=processor)
        b=display_pixels(source,transform='sRGB')
        np.testing.assert_allclose(a,b,atol=1);np.testing.assert_array_equal(source,before)
        self.assertGreater(int(a[0,0,0]),100)
