#!/usr/bin/env python3
"""
Ink by Santos - flash plate generator.

Builds the placeholder gallery plates in assets/img as SVG. Every plate is a
guilloche/engraving ornament with a hand-built figure over it, printed on bone
stock with registration marks and a deliberately misregistered red pass.

Swap these out for real photography when it lands - keep the file names and the
gallery markup keeps working.

    python tools/flash-generator.py
"""

from __future__ import annotations

import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "img"

INK = "#0A0A0B"
BONE = "#EFEAE0"
BONE_D = "#E2DACA"
BLOOD = "#C8102E"


# ---------------------------------------------------------------- primitives

def path_from(points, close=False, precision=1):
    """Turn a list of (x, y) into a compact SVG path string."""
    out = []
    for i, (x, y) in enumerate(points):
        cmd = "M" if i == 0 else "L"
        out.append(f"{cmd}{round(x, precision)} {round(y, precision)}")
    if close:
        out.append("Z")
    return "".join(out)


def epitrochoid(cx, cy, R, r, d, turns=1, steps=760, scale=1.0):
    """Spirograph curve - the backbone of every guilloche ornament here."""
    pts = []
    total = 2 * math.pi * turns
    for i in range(steps + 1):
        t = total * i / steps
        x = (R + r) * math.cos(t) - d * math.cos((R + r) / r * t)
        y = (R + r) * math.sin(t) - d * math.sin((R + r) / r * t)
        pts.append((cx + x * scale, cy + y * scale))
    return pts


def rose(cx, cy, a, k, steps=720, phase=0.0):
    """Rhodonea curve r = a * cos(k * theta)."""
    pts = []
    turns = 2 if (k % 2 == 0 or isinstance(k, float)) else 1
    for i in range(steps + 1):
        t = 2 * math.pi * turns * i / steps
        r = a * math.cos(k * t + phase)
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def lissajous(cx, cy, ax, ay, fx, fy, delta, steps=820):
    pts = []
    for i in range(steps + 1):
        t = 2 * math.pi * i / steps
        pts.append((cx + ax * math.sin(fx * t + delta), cy + ay * math.sin(fy * t)))
    return pts


def ring(cx, cy, r, steps=240, wobble=0.0, seed=1):
    rnd = random.Random(seed)
    pts = []
    for i in range(steps + 1):
        t = 2 * math.pi * i / steps
        rr = r + (rnd.uniform(-wobble, wobble) if wobble else 0)
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    return pts


def ribbon(centerline, widths):
    """Offset a centerline into a closed ribbon - used for the serpent."""
    left, right = [], []
    n = len(centerline)
    for i, (x, y) in enumerate(centerline):
        px, py = centerline[max(i - 1, 0)]
        nx, ny = centerline[min(i + 1, n - 1)]
        dx, dy = nx - px, ny - py
        length = math.hypot(dx, dy) or 1
        ox, oy = -dy / length, dx / length
        w = widths[i]
        left.append((x + ox * w, y + oy * w))
        right.append((x - ox * w, y - oy * w))
    return left + right[::-1]


# ------------------------------------------------------------------- plating

def speckle(w, h, seed, count=520):
    """Paper tooth. Keeps the bone from reading as flat digital fill."""
    rnd = random.Random(seed)
    dots = []
    for _ in range(count):
        x = round(rnd.uniform(0, w), 1)
        y = round(rnd.uniform(0, h), 1)
        r = round(rnd.uniform(0.4, 1.5), 2)
        o = round(rnd.uniform(0.05, 0.22), 2)
        dots.append(f'<circle cx="{x}" cy="{y}" r="{r}" opacity="{o}"/>')
    return f'<g fill="{INK}">' + "".join(dots) + "</g>"


def reg_marks(w, h, pad=34, size=17):
    """Printer's registration crosshairs, one per corner."""
    g = []
    for cx, cy in ((pad, pad), (w - pad, pad), (pad, h - pad), (w - pad, h - pad)):
        g.append(
            f'<g transform="translate({cx} {cy})">'
            f'<path d="M-{size} 0H{size}M0 -{size}V{size}"/>'
            f'<circle r="{size * 0.46}" fill="none"/></g>'
        )
    return (
        f'<g stroke="{INK}" stroke-width="1.1" opacity=".5" fill="none">'
        + "".join(g)
        + "</g>"
    )


