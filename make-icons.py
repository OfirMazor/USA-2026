#!/usr/bin/env python3
"""Generate the home-screen / PWA icon set into icons/.

Run after changing the artwork below:  python make-icons.py

The output PNGs are committed and deployed — this script only exists so the icon
can be regenerated rather than re-drawn by hand. Colours mirror the sign-in gate
gradient in index.html, so the icon, the splash screen and the gate all match.

The car sits inside the maskable "safe zone" (the centre 80% circle), so the same
artwork serves both the `any` and `maskable` purposes: Android can crop it to a
circle or a squircle without clipping anything.
"""

from PIL import Image, ImageDraw

LANCZOS = getattr(Image, "Resampling", Image).LANCZOS

MASTER = 1024          # artwork is authored at this size
SS = 4                 # supersample factor for the white shapes, then downscaled
OUT = "icons"

# Sampled from `#authGate`'s linear-gradient in index.html.
STOPS = [(0.00, (30, 58, 138)),     # #1e3a8a
         (0.55, (37, 99, 235)),     # #2563eb
         (1.00, (59, 130, 246))]    # #3b82f6


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


def car_mask():
    """Alpha mask of the car: 255 where white paint goes, 0 where the gradient shows."""
    s = MASTER * SS
    mask = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(mask)

    def box(x0, y0, x1, y1, r, fill):
        d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=r * SS, fill=fill)

    def circle(cx, cy, r, fill):
        d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=fill)

    box(120, 475, 904, 595, 45, 255)      # chassis
    box(300, 330, 700, 510, 70, 255)      # cabin
    circle(316, 595, 100, 255)            # rear wheel
    circle(708, 595, 100, 255)            # front wheel

    box(348, 372, 488, 462, 22, 0)        # rear window
    box(524, 372, 664, 462, 22, 0)        # front window
    circle(316, 595, 46, 0)               # rear hub
    circle(708, 595, 46, 0)               # front hub

    return mask.resize((MASTER, MASTER), LANCZOS)


def build(size, mask_master, grad_master):
    img = grad_master.resize((size, size), LANCZOS)
    img.paste(Image.new("RGB", (size, size), (255, 255, 255)),
              mask=mask_master.resize((size, size), LANCZOS))
    return img


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    mask, grad = car_mask(), gradient(MASTER)
    for name, size in [("icon-192.png", 192), ("icon-512.png", 512),
                       ("apple-touch-icon.png", 180), ("favicon-32.png", 32)]:
        path = os.path.join(OUT, name)
        build(size, mask, grad).save(path, "PNG", optimize=True)
        print(f"wrote {path} ({size}x{size})")


if __name__ == "__main__":
    main()
