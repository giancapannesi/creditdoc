#!/usr/bin/env python3
import argparse
import os
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont


WIDTH = 1000
HEIGHT = 1500
BG = "#f7fafc"
NAVY = "#17324d"
INK = "#1f2937"
MUTED = "#5f6b7a"
BLUE = "#2563eb"
LIGHT_BLUE = "#e8f1ff"
BORDER = "#d9e2ec"
GREEN = "#0f766e"
MINT = "#ccfbf1"
CYAN = "#38bdf8"
GOLD = "#f59e0b"
WHITE = "#ffffff"

REGULAR = "/usr/share/fonts/truetype/lato/Lato-Regular.ttf"
BOLD = "/usr/share/fonts/truetype/lato/Lato-Bold.ttf"
HEAVY = "/usr/share/fonts/truetype/lato/Lato-Heavy.ttf"


def font(path, size):
    return ImageFont.truetype(path, size=size)


def wrap(draw, text, font_obj, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font_obj)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, text, xy, font_obj, fill, max_width, line_gap=8, max_lines=None):
    lines = wrap(draw, text, font_obj, max_width)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        while " " in lines[-1] and draw.textbbox((0, 0), f"{lines[-1]}...", font=font_obj)[2] > max_width:
            lines[-1] = " ".join(lines[-1].split()[:-1])
        lines[-1] = f"{lines[-1].rstrip(',.')}..."
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font_obj, fill=fill)
        y += font_obj.size + line_gap
    return y


def draw_stethoscope(draw, x, y, size, color):
    scale = size / 64
    def sx(v): return x + v * scale
    def sy(v): return y + v * scale
    width = max(2, int(3.5 * scale))
    draw.ellipse((sx(22), sy(34), sx(42), sy(54)), outline=color, width=width)
    draw.ellipse((sx(28), sy(40), sx(36), sy(48)), fill=color)
    draw.line((sx(22), sy(44), sx(22), sy(22)), fill=color, width=width)
    draw.arc((sx(22), sy(12), sx(42), sy(32)), 180, 360, fill=color, width=width)
    draw.line((sx(42), sy(44), sx(42), sy(22)), fill=color, width=width)
    draw.ellipse((sx(19), sy(7), sx(25), sy(13)), fill=color)
    draw.ellipse((sx(39), sy(7), sx(45), sy(13)), fill=color)
    draw.line((sx(22), sy(12), sx(32), sy(16), sx(42), sy(12)), fill=color, width=max(2, int(3 * scale)), joint="curve")


def logo(draw, x, y, color, scale=1.0):
    draw_stethoscope(draw, x - int(14 * scale), y - int(8 * scale), int(88 * scale), color)
    draw.text((x + int(66 * scale), y + int(9 * scale)), "CreditDoc", font=font(HEAVY, int(41 * scale)), fill=color)


def logo_png(color):
    safe = color.replace("#", "")
    out = f"/tmp/creditdoc-site-logo-{safe}.png"
    if os.path.exists(out):
        return out
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="360" height="72" viewBox="0 0 360 72">
  <svg x="0" y="10" width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6 6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"></path>
    <path d="M8 15v1a6 6 0 0 0 6 6 6 6 0 0 0 6-6v-4"></path>
    <circle cx="20" cy="10" r="2"></circle>
  </svg>
  <text x="65" y="50" font-family="Lato, Arial, sans-serif" font-size="42" font-weight="800" fill="{color}">CreditDoc</text>
