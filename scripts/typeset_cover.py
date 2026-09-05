#!/usr/bin/env python3
"""Typeset the cover title with real simplified Chinese font glyphs.

Requires Pillow. On macOS the default is Songti SC Bold. Pass --font and
--font-index to use another installed CJK font. Only the top title area changes.
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', type=Path, default=Path(__file__).resolve().parents[1] / 'cover.png')
    parser.add_argument('--font', default='/System/Library/Fonts/Supplemental/Songti.ttc')
    parser.add_argument('--font-index', type=int, default=1)
    args = parser.parse_args()
    with Image.open(args.image) as source:
        image = source.convert('RGB')
    width, height = image.size
    if (width, height) != (1024, 1536):
        raise SystemExit('Expected the reviewed 1024 × 1536 cover layout')
    # Reconstruct the dark background from its unlettered left/right margins.
    # The copper rule starts below y=380 and is preserved with the illustration.
    pixels = image.load()
    for y in range(380):
        left, right = pixels[0, y], pixels[width - 1, y]
        for x in range(width):
            ratio = x / (width - 1)
            pixels[x, y] = tuple(round(a * (1 - ratio) + b * ratio) for a, b in zip(left, right))
    font = ImageFont.truetype(args.font, 280, index=args.font_index)
    title = '\u5fa1\u8206'  # 御舆, never the traditional 輿 (U+8F3F).
    draw = ImageDraw.Draw(image)
    bounds = draw.textbbox((0, 0), title, font=font)
    x = (width - (bounds[2] - bounds[0])) / 2 - bounds[0]
    y = 90 - bounds[1]
    draw.text((x, y), title, font=font, fill='#EED5A2')
    image.save(args.image, optimize=True)
    print(f'Typeset {title} using {font.getname()}: {args.image}')


if __name__ == '__main__':
    main()
