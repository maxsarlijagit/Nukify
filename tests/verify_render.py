"""Run in Blender after worker integration test. Assert EXR content, not just files."""
from pathlib import Path
import bpy
root = Path(__file__).resolve().parents[1]
out = root / 'validation' / 'render'
image = bpy.data.images.load(str(out / 'comp_0001.exr'))
assert tuple(image.size) == (960, 540), tuple(image.size)
assert image.is_float
px = list(image.pixels)
def pixel(x, y):
    start = 4 * (y * 960 + x)
    return px[start:start+4]
center = pixel(480, 270)
corner = pixel(100, 100)
assert center[0] > center[2] * 2, center
assert corner[2] > corner[0], corner
assert abs(center[3] - 1) < .0001
assert abs(corner[3] - 1) < .0001
assert (out / 'comp_0002.exr').is_file()
print('RENDER_PIXELS_OK', center, corner)
