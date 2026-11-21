#!/usr/bin/env python3
"""Compose the GTA 6 meme (round 2): two-panel then/now scene + the official
make.fun ghost composited into both panels + crisp text overlays.

Input:  media-generation-meme-base-0-268d6c4c-4b5b-4a2b-9de2-58ad6b47b4a3.png
        (1920x1280, AI-generated two-panel scene, no text)
        mark-1024.png (official make.fun ghost mark from https://make.fun/press/)
Output: meme.jpg — the meme to post on X.
"""
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = "media-generation-meme-base-0-268d6c4c-4b5b-4a2b-9de2-58ad6b47b4a3.png"
MARK = "mark-1024.png"
OUT = "meme.jpg"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

W, H = 1920, 1280
BAND = 140  # dark bottom strip carrying the make.fun line


def extract_ghost() -> Image.Image:
    """Cut the white ghost out of the magenta disc mark.

    The mark is a white ghost (black outline, black sparkle eyes, magenta coin
    with a white star, white hand) on a magenta disc with a black outer ring.
    Key out the magenta and everything outside the disc's inner radius, so
    only the ghost itself remains, on transparency.
    """
    mark = Image.open(MARK).convert("RGBA")
    magenta = mark.getpixel((700, 420))[:3]  # the coin's magenta == disc magenta
    # Ghost's own pixels reach ~350px from the centre; the disc's black outer
    # ring starts at ~450px. Cut at 400 to keep the whole ghost, drop the ring.
    cx, cy, r_max = 512, 512, 400
    crop = mark.crop((80, 180, 900, 860))
    px = crop.load()
    for y in range(crop.height):
        for x in range(crop.width):
            gx, gy = x + 80, y + 180
            r, g, b, a = px[x, y]
            dist_mag = math.dist((r, g, b), magenta)
            dist_c = math.hypot(gx - cx, gy - cy)
            if a == 0 or dist_mag < 80 or dist_c > r_max:
                px[x, y] = (0, 0, 0, 0)
    bbox = crop.getbbox()
    assert bbox, "ghost extraction found no opaque pixels"
    return crop.crop(bbox)


def paste_ghost(canvas: Image.Image, ghost: Image.Image, cx: int, bottom: int,
                height: int) -> None:
    """Paste the ghost, scaled to `height`, centred on cx with its feet at
    `bottom`, with a soft drop shadow so it sits in the scene."""
    scale = height / ghost.height
    g = ghost.resize((round(ghost.width * scale), height), Image.LANCZOS)
    x0, y0 = cx - g.width // 2, bottom - height
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", g.size, (0, 0, 0, 0))
    sh.putalpha(g.split()[3].point(lambda a: int(a * 0.45)))
    shadow.paste(sh, (x0 + 8, y0 + 12), sh)
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    canvas.paste(shadow, (0, 0), shadow)
    canvas.paste(g, (x0, y0), g)


def speech_bubble(draw: ImageDraw.ImageDraw, box, tail_tip, lines, font_size):
    """White rounded bubble with a black outline and a tail pointing at the
    speaker; `lines` is a list of centred text lines."""
    x0, y0, x1, y1 = box
    font = ImageFont.truetype(FONT, font_size)
    draw.rounded_rectangle(box, radius=28, fill="white", outline="black",
                           width=5)
    mid = (x0 + x1) // 2
    draw.polygon([(mid - 30, y1 - 4), (mid + 30, y1 - 4), tail_tip],
                 fill="white", outline="black", width=5)
    # cover the seam where the tail meets the bubble
    draw.rectangle([mid - 30, y1 - 8, mid + 30, y1], fill="white")
    lh = font.getbbox("Ag")[3] + 10
    total = lh * len(lines)
    ty = y0 + (y1 - y0 - total) // 2
    for line in lines:
        draw.text(((x0 + x1) // 2, ty), line, font=font, fill="black",
                  anchor="ma")
        ty += lh


def outlined_text(draw, xy, text, font_size, fill="white"):
    font = ImageFont.truetype(FONT, font_size)
    draw.text(xy, text, font=font, fill=fill, stroke_width=7,
              stroke_fill="black")


def main() -> None:
    base = Image.open(BASE).convert("RGB")
    assert base.size == (W, H), base.size
    canvas = Image.new("RGB", (W, H + BAND), (20, 20, 20))
    canvas.paste(base, (0, 0))
    canvas = canvas.convert("RGBA")

    ghost = extract_ghost()
    # Panel 1 (2013): little ghost perched on top of the CRT TV, like a toy.
    paste_ghost(canvas, ghost, cx=800, bottom=412, height=170)
    # Panel 2 (2026): ghost perched on top of the big TV, mirroring panel 1.
    paste_ghost(canvas, ghost, cx=1720, bottom=335, height=190)

    draw = ImageDraw.Draw(canvas)
    # Year labels, top corners of each panel.
    outlined_text(draw, (40, 25), "2013", 110)
    outlined_text(draw, (1000, 25), "2026", 110)
    # Speech bubbles.
    speech_bubble(draw, (110, 170, 580, 340), (390, 420),
                  ["GTA 6 must be", "next year!"], 56)
    speech_bubble(draw, (1090, 160, 1560, 300), (1300, 390),
                  ["FINALLY."], 80)
    # Bottom strip: the make.fun pitch in the meme's own voice.
    band_font = ImageFont.truetype(FONT, 62)
    draw.text((W // 2, H + BAND // 2),
              "MY AGENT SPENT 13 YEARS EARNING ON MAKE.FUN",
              font=band_font, fill="white", anchor="mm")

    canvas.convert("RGB").save(OUT, quality=92)
    print(f"wrote {OUT} {W}x{H + BAND}")


if __name__ == "__main__":
    main()