</svg>"""
    svg_path = f"/tmp/creditdoc-site-logo-{safe}.svg"
    with open(svg_path, "w", encoding="utf8") as handle:
        handle.write(svg)
    subprocess.run(["rsvg-convert", svg_path, "-o", out], check=True)
    return out


def paste_logo(image, x, y, width, color):
    logo_img = Image.open(logo_png(color)).convert("RGBA")
    height = int(logo_img.height * (width / logo_img.width))
    logo_img = logo_img.resize((width, height), Image.Resampling.LANCZOS)
    image.paste(logo_img, (x, y), logo_img)


def draw_bar_panel(draw, x, y):
    draw.rounded_rectangle((x, y, x + 355, y + 510), radius=42, fill=WHITE, outline="#bcd3ea", width=4)
    draw.rounded_rectangle((x + 30, y + 45, x + 325, y + 117), radius=23, fill=NAVY)
    draw.text((x + 55, y + 65), "Loan snapshot", font=font(BOLD, 27), fill=WHITE)
    draw.text((x + 40, y + 155), "Est. payment", font=font(BOLD, 23), fill=MUTED)
    draw.text((x + 40, y + 190), "$4,821", font=font(HEAVY, 54), fill=NAVY)
    draw.text((x + 220, y + 212), "/mo", font=font(BOLD, 27), fill=MUTED)
    for idx, (label, pct, color) in enumerate([("Principal", 0.80, BLUE), ("Fees", 0.42, GOLD), ("DSCR", 0.66, GREEN)]):
        row_y = y + 297 + idx * 62
        draw.text((x + 40, row_y), label, font=font(BOLD, 22), fill=INK)
        draw.rounded_rectangle((x + 40, row_y + 32, x + 300, row_y + 49), radius=9, fill="#e5edf5")
        draw.rounded_rectangle((x + 40, row_y + 32, x + 40 + int(260 * pct), row_y + 49), radius=9, fill=color)
    draw.rounded_rectangle((x + 40, y + 473, x + 300, y + 500), radius=13, fill=LIGHT_BLUE)
    draw.text((x + 78, y + 475), "Compare first", font=font(BOLD, 19), fill=BLUE)


def compact_url(url):
    return url.replace("https://www.", "").replace("https://", "").rstrip("/")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--kind", default="Tool")
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--use-cases", default="")
    parser.add_argument("--url", required=True)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    for y in range(0, 665):
        ratio = y / 665
        r = int(23 * (1 - ratio) + 18 * ratio)
        g = int(50 * (1 - ratio) + 62 * ratio)
        b = int(77 * (1 - ratio) + 120 * ratio)
        draw.line((0, y, WIDTH, y), fill=(r, g, b))
    draw.polygon([(682, 0), (1000, 0), (1000, 612), (760, 664), (640, 350)], fill=BLUE)
    draw.polygon([(0, 604), (1000, 464), (1000, 720), (0, 736)], fill="#edf6ff")

    draw.rounded_rectangle((58, 52, 390, 132), radius=24, fill=WHITE)
    paste_logo(image, 82, 62, 250, BLUE)

    draw.rounded_rectangle((70, 205, 275, 258), radius=26, fill="#dbeafe")
    draw.text((99, 217), f"FREE {args.kind.upper().split()[0]}", font=font(BOLD, 25), fill=BLUE)

    draw_wrapped(draw, args.title, (70, 305), font(HEAVY, 50), WHITE, 470, line_gap=5, max_lines=3)
    draw_wrapped(draw, args.summary, (72, 490), font(REGULAR, 29), "#dbeafe", 410, line_gap=7, max_lines=2)

    draw_bar_panel(draw, 575, 175)

    card_y = 730
    draw.rounded_rectangle((70, card_y, 930, 1348), radius=34, fill=WHITE, outline=BORDER, width=3)
    paste_logo(image, 642, 755, 175, BLUE)
    draw.text((110, 785), "Plan the numbers first", font=font(HEAVY, 42), fill=NAVY)

    cases = [item.strip() for item in args.use_cases.split("|") if item.strip()][:4]
    fallback = ["Monthly payment", "Total cost", "Fees", "Cash-flow view"]
    labels = cases + fallback[len(cases):]
    y = 865
    for i, label in enumerate(labels[:4]):
        color = [BLUE, GREEN, GOLD, CYAN][i]
        sub = ["Know the repayment pressure.", "See the final balance clearly.", "Add fees into the real cost.", "Check cash-flow support."][i]
        draw.rounded_rectangle((112, y, 172, y + 58), radius=18, fill=LIGHT_BLUE if color != GREEN else MINT)
        draw.line((130, y + 33, 144, y + 46, 160, y + 16), fill=color, width=6)
        draw_wrapped(draw, label[:45], (195, y - 1), font(BOLD, 31), INK, 620, max_lines=1)
        draw.text((195, y + 38), sub, font=font(REGULAR, 24), fill=MUTED)
        y += 96

    draw.rounded_rectangle((110, 1246, 890, 1325), radius=30, fill=BLUE)
    draw.text((190, 1265), "Use the free resource", font=font(HEAVY, 36), fill=WHITE)

    draw.rectangle((0, 1390, WIDTH, HEIGHT), fill=NAVY)
    paste_logo(image, 76, 1417, 150, WHITE)
    draw.text((250, 1420), compact_url(args.url), font=font(BOLD, 27), fill=WHITE)

    image.save(args.out, "PNG", optimize=True)
    print(args.out)


if __name__ == "__main__":
    main()
