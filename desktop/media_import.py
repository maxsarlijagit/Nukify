# SPDX-License-Identifier: GPL-3.0-or-later
"""Resolve stills and numbered sequences without decoding media."""
import re
from pathlib import Path

IMAGE_EXTENSIONS = {'.bmp', '.cin', '.dpx', '.exr', '.hdr', '.jpeg', '.jpg',
                    '.png', '.rgb', '.rgba', '.sgi', '.tga', '.tif', '.tiff', '.webp'}
FILE_FILTER = 'Images (' + ' '.join('*' + ext for ext in sorted(IMAGE_EXTENSIONS)) + ')'


def sequence_key(path):
    match = re.fullmatch(r'(.*?)(\d+)', path.stem)
    if match:
        prefix, digits = match.groups()
        return prefix, len(digits), path.suffix
    return None


def read_paths(paths):
    """Group siblings even for a single dropped frame; keep isolated stills literal."""
    directories, result, seen = {}, [], set()
    for value in paths:
        path = Path(value)
        if path.suffix.lower() not in IMAGE_EXTENSIONS or not path.is_file():
            continue
        key = sequence_key(path)
        if key:
            if path.parent not in directories:
                groups = {}
                try:
                    for sibling in path.parent.iterdir():
                        sibling_key = sequence_key(sibling)
                        if sibling_key and sibling.is_file():
                            groups[sibling_key] = groups.get(sibling_key, 0) + 1
                except OSError:
                    groups = {}
                directories[path.parent] = groups
            if directories[path.parent].get(key, 0) > 1:
                prefix, padding, suffix = key
                path = path.with_name(prefix + '#' * padding + suffix)
        identity = str(path).casefold()
        if identity not in seen:
            seen.add(identity)
            result.append(str(path))
    return result
