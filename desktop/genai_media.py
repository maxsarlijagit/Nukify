# SPDX-License-Identifier: GPL-3.0-or-later
"""Local media preparation. Proxies never replace source or generated originals."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
from PIL import Image, ImageOps

VIDEO = {'.mp4', '.mov', '.webm', '.mkv', '.avi'}
IMAGE = {'.png', '.jpg', '.jpeg', '.webp'}


def ffmpeg_path(configured=''):
    result = configured or shutil.which('ffmpeg')
    if not result or not Path(result).is_file():
        raise ValueError('Configurá FFmpeg para proxies y secuencias de video')
    return str(result)


def run_ffmpeg(args, configured=''):
    result = subprocess.run([ffmpeg_path(configured), '-nostdin', '-hide_banner', '-loglevel', 'error', *args],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if result.returncode:
        raise ValueError('FFmpeg no pudo convertir el medio. Revisá formato, ruta y espacio en disco.')


def proxy(source, directory, size, ffmpeg=''):
    source, directory = Path(source), Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if not size:
        return str(source)
    if source.suffix.lower() in IMAGE:
        target = directory / 'proxy.png'
        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original).convert('RGBA')
            image.thumbnail((size, size), Image.Resampling.LANCZOS)
            image.save(target)
    elif source.suffix.lower() in VIDEO:
        target = directory / 'proxy.mp4'
        scale = f"scale=w='min({size},iw)':h='min({size},ih)':force_original_aspect_ratio=decrease:force_divisible_by=2"
        run_ffmpeg(['-y', '-i', str(source), '-vf', scale, '-c:v', 'libx264', '-crf', '20',
                    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart', str(target)], ffmpeg)
    else:
        raise ValueError('Proxy admite PNG/JPEG/WebP o MP4/MOV/WebM/MKV/AVI')
    return str(target)


def sequence(source, directory, ffmpeg='', preview=False):
    source = Path(source)
    stat = source.stat()
    signature = hashlib.sha256(f'{source.resolve()}|{stat.st_size}|{stat.st_mtime_ns}|{preview}'.encode()).hexdigest()[:16]
    directory = Path(directory) / signature
    directory.mkdir(parents=True, exist_ok=True)
    manifest = directory / 'sequence.json'
    if manifest.is_file():
        result = json.loads(manifest.read_text())
        if Path(result['first_file']).is_file() and len(list(directory.glob('frame_*.' + ('jpg' if preview else 'png')))) == result['frames']:
            return result
    args = ['-y', '-i', str(source)]
    if preview:
        args += ['-vf', "fps=12,scale=w='min(640,iw)':h='min(640,ih)':force_original_aspect_ratio=decrease", '-q:v', '3']
    else:
        args += ['-fps_mode', 'passthrough']
    ext = 'jpg' if preview else 'png'
    run_ffmpeg(args + [str(directory / ('frame_%06d.' + ext))], ffmpeg)
    files = sorted(directory.glob('frame_*.' + ext))
    if not files:
        raise ValueError('No se pudieron extraer frames')
    result = dict(path=str(directory / ('frame_######.' + ext)), first_file=str(files[0]),
                  frames=len(files), preview_fps=12 if preview else None)
    manifest.write_text(json.dumps(result), encoding='utf-8')
    return result
