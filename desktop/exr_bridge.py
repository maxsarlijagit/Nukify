# SPDX-License-Identifier: GPL-3.0-or-later
"""Keep third-party OpenEXR ABI out of Blender's process."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
import numpy as np


def call(task,**kwargs):
    python=Path(sys.executable)
    if python.name.lower()!='python.exe':python=python.parent/'4.5/python/bin/python.exe'
    if not python.is_file():raise ValueError('No se encuentra el Python incluido para EXR')
    with tempfile.TemporaryDirectory(prefix='nukify-exr-') as directory:
        root=Path(directory);job=dict(task=task,result=str(root/'result.json'),pixels=str(root/'pixels.npy'),**kwargs)
        path=root/'job.json';path.write_text(json.dumps(job),encoding='utf-8')
        env=dict(os.environ)
        for key in ('PYTHONPATH','PYTHONHOME'):env.pop(key,None)
        process=subprocess.run([str(python),str(Path(__file__).with_name('exr_io.py')),str(path)],env=env,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,timeout=120)
        if process.returncode:raise ValueError('EXR: '+process.stderr[-1500:])
        result=json.loads(Path(job['result']).read_text())
        if task=='read':return np.load(job['pixels'])
        return result
