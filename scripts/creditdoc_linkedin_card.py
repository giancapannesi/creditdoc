#!/usr/bin/env python3
import argparse
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont


WIDTH = 1200
HEIGHT = 627
BG = "#f7fafc"
NAVY = "#17324d"
INK = "#1f2937"
MUTED = "#5f6b7a"
BLUE = "#2563eb"
LIGHT_BLUE = "#e8f1ff"
BORDER = "#d9e2ec"
GREEN = "#0f766e"


def font(path, size):
    return ImageFont.truetype(path, size=size)


REGULAR = "/usr/share/fonts/truetype/lato/Lato-Regular.ttf"
BOLD = "/usr/share/fonts/truetype/lato/Lato-Bold.ttf"
HEAVY = "/usr/share/fonts/truetype/lato/Lato-Heavy.ttf"


def draw_wrapped(draw, text, xy, font_obj, fill, max_width, line_gap=8, max_lines=None):
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
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines[-1] and draw.textbbox((0, 0), f"{lines[-1]}...", font=font_obj)[2] > max_width:
            lines[-1] = " ".join(lines[-1].split()[:-1])
        lines[-1] = f"{lines[-1]}..."

    x, y = xy
    line_height = font_obj.size + line_gap
    for line in lines:
        draw.text((x, y), line, font=font_obj, fill=fill)
        y += line_height
    return y


def pill(draw, xy, text, font_obj, fill, outline=None, text_fill=NAVY):
    x, y = xy
    padding_x = 18
    padding_y = 8
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    w = bbox[2] - bbox[0] + padding_x * 2
    h = bbox[3] - bbox[1] + padding_y * 2
    draw.rounded_rectangle((x, y, x + w, y + h), radius=18, fill=fill, outline=outline)
    draw.text((x + padding_x, y + padding_y - 2), text, font=font_obj, fill=text_fill)
    return x + w


def draw_metric_panel(draw, x, y, w, h, kind):
    draw.rounded_rectangle((x, y, x + w, y + h), radius=24, fill="white", outline=BORDER, width=2)
    draw.rectangle((x, y, x + w, y + 72), fill=NAVY)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=24, outline=BORDER, width=2)
    draw.text((x + 28, y + 22), "CreditDoc planning view", font=font(BOLD, 24), fill="white")

    labels = {
        "Tool": ["Payment", "Fees", "Cash flow", "Compare"],
        "Course": ["Reports", "Scores", "Debt", "Disputes"],
        "Answer": ["Question", "Context", "Risks", "Next steps"],
    }.get(kind, ["Payment", "Fees", "Cash flow", "Compare"])

    start_y = y + 100
    for i, label in enumerate(labels):
        row_y = start_y + i * 56
        color = BLUE if i in (0, 3) else GREEN
        draw.rounded_rectangle((x + 30, row_y, x + 86, row_y + 42), radius=12, fill=LIGHT_BLUE)
        draw.line((x + 46, row_y + 23, x + 58, row_y + 34, x + 74, row_y + 13), fill=color, width=5)
        draw.text((x + 108, row_y + 4), label, font=font(BOLD, 25), fill=INK)
        draw.rectangle((x + 108, row_y + 38, x + w - 34, row_y + 42), fill="#edf2f7")

    draw.rounded_rectangle((x + 30, y + h - 62, x + w - 30, y + h - 20), radius=16, fill=LIGHT_BLUE)
    draw.text((x + 54, y + h - 54), "Free resource", font=font(BOLD, 22), fill=BLUE)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--kind", default="Tool")
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--use-cases", default="")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    # Quiet corporate background bands.
    draw.rectangle((0, 0, WIDTH, 92), fill=NAVY)
    draw.rectangle((0, HEIGHT - 22, WIDTH, HEIGHT), fill=BLUE)
    draw.rounded_rectangle((54, 126, 1146, 570), radius=28, fill="white", outline=BORDER, width=2)

    draw.text((64, 28), "CreditDoc", font=font(HEAVY, 36), fill="white")
    draw.text((250, 36), "Financial tools, courses, and research", font=font(REGULAR, 22), fill="#dbeafe")

    pill(draw, (92, 164), args.kind.upper(), font(BOLD, 20), LIGHT_BLUE, text_fill=BLUE)

    y = 220
    y = draw_wrapped(draw, args.title, (92, y), font(HEAVY, 50), NAVY, 650, line_gap=4, max_lines=2)
    y += 18
    y = draw_wrapped(draw, args.summary, (94, y), font(REGULAR, 24), INK, 660, line_gap=8, max_lines=3)

    if args.use_cases:
        cases = [item.strip() for item in args.use_cases.split("|") if item.strip()][:2]
        y = min(y + 16, 455)
        draw.text((94, y), "Useful for", font=font(BOLD, 21), fill=MUTED)
        y += 34
        for case in cases:
            draw.ellipse((98, y + 9, 112, y + 23), fill=BLUE)
            draw_wrapped(draw, case, (126, y), font(REGULAR, 21), INK, 560, line_gap=4, max_lines=1)
            y += 32

    draw_metric_panel(draw, 795, 150, 300, 375, args.kind)
    draw.text((94, 526), "creditdoc.co", font=font(BOLD, 24), fill=BLUE)
    draw.text((250, 527), "Free, practical planning resources", font=font(REGULAR, 22), fill=MUTED)

    image.save(args.out, "PNG", optimize=True)
    print(args.out)


if __name__ == "__main__":
    main()
