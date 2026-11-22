"""Rebuild the original flat Joy-Con desktop icon (requires Pillow)."""
from pathlib import Path

from PIL import Image, ImageDraw


def make_icon():
    scale = 8
    image = Image.new("RGBA", (64 * scale, 64 * scale))
    draw = ImageDraw.Draw(image)
    dark, blue, coral = "#18283d", "#4ec7f5", "#ff8371"

    def circle(coords):
        draw.ellipse(tuple(int(n * scale) for n in coords), fill=dark)

    def curve(start, c1, c2, end):
        return [tuple((1-t)**3 * start[k] + 3*(1-t)**2*t*c1[k]
                      + 3*(1-t)*t*t*c2[k] + t**3*end[k] for k in (0, 1))
                for t in (i / 64 for i in range(65))]

    left = [(29, 2), (23, 2)] + curve((23, 2), (9, 2), (3, 10), (3, 23))
    left += [(3, 41)] + curve((3, 41), (3, 54), (9, 62), (23, 62)) + [(29, 62)]
    right = [(64 - x, y) for x, y in left]
    for points, color in ((left, blue), (right, coral)):
        draw.polygon([(round(x * scale), round(y * scale)) for x, y in points], fill=color)
    circle((10, 16, 22, 28))
    circle((42, 36, 54, 48))
    for x, y in ((48, 15), (53, 20), (48, 25), (43, 20)):
        circle((x - 1.8, y - 1.8, x + 1.8, y + 1.8))
    draw.line((12 * scale, 43 * scale, 20 * scale, 43 * scale), fill=dark, width=3 * scale)
    draw.line((16 * scale, 39 * scale, 16 * scale, 47 * scale), fill=dark, width=3 * scale)
    for x, y in ((12, 43), (20, 43), (16, 39), (16, 47)):
        circle((x - 1.5, y - 1.5, x + 1.5, y + 1.5))
    output = Path(__file__).resolve().parents[1] / "assets" / "app.ico"
    output.parent.mkdir(parents=True, exist_ok=True)
    image.resize((256, 256), Image.Resampling.LANCZOS).save(
        output, format="ICO", sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)]
    )
    image.resize((256, 256), Image.Resampling.LANCZOS).save(output.with_suffix(".png"))
    (output.parents[1] / 'joycon2_assistant' / 'static' / 'favicon.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<path d="M29 2H23C9 2 3 10 3 23v18c0 13 6 21 20 21h6Z" fill="#4ec7f5"/>'
        '<path d="M35 2h6c14 0 20 8 20 21v18c0 13-6 21-20 21h-6Z" fill="#ff8371"/>'
        '<g fill="#18283d"><circle cx="16" cy="22" r="6"/>'
        '<circle cx="48" cy="42" r="6"/><circle cx="48" cy="15" r="1.8"/>'
        '<circle cx="53" cy="20" r="1.8"/><circle cx="48" cy="25" r="1.8"/>'
        '<circle cx="43" cy="20" r="1.8"/></g>'
        '<path d="M12 43h8m-4-4v8" stroke="#18283d" stroke-width="3" stroke-linecap="round"/>'
        '</svg>\n', encoding='utf-8')
    print(output)


if __name__ == "__main__":
    make_icon()
