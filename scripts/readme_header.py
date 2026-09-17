# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools[woff]>=4.59,<5", "brotli>=1.1,<2", "pillow>=11,<13"]
# ///
"""Draw the README header from saved results, without image-generation services.

uv run scripts/readme_header.py --fonts <website>/public/lab/jev-reranking/fonts

Uses the website's Archivo and Geist Mono files. Fonts are not copied into this
repository: SVG lettering is outlined and the PNG is ready for GitHub.
"""
from __future__ import annotations

import argparse
import html
import io
import json
from functools import lru_cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, SCALE = 1600, 650, 2
BG, WHITE, GREEN, PURPLE = '#090a0a', '#eeeeea', '#00ff94', '#bb9aff'
DIM, GRID = '#a9ada9', '#29302d'
BAYER = ((0,48,12,60,3,51,15,63), (32,16,44,28,35,19,47,31),
         (8,56,4,52,11,59,7,55), (40,24,36,20,43,27,39,23),
         (2,50,14,62,1,49,13,61), (34,18,46,30,33,17,45,29),
         (10,58,6,54,9,57,5,53), (42,26,38,22,41,25,37,21))


class Header:
    def __init__(self, fonts: Path, description: str):
        self.fonts = fonts
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img">',
                      '<title>Jev as a reranker</title>', f'<desc>{html.escape(description)}</desc>']
        self.image = Image.new('RGB', (WIDTH * SCALE, HEIGHT * SCALE), BG)
        self.draw = ImageDraw.Draw(self.image)
        self.rect(0, 0, WIDTH, HEIGHT, BG)

    @lru_cache
    def face(self, kind: str):
        mono = kind == 'mono'
        font = TTFont(self.fonts / ('geist-mono.woff' if mono else 'archivo-latin.woff2'))
        axes = {'wght': 500 if mono else (820 if kind == 'display' else 500)}
        if not mono:
            axes['wdth'] = 115 if kind == 'display' else 100
        font = instantiateVariableFont(font, axes, inplace=True)
        font.flavor = None
        buffer = io.BytesIO()
        font.save(buffer)
        return font, font.getGlyphSet(), font.getBestCmap(), font['head'].unitsPerEm, buffer.getvalue()

    def rect(self, x, y, w, h, fill):
        self.parts.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="{fill}"/>')
        self.draw.rectangle((round(x*SCALE), round(y*SCALE), round((x+w)*SCALE)-1, round((y+h)*SCALE)-1), fill=fill)

    def line(self, x1, y1, x2, y2, fill, width=1):
        self.parts.append(f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{fill}" stroke-width="{width}"/>')
        self.draw.line((x1*SCALE, y1*SCALE, x2*SCALE, y2*SCALE), fill=fill, width=round(width*SCALE))

    def text(self, value, x, y, size, kind='body', fill=WHITE, align='left'):
        _, glyphs, cmap, units, ttf = self.face(kind)
        extent = sum(glyphs[cmap[ord(c)]].width for c in value) / units * size
        if align == 'right':
            x -= extent
        if not (0 <= x <= x + extent <= WIDTH):
            raise ValueError(f'Text outside canvas: {value}')
        scale = size / units
        self.parts.append(f'<g aria-label="{html.escape(value, quote=True)}" fill="{fill}" transform="translate({x:.3f} {y:.3f}) scale({scale:.6f} {-scale:.6f})">')
        cursor = 0
        for char in value:
            glyph = glyphs[cmap[ord(char)]]
            pen = SVGPathPen(glyphs)
            glyph.draw(pen)
            if pen.getCommands():
                self.parts.append(f'<path d="{pen.getCommands()}" transform="translate({cursor} 0)"/>')
            cursor += glyph.width
        self.parts.append('</g>')
        font = ImageFont.truetype(io.BytesIO(ttf), size=round(size*SCALE))
        self.draw.text((x*SCALE, y*SCALE), value, font=font, fill=fill, anchor='ls', features=['-kern', '-liga'])

    def bar(self, x, y, w, h, color):
        # Identical screen on every series; length alone encodes the score.
        step = 3
        for row in range(0, h, step):
            coverage = .9 - .62 * (row / h) ** .8
            for col in range(0, int(w), step):
                if coverage > (BAYER[(row//step) % 8][(col//step) % 8] + .5) / 64:
                    self.rect(x+col, y+row, min(step, w-col), min(step, h-row), color)
        self.line(x, y, x+w, y, color, 2)
        self.line(x+w, y, x+w, y+h, color, 2)

    def save(self, destination: Path):
        destination.mkdir(parents=True, exist_ok=True)
        (destination/'readme-header.svg').write_text('\n'.join(self.parts + ['</svg>'])+'\n', encoding='utf-8')
        self.image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(destination/'readme-header.png', optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts', type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads((ROOT/'results/summary.json').read_text(encoding='utf-8'))
    models = summary['overall_english']
    methods = [('jev-score-batch', 'Jev rubric', GREEN), ('cohere-pro', 'Cohere Pro', WHITE), ('zerank-2', 'zerank-2', PURPLE)]
    dataset_ids = models['jev-score-batch']['datasets']
    count = sum(summary['datasets'][d]['queries_with_answer_in_top30'] for d in dataset_ids)
    description = ('Equal-dataset nDCG@10 over ' + str(len(dataset_ids)) + ' English datasets and ' + f'{count:,}' + ' scored queries. ' +
                   ', '.join(f'{label}: {models[key]["ndcg10"]:.3f}' for key,label,_ in methods) + '. All bars start at zero. No established winner between Jev and Cohere.')
    c = Header(args.fonts, description)
    c.text('ANESS BELBATI', 64, 73, 24, 'mono', DIM)
    c.text('Jev as a', 60, 246, 104, 'display')
    c.text('reranker.', 60, 358, 104, 'display', GREEN)
    c.text('Benchmarks, raw responses and code.', 64, 434, 29)
    c.text(f'{len(dataset_ids)} datasets · {count:,} scored queries', 64, 578, 27, fill=DIM)

    x, w = 846, 690
    c.text('Ranking quality', x, 74, 35, 'display')
    c.text('nDCG@10 · equal dataset weight', x, 119, 27, fill=DIM)
    for tick in (0, .5, 1):
        c.line(x + w*tick, 165, x + w*tick, 505, GRID)
    for i, (key, label, color) in enumerate(methods):
        score = models[key]['ndcg10']
        y = 198 + i*118
        c.text(label, x, y, 30, fill=color)
        c.text(f'{score:.3f}', x+w, y, 34, 'mono', color, 'right')
        c.bar(x, y+19, w*score, 50, color)
    c.text('0', x, 542, 25, 'mono', DIM)
    c.text('1', x+w, 542, 25, 'mono', DIM, 'right')
    c.text('No clear winner between Jev and Cohere.', x, 596, 26, fill=DIM)
    c.save(ROOT/'docs')
    print(json.dumps({'size':[WIDTH,HEIGHT], 'scored_queries':count, 'scores':{key:models[key]['ndcg10'] for key,_,_ in methods},
                      'png_bytes':(ROOT/'docs/readme-header.png').stat().st_size}))


if __name__ == '__main__':
    main()
