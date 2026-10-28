"""Technical 48-frame moving image sequence for playback validation."""
import math
from pathlib import Path
from PIL import Image
root = Path(__file__).resolve().parents[1] / 'assets'
folder = root / 'sequence'
folder.mkdir(exist_ok=True)
source = Image.open(root / 'foreground.png')
for frame in range(1, 49):
    phase = (frame-1) * math.tau / 48
    image = Image.new('RGBA', source.size)
    image.paste(source, (round(95*math.sin(phase)), round(35*math.sin(2*phase))))
    image.save(folder / f'foreground_{frame:04d}.png')
print('48 frame PNG sequence ready')
