#!/usr/bin/env python3
"""Generate JobHuntKit's GitHub social-preview card (1280x640).

Maintainer tooling, not user tooling — it lives in .github/ rather than scripts/ because it
only ever produces *this* repo's own metadata image. A stranger cloning JobHuntKit has no use
for it.

GitHub's social preview accepts exactly one image and has no light/dark variant support (the
card is a plain OpenGraph image; feeds render it as-is). Both themes are generated anyway:
the dark one ships as the live card, and the light one is here in case a README banner ever
wants a `<picture>` + `prefers-color-scheme` pair, which *is* supported.

Usage:
    python .github/make_social_card.py                  # both themes
    python .github/make_social_card.py --theme light    # one
    python .github/make_social_card.py --out /tmp       # elsewhere

Requires a Chromium-family browser, found via engine/lib.sh's find_browser (same helper every
renderer uses; honors $BROWSER_BIN).
"""

import argparse
import base64
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FONTS = os.path.join(REPO, "engine", "render-support", "fonts")
CV_PNG = os.path.join(REPO, "examples", "demo", "output", "cv-minimal.png")

WIDTH, HEIGHT = 1280, 640

THEMES = {
    "dark": {
        "file": "social-preview.png",
        "bg": "#0d1017",
        "glow_a": "rgba(96,132,255,0.16)",
        "glow_b": "rgba(120,220,200,0.07)",
        "grid": "rgba(255,255,255,0.028)",
        "kicker": "#6b7bd6",
        "title": "#f4f6fb",
        "tagline": "#9fabc4",
        "meta": "#5c6782",
        "meta_strong": "#8792ad",
        "paper_ring": "rgba(255,255,255,0.07)",
        "paper_shadow": "0 44px 90px rgba(0,0,0,0.62), 0 10px 26px rgba(0,0,0,0.42)",
        "fade_to": "rgba(13,16,23,0.92)",
    },
    "light": {
        "file": "social-preview-light.png",
        "bg": "#fbfcfd",
        "glow_a": "rgba(79,91,213,0.10)",
        "glow_b": "rgba(20,160,140,0.05)",
        "grid": "rgba(15,23,42,0.035)",
        "kicker": "#4f5bd5",
        "title": "#0b0d12",
        "tagline": "#59627a",
        "meta": "#8b93a6",
        "meta_strong": "#454d60",
        "paper_ring": "rgba(15,23,42,0.12)",
        "paper_shadow": "0 34px 70px rgba(15,23,42,0.20), 0 8px 20px rgba(15,23,42,0.10)",
        "fade_to": "rgba(251,252,253,0.92)",
    },
}


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def font_face(family, weight, filename):
    src = b64(os.path.join(FONTS, filename))
    return (
        "@font-face {\n"
        f"  font-family: '{family}';\n"
        f"  font-weight: {weight};\n"
        "  font-style: normal;\n"
        f"  src: url(data:font/woff2;base64,{src}) format('woff2');\n"
        "}"
    )


