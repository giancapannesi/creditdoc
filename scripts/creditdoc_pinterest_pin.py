#!/usr/bin/env python3
import argparse
import hashlib
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
SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


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


def draw_roadmap_pin(image, draw, args):
    for y in range(0, HEIGHT):
        ratio = y / HEIGHT
        r = int(248 * (1 - ratio) + 236 * ratio)
        g = int(251 * (1 - ratio) + 246 * ratio)
        b = int(255 * (1 - ratio) + 238 * ratio)
        draw.line((0, y, WIDTH, y), fill=(r, g, b))

    draw.rectangle((0, 0, WIDTH, 176), fill=NAVY)
    paste_logo(image, 72, 52, 250, WHITE)
    draw.rounded_rectangle((712, 54, 926, 118), radius=28, fill=WHITE)
    draw.text((760, 70), "FREE TOOL", font=font(BOLD, 24), fill=BLUE)

    draw.text((70, 235), "SBA Funding", font=font(HEAVY, 60), fill=NAVY)
    draw.text((70, 302), "readiness map", font=font(HEAVY, 60), fill=BLUE)
    draw_wrapped(draw, args.summary, (74, 395), font(REGULAR, 30), MUTED, 820, line_gap=8, max_lines=3)

    draw.rounded_rectangle((70, 545, 930, 982), radius=44, fill=WHITE, outline="#c8d8ea", width=3)
    draw.text((118, 600), "Before you talk to a lender", font=font(HEAVY, 38), fill=NAVY)

    steps = [
        ("1", "Estimate payment", "See the monthly obligation before applying."),
        ("2", "Add fees", "Model SBA fees and total repayment."),
        ("3", "Check cash flow", "Stress-test the payment against revenue."),
    ]
    x_positions = [120, 392, 664]
    for idx, (num, title, body) in enumerate(steps):
        x = x_positions[idx]
        draw.rounded_rectangle((x, 690, x + 216, 908), radius=30, fill=["#eff6ff", "#ecfdf5", "#fff7ed"][idx])
        draw.ellipse((x + 72, 722, x + 144, 794), fill=[BLUE, GREEN, GOLD][idx])
        w = draw.textbbox((0, 0), num, font=font(HEAVY, 36))[2]
        draw.text((x + 108 - w / 2, 735), num, font=font(HEAVY, 36), fill=WHITE)
        draw_wrapped(draw, title, (x + 24, 815), font(BOLD, 24), INK, 168, line_gap=2, max_lines=2)
        draw_wrapped(draw, body, (x + 24, 870), font(REGULAR, 16), MUTED, 168, line_gap=2, max_lines=2)

    draw.line((336, 780, 392, 780), fill="#bfd3ea", width=7)
    draw.line((608, 780, 664, 780), fill="#bfd3ea", width=7)

    cases = [item.strip() for item in args.use_cases.split("|") if item.strip()][:4]
    draw.rounded_rectangle((70, 1035, 930, 1264), radius=38, fill=NAVY)
    draw.text((118, 1074), "Use it for", font=font(HEAVY, 36), fill=WHITE)
    y = 1134
    for idx, label in enumerate(cases):
        x = 118 if idx % 2 == 0 else 545
        if idx == 2:
            y += 70
        draw.ellipse((x, y + 6, x + 28, y + 34), fill=CYAN if idx % 2 == 0 else GOLD)
        draw_wrapped(draw, label, (x + 44, y), font(BOLD, 21), "#eef6ff", 320, line_gap=2, max_lines=2)

    draw.rounded_rectangle((100, 1314, 900, 1390), radius=32, fill=BLUE)
    draw.text((215, 1333), "Open the calculator", font=font(HEAVY, 36), fill=WHITE)

    draw.rectangle((0, 1430, WIDTH, HEIGHT), fill=NAVY)
    paste_logo(image, 72, 1445, 128, WHITE)
    draw.text((250, 1450), compact_url(args.url), font=font(BOLD, 26), fill=WHITE)


