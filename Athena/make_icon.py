"""Generate Athena .ico file — navy circle with white 'A'."""
from PIL import Image, ImageDraw, ImageFont
import os

SIZES = [16, 32, 48, 64, 128, 256]
NAVY  = (10, 37, 64)
GOLD  = (196, 146, 42)
WHITE = (255, 255, 255)

out = r"C:\Users\huann\LatitudeMedTech\Athena\athena.ico"

frames = []
for sz in SIZES:
    img  = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Navy circle
    pad = max(1, sz // 12)
    draw.ellipse([pad, pad, sz - pad, sz - pad], fill=NAVY)

    # Gold accent arc at bottom
    arc_h = sz // 5
    draw.arc([pad*2, sz - arc_h - pad, sz - pad*2, sz - pad],
             start=0, end=180, fill=GOLD, width=max(1, sz // 16))

    # White "A" — use default bitmap font for small sizes, scale up for large
    letter = "A"
    font_size = int(sz * 0.55)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/calibrib.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (sz - tw) // 2 - bbox[0]
    ty = (sz - th) // 2 - bbox[1] - sz // 12
    draw.text((tx, ty), letter, fill=WHITE, font=font)

    frames.append(img)

frames[0].save(out, format="ICO", sizes=[(s, s) for s in SIZES],
               append_images=frames[1:])
print(f"Icon saved: {out}")
