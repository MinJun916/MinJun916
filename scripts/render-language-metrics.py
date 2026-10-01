"""Keep Metrics' analysis data; render a sized SVG without HTML overflow."""
import argparse
import math
from pathlib import Path
import re
import textwrap
import xml.etree.ElementTree as ET
from html import escape


def render(source):
    root = ET.fromstring(source)
    rows = []
    summary = ''
    language_count = ''
    for element in root.iter():
        if element.tag.endswith('h2'):
            language_count = ' '.join(''.join(element.itertext()).split())
        if element.tag.endswith('small') and 'estimation from' in ''.join(element.itertext()):
            summary = ' '.join(''.join(element.itertext()).split())
        if element.attrib.get('class') != 'field language details':
            continue
        label, details = list(element)
        name = ' '.join(''.join(label.itertext()).split())
        values = [' '.join(''.join(item.itertext()).split()) for item in details]
        lines = next(value for value in values if 'line' in value)
        share = next(value for value in values if value.endswith('%'))
        percent = float(share[:-1])
        if not math.isfinite(percent) or not 0 <= percent <= 100:
            raise ValueError(f'Invalid percentage: {share}')
        color = next(item.attrib['fill'] for item in label.iter() if 'fill' in item.attrib)
        if not re.fullmatch(r'#[0-9a-fA-F]{3,8}', color):
            raise ValueError(f'Invalid language color: {color}')
        rows.append((name, lines, share, percent, color))
    if not rows or len({row[0] for row in rows}) != len(rows) or not summary:
        raise ValueError('Metrics language data is missing or duplicated; refusing to replace the card')
    rows.sort(key=lambda row: row[3], reverse=True)
    if language_count:
        summary = f'{language_count} · {summary}'
    summary_lines = textwrap.wrap(summary, width=61)
    start = 112 + len(summary_lines) * 18
    height = start + len(rows) * 40 + 12
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="{height}" viewBox="0 0 480 {height}" role="img" aria-labelledby="title description">',
             '<title id="title">Most used languages</title>',
             f'<desc id="description">{escape(summary)}. '+escape('; '.join(f'{name}: {lines}, {share}' for name, lines, share, _, _ in rows))+'</desc>',
             f'<rect x=".5" y=".5" width="479" height="{height-1}" rx="12" fill="#ffffff" stroke="#d1d9e0"/>',
             '<g font-family="Arial,Helvetica,sans-serif" fill="#1f2328">',
             '<text x="24" y="36" font-size="22" font-weight="600">Most used languages</text>']
    for index, line in enumerate(summary_lines):
        parts.append(f'<text x="24" y="{62 + index * 18}" font-size="12" fill="#59636e">{escape(line)}</text>')
    parts.append(f'<g font-size="12" fill="#59636e"><text x="24" y="{start-28}">Language</text><text x="362" y="{start-28}" text-anchor="end">Lines</text><text x="456" y="{start-28}" text-anchor="end">Share</text></g>')
    for index, (name, lines, share, percent, color) in enumerate(rows):
        y = start + index * 40
        parts.extend([f'<circle cx="28" cy="{y-5}" r="5" fill="{color}"/>',
                      f'<text x="42" y="{y}" font-size="17">{escape(name)}</text>',
                      f'<text x="362" y="{y}" font-size="15" text-anchor="end">{escape(lines)}</text>',
                      f'<text x="456" y="{y}" font-size="15" text-anchor="end">{escape(share)}</text>',
                      f'<rect x="42" y="{y+9}" width="414" height="4" rx="2" fill="#eaeef2"/>',
                      f'<rect x="42" y="{y+9}" width="{414 * percent / 100:.3f}" height="4" rx="2" fill="{color}"/>'])
    return '\n'.join(parts + ['</g></svg>']) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    result = render(args.source.read_text())
    args.destination.write_text(result)
