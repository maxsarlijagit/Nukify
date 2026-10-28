"""Run after PyInstaller. Stage exact tested Blender, source and notices."""
import hashlib
import json
import shutil
import zipfile
import argparse,subprocess,sys,importlib.metadata
from pathlib import Path

root = Path(__file__).resolve().parents[1]
config=json.loads((root/'packaging/release.json').read_text())
parser=argparse.ArgumentParser();parser.add_argument('--blender-dir',required=True);args=parser.parse_args()
version=config['version'];dest=root/'releases'/version/'Nukify'
engine=Path(args.blender_dir).resolve()
assert (dest / 'Nukify.exe').is_file()
assert hashlib.sha256((engine / 'blender.exe').read_bytes()).hexdigest() == config['blender_exe_sha256'],'Blender build does not match release configuration'
shutil.copytree(engine, dest / 'engine', dirs_exist_ok=True)
for name in ['LICENSE', 'THIRD_PARTY.md','AUTHORS.md','README.md','README.es.md','BUILDING.md','CONTRIBUTING.md','AGENTS.md']:
    shutil.copy2(root / name, dest / name)
shutil.copy2(root / 'docs/desktop-0.9.md', dest / 'LEEME.md')
shutil.copytree(root / 'docs', dest / 'docs', dirs_exist_ok=True)
shutil.copytree(root / 'agents', dest / 'agents', dirs_exist_ok=True)
(dest / 'assets').mkdir(exist_ok=True)
shutil.copy2(root / 'assets/nukify-logo.png', dest / 'assets/nukify-logo.png')
sources = dest / 'sources'
sources.mkdir(exist_ok=True)
for url in config['source_urls']:shutil.copy2(root/'sources'/url.rsplit('/',1)[1],sources)
shutil.copy2(root/'sources/upstream-sources.json',sources)
licenses=dest/'licenses';licenses.mkdir(exist_ok=True)
shutil.copytree(root/'licenses',licenses,dirs_exist_ok=True)
python_license=Path(sys.base_prefix)/'LICENSE.txt'
if python_license.is_file():shutil.copy2(python_license,licenses/'Python-3.12-LICENSE.txt')
metadata_dirs=list((root/'.buildenv/Lib/site-packages').glob('*.dist-info'))+list((root/'desktop/vendor').glob('*.dist-info'))
for metadata in metadata_dirs:
    for p in metadata.rglob('*'):
        if p.is_file() and ('license' in p.name.lower() or 'copying' in p.name.lower()):
            target=licenses/metadata.name/p.relative_to(metadata);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
assert 'README.md' in tracked,'Initialize and stage the source repository before packaging'
with zipfile.ZipFile(sources / f'Nukify-{version}-source.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for name in tracked:
        if name and (root/name).is_file():z.write(root/name,name)
inventory=[]
for directory in metadata_dirs:
    distribution=importlib.metadata.PathDistribution(directory)
    inventory.append({'name':distribution.metadata['Name'],'version':distribution.version,'license':distribution.metadata.get('License-Expression') or distribution.metadata.get('License','See upstream notices')})
(licenses/'python-components.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
manifest = {'app': version, 'engine': 'Blender 4.5.14 LTS', 'engine_build': config['blender_build'],
            'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
            'engine_sha256': hashlib.sha256((dest / 'engine/blender.exe').read_bytes()).hexdigest(),
            'app_sha256': hashlib.sha256((dest / 'Nukify.exe').read_bytes()).hexdigest()}
(dest / 'release.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