def find_browser():
    """Reuse engine/lib.sh's discovery rather than reimplementing it here."""
    lib = os.path.join(REPO, "engine", "lib.sh").replace("\\", "/")
    try:
        out = subprocess.run(
            ["bash", "-c", f'. "{lib}" && find_browser'],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        sys.exit(f"could not locate a browser via engine/lib.sh: {exc}")
    path = out.stdout.strip()
    if not path:
        sys.exit("engine/lib.sh's find_browser returned nothing — set BROWSER_BIN")
    # lib.sh runs under Git Bash and answers in MSYS form (/c/Program Files/...), which
    # Windows Python can't hand to CreateProcess. Convert /<drive>/ back to <DRIVE>:/.
    if os.name == "nt" and len(path) > 2 and path[0] == "/" and path[2] == "/":
        path = f"{path[1].upper()}:/{path[3:]}"
    return path


def build_html(theme):
    t = THEMES[theme]
    faces = "\n".join([
        font_face("Plex Sans", 400, "IBMPlexSans-Regular.woff2"),
        font_face("Plex Sans", 600, "IBMPlexSans-SemiBold.woff2"),
        font_face("Plex Mono", 400, "IBMPlexMono-Regular.woff2"),
        font_face("Plex Mono", 600, "IBMPlexMono-SemiBold.woff2"),
    ])
    return f"""<!doctype html>
<meta charset="utf-8">
<style>
{faces}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {WIDTH}px; height: {HEIGHT}px; overflow: hidden; }}
body {{
  position: relative;
  background: {t["bg"]};
  background-image:
    radial-gradient(900px 520px at 88% 50%, {t["glow_a"]}, transparent 62%),
    radial-gradient(680px 420px at 4% 8%, {t["glow_b"]}, transparent 60%);
  font-family: 'Plex Sans', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}}
body::before {{
  content: '';
  position: absolute; inset: 0;
  background-image:
    linear-gradient({t["grid"]} 1px, transparent 1px),
    linear-gradient(90deg, {t["grid"]} 1px, transparent 1px);
  background-size: 48px 48px;
}}
/* left: 220px, not the 76px this started at. Two reasons, both measured against GitHub's own
   repository-open-graph-template.png, whose red guides mark a safe zone of x 80..1200,
   y 80..560. At 76px the text sat just outside the left guide; more importantly, a square
   centre crop (x 320..960, which is what chat apps use for small link thumbnails) cut the
   title in half. Shifting right keeps the left-aligned composition and the angled CV bleeding
   off the right edge, while putting most of the title inside that crop band. */
.copy {{
  position: absolute; left: 220px; top: 50%;
  transform: translateY(-50%); width: 640px; z-index: 2;
}}
.mark {{
  font-family: 'Plex Mono', monospace; font-size: 15px; font-weight: 600;
  letter-spacing: 0.22em; text-transform: uppercase;
  color: {t["kicker"]}; margin-bottom: 22px;
}}
h1 {{
  font-size: 82px; font-weight: 600; letter-spacing: -0.028em;
  line-height: 1; color: {t["title"]}; margin-bottom: 22px;
}}
.tagline {{
  font-size: 35px; font-weight: 400; line-height: 1.28;
  letter-spacing: -0.012em; color: {t["tagline"]};
}}
/* bottom: 90px, not 62px — at 62px this line rendered at y 560..575, straddling the template's
   bottom guide at y=560 and running 15px past it. It carries the one-line pitch, so it's the
   worst thing on the card to have cropped. */
.meta {{
  position: absolute; left: 220px; bottom: 90px; z-index: 2;
  font-family: 'Plex Mono', monospace; font-size: 17px;
  letter-spacing: 0.02em; color: {t["meta"]};
}}
.meta b {{ color: {t["meta_strong"]}; font-weight: 400; }}
/* The CV is texture, not content — it signals "this makes a clean document" without asking
   anyone to read 3px type in a feed thumbnail. */
.paper {{
  position: absolute; right: -46px; top: 50%; width: 352px;
  transform: translateY(-50%) rotate(-7deg);
  border-radius: 7px; overflow: hidden; z-index: 1;
  box-shadow: {t["paper_shadow"]}, 0 0 0 1px {t["paper_ring"]};
}}
.paper img {{ display: block; width: 100%; }}
.paper::after {{
  content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 120px;
  background: linear-gradient(transparent, {t["fade_to"]});
}}
</style>
<div class="copy">
  <div class="mark">Open source &middot; MIT</div>
  <h1>JobHuntKit</h1>
  <div class="tagline">Job hunting made easier.</div>
</div>
<div class="meta">
  <b>Markdown in, tailored PDF out.</b> &nbsp;Agent-driven or entirely by hand.
</div>
<div class="paper"><img src="data:image/png;base64,{b64(CV_PNG)}"></div>
"""


def render(theme, out_dir, browser, scale=1.0, suffix=""):
    """`scale` is Chrome's device pixel ratio, not a CSS change: the page is always laid out at
    WIDTH x HEIGHT CSS pixels, so the design is identical at any scale and only the output
    resolution changes. Every font size in build_html() is an absolute px value tuned for a
    1280-wide canvas — rendering into a smaller window instead would reflow it into nonsense.
    """
    html_path = os.path.join(out_dir, f".social-card-{theme}.html")
    base = THEMES[theme]["file"]
    png_path = os.path.join(out_dir, base.replace(".png", f"{suffix}.png"))
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html(theme))

    url = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    subprocess.run([
        browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        f"--force-device-scale-factor={scale}",
        f"--screenshot={png_path}", f"--window-size={WIDTH},{HEIGHT}", url,
    ], capture_output=True, check=True)
    os.remove(html_path)
    print(f"  {theme:5s} -> {os.path.relpath(png_path, REPO)} "
          f"({int(WIDTH * scale)}x{int(HEIGHT * scale)})")
    return png_path