def plate_furniture(w, h, code, caption):
    """Border, marks and the mono slugline every plate carries."""
    return f"""
  <rect x="26" y="26" width="{w - 52}" height="{h - 52}" fill="none"
        stroke="{INK}" stroke-width="1.2" opacity=".38"/>
  {reg_marks(w, h)}
  <g font-family="ui-monospace, 'Space Mono', monospace" font-size="15"
     letter-spacing="2.4" fill="{INK}" opacity=".62">
    <text x="46" y="{h - 42}">{code}</text>
    <text x="{w - 46}" y="{h - 42}" text-anchor="end">{caption}</text>
  </g>"""


def halftone_defs():
    return f"""
  <defs>
    <pattern id="ht" width="9" height="9" patternUnits="userSpaceOnUse"
             patternTransform="rotate(22)">
      <circle cx="4.5" cy="4.5" r="2.05" fill="{INK}"/>
    </pattern>
    <pattern id="htf" width="7" height="7" patternUnits="userSpaceOnUse"
             patternTransform="rotate(-15)">
      <circle cx="3.5" cy="3.5" r="1.1" fill="{INK}"/>
    </pattern>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="1"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <mask id="fademask">
      <rect width="100%" height="100%" fill="url(#fade)"/>
    </mask>
  </defs>"""


