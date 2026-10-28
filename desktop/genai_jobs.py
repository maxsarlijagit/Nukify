# SPDX-License-Identifier: GPL-3.0-or-later
"""Recoverable queue lifecycle; no automatic re-submission of paid operations."""
import copy
import hashlib
from pathlib import Path
import time
import urllib.parse
from genai import FalError, now, output_files, input_schema, validate, fingerprint
from genai_media import proxy, sequence, VIDEO, IMAGE


def local_inputs(payload):
    """Only explicit local: references are uploads; ordinary strings stay strings."""
    found = []
    def walk(value):
        if isinstance(value, str) and value.startswith('local:'):
            path = Path(value[6:]).resolve()
            if not path.is_file() or path.suffix.lower() not in VIDEO | IMAGE:
                raise ValueError('Medio local inexistente o formato no soportado')
            found.append(str(path))
        elif isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    # Upload markers are only accepted in media URL fields, never in a prompt.
    for key, value in payload.items():
        if key.endswith(('_url', '_urls')):
            walk(value)
    return sorted(set(found))


def input_signature(payload):
    return {name: {'size': Path(name).stat().st_size, 'mtime': Path(name).stat().st_mtime_ns}
            for name in local_inputs(payload)}


class JobRunner:
    def __init__(self, client, store, progress=lambda job: None, stop=None):
        import threading
        self.client, self.store, self.progress = client, store, progress
        self.stop = stop or threading.Event()

    def event(self, job, state, message):
        job['state'] = state
        job['events'].append({'at': now(), 'message': message})
        job['events'] = job['events'][-150:]
        self.store.save(job)
        self.progress(copy.deepcopy(job))

    def start(self, spec, estimate):
        if estimate.get('spec_hash') != fingerprint(spec) or not 0 <= time.time() - estimate.get('received', 0) <= 300:
            raise ValueError('Estimación vencida o no corresponde a estos parámetros')
        if input_signature(spec['payload']) != spec['input_signature']:
            raise ValueError('Cambió un medio desde la estimación. Calculá de nuevo.')
        validate(spec['payload'], input_schema(spec['schema']), spec['schema'])
        job = self.store.create(spec, estimate)
        try:
            payload = copy.deepcopy(spec['payload'])
            uploads = {}
            for i, source in enumerate(local_inputs(payload)):
                self.event(job, 'UPLOADING', f'Preparando y enviando medio {i + 1}')
                if self.stop.is_set():
                    self.event(job, 'STOPPED', 'Preparación detenida antes de enviar la generación')
                    return job
                media = proxy(source, Path(job['directory']) / f'input_{i}', spec['send_proxy'], spec['ffmpeg'])
                uploads[source] = self.client.upload(media)
            def replace(value):
                if isinstance(value, str) and value.startswith('local:'):
                    return uploads[str(Path(value[6:]).resolve())]
                if isinstance(value, list):
                    return [replace(v) for v in value]
                if isinstance(value, dict):
                    return {k: replace(v) for k, v in value.items()}
                return value
            for key in payload:
                if key.endswith(('_url', '_urls')):
                    payload[key] = replace(payload[key])
            if self.stop.is_set():
                self.event(job, 'STOPPED', 'Preparación detenida; no se envió la generación')
                return job
            self.event(job, 'SUBMITTING', 'Enviando una solicitud a fal')
            remote = self.client.submit(spec['endpoint'], payload)
            job['remote'] = {k: remote[k] for k in ('request_id', 'status_url', 'response_url', 'cancel_url') if k in remote}
            self.store.save(job)  # Persist request id before any further network operation.
            if not all(k in job['remote'] for k in ('request_id', 'status_url', 'response_url')):
                self.event(job, 'UNKNOWN', 'Respuesta incompleta. Revisá fal antes de volver a generar.')
                return job
        except Exception as exc:
            state = 'UNKNOWN' if job['state'] == 'SUBMITTING' else 'FAILED'
            self.event(job, state, 'No se confirmó el envío; revisá fal antes de reintentar.' if state == 'UNKNOWN'
                       else 'Falló la preparación o subida de medios. No se envió la generación.')
            return job
        return self.resume(job)

    def resume(self, job):
        if not job.get('remote', {}).get('request_id'):
            raise ValueError('Sin request ID: no se puede reanudar ni reenviar automáticamente')
        try:
            while not self.stop.is_set():
                remote = job['remote']
                url = remote['status_url']
                status = self.client.queue_request(url + ('&' if '?' in url else '?') + 'logs=1')
                if status.get('error'):
                    self.event(job, 'FAILED', 'fal informó un error. Consultá el request ID en el dashboard.')
                    return job
                state = status['status']
                if state not in ('IN_QUEUE', 'IN_PROGRESS', 'COMPLETED'):
                    raise ValueError('Estado desconocido')
                message = state
                if state == 'IN_QUEUE':
                    message += ' · posición ' + str(status.get('queue_position', '?'))
                # Logs are shown in memory only; redact the configured key and URL tokens.
                logs = status.get('logs') or []
                if isinstance(logs, list):
                    import re
                    job['live_logs'] = [re.sub(r'https?://\S+', '[URL]', str(x.get('message', '')))
                                        .replace(self.client.key, '[clave]')[:500]
                                        for x in logs[-10:] if isinstance(x, dict)] if self.client.key else []
                self.event(job, 'REMOTE_COMPLETED' if state == 'COMPLETED' else state, message)
                if state == 'COMPLETED':
                    result = self.client.queue_request(remote['response_url'])
                    if result.get('error'):
                        self.event(job, 'FAILED', 'fal devolvió un error de generación')
                        return job
                    return self.receive(job, result)
                if self.stop.wait(3):
                    break
            self.event(job, 'PAUSED', 'Seguimiento pausado; el trabajo remoto puede seguir y cobrar')
        except FalError as exc:
            self.event(job, 'FAILED' if exc.code in (400, 422) else 'PAUSED', str(exc))
        except Exception:
            self.event(job, 'PAUSED', 'Seguimiento o descarga interrumpidos. Reanudar no genera otro cobro.')
        return job

    def receive(self, job, result):
        self.event(job, 'DOWNLOADING', 'Recibiendo originales')
        directory = Path(job['directory'])
        outputs = []
        for index, item in enumerate(output_files(result)):
            url = item['url']
            suffix = Path(urllib.parse.urlsplit(url).path).suffix.lower()
            if suffix not in VIDEO | IMAGE:
                mime = item.get('content_type', '')
                suffix = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp',
                          'video/mp4': '.mp4', 'video/webm': '.webm'}.get(mime)
            if not suffix:
                raise ValueError('Formato de resultado no admitido')
            target = directory / f'original_{index:02d}{suffix}'
            self.client.download(url, target)
            if suffix in IMAGE:
                from PIL import Image
                with Image.open(target) as downloaded:
                    downloaded.verify()
            with target.open('rb') as f:
                digest = hashlib.file_digest(f, 'sha256').hexdigest()
            entry = dict(original=str(target), sha256=digest, proxy=None, preview=None)
            outputs.append(entry)
            job['outputs'] = outputs
            self.store.save(job)
            try:
                self.event(job, 'PROXY', f'Preparando proxy del resultado {index + 1}')
                entry['proxy'] = proxy(target, directory / f'receive_{index}', job['spec']['receive_proxy'], job['spec']['ffmpeg'])
                if suffix in VIDEO:
                    entry['preview'] = sequence(entry['proxy'], directory / f'preview_{index}', job['spec']['ffmpeg'], True)
            except Exception:
                entry['proxy_error'] = 'Original guardado. Configurá FFmpeg o revisá el medio para preparar el proxy.'
        self.event(job, 'READY', 'Originales guardados; disponibles en la biblioteca')
        return job