# Deliberately matched to GitHub's own auto-generated card, which is PNG 1200x600 at 46KB.
# That card demonstrably gets WhatsApp's large banner layout; this card at 1280x640 PNG (268KB)
# got downgraded to a small square thumbnail, which crops a 2:1 image to nonsense. The exact
# threshold isn't documented anywhere, so rather than guess at one, target the weight of the
# image that is known to work. 1200x600 q70 lands at ~42KB.
SHARE_SIZE = (1200, 600)
SHARE_QUALITY = 70


def to_jpeg(png_path, size=SHARE_SIZE, quality=SHARE_QUALITY):
    """PNG -> the JPEG that actually gets uploaded. See SHARE_SIZE for why these numbers.

    The PNG stays the high-fidelity archive; this is the share artifact. At q70 the title and
    subtitle are still crisp and the CV reads as the texture it's meant to be — it is only ever
    seen as a link thumbnail, never at 100%.
    """
    try:
        from PIL import Image
    except ImportError:
        sys.exit("--jpeg needs Pillow: pip install pillow")

    jpg_path = os.path.splitext(png_path)[0] + ".jpg"
    img = Image.open(png_path).convert("RGB")
    if img.size != size:
        img = img.resize(size, Image.LANCZOS)
    img.save(jpg_path, "JPEG", quality=quality, optimize=True, progressive=True)
    kb = os.path.getsize(jpg_path) / 1024
    print(f"        -> {os.path.relpath(jpg_path, REPO)} "
          f"({size[0]}x{size[1]}, q{quality}, {kb:.0f} KB — GitHub's own card is 46 KB)")
    return jpg_path


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--theme", choices=["light", "dark", "both"], default="both")
    ap.add_argument("--out", default=HERE, help="output directory (default: .github/)")
    ap.add_argument("--half", action="store_true",
                    help="also emit 640x320 '-640' variants. Same 1280x640 layout at half the "
                         "device pixel ratio, so the file is roughly a quarter the size")
    ap.add_argument("--jpeg", action="store_true",
                    help="also emit a full-size .jpg (~80KB vs the PNG's ~270KB). This is the "
                         "one to upload: WhatsApp downgrades a link preview from the large "
                         "banner to a small square thumbnail when the image is heavy, and at "
                         "that size the card is cropped to nonsense. Needs Pillow.")
    args = ap.parse_args()

    if not os.path.isfile(CV_PNG):
        sys.exit(f"missing {CV_PNG} — run `bash demo.sh` first")

    os.makedirs(args.out, exist_ok=True)
    browser = find_browser()
    themes = ["dark", "light"] if args.theme == "both" else [args.theme]
    print(f"browser: {browser}")
    for theme in themes:
        png = render(theme, args.out, browser)
        if args.half:
            render(theme, args.out, browser, scale=0.5, suffix="-640")
        if args.jpeg:
            to_jpeg(png)


if __name__ == "__main__":
    main()
