# SPDX-License-Identifier: GPL-3.0-or-later
"""Inspect staged publication contents without printing possible secret values."""
import json,re,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
files=[p for p in subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0') if p]
patterns=[r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'\bAKIA[0-9A-Z]{16}\b',r'\bgh[pousr]_[A-Za-z0-9]{30,}\b',r'github_pat_[A-Za-z0-9_]{40,}']
issues=[];total=0
for name in files:
    path=root/name;total+=path.stat().st_size
    if name.startswith(('releases/','build/','dist/','validation/','sources/','desktop/vendor/','.buildenv/','.venv/')):issues.append((name,'Generated or private directory'))
    if path.stat().st_size>10*1024**2:issues.append((name,'Large tracked file'))
    if path.suffix.lower() in ('.py','.md','.txt','.json','.yml','.ps1','.cmd'):
        text=path.read_text(encoding='utf-8-sig',errors='replace')
        if any(re.search(pattern,text) for pattern in patterns):issues.append((name,'Possible credential pattern'))
print(json.dumps({'files':len(files),'total_bytes':total,'issues':issues},indent=2))
raise SystemExit(1 if issues else 0)
