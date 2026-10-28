import pefile
from pathlib import Path
root = Path(__file__).resolve().parents[1] / 'dist/Nukify/_internal'
files = {p.name.lower(): p for p in root.rglob('*') if p.suffix.lower() in ('.dll', '.pyd')}
for p in list(files.values()):
    if p.name not in ['QtCore.pyd', 'Qt6Core.dll', 'pyside6.abi3.dll', 'shiboken6.abi3.dll', 'icuuc.dll']:
        continue
    pe = pefile.PE(str(p))
    print(p.name)
    for imp in pe.DIRECTORY_ENTRY_IMPORT:
        name = imp.dll.decode()
        dep = files.get(name.lower())
        print('  ' + name)
        if dep:
            d = pefile.PE(str(dep))
            exports = {x.name for x in getattr(d, 'DIRECTORY_ENTRY_EXPORT', type('X', (), {'symbols': []})()).symbols}
            missing = [x.name for x in imp.imports if x.name and x.name not in exports]
            if missing:
                print('MISSING', missing[:30])