def write(name, w, h, body, code, caption, seed):
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
     width="{w}" height="{h}" role="img" aria-label="{caption} - placeholder flash plate">
  <title>{caption}</title>
{halftone_defs()}
  <rect width="{w}" height="{h}" fill="{BONE}"/>
  <rect width="{w}" height="{h}" fill="{BONE_D}" opacity=".55"
        mask="url(#fademask)"/>
  {speckle(w, h, seed)}
{body}
{plate_furniture(w, h, code, caption)}
</svg>
"""
    (OUT / name).write_text(svg, encoding="utf-8")
    print(f"  wrote {name}  ({w}x{h})")


# -------------------------------------------------------------------- pieces

def stroke_g(d, width=2.2, opacity=1.0, color=INK, extra=""):
    return (
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
        f'stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}" {extra}/>'
    )


def red_pass(shapes, offset=(7, -6), opacity=".92"):
    """The off-register red plate. Multiply keeps it screen-print honest."""
    dx, dy = offset
    return (
        f'<g transform="translate({dx} {dy})" fill="{BLOOD}" '
        f'opacity="{opacity}" style="mix-blend-mode:multiply">' + shapes + "</g>"
    )


def dagger(cx, cy, length=470, width=44):
    """Blade, guard, grip, pommel - built top-down."""
    top = cy - length / 2
    bot = cy + length / 2
    blade_end = bot - length * 0.32
    guard_y = blade_end
    grip_end = bot - length * 0.10
    d = (
        f"M{cx} {top}"
        f"L{cx + width} {top + length * 0.20}"
        f"L{cx + width * 0.62} {guard_y}"
        f"L{cx - width * 0.62} {guard_y}"
        f"L{cx - width} {top + length * 0.20}Z"
    )
    parts = [stroke_g(d, 5.2)]
    parts.append(stroke_g(f"M{cx} {top + 22}V{guard_y - 16}", 1.6, 0.55))
    parts.append(
        stroke_g(
            f"M{cx - width * 1.95} {guard_y}"
            f"C{cx - width * 1.2} {guard_y - 16},{cx + width * 1.2} {guard_y - 16},"
            f"{cx + width * 1.95} {guard_y}"
            f"C{cx + width * 1.2} {guard_y + 18},{cx - width * 1.2} {guard_y + 18},"
            f"{cx - width * 1.95} {guard_y}Z",
            5.2,
        )
    )
    parts.append(
        stroke_g(
            f"M{cx - width * 0.42} {guard_y + 14}"
            f"V{grip_end}"
            f"M{cx + width * 0.42} {guard_y + 14}V{grip_end}",
            5.2,
        )
    )
    for i in range(4):
        y = guard_y + 26 + i * ((grip_end - guard_y - 30) / 3)
        parts.append(stroke_g(f"M{cx - width * 0.42} {y}H{cx + width * 0.42}", 1.5, 0.5))
    parts.append(
        f'<circle cx="{cx}" cy="{grip_end + 20}" r="{width * 0.58}" fill="none" '
        f'stroke="{INK}" stroke-width="5.2"/>'
    )
    return "".join(parts)


def serpent(cx, cy, height=620, amp=150):
    pts, widths = [], []
    steps = 260
    for i in range(steps + 1):
        t = i / steps
        y = cy - height / 2 + height * t
        x = cx + math.sin(t * math.pi * 2.35) * amp * (1 - t * 0.42)
        pts.append((x, y))
        widths.append(9 + 30 * math.sin(math.pi * min(t * 1.12, 1)) ** 0.75)
    body = path_from(ribbon(pts, widths), close=True)
    parts = [f'<path d="{body}" fill="none" stroke="{INK}" stroke-width="4.6"/>']
    for i in range(6, steps - 20, 11):
        x, y = pts[i]
        w = widths[i] * 0.72
        parts.append(stroke_g(f"M{x - w} {y}Q{x} {y + 13},{x + w} {y}", 1.5, 0.62))
    hx, hy = pts[0]
    parts.append(
        stroke_g(
            f"M{hx - 56} {hy + 10}C{hx - 64} {hy - 46},{hx + 64} {hy - 46},"
            f"{hx + 56} {hy + 10}C{hx + 36} {hy + 50},{hx - 36} {hy + 50},"
            f"{hx - 56} {hy + 10}Z",
            4.6,
        )
    )
    for sx in (-1, 1):
        parts.append(
            f'<circle cx="{hx + sx * 22}" cy="{hy - 8}" r="7" fill="{INK}"/>'
        )
        parts.append(
            stroke_g(f"M{hx + sx * 34} {hy - 24}Q{hx + sx * 22} {hy - 32},"
                     f"{hx + sx * 10} {hy - 24}", 1.6, 0.6)
        )
    # forked tongue
    parts.append(stroke_g(f"M{hx} {hy + 44}v24", 3.0))
    parts.append(stroke_g(f"M{hx} {hy + 68}l-13 17M{hx} {hy + 68}l13 17", 3.0))
    return "".join(parts)


def moth(cx, cy, span=380, drop=250):
    wing = (
        f"M{cx} {cy - drop * 0.30}"
        f"C{cx - span * 0.34} {cy - drop * 0.95},{cx - span} {cy - drop * 0.62},"
        f"{cx - span * 0.92} {cy - drop * 0.06}"
        f"C{cx - span * 0.86} {cy + drop * 0.44},{cx - span * 0.36} {cy + drop * 0.52},"
        f"{cx - span * 0.16} {cy + drop * 0.86}"
        f"C{cx - span * 0.06} {cy + drop * 0.40},{cx} {cy + drop * 0.16},{cx} {cy - drop * 0.30}Z"
    )
    parts = [stroke_g(wing, 4.4)]
    parts.append(
        f'<g transform="translate({cx * 2} 0) scale(-1 1)">{stroke_g(wing, 4.4)}</g>'
    )
    for f in (0.42, 0.64, 0.84):
        parts.append(
            stroke_g(
                f"M{cx - span * 0.06} {cy - drop * 0.16}"
                f"C{cx - span * f * 0.7} {cy - drop * 0.5},{cx - span * f} {cy - drop * 0.1},"
                f"{cx - span * f * 0.94} {cy + drop * 0.30}",
                1.5,
                0.55,
            )
        )
        parts.append(
            f'<g transform="translate({cx * 2} 0) scale(-1 1)">'
            + stroke_g(
                f"M{cx - span * 0.06} {cy - drop * 0.16}"
                f"C{cx - span * f * 0.7} {cy - drop * 0.5},{cx - span * f} {cy - drop * 0.1},"
                f"{cx - span * f * 0.94} {cy + drop * 0.30}",
                1.5,
                0.55,
            )
            + "</g>"
        )
    parts.append(
        f'<ellipse cx="{cx}" cy="{cy + drop * 0.16}" rx="26" ry="{drop * 0.52}" '
        f'fill="none" stroke="{INK}" stroke-width="4.4"/>'
    )
    parts.append(
        f'<ellipse cx="{cx}" cy="{cy - drop * 0.42}" rx="30" ry="26" fill="{INK}"/>'
    )
    parts.append(stroke_g(f"M{cx - 16} {cy - drop * 0.58}C{cx - 70} {cy - drop * 1.0},{cx - 92} {cy - drop * 0.84},{cx - 104} {cy - drop * 1.06}", 3.0))
    parts.append(stroke_g(f"M{cx + 16} {cy - drop * 0.58}C{cx + 70} {cy - drop * 1.0},{cx + 92} {cy - drop * 0.84},{cx + 104} {cy - drop * 1.06}", 3.0))
    return "".join(parts)


def eye(cx, cy, w=210, h=112):
    parts = [
        stroke_g(f"M{cx - w} {cy}Q{cx} {cy - h * 1.55},{cx + w} {cy}", 5.0),
        stroke_g(f"M{cx - w} {cy}Q{cx} {cy + h * 1.55},{cx + w} {cy}", 5.0),
        f'<circle cx="{cx}" cy="{cy}" r="{h * 0.66}" fill="none" stroke="{INK}" stroke-width="4.4"/>',
        f'<circle cx="{cx}" cy="{cy}" r="{h * 0.30}" fill="{INK}"/>',
        f'<circle cx="{cx + h * 0.16}" cy="{cy - h * 0.16}" r="{h * 0.09}" fill="{BONE}"/>',
    ]
    for i in range(16):
        a = 2 * math.pi * i / 16
        r0, r1 = h * 0.40, h * 0.62
        parts.append(
            stroke_g(
                f"M{cx + r0 * math.cos(a)} {cy + r0 * math.sin(a)}"
                f"L{cx + r1 * math.cos(a)} {cy + r1 * math.sin(a)}",
                1.4,
                0.6,
            )
        )
    for i in range(9):
        t = -0.78 + i * 0.195
        x0 = cx + math.sin(t) * w * 0.94
        y0 = cy - abs(math.cos(t)) * h * 0.62 - 6
        parts.append(stroke_g(f"M{x0} {y0}l{math.sin(t) * 34} {-42 + abs(math.sin(t)) * 14}", 2.6))
    return "".join(parts)


def crescent(cx, cy, r=180, bite=0.62):
    return (
        f'<path d="M{cx} {cy - r}A{r} {r} 0 1 0 {cx} {cy + r}'
        f'A{r * bite * 1.42} {r} 0 1 1 {cx} {cy - r}Z" fill="{INK}"/>'
    )


def banner(cx, cy, w=430, h=76):
    d = (
        f"M{cx - w} {cy - h * 0.38}"
        f"Q{cx} {cy - h * 0.95},{cx + w} {cy - h * 0.38}"
        f"L{cx + w} {cy + h * 0.46}"
        f"Q{cx} {cy - h * 0.10},{cx - w} {cy + h * 0.46}Z"
    )
    tail_l = f"M{cx - w} {cy - h * 0.38}l-58 -30 6 46 -52 8 104 40Z"
    tail_r = f"M{cx + w} {cy - h * 0.38}l58 -30 -6 46 52 8 -104 40Z"
    return (
        stroke_g(d, 4.4)
        + stroke_g(tail_l, 4.4)
        + stroke_g(tail_r, 4.4)
    )


def star(cx, cy, r, points=4, sharp=0.34):
    pts = []
    for i in range(points * 2):
        a = math.pi * i / points - math.pi / 2
        rr = r if i % 2 == 0 else r * sharp
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return f'<path d="{path_from(pts, close=True)}" fill="{INK}"/>'


# -------------------------------------------------------------------- plates

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    print("Generating flash plates ->", OUT)

    # 01 - rosette + dagger, the anchor image
    cx, cy = 500, 600
    orn = "".join(
        stroke_g(path_from(epitrochoid(cx, cy, 210, -62, 96 + i * 14, scale=1.0)), 1.25, 0.72)
        for i in range(3)
    )
    orn += stroke_g(path_from(ring(cx, cy, 330)), 1.6, 0.5)
    orn += stroke_g(path_from(ring(cx, cy, 342)), 1.0, 0.35)
    body = (
        red_pass(f'<circle cx="{cx}" cy="{cy}" r="196"/>', (10, -8), ".16")
        + orn
        + dagger(cx, cy, 560, 46)
        + red_pass(f'<circle cx="{cx}" cy="{cy - 250}" r="13"/>', (0, 0), ".9")
    )
    write("flash-01.svg", 1000, 1250, body, "IBS · PLATE 01", "Rosette & Dagger", 11)

    # 02 - serpent down a fine-line column
    cx, cy = 500, 620
    col = "".join(
        stroke_g(f"M{cx - 300 + i * 40} 150V1090", 1.0, 0.20) for i in range(16)
    )
    body = (
        col
        + red_pass(
            f'<circle cx="{cx}" cy="{cy + 60}" r="205"/>',
            (12, -10),
            ".15",
        )
        + serpent(cx, cy, 700, 168)
        + stroke_g(path_from(ring(cx, cy + 240, 118)), 1.3, 0.45)
    )
    write("flash-02.svg", 1000, 1250, body, "IBS · PLATE 02", "Serpent", 23)

    # 03 - moth, square crop
    cx, cy = 500, 500
    halo = "".join(
        stroke_g(path_from(rose(cx, cy, 300 - i * 26, 6, phase=i * 0.22)), 1.15, 0.55)
        for i in range(3)
    )
    body = (
        red_pass(f'<circle cx="{cx}" cy="{cy}" r="250"/>', (-9, 8), ".14")
        + halo
        + moth(cx, cy, 330, 240)
    )
    write("flash-03.svg", 1000, 1000, body, "IBS · PLATE 03", "Moth", 31)

    # 04 - crescent, burst, stars
    cx, cy = 500, 560
    rays = "".join(
        stroke_g(
            f"M{cx + 250 * math.cos(2 * math.pi * i / 44)} {cy + 250 * math.sin(2 * math.pi * i / 44)}"
            f"L{cx + (352 + (i % 3) * 26) * math.cos(2 * math.pi * i / 44)} "
            f"{cy + (352 + (i % 3) * 26) * math.sin(2 * math.pi * i / 44)}",
            1.9,
            0.66,
        )
        for i in range(44)
    )
    body = (
        rays
        + red_pass(f'<circle cx="{cx}" cy="{cy}" r="212"/>', (14, 10), ".18")
        + crescent(cx + 22, cy, 196)
        + star(cx - 232, cy - 232, 46)
        + star(cx + 250, cy + 196, 30)
        + star(cx + 196, cy - 262, 20)
        + stroke_g(path_from(ring(cx, cy, 420)), 1.2, 0.34)
    )
    write("flash-04.svg", 1000, 1250, body, "IBS · PLATE 04", "Crescent", 47)

    # 05 - rose curve, pure ornament
    cx, cy = 500, 500
    layers = "".join(
        stroke_g(path_from(rose(cx, cy, 380 - i * 40, 5 if i % 2 == 0 else 7, phase=i * 0.4)), 1.35, 0.8 - i * 0.1)
        for i in range(5)
    )
    body = (
        red_pass(f'<circle cx="{cx}" cy="{cy}" r="92"/>', (8, -8), ".85")
        + layers
        + f'<circle cx="{cx}" cy="{cy}" r="46" fill="{INK}"/>'
    )
    write("flash-05.svg", 1000, 1000, body, "IBS · PLATE 05", "Rosace", 53)

    # 06 - all-seeing eye in a spirograph
    cx, cy = 500, 580
    spiro = "".join(
        stroke_g(path_from(epitrochoid(cx, cy, 190, -47, 120 + i * 22, scale=1.15)), 1.1, 0.6)
        for i in range(4)
    )
    body = (
        spiro
        + red_pass(f'<circle cx="{cx}" cy="{cy}" r="128"/>', (-11, 9), ".2")
        + eye(cx, cy, 232, 122)
        + stroke_g(f"M{cx - 300} {cy + 330}L{cx} {cy + 150}L{cx + 300} {cy + 330}", 4.0, 0.9)
    )
    write("flash-06.svg", 1000, 1250, body, "IBS · PLATE 06", "Providence", 67)

    # 07 - lissajous knot
    cx, cy = 500, 500
    knot = "".join(
        stroke_g(path_from(lissajous(cx, cy, 360 - i * 12, 320 - i * 12, 3, 4, math.pi / 2 + i * 0.10)), 1.5, 0.85 - i * 0.13)
        for i in range(5)
    )
    body = (
        red_pass(f'<rect x="{cx - 300}" y="{cy - 300}" width="600" height="600"/>', (13, -11), ".1")
        + knot
        + stroke_g(path_from(ring(cx, cy, 402)), 1.0, 0.4)
    )
    write("flash-07.svg", 1000, 1000, body, "IBS · PLATE 07", "Knotwork", 71)

    # 08 - heart, banner, script placeholder
    cx, cy = 500, 520
    heart = (
        f"M{cx} {cy + 170}"
        f"C{cx - 230} {cy + 30},{cx - 180} {cy - 190},{cx - 74} {cy - 156}"
        f"C{cx - 26} {cy - 140},{cx} {cy - 92},{cx} {cy - 60}"
        f"C{cx} {cy - 92},{cx + 26} {cy - 140},{cx + 74} {cy - 156}"
        f"C{cx + 180} {cy - 190},{cx + 230} {cy + 30},{cx} {cy + 170}Z"
    )
    body = (
        "".join(
            stroke_g(path_from(epitrochoid(cx, cy - 20, 170, -43, 92 + i * 18, scale=1.35)), 1.0, 0.42)
            for i in range(3)
        )
        + red_pass(f'<path d="{heart}"/>', (12, -9), ".9")
        + stroke_g(heart, 5.0)
        + banner(cx, cy + 300, 360, 78)
        + f'<g opacity=".55" font-family="ui-monospace, monospace" font-size="20" '
          f'letter-spacing="5" fill="{INK}" text-anchor="middle">'
          f'<text x="{cx}" y="{cy + 316}">YOUR WORDS HERE</text></g>'
    )
    write("flash-08.svg", 1000, 1250, body, "IBS · PLATE 08", "Sacred", 83)

    # 09 - wide landscape, arch + rays (script / lettering slot)
    cx, cy = 700, 420
    arch = f"M{cx - 300} {cy + 250}V{cy - 40}A300 300 0 0 1 {cx + 300} {cy - 40}V{cy + 250}"
    lines = "".join(stroke_g(f"M120 {200 + i * 26}H{cx - 340}", 1.1, 0.28) for i in range(14))
    body = (
        lines
        + red_pass(f'<path d="{arch}Z"/>', (14, -12), ".12")
        + stroke_g(arch, 5.0)
        + "".join(
            stroke_g(f"M{cx - 240 + i * 60} {cy + 250}V{cy - 120 + abs(i - 4) * 26}", 1.6, 0.5)
            for i in range(9)
        )
        + f'<circle cx="{cx}" cy="{cy - 40}" r="74" fill="{INK}"/>'
        + red_pass(f'<circle cx="{cx}" cy="{cy - 40}" r="30"/>', (0, 0), ".95")
    )
    write("flash-09.svg", 1400, 900, body, "IBS · PLATE 09", "Arch", 97)

    # 10 - dense blackwork square
    cx, cy = 500, 500
    dense = "".join(
        stroke_g(path_from(epitrochoid(cx, cy, 220, -31, 150 + i * 6, scale=0.92)), 0.85, 0.5)
        for i in range(9)
    )
    body = (
        f'<circle cx="{cx}" cy="{cy}" r="300" fill="url(#ht)" opacity=".5"/>'
        + dense
        + red_pass(f'<circle cx="{cx}" cy="{cy}" r="120"/>', (-12, 10), ".88")
        + f'<circle cx="{cx}" cy="{cy}" r="112" fill="{INK}"/>'
        + stroke_g(path_from(ring(cx, cy, 356)), 2.4, 0.8)
    )
    write("flash-10.svg", 1000, 1000, body, "IBS · PLATE 10", "Blackwork", 101)

    # 11 - tall fine-line column study
    cx = 500
    body = "".join(
        stroke_g(path_from(rose(cx, 250 + i * 380, 160, 3, phase=i * 0.7)), 1.3, 0.8)
        for i in range(3)
    ) + stroke_g(f"M{cx} 90V1160", 1.0, 0.4) + red_pass(
        f'<circle cx="{cx}" cy="630" r="16"/>', (0, 0), ".9"
    )
    write("flash-11.svg", 1000, 1250, body, "IBS · PLATE 11", "Fine Line", 103)

    # 12 - wide banner study
    cx, cy = 700, 450
    body = (
        "".join(
            stroke_g(path_from(lissajous(cx, cy, 420 - i * 30, 180 - i * 14, 1, 2, math.pi / 2)), 1.2, 0.6)
            for i in range(6)
        )
        + red_pass(f'<rect x="{cx - 430}" y="{cy - 26}" width="860" height="52"/>', (0, 0), ".9")
        + banner(cx, cy, 400, 84)
    )
    write("flash-12.svg", 1400, 900, body, "IBS · PLATE 12", "Script Banner", 107)

    portrait()
    print("done.")


def portrait():
    """Halftone profile for the about page."""
    w, h = 1000, 1250
    cx, cy = 520, 640
    head = (
        f"M{cx - 40} {cy + 330}"
        f"C{cx - 240} {cy + 300},{cx - 250} {cy + 60},{cx - 210} {cy - 60}"
        f"C{cx - 176} {cy - 250},{cx - 40} {cy - 340},{cx + 70} {cy - 306}"
        f"C{cx + 200} {cy - 266},{cx + 244} {cy - 120},{cx + 214} {cy + 30}"
        f"C{cx + 190} {cy + 150},{cx + 150} {cy + 190},{cx + 168} {cy + 250}"
        f"C{cx + 186} {cy + 312},{cx + 120} {cy + 340},{cx + 40} {cy + 332}Z"
    )
    body = (
        f'<g opacity=".22">'
        + "".join(stroke_g(f"M90 {180 + i * 34}H910", 1.0, 1) for i in range(28))
        + "</g>"
        + red_pass(f'<path d="{head}"/>', (16, -13), ".9")
        + f'<path d="{head}" fill="url(#ht)"/>'
        + f'<path d="{head}" fill="none" stroke="{INK}" stroke-width="4.6"/>'
        + stroke_g(f"M{cx - 210} {cy - 60}C{cx - 120} {cy - 30},{cx - 60} {cy - 40},{cx - 20} {cy - 90}", 2.0, 0.6)
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
     width="{w}" height="{h}" role="img" aria-label="Portrait placeholder">
  <title>Portrait placeholder</title>
{halftone_defs()}
  <rect width="{w}" height="{h}" fill="{BONE}"/>
  {speckle(w, h, 7)}
{body}
{plate_furniture(w, h, "IBS · FIG. A", "Portrait")}
</svg>
"""
    (OUT / "portrait.svg").write_text(svg, encoding="utf-8")
    print("  wrote portrait.svg  (1000x1250)")


