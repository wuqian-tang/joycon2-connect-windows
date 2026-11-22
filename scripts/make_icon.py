"""Rebuild the original flat Joy-Con desktop icon (requires Pillow)."""
from pathlib import Path

from PIL import Image, ImageDraw


def make_icon():
    scale = 8
    image = Image.new("RGBA", (64 * scale, 64 * scale))
    draw = ImageDraw.Draw(image)
    dark, blue, coral = "#18283d", "#4ec7f5", "#ff8371"

    def box(coords, **kwargs):
        draw.rounded_rectangle(tuple(int(n * scale) for n in coords), **kwargs)

    def circle(coords):
        draw.ellipse(tuple(int(n * scale) for n in coords), fill=dark)

    def curve(start, c1, c2, end):
        return [tuple((1-t)**3 * start[k] + 3*(1-t)**2*t*c1[k]
                      + 3*(1-t)*t*t*c2[k] + t**3*end[k] for k in (0, 1))
                for t in (i / 64 for i in range(65))]

    box((0, 0, 64, 64), radius=18 * scale, fill=dark)
    left = [(29, 11), (23, 11)] + curve((23, 11), (12, 11), (9, 19), (9, 29))
    left += [(9, 39)] + curve((9, 39), (9, 49), (13, 53), (23, 53)) + [(29, 53)]
    right = [(35, 11), (41, 11)] + curve((41, 11), (52, 11), (55, 19), (55, 29))
    right += [(55, 39)] + curve((55, 39), (55, 49), (51, 53), (41, 53)) + [(35, 53)]
    for points, color in ((left, blue), (right, coral)):
        draw.polygon([(round(x * scale), round(y * scale)) for x, y in points], fill=color)
    circle((16, 20, 26, 30))
    circle((39, 34, 49, 44))
    circle((42, 21, 46, 25))
    draw.line((17 * scale, 40 * scale, 25 * scale, 40 * scale), fill=dark, width=3 * scale)
    draw.line((21 * scale, 36 * scale, 21 * scale, 44 * scale), fill=dark, width=3 * scale)
    for x, y in ((17, 40), (25, 40), (21, 36), (21, 44)):
        circle((x - 1.5, y - 1.5, x + 1.5, y + 1.5))
    output = Path(__file__).resolve().parents[1] / "assets" / "app.ico"
    output.parent.mkdir(parents=True, exist_ok=True)
    image.resize((256, 256), Image.Resampling.LANCZOS).save(
        output, format="ICO", sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)]
    )
    image.resize((256, 256), Image.Resampling.LANCZOS).save(output.with_suffix(".png"))
    print(output)


if __name__ == "__main__":
    make_icon()
