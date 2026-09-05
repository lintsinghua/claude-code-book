#!/usr/bin/env python3
"""Check repository Markdown links, fences and known Mermaid display pitfalls.

This dependency-free check does not replace Mermaid parsing or visual review.
"""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT):
    errors = []
    files = sorted(
        path for path in root.rglob('*.md')
        if not any(part.startswith('.') or part == 'node_modules'
                   for part in path.relative_to(root).parts)
    )
    diagrams = 0
    for path in files:
        if any(part.startswith('.') for part in path.relative_to(root).parts):
            continue
        fence = None
        visible = []
        mermaid = False
        for number, line in enumerate(path.read_text().splitlines(), 1):
            marker = re.match(r'^\s*(`{3,}|~{3,})(.*)$', line)
            if marker:
                token, info = marker.groups()
                if fence is None:
                    fence = token
                    mermaid = info.strip() == 'mermaid'
                    diagrams += int(mermaid)
                elif token[0] == fence[0] and len(token) >= len(fence) and not info.strip():
                    fence = None
                    mermaid = False
                continue
            if fence:
                if mermaid and r'\n' in line:
                    errors.append(f'{path.relative_to(root)}:{number}: literal \\n in Mermaid; use <br/>')
                continue
            visible.append((number, line))
        if fence:
            errors.append(f'{path.relative_to(root)}: unclosed code fence')
        for number, line in visible:
            links = re.findall(r'\]\(([^\s)]+)(?:\s+"[^"]*")?\)', line)
            links += re.findall(r'(?:src|href|srcset)="([^"]+)"', line)
            for link in links:
                url = urlsplit(link.strip('<>'))
                if url.scheme or url.netloc or not url.path:
                    continue
                target = (path.parent / unquote(url.path)).resolve()
                if not target.exists():
                    errors.append(f'{path.relative_to(root)}:{number}: missing target {link}')
    return files, diagrams, errors


if __name__ == '__main__':
    files, diagrams, errors = check()
    for error in errors:
        print(error)
    print(f'{len(files)} Markdown files, {diagrams} Mermaid diagrams, {len(errors)} errors')
    sys.exit(bool(errors))
