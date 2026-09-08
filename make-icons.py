#!/usr/bin/env python3
"""Generate the home-screen / PWA icon set into icons/.

Run after changing the artwork below:  python make-icons.py

The output PNGs are committed and deployed — this script only exists so the icon
can be regenerated rather than re-drawn by hand. Colours mirror the sign-in gate
gradient in index.html, so the icon, the splash screen and the gate all match.

The mountain icon sits inside the maskable "safe zone" (the centre 80% circle), so the same
artwork serves both the `any` and `maskable` purposes: Android can crop it to a
circle or a squircle without clipping anything.
"""

from PIL import Image, ImageDraw

LANCZOS = getattr(Image, "Resampling", Image).LANCZOS

MASTER = 1024          # artwork is authored at this size
SS = 4                 # supersample factor for the white shapes, then downscaled
OUT = "icons"

# Green gradient for mountain icon
STOPS = [(0.00, (20, 80, 40)),      # dark green
         (0.55, (30, 120, 60)),     # medium green
         (1.00, (40, 150, 80))]     # light green


def gradient(size):
    """Vertical three-stop gradient, full bleed."""
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        for i in range(len(STOPS) - 1):
            t0, c0 = STOPS[i]
            t1, c1 = STOPS[i + 1]
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0)
                draw.line([(0, y), (size, y)],
                          fill=tuple(round(a + (b - a) * k) for a, b in zip(c0, c1)))
                break
    return img


def mountain_mask():
    """Alpha mask of mountains: 255 where white paint goes, 0 where the gradient shows."""
    s = MASTER * SS
    mask = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(mask)

    # Mountain peaks with green outline effect (drawing as white shapes)
    # Left peak
    left_peak = [(150 * SS, 600 * SS), (300 * SS, 250 * SS), (380 * SS, 450 * SS)]
    d.polygon(left_peak, fill=255)

    # Center peak (tallest)
    center_peak = [(350 * SS, 700 * SS), (512 * SS, 150 * SS), (620 * SS, 500 * SS)]
    d.polygon(center_peak, fill=255)

    # Right peak
    right_peak = [(590 * SS, 550 * SS), (750 * SS, 280 * SS), (850 * SS, 650 * SS)]
    d.polygon(right_peak, fill=255)

    # Snow caps (white tips on peaks)
    d.polygon([(512 * SS, 150 * SS), (485 * SS, 250 * SS), (540 * SS, 250 * SS)], fill=255)
    d.polygon([(300 * SS, 250 * SS), (280 * SS, 320 * SS), (320 * SS, 320 * SS)], fill=255)
    d.polygon([(750 * SS, 280 * SS), (725 * SS, 360 * SS), (775 * SS, 360 * SS)], fill=255)

    return mask.resize((MASTER, MASTER), LANCZOS)


def build(size, mask_master, grad_master):
    img = grad_master.resize((size, size), LANCZOS)
    img.paste(Image.new("RGB", (size, size), (255, 255, 255)),
              mask=mask_master.resize((size, size), LANCZOS))
    return img


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    mask, grad = mountain_mask(), gradient(MASTER)
    for name, size in [("icon-192.png", 192), ("icon-512.png", 512),
                       ("apple-touch-icon.png", 180), ("favicon-32.png", 32)]:
        path = os.path.join(OUT, name)
        build(size, mask, grad).save(path, "PNG", optimize=True)
        print(f"wrote {path} ({size}x{size})")


if __name__ == "__main__":
    main()