def draw_briefing_pin(image, draw, args):
    accent = [BLUE, GREEN, GOLD, CYAN][((args.variant or 0) // 4) % 4]
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill="#f8fafc")
    draw.rectangle((0, 0, 340, HEIGHT), fill=NAVY)
    draw.polygon([(340, 0), (520, 0), (340, HEIGHT)], fill=accent)
    paste_logo(image, 70, 62, 235, WHITE)

    draw.rounded_rectangle((74, 1250, 292, 1320), radius=28, fill=WHITE)
    draw.text((113, 1268), args.kind.upper().split()[0], font=font(BOLD, 24), fill=BLUE)

    draw.text((420, 90), "CreditDoc resource", font=font(BOLD, 28), fill=accent)
    draw_wrapped(draw, args.title, (420, 150), font(HEAVY, 58), NAVY, 500, line_gap=4, max_lines=4)
    draw_wrapped(draw, args.summary, (420, 430), font(REGULAR, 29), MUTED, 470, line_gap=8, max_lines=4)

    cases = [item.strip() for item in args.use_cases.split("|") if item.strip()][:4]
    y = 650
    for idx, label in enumerate(cases):
        color = [BLUE, GREEN, GOLD, CYAN][idx]
        draw.rounded_rectangle((420, y, 910, y + 105), radius=28, fill=WHITE, outline="#d7e3f1", width=2)
        draw.rounded_rectangle((445, y + 24, 500, y + 79), radius=18, fill=color)
        draw.text((465, y + 32), str(idx + 1), font=font(HEAVY, 24), fill=WHITE)
        draw_wrapped(draw, label, (525, y + 25), font(BOLD, 27), INK, 345, line_gap=2, max_lines=2)
        y += 130

    draw.rounded_rectangle((420, 1248, 910, 1340), radius=34, fill=accent)
    draw.text((510, 1272), "Use the free resource", font=font(HEAVY, 30), fill=WHITE)
    draw.text((420, 1428), compact_url(args.url), font=font(BOLD, 25), fill=NAVY)


def draw_checklist_pin(image, draw, args):
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill="#fbf7ef")
    draw.rectangle((0, 0, WIDTH, 118), fill=WHITE)
    paste_logo(image, 64, 32, 258, BLUE)
    draw.rounded_rectangle((695, 34, 920, 86), radius=22, fill="#17324d")
    draw.text((731, 48), "FREE SBA TOOL", font=font(BOLD, 20), fill=WHITE)

    draw.rectangle((0, 118, WIDTH, 456), fill="#f7c948")
    draw.rectangle((0, 456, WIDTH, 592), fill="#17324d")
    draw.text((70, 168), "Two SBA offers", font=font(SERIF_BOLD, 78), fill=NAVY)
    draw.text((70, 258), "can look similar.", font=font(SERIF_BOLD, 70), fill=NAVY)
    draw.text((72, 488), "The payment story may be completely different.", font=font(HEAVY, 34), fill=WHITE)

    def offer_card(x, y, title, payment, fee, total, stripe):
        draw.rounded_rectangle((x, y, x + 385, y + 438), radius=26, fill=WHITE, outline="#dbc186", width=3)
        draw.rectangle((x + 34, y + 36, x + 351, y + 48), fill=stripe)
        draw.text((x + 34, y + 82), title, font=font(HEAVY, 30), fill=NAVY)
        draw.text((x + 34, y + 145), "Monthly payment", font=font(BOLD, 22), fill=MUTED)
        draw.text((x + 34, y + 177), payment, font=font(HEAVY, 58), fill=stripe)
        draw.line((x + 34, y + 260, x + 351, y + 260), fill="#e8ddc5", width=3)
        draw.text((x + 34, y + 292), "Estimated fees", font=font(BOLD, 22), fill=MUTED)
        draw.text((x + 232, y + 288), fee, font=font(HEAVY, 27), fill=NAVY)
        draw.text((x + 34, y + 346), "Total repayment", font=font(BOLD, 22), fill=MUTED)
        draw.text((x + 220, y + 342), total, font=font(HEAVY, 27), fill=NAVY)

    offer_card(70, 662, "Offer A", "$4,821", "$7,240", "$578k", GREEN)
    offer_card(545, 662, "Offer B", "$5,106", "$3,980", "$613k", BLUE)

    draw.rounded_rectangle((105, 1138, 895, 1266), radius=32, fill=NAVY)
    draw.text((150, 1170), "Before the lender call:", font=font(HEAVY, 32), fill=WHITE)
    draw.text((150, 1210), "test loan amount, rate, term, fees, and repayment pressure.", font=font(REGULAR, 25), fill="#dbeafe")

    draw.rounded_rectangle((86, 1310, 914, 1430), radius=0, fill=WHITE, outline="#e5c58f", width=3)
    paste_logo(image, 112, 1340, 190, BLUE)
    draw.text((342, 1335), "Use CreditDoc's free SBA loan calculator", font=font(HEAVY, 29), fill=NAVY)
    draw.text((342, 1382), compact_url(args.url), font=font(BOLD, 23), fill=GREEN)


