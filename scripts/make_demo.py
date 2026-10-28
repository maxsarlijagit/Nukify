"""Deterministic technical fixtures, not production artwork."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1] / 'assets'
root.mkdir(exist_ok=True)
w, h = 960, 540
bg = Image.new('RGBA', (w, h))
draw = ImageDraw.Draw(bg)
for y in range(h):
    t = y / h
    draw.line((0, y, w, y), fill=(int(24 + 25*t), int(37 + 26*t), int(55 + 25*t), 255))
for x in range(0, w, 60):
    draw.line((x, 0, x, h), fill=(61, 76, 94, 255))
for y in range(0, h, 60):
    draw.line((0, y, w, y), fill=(61, 76, 94, 255))
draw.text((35, 30), 'NUKIFY / TECHNICAL COMPOSITING DEMO', fill=(202, 214, 228, 255), font_size=24)
draw.text((35, 490), 'Read + Exposure + Ellipse Mask + Alpha Over > EXR 32-bit', fill=(168, 186, 203, 255), font_size=18)
bg.save(root / 'background.png')
fg = Image.new('RGBA', (w, h), (0, 0, 0, 0))
pixels = fg.load()
for y in range(135, 405):
    for x in range(345, 615):
        dx, dy = (x - 480) / 135, (y - 270) / 135
        r2 = dx*dx + dy*dy
        if r2 <= 1:
            z = (1-r2)**.5
            light = min(1, max(.13, -.35*dx - .5*dy + .75*z))
            pixels[x,y] = (int(244*light), int(160*light), int(75*light), 255)
fg.save(root / 'foreground.png')
print(root)
