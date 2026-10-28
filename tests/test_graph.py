import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from model import demo, connect, ordered, sequence_path

class GraphTests(unittest.TestCase):
    def setUp(self):
        self.g = demo(Path(__file__).resolve().parents[1] / 'assets')

    def test_cycle_rejected_without_mutation(self):
        before = copy.deepcopy(self.g)
        with self.assertRaisesRegex(ValueError, 'ciclo'):
            connect(self.g, 'Merge1', 'Color1', 'Image')
        self.assertEqual(before, self.g)

    def test_type_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            connect(self.g, 'Read1', 'Merge1', 'Mask')

    def test_missing_frame_fails_before_render(self):
        self.g['nodes'][0]['params']['path'] = 'absent_####.exr'
        with self.assertRaisesRegex(ValueError, 'archivo no encontrado'):
            ordered(self.g, 'Write1', 34)

    def test_complete_demo_topological_order(self):
        result = [n['id'] for n in ordered(self.g, 'Write1')]
        self.assertLess(result.index('Read2'), result.index('Color1'))
        self.assertLess(result.index('Mask1'), result.index('Merge1'))
        self.assertEqual(result[-1], 'Write1')

    def test_sequence(self):
        self.assertEqual(sequence_path('plate_####.exr', 23), 'plate_0023.exr')

if __name__ == '__main__':
    unittest.main()
