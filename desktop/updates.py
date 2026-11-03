# SPDX-License-Identifier: GPL-3.0-or-later
"""GitHub releases and verified downloads. No Qt, credentials or Blender imports."""
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

REPOSITORY = 'maxsarlijagit/Nukify'
API = f'https://api.github.com/repos/{REPOSITORY}/releases?per_page=100'
RELEASES = f'https://github.com/{REPOSITORY}/releases'


def version_key(value):
    match = re.fullmatch(r'v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(alpha|beta|rc)\.(0|[1-9]\d*))?(?:\+[\w.-]+)?', value)
    if not match:
        raise ValueError('Invalid release version: ' + str(value))
    major, minor, patch, stage, number = match.groups()
    return (int(major), int(minor), int(patch), {None: 3, 'rc': 2, 'beta': 1, 'alpha': 0}[stage], int(number or 0))


def installed_version():
    path = (Path(sys.executable).parent / 'release.json' if getattr(sys, 'frozen', False)
            else Path(__file__).resolve().parents[1] / 'packaging/release.json')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        value = data.get('app') or data['version']
        version_key(value)
        return value
    except (OSError, ValueError, KeyError, TypeError):
        return None


def official_url(url, prefix=RELEASES + '/'):
    return isinstance(url, str) and url.startswith(prefix) and urlparse(url).netloc == 'github.com'


def request(url):
    return urlopen(Request(url, headers={'User-Agent': 'Nukify-Updater',
                   'Accept': 'application/vnd.github+json' if url.startswith(API.split('?')[0]) else 'application/octet-stream',
                   'X-GitHub-Api-Version': '2022-11-28'}), timeout=20)


def fetch_releases():
    with request(API) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError('Release response too large')
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError('Invalid GitHub release response')
    return data


def select_release(releases, current, include_beta=True):
    current_key = version_key(current)
    candidates = []
    for release in releases:
        try:
            key = version_key(release['tag_name'])
            if release.get('draft') or not release.get('published_at') or key <= current_key:
                continue
            if not include_beta and (release.get('prerelease') or key[3] < 3):
                continue
            if not official_url(release.get('html_url', ''), RELEASES + '/tag/'):
                continue
            version = release['tag_name'].removeprefix('v')
            name = f'Nukify-Setup-{version}.exe'
            asset = next((a for a in release.get('assets', []) if a.get('name') == name and a.get('state') == 'uploaded'), None)
            if not asset or not official_url(asset.get('browser_download_url', ''), RELEASES + '/download/' + release['tag_name'] + '/'):
                continue
            digest = asset.get('digest') or ''
            if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}', digest) or not 0 < asset.get('size', 0) <= 4 * 1024**3:
                continue
            candidates.append((key, dict(version=version, title=release.get('name') or version,
                notes=release.get('body') or '', url=release['html_url'], name=name,
                download=asset['browser_download_url'], size=asset['size'], sha256=digest[7:].lower(),
                prerelease=bool(release.get('prerelease') or key[3] < 3))))
        except (KeyError, ValueError, TypeError, AttributeError):
            continue
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def verify_installer(path, release):
    path = Path(path)
    if path.stat().st_size != release['size']:
        raise ValueError('Installer size mismatch')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != release['sha256']:
        raise ValueError('Installer SHA256 mismatch')
    return path


def download_installer(release, directory, cancelled, progress=lambda value: None):
    if not official_url(release['download'], RELEASES + '/download/') or Path(release['name']).name != release['name']:
        raise ValueError('Invalid installer URL or filename')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / release['name']
    temporary = target.with_suffix('.exe.part')
    received = 0
    try:
        with request(release['download']) as response, temporary.open('wb') as stream:
            while True:
                if cancelled.is_set():
                    raise InterruptedError('Download cancelled')
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                received += len(chunk)
                if received > release['size']:
                    raise ValueError('Installer size mismatch')
                stream.write(chunk)
                progress(int(received * 100 / release['size']))
        verify_installer(temporary, release)
        if cancelled.is_set():
            raise InterruptedError('Download cancelled')
        temporary.replace(target)
        return str(target)
    finally:
        temporary.unlink(missing_ok=True)


def read_settings(directory):
    defaults = dict(automatic=True, include_beta=True, last_check=0, skipped='')
    try:
        data = json.loads((Path(directory) / 'updates.json').read_text(encoding='utf-8'))
        for key in defaults:
            if type(data.get(key)) is type(defaults[key]):
                defaults[key] = data[key]
    except (OSError, ValueError, AttributeError):
        pass
    return defaults


def save_settings(directory, settings):
    path = Path(directory) / 'updates.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(settings, indent=2), encoding='utf-8')
    temporary.replace(path)


def check_due(settings, now=None):
    now = int(time.time()) if now is None else now
    return settings['automatic'] and (now - settings['last_check'] >= 86400 or now < settings['last_check'])