if __name__ == "__main__":
    build()


# ------------------------------------------------------------- hero + marks

def hero_geometry(cx, cy):
    """Shared geometry so the finished plate and the stencil register exactly."""
    orn = [
        (path_from(epitrochoid(cx, cy - 40, 190, -56, 88 + i * 15, scale=1.0)), 1.3, 0.8)
        for i in range(3)
    ]
    orn.append((path_from(ring(cx, cy - 40, 300)), 1.1, 0.45))
    figure = []
    # dagger
    top, width, length = cy - 40 - 300, 40, 620
    figure.append((
        f"M{cx} {cy - 330}L{cx + width} {cy - 210}L{cx + width * .62} {cy + 120}"
        f"L{cx - width * .62} {cy + 120}L{cx - width} {cy - 210}Z", 4.6, 1))
    figure.append((f"M{cx} {cy - 300}V{cy + 96}", 1.4, .5))
    figure.append((
        f"M{cx - 82} {cy + 120}C{cx - 48} {cy + 104},{cx + 48} {cy + 104},{cx + 82} {cy + 120}"
        f"C{cx + 48} {cy + 140},{cx - 48} {cy + 140},{cx - 82} {cy + 120}Z", 4.6, 1))
    figure.append((f"M{cx - 17} {cy + 136}V{cy + 250}M{cx + 17} {cy + 136}V{cy + 250}", 4.6, 1))
    for i in range(4):
        y = cy + 154 + i * 26
        figure.append((f"M{cx - 17} {y}H{cx + 17}", 1.3, .5))
    figure.append((f"M{cx - 26} {cy + 250}a26 26 0 1 0 52 0a26 26 0 1 0 -52 0", 4.6, 1))
    # banner
    figure.append((
        f"M{cx - 300} {cy + 330}Q{cx} {cy + 282},{cx + 300} {cy + 330}"
        f"L{cx + 300} {cy + 396}Q{cx} {cy + 344},{cx - 300} {cy + 396}Z", 4.0, 1))
    return orn, figure


