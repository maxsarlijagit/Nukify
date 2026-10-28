# SPDX-License-Identifier: GPL-3.0-or-later
"""Single persistent Blender process; one in-flight job and latest request wins."""
import copy
import ctypes
import hashlib
import json
from pathlib import Path
import sys
from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, Signal
from model import evaluation_order, sequence_path,active_inputs
from animation import parameters,render_parameters


def fingerprint(graph, target, frame, proxy):
    nodes = evaluation_order(graph, target, frame)
    data = {'schema': 8, 'target': target, 'frame': frame, 'proxy': proxy,
            'width': graph['width'], 'height': graph['height'], 'nodes': [], 'engine': graph['blender'], 'ocio': graph.get('ocio','')}
    if graph.get('ocio'):
        p = Path(graph['ocio']); st = p.stat()
        data['ocio_stat'] = [st.st_size, st.st_mtime_ns]
    for node, time in nodes:
        n = dict(id=node['id'],kind=node['kind'],disabled=node.get('disabled',False),inputs=active_inputs(node,time,graph),evaluated_frame=time)
        n['evaluated_params']=render_parameters(node,time,graph)
        # Reference corners affect inverse planar geometry independently of current values.
        if node.get('tracking_reference_corners'):n['tracking_reference_corners']=node['tracking_reference_corners']
        if node['kind'] in ('Read','Cryptomatte'):
            path = Path(sequence_path(parameters(node,time)['path'], time))
            stat = path.stat()
            n['media'] = [str(path.resolve()), stat.st_size, stat.st_mtime_ns]
        data['nodes'].append(n)
        if node['params'].get('texture_path'):
            p=Path(node['params']['texture_path']);s=p.stat();n['texture_stat']=[str(p.resolve()),s.st_size,s.st_mtime_ns]
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:28]



class LiveEngine(QObject):
    ready = Signal(dict)
    failed = Signal(str)
    message = Signal(str)

    def __init__(self, root, cache, parent=None):
        super().__init__(parent)
        self.root, self.cache = Path(root), Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.process = None
        self.executable = None
        self.busy = None
        self.pending = None
        self.buffer = b''
        self.jobs_sent = 0
        self.starts = 0
        self.stopping = False

    def cached(self, key):
        meta = self.cache / (key + '.json')
        try:
            info = json.loads(meta.read_text())
            raw = Path(info['raw'])
            if raw.stat().st_size == info['width'] * info['height'] * 16:
                return info
        except (OSError, ValueError, KeyError):
            pass
        return None

    def request(self, graph, target, frame, proxy=1):
        key = fingerprint(graph, target, frame, proxy)
        cached = self.cached(key)
        if cached:
            Path(cached['raw']).touch()
            self.pending = None
            self.ready.emit(dict(cached, key=key, frame=frame, target=target, cached=True))
            return key
        request = {'key': key, 'graph': copy.deepcopy(graph), 'target': target,
                   'frame': frame, 'proxy': proxy, 'cache': str(self.cache)}
        if self.busy and self.busy['key'] == key:
            self.pending = None
            return key
        if self.busy:
            self.pending = request
        else:
            self.send(request)
        return key

    def send(self, request):
        executable = request['graph']['blender']
        if not Path(executable).is_file():
            self.failed.emit('Falta el motor incluido. Reinstala Nukify para repararlo.')
            return
        ocio = request['graph'].get('ocio', '')
        if self.process and (self.executable != executable or getattr(self, 'ocio', '') != ocio):
            self.stop()
        if not self.process:
            self.stopping = False
            self.buffer = b''
            self.executable = executable
            self.ocio = ocio
            self.process = QProcess(self)
            env = QProcessEnvironment.systemEnvironment()
            for key in ('PYTHONHOME', 'PYTHONPATH', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH'):
                env.remove(key)
            env.insert('PYTHONUNBUFFERED', '1')
            if ocio: env.insert('OCIO', ocio)
            else: env.remove('OCIO')
            self.process.setProcessEnvironment(env)
            self.process.setProcessChannelMode(QProcess.MergedChannels)
            self.process.readyReadStandardOutput.connect(self.read)
            self.process.finished.connect(self.exited)
            frozen = sys.platform == 'win32' and getattr(sys, 'frozen', False)
            if frozen:
                ctypes.windll.kernel32.SetDllDirectoryW(None)
            try:
                self.process.start(executable, ['--background', '--factory-startup', '--threads', '4',
                    '--python-exit-code', '1', '--python', str(self.root / 'desktop' / 'worker.py'), '--', '--serve'])
                started = self.process.waitForStarted(5000)
            finally:
                if frozen:
                    ctypes.windll.kernel32.SetDllDirectoryW(str(self.root))
            if not started:
                self.process.deleteLater()
                self.process = None
                self.failed.emit('No se pudo iniciar el motor Blender.')
                return
            self.starts += 1
        self.busy = request
        self.jobs_sent += 1
        self.process.write((json.dumps(request) + '\n').encode())

    def read(self):
        if not self.process:
            return
        self.buffer += bytes(self.process.readAllStandardOutput())
        while b'\n' in self.buffer:
            line, self.buffer = self.buffer.split(b'\n', 1)
            text = line.decode('utf-8', errors='replace').strip()
            if not text.startswith('@@NUKIFY '):
                if text:
                    self.message.emit(text)
                continue
            result = json.loads(text[len('@@NUKIFY '):])
            if result.get('status') == 'ready':
                continue
            request = self.busy
            self.busy = None
            if request:
                if result.get('ok'):
                    self.ready.emit(dict(result, key=request['key'], frame=request['frame'], target=request['target'], cached=False))
                elif not self.pending:
                    self.failed.emit(result.get('error', 'Error de composicion'))
            if self.pending:
                next_job, self.pending = self.pending, None
                self.send(next_job)

    def exited(self, code, status):
        self.busy = self.pending = None
        if self.process:
            self.process.deleteLater()
            self.process = None
        if not self.stopping:
            self.failed.emit(f'El motor Blender se cerro ({code}). Cambia un parametro para reintentar.')

    def stop(self):
        self.stopping = True
        self.pending = self.busy = None
        if self.process:
            process, self.process = self.process, None
            process.blockSignals(True)
            process.kill()
            process.waitForFinished(3000)
            process.deleteLater()

    def prune(self, budget=None):
        """Only own cache pairs, oldest first. Call when no render is active."""
        if self.busy:
            return
        budget=budget if budget is not None else getattr(self,'budget',1024**3)
        files = sorted(self.cache.glob('*.rgba'), key=lambda p: p.stat().st_mtime)
        total = sum(p.stat().st_size for p in files)
        for raw in files:
            if total <= budget:
                break
            total -= raw.stat().st_size
            raw.unlink(missing_ok=True)
            raw.with_suffix('.json').unlink(missing_ok=True)
