import copy
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from viewer import display_pixels
from live_engine import fingerprint
from model import demo

class ViewerTests(unittest.TestCase):
    def test_display_controls_do_not_mutate_hdr(self):
        data = np.array([[[2., -.2, .18, .4]]], dtype=np.float32)
        original = data.copy()
        display_pixels(data, exposure=3, gamma=2)
        np.testing.assert_array_equal(data, original)

    def test_linear_alpha_ignores_rgb_transform(self):
        data = np.array([[[2., -.2, .18, .5]]], dtype=np.float32)
        np.testing.assert_array_equal(display_pixels(data, 'A', 10, 3), [[[128,128,128]]])

    def test_cache_ignores_layout_but_tracks_parameters_and_frame(self):
        g = demo(Path(__file__).resolve().parents[1] / 'assets')
        g['blender'] = 'test'
        before = fingerprint(g, 'Merge1', 1, 2)
        g['nodes'][0]['x'] += 50
        self.assertEqual(before, fingerprint(g, 'Merge1', 1, 2))
        self.assertNotEqual(before, fingerprint(g, 'Merge1', 2, 2))
        g['nodes'][2]['params']['exposure'] = 1
        self.assertNotEqual(before, fingerprint(g, 'Merge1', 1, 2))

if __name__ == '__main__':
    unittest.main()