def hero_plates():
    w, h, cx, cy = 900, 1150, 450, 520
    orn, figure = hero_geometry(cx, cy)

    def render(color, mult, extra_head="", tail=""):
        out = [stroke_g(d, sw * mult, op, color) for d, sw, op in orn]
        out += [stroke_g(d, sw * mult, op, color) for d, sw, op in figure]
        return extra_head + "".join(out) + tail

    stars = "".join(
        f'<path d="M{x} {y - r}L{x + r * .3} {y - r * .3}L{x + r} {y}'
        f'L{x + r * .3} {y + r * .3}L{x} {y + r}L{x - r * .3} {y + r * .3}'
        f'L{x - r} {y}L{x - r * .3} {y - r * .3}Z" fill="{{c}}" opacity=".9"/>'
        for x, y, r in ((150, 210, 30), (770, 330, 20), (120, 800, 18), (800, 880, 26))
    )

    finished = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
     width="{w}" height="{h}" role="img" aria-label="Finished tattoo artwork placeholder">
  <defs>
    <pattern id="hth" width="10" height="10" patternUnits="userSpaceOnUse"
             patternTransform="rotate(24)">
      <circle cx="5" cy="5" r="2.3" fill="{BONE}"/>
    </pattern>
  </defs>
  <circle cx="{cx}" cy="{cy - 40}" r="252" fill="url(#hth)" opacity=".30"/>
  {render(BONE, 1.0)}
  {stars.format(c=BONE)}
</svg>
"""
    stencil = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
     width="{w}" height="{h}" role="img" aria-label="Stencil linework placeholder">
  <g opacity=".2" stroke="{BLOOD}" stroke-width="1">
    {''.join(f'<path d="M60 {120 + i * 46}H840"/>' for i in range(21))}
  </g>
  {render(BLOOD, 0.42)}
  {stars.format(c=BLOOD)}
</svg>
"""
    (OUT / "hero-finished.svg").write_text(finished, encoding="utf-8")
    (OUT / "hero-stencil.svg").write_text(stencil, encoding="utf-8")
    print("  wrote hero-finished.svg / hero-stencil.svg")


def favicon():
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" fill="{INK}"/>
  <path d="M32 8l7 22 22 2-22 2-7 22-7-22-22-2 22-2z" fill="{BLOOD}"/>
  <path d="M32 18v28" stroke="{BONE}" stroke-width="3" stroke-linecap="round"/>
</svg>
"""
    (OUT.parent / "favicon.svg").write_text(svg, encoding="utf-8")
    print("  wrote favicon.svg")


hero_plates()
favicon()
