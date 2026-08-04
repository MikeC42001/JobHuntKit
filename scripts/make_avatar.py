#!/usr/bin/env python3
"""make_avatar.py — draws a simple initials-in-a-circle placeholder avatar.

Used once to generate examples/demo/images/avatar.png so the demo persona has a photo without
using a stock image, a real likeness, or anything with a licensing question attached. Not part
of the render pipeline and not run automatically — the PNG it produces is committed, and this
script is only here so the image is reproducible/tweakable rather than an opaque binary.

Requires Pillow (`pip install pillow`) — a one-time dev dependency for this script only, not a
dependency of the engine or any renderer.

Usage:
    python scripts/make_avatar.py "Robin Vale" examples/demo/images/avatar.png
    python scripts/make_avatar.py "Robin Vale" out.png --bg "#D97757" --fg "#FFFFFF" --size 512
"""

import argparse
import sys


def initials(name):
    parts = [p for p in name.split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="full name to derive initials from")
    parser.add_argument("out_path", help="output PNG path")
    parser.add_argument("--size", type=int, default=512, help="square image size in px (default 512)")
    parser.add_argument("--bg", default="#D97757", help="background circle color (default: JobHuntKit ember)")
    parser.add_argument("--fg", default="#FFFFFF", help="initials text color (default: white)")
    args = parser.parse_args()

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("make_avatar: requires Pillow — pip install pillow", file=sys.stderr)
        return 1

    size = args.size
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size, size), fill=args.bg)

    text = initials(args.name)
    font = None
    for candidate_size in (int(size * 0.42),):
        try:
            font = ImageFont.truetype("arialbd.ttf", candidate_size)
        except OSError:
            font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - text_w) / 2 - bbox[0], (size - text_h) / 2 - bbox[1]),
        text, fill=args.fg, font=font,
    )

    img.save(args.out_path)
    print(f"make_avatar: wrote {args.out_path} ({text})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
