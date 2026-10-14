"""Trace the official raster into transparent, independently animated SVG layers.

Build-only dependencies: Pillow, numpy, opencv-python-headless. No browser library.
The original branding asset is never modified. Geometry uses original coordinates.
"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
rgb = np.array(Image.open(ROOT / 'static/branding/ytr-logo.png').convert('RGB'))
r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
y, x = np.indices(r.shape)
dark = (r < 95) & (g < 95) & (b < 95)
blue = (b > 125) & (b > r + 20) & (g > r + 15)
brown = (r > g * 1.35) & (r > b * 1.6) & (g < 120) & (r < 200)
orange = (r > 190) & (g > 65) & (b < 120)
white = (r > 215) & (g > 215) & (b > 215)

def paths(mask):
    contours, _ = cv2.findContours(mask.astype('uint8'), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    result = []
    for contour in contours:
        if abs(cv2.contourArea(contour)) < 3:
            continue
        points = cv2.approxPolyDP(contour, .65, True).reshape(-1, 2)
        result.append('M' + 'L'.join(f'{a},{b}' for a, b in points) + 'Z')
    return ''.join(result)

layers = [
    ('globe', blue, '#8dd9ef'),
    ('frame', brown & (((x - 540) ** 2 + (y - 540) ** 2) > 500 ** 2), '#79330e'),
    ('africa', dark & (y >= 270) & (y < 550), '#17120f'),
    ('cross', dark & (y < 170) & (x > 485) & (x < 595), '#17120f'),
    ('bible', dark & (y < 288) & ~((x > 485) & (x < 595)), '#17120f'),
    ('dove', dark & (y >= 140) & (y < 230) & (x > 485) & (x < 595), '#17120f'),
    ('people', dark & (y >= 550), '#17120f'),
    ('people-detail', brown & (y >= 390) & (y < 855) & (x > 55) & (x < 1020), '#62442d'),
    ('roots', brown & (y >= 850) & (y <= 1035) & (x > 55) & (x < 1020), '#79330e'),
    ('fire', orange & (g < 205), '#ff8b24'),
    ('fire-core', orange & (g >= 205), '#ffe477'),
]
# Retain small enclosed white details (robes, hair, weapons); discard white fields.
count, labels, stats, _ = cv2.connectedComponentsWithStats(white.astype('uint8'))
details = np.zeros_like(white)
for label in range(1, count):
    if 4 < stats[label, cv2.CC_STAT_AREA] < 6000:
        details |= labels == label
layers.append(('details', details & (y > 460) & (y < 860), '#fff4df'))
groups = []
for name, mask, color in layers:
    if name in ('fire', 'fire-core'):
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype('uint8'))
        flames = []
        for label in range(1, count):
            if stats[label, cv2.CC_STAT_AREA] < 8:
                continue
            flames.append(f'<path class="logo-flame" style="--flame-delay:{-(label % 9) * .7}s;--flame-duration:{4 + label % 4}s" fill-rule="evenodd" d="{paths(labels == label)}"/>')
        groups.append(f'<g class="logo-{name}" fill="{color}">' + ''.join(flames) + '</g>')
    else:
        groups.append(f'<g class="logo-{name}" fill="{color}"><path fill-rule="evenodd" d="{paths(mask)}"/></g>')
svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1080" fill="none" focusable="false" class="hero-logo-art">' + ''.join(groups) + '</svg>'
(ROOT / 'static/branding/ytr-logo-layered.svg').write_text(svg, encoding='utf-8')
(ROOT / 'templates/home/partials/hero_logo_art.html').write_text(svg, encoding='utf-8')
print(f'Layered transparent SVG: {len(svg):,} bytes')
