#!/usr/bin/env python3
"""Typeset the book cover with real simplified Chinese font glyphs.

Requires Pillow and installed CJK fonts. The default fonts are macOS Songti SC
and Heiti SC. The unlettered artwork is kept separately so every run builds the
same cover without painting over previous text.
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'scripts/assets/cover-art.png')
    parser.add_argument('--image', type=Path, default=ROOT / 'cover.png')
    parser.add_argument('--font', default='/System/Library/Fonts/Supplemental/Songti.ttc')
    parser.add_argument('--font-index', type=int, default=0)
    parser.add_argument('--sans-font', default='/System/Library/Fonts/STHeiti Medium.ttc')
    parser.add_argument('--sans-font-index', type=int, default=1)
    args = parser.parse_args()

    if args.source.resolve() == args.image.resolve():
        raise SystemExit('The artwork source and cover output must be separate files')
    with Image.open(args.source) as source:
        image = source.convert('RGB')
    if image.size != (1024, 1536):
        raise SystemExit('Expected the 1024 × 1536 unlettered cover artwork')

    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(args.font, 252, index=args.font_index)

    def sans(size):
        return ImageFont.truetype(args.sans_font, size, index=args.sans_font_index)

    def text_at(text, face, left, top, color):
        x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=face)
        if left < 0 or top < 0 or left + x1 - x0 > image.width or top + y1 - y0 > image.height:
            raise SystemExit(f'Text falls outside the cover: {text}')
        draw.text((left - x0, top - y0), text, font=face, fill=color)

    # Shared left alignment connects the title block and footer. The illustration
    # retains its own generous width between these two typographic anchors.
    text_at('AGENT HARNESS ENGINEERING', sans(20), 84, 66, 'white')
    text_at('\u5fa1\u8206', title_font, 78, 130, 'white')  # 御舆 (simplified 舆).
    text_at('解码 Agent Harness', sans(48), 84, 415, 'white')
    draw.line((84, 1358, 940, 1358), fill='#A4058B', width=2)
    text_at('Claude Code 架构深度剖析', sans(34), 84, 1388, '#202020')
    text_at('LinTsinghua', sans(36), 84, 1462, '#252525')

    image.save(args.image, optimize=True)
    print(f'Typeset 御舆 using {title_font.getname()}: {args.image}')


if __name__ == '__main__':
    main()