def draw_focus_pin(image, draw, args):
    accent = [GREEN, BLUE, GOLD, CYAN][((args.variant or 0) // 4) % 4]
    lower_title = args.title.lower()
    is_receivables = "receivable" in lower_title or "invoice" in lower_title
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill="#fffaf2")
    draw.rectangle((0, 0, WIDTH, 116), fill=WHITE)
    paste_logo(image, 64, 30, 260, BLUE)
    draw.rounded_rectangle((690, 34, 920, 86), radius=22, fill="#e7f8f2")
    draw.text((724, 48), f"FREE {args.kind.upper().split()[0]}", font=font(BOLD, 21), fill=GREEN)

    draw.rectangle((0, 116, WIDTH, 642), fill="#0f2f46")
    draw.polygon([(0, 525), (1000, 410), (1000, 642), (0, 642)], fill="#f59e0b")
    draw.polygon([(0, 590), (1000, 480), (1000, 642), (0, 642)], fill="#fffaf2")

    headline = "Cash tied up in invoices?" if is_receivables else "Check the cost before you choose."
    subhead = (
        "Estimate the advance, reserve, fees, and net cash before receivables financing becomes urgent."
        if is_receivables
        else "Use the free CreditDoc resource to compare the numbers before making a financial decision."
    )
    draw_wrapped(draw, headline, (68, 178), font(SERIF_BOLD, 72), WHITE, 780, line_gap=6, max_lines=2)
    draw.rounded_rectangle((68, 360, 680, 470), radius=24, fill="#143b58")
    draw_wrapped(draw, subhead, (94, 382), font(REGULAR, 25), "#dbeafe", 555, line_gap=6, max_lines=2)

    def invoice_card(x, y, w, h, angle, label, amount, color):
        card = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((20, 20, w + 20, h + 20), radius=28, fill=WHITE, outline="#b7cfe5", width=3)
        cd.rectangle((48, 56, w - 40, 66), fill=color)
        cd.text((48, 92), label, font=font(BOLD, 24), fill=NAVY)
        cd.text((48, 138), amount, font=font(HEAVY, 44), fill=color)
        for idx in range(3):
            yy = 212 + idx * 34
            cd.rounded_rectangle((48, yy, w - 70, yy + 14), radius=7, fill="#e5edf5")
        rotated = card.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        image.paste(rotated, (x, y), rotated)

    invoice_card(612, 185, 310, 365, 6, "Invoice value", "$18,400", GREEN)
    invoice_card(505, 402, 300, 330, -8, "Net cash", "$15,920", BLUE)

    draw.rounded_rectangle((70, 720, 930, 1078), radius=38, fill=WHITE, outline="#e5c58f", width=3)
    draw.text((116, 768), "What the calculator helps show", font=font(HEAVY, 38), fill=NAVY)
    points = [
        ("Advance", "How much cash may arrive upfront"),
        ("Reserve", "What may be held back"),
        ("Fees", "What the financing may cost"),
    ]
    for idx, (label, body) in enumerate(points):
        x = 116 + idx * 270
        draw.rounded_rectangle((x, 850, x + 220, 1018), radius=26, fill=["#ecfdf5", "#eff6ff", "#fff7ed"][idx])
        draw.text((x + 26, 882), label, font=font(HEAVY, 25), fill=[GREEN, BLUE, GOLD][idx])
        draw_wrapped(draw, body, (x + 26, 930), font(BOLD, 21), INK, 160, line_gap=3, max_lines=3)

    draw.rectangle((0, 1146, WIDTH, HEIGHT), fill=NAVY)
    draw.text((70, 1192), "Use the free CreditDoc calculator.", font=font(HEAVY, 40), fill=WHITE)
    bottom_copy = (
        "Model invoice amount, advance rate, reserve holdback, and fees so you can see the net funds before applying."
        if is_receivables
        else "Open the resource, compare the key numbers, and make the next borrowing decision with more context."
    )
    draw_wrapped(draw, bottom_copy, (74, 1260), font(REGULAR, 27), "#dbeafe", 810, line_gap=7, max_lines=3)
    paste_logo(image, 74, 1370, 195, WHITE)
    draw.rounded_rectangle((330, 1376, 910, 1430), radius=24, fill="#e7f8f2")
    draw.text((368, 1391), compact_url(args.url), font=font(BOLD, 20), fill=NAVY)


def variant_for(args):
    if args.variant is not None:
        return args.variant % 4
    key = f"{args.url}|{args.title}".encode("utf-8")
    return int(hashlib.sha1(key).hexdigest()[:8], 16) % 4


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
    parser.add_argument("--variant", type=int, default=None)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    variant = variant_for(args)
    if variant == 0:
        draw_roadmap_pin(image, draw, args)
        image.save(args.out, "PNG", optimize=True)
        print(args.out)
        return
    if variant == 1:
        draw_briefing_pin(image, draw, args)
        image.save(args.out, "PNG", optimize=True)
        print(args.out)
        return
    if variant == 2:
        draw_checklist_pin(image, draw, args)
        image.save(args.out, "PNG", optimize=True)
        print(args.out)
        return
    draw_focus_pin(image, draw, args)
    image.save(args.out, "PNG", optimize=True)
    print(args.out)
    return

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
