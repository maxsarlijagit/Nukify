# SPDX-License-Identifier: GPL-3.0-or-later
"""Fetch unmodified upstream source archives and preserve their license notices."""
import hashlib,json,shutil,tarfile,urllib.request
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
def main():
    config=json.loads((ROOT/'packaging/release.json').read_text())
    directory=ROOT/'sources';directory.mkdir(exist_ok=True);manifest=[]
    for url in config['source_urls']:
        path=directory/url.rsplit('/',1)[1]
        if not path.is_file():
            print('Downloading '+path.name,flush=True)
            temp=path.with_suffix(path.suffix+'.part')
            with urllib.request.urlopen(url,timeout=90) as response,temp.open('wb') as out:shutil.copyfileobj(response,out)
            with tarfile.open(temp):pass
            temp.replace(path)
        manifest.append(dict(file=path.name,url=url,sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()))
        if path.name.startswith(('qt','pyside')):
            with tarfile.open(path) as archive:
                for member in archive:
                    parts=PurePosixPath(member.name).parts
                    if not member.isfile() or member.size>2_000_000 or '..' in parts:continue
                    if not any(word in parts[-1].lower() for word in ('license','copying','notice','copyright')) and 'LICENSES' not in parts:continue
                    if not parts[-1].lower().endswith(('.txt','.md','.rst','.html')) and parts[-1].upper() not in ('LICENSE','COPYING','NOTICE'):continue
                    target=ROOT/'licenses/upstream'/Path(*parts)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with archive.extractfile(member) as src,target.open('wb') as out:shutil.copyfileobj(src,out)
        print('Ready '+path.name,flush=True)
    (directory/'upstream-sources.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
if __name__=='__main__':main()
