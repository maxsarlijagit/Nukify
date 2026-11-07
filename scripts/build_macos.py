# SPDX-License-Identifier: GPL-3.0-or-later
"""Build an Apple Silicon .app and drag-to-Applications DMG with private Blender.

Run with the UI's Python 3.12 on macOS. Requires an official Blender DMG and
its pinned SHA256 from packaging/macos.json. Never modifies /Applications.
"""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import plistlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender-dmg', type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != 'darwin' or platform.machine() != 'arm64' or sys.version_info[:2] != (3, 12):
        parser.error('Build requires native macOS arm64 and Python 3.12')
    if not (ROOT / 'desktop/vendor/cv2').is_dir() or not list((ROOT / 'desktop/vendor').glob('OpenEXR*.so')):
        parser.error('Prepare macOS CPython 3.11 worker wheels in desktop/vendor first')
    config = json.loads((ROOT / 'packaging/release.json').read_text())
    mac = json.loads((ROOT / 'packaging/macos.json').read_text())
    if sha256(args.blender_dmg) != mac['blender_dmg_sha256']:
        parser.error('Blender DMG SHA256 does not match packaging/macos.json')
    if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=normal'], cwd=ROOT).strip():
        parser.error('Commit source changes before building; the manifest records HEAD')
    version = config['version']
    output = ROOT / 'releases' / version / 'macOS-arm64'
    output.mkdir(parents=True, exist_ok=True)
    run(sys.executable, ROOT / 'scripts/fetch_sources.py', cwd=ROOT)
    desktop_data = ROOT / 'build/macos-data/desktop'
    if desktop_data.exists():
        shutil.rmtree(desktop_data)
    shutil.copytree(ROOT / 'desktop', desktop_data, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    run(sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', '--windowed',
        '--onedir', '--name', 'Nukify', '--distpath', output,
        '--icon', ROOT / 'assets/nukify-logo.png', '--paths', ROOT / 'desktop',
        '--osx-bundle-identifier', 'com.maxsarlija.nukify', '--target-arch', 'arm64',
        '--collect-all', 'PyOpenColorIO', '--add-data', f'{desktop_data}:desktop',
        '--add-data', f'{ROOT / "assets"}:assets', ROOT / 'desktop/app.py', cwd=ROOT)
    app = output / 'Nukify.app'
    resources = app / 'Contents/Resources'
    # ditto preserves Blender's symlinks, executable permissions and signatures.
    with tempfile.TemporaryDirectory(prefix='nukify-mount-') as mount:
        run('hdiutil', 'attach', args.blender_dmg.resolve(), '-readonly', '-nobrowse', '-mountpoint', mount)
        try:
            engine = resources / 'engine/Blender.app'
            engine.parent.mkdir(exist_ok=True)
            run('ditto', Path(mount) / 'Blender.app', engine)
        finally:
            run('hdiutil', 'detach', mount)
    blender = engine / 'Contents/MacOS/Blender'
    info = subprocess.check_output([str(blender), '--background', '--factory-startup', '--version'], text=True)
    if f'Blender {config["blender_version"]}' not in info or config['blender_build'] not in info:
        raise RuntimeError('Unexpected Blender version/build: ' + info)
    for name in ('LICENSE', 'THIRD_PARTY.md', 'AUTHORS.md', 'README.md', 'README.es.md', 'BUILDING.md', 'CONTRIBUTING.md', 'AGENTS.md'):
        shutil.copy2(ROOT / name, resources / name)
    for name in ('licenses', 'docs', 'agents', 'sources'):
        shutil.copytree(ROOT / name, resources / name, dirs_exist_ok=True)
    licenses = resources / 'licenses'
    inventory = []
    for distribution in importlib.metadata.distributions():
        inventory.append({'name': distribution.metadata['Name'], 'version': distribution.version})
        for file in distribution.files or []:
            if 'license' in str(file).lower() or 'copying' in str(file).lower():
                target = licenses / 'python' / Path(str(file))
                if '..' in target.parts:
                    continue
                source = distribution.locate_file(file)
                if source.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    for source in (Path(sys.base_prefix) / 'LICENSE.txt', Path(sys.base_prefix) / 'lib/python3.12/LICENSE.txt'):
        if source.is_file():
            shutil.copy2(source, licenses / 'Python-3.12-LICENSE.txt')
            break
    # Worker wheels carry their own notices, separate from UI distributions.
    for source in (ROOT / 'desktop/vendor').glob('*.dist-info'):
        shutil.copytree(source, licenses / 'worker' / source.name, dirs_exist_ok=True)
    (licenses / 'python-components.json').write_text(json.dumps(inventory, indent=2))
    with zipfile.ZipFile(resources / 'sources' / f'Nukify-{version}-source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
        for name in tracked:
            if name and (ROOT / name).is_file():
                archive.write(ROOT / name, name)
    manifest = dict(app=version, platform='macOS-arm64', engine=config['blender_version'],
                    engine_build=config['blender_build'], engine_dmg_sha256=mac['blender_dmg_sha256'],
                    engine_sha256=sha256(blender),
                    source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                    signing='ad-hoc; not Developer ID signed or notarized')
    # Keep release.json beside the launcher, as on Windows, for updater discovery.
    (app / 'Contents/MacOS/release.json').write_text(json.dumps(manifest, indent=2))
    plist = app / 'Contents/Info.plist'
    data = plistlib.loads(plist.read_bytes())
    data.update(CFBundleShortVersionString=version, CFBundleVersion=version, LSMinimumSystemVersion='12.0')
    plist.write_bytes(plistlib.dumps(data))
    run('codesign', '--force', '--deep', '--sign', '-', app)
    run('codesign', '--verify', '--deep', '--strict', app)
    stem = f'Nukify-{version}-macOS-arm64'
    with tempfile.TemporaryDirectory(prefix='nukify-dmg-') as staging:
        run('ditto', app, Path(staging) / 'Nukify.app')
        (Path(staging) / 'Applications').symlink_to('/Applications', target_is_directory=True)
        (Path(staging) / 'INSTALL.txt').write_text('Drag Nukify.app to Applications. Requires macOS 12+, Apple Silicon.\nThis beta is ad-hoc signed, not notarized. See README for Gatekeeper instructions.\n')
        run('hdiutil', 'create', '-volname', 'Nukify', '-srcfolder', staging, '-ov', '-format', 'UDZO', output / f'{stem}.dmg')
    run('ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', app, output / f'{stem}.zip')
    artifacts = [output / f'{stem}.dmg', output / f'{stem}.zip']
    (output / 'SHA256SUMS-macOS-arm64.txt').write_text(''.join(f'{sha256(p)}  {p.name}\n' for p in artifacts))
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
