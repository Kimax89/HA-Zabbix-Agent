"""Render the editable app icon artwork to transparent PNG files (requires Pillow)."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SIZE = 256
SCALE = 4
RED = "#D40000"
WHITE = "#FFFFFF"

# The Z outline from Zabbix's official wordmark, translated to its own origin.
# Source: https://assets.zabbix.com/img/trademark/logos_570x580.svg
Z_OUTLINE = [
    (0, 18.013),
    (0, 15.775),
    (9.9395, 2.445),
    (0, 2.445),
    (0, 0),
    (13.3221, 0),
    (13.3221, 2.239),
    (3.3826, 15.569),
    (13.3221, 15.569),
    (13.3221, 18.013),
]
Z_POINTS = [(75 + x * 8, 54 + y * 8) for x, y in Z_OUTLINE]


def badge_font():
    for filename in ("C:/Windows/Fonts/arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(filename, 44 * SCALE)
        except OSError:
            continue
    raise RuntimeError(
        "Install Arial Bold or DejaVu Sans Bold to render the Agent 2 badge."
    )


def render():
    base = Image.new("RGBA", (SIZE * SCALE, SIZE * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    draw.ellipse(tuple(v * SCALE for v in (8, 8, 248, 248)), fill=RED)
    draw.polygon([(x * SCALE, y * SCALE) for x, y in Z_POINTS], fill=WHITE)

    points = " ".join(f"{x:.4f},{y:.4f}" for x, y in Z_POINTS)
    common_svg = (
        f'<circle cx="128" cy="128" r="120" fill="{RED}"/>\n'
        f'<polygon points="{points}" fill="{WHITE}"/>\n'
    )
    for app, title, badge in (
        ("zabbix_agent", "Zabbix Agent", False),
        ("zabbix_agent2", "Zabbix Agent 2", True),
    ):
        image = base.copy()
        extra_svg = ""
        if badge:
            draw = ImageDraw.Draw(image)
            draw.ellipse(tuple(v * SCALE for v in (178, 178, 246, 246)), fill=RED)
            draw.ellipse(tuple(v * SCALE for v in (181, 181, 243, 243)), fill=WHITE)
            font = badge_font()
            left, top, right, bottom = draw.textbbox((0, 0), "2", font=font)
            draw.text(
                (212 * SCALE - (left + right) / 2, 212 * SCALE - (top + bottom) / 2),
                "2",
                font=font,
                fill=RED,
            )
            extra_svg = (
                f'<circle cx="212" cy="212" r="34" fill="{RED}"/>\n'
                f'<circle cx="212" cy="212" r="31" fill="{WHITE}"/>\n'
                f'<text x="212" y="212" dy=".35em" text-anchor="middle" '
                f'font-family="Arial, DejaVu Sans, sans-serif" font-weight="700" '
                f'font-size="44" fill="{RED}">2</text>\n'
            )
        image = image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
        image.save(ROOT / app / "icon.png", optimize=True)
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" '
            f'viewBox="0 0 256 256" role="img" aria-label="{title}">\n'
            f"<title>{title}</title>\n" + common_svg + extra_svg + "</svg>\n"
        )
        (HERE / (app.replace("_", "-") + ".svg")).write_text(
            svg, encoding="utf-8", newline="\n"
        )


if __name__ == "__main__":
    render()
