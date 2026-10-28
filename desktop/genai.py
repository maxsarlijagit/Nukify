# SPDX-License-Identifier: GPL-3.0-or-later
"""fal queue transport, schema contracts and durable local generation history.

No inference or upload happens on import. Credentials are memory/environment only.
"""
import copy
import hashlib
import ipaddress
import json
import math
import mimetypes
import os
from pathlib import Path
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone

API = 'https://api.fal.ai/v1'
QUEUE = 'https://queue.fal.run'
CATEGORIES = {'text-to-image': 'Generar imagen', 'image-to-image': 'Editar imagen',
              'text-to-video': 'Generar video', 'image-to-video': 'Imagen a video',
              'video-to-video': 'Editar video'}


def now():
    return datetime.now(timezone.utc).isoformat()


def endpoint_id(value):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_.-]+)+', value):
        raise ValueError('Endpoint fal inválido')
    if any(p in ('.', '..') for p in value.split('/')):
        raise ValueError('Endpoint fal inválido')
    return value


def public_url(value):
    p = urllib.parse.urlsplit(value)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.port not in (None, 443):
        raise ValueError('Se requiere una URL HTTPS pública')
    for result in socket.getaddrinfo(p.hostname, 443, type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(result[4][0]).is_global:
            raise ValueError('No se permiten direcciones de red local')
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward a fal key or upload token through redirects.
        if req.has_header('Authorization'):
            raise ValueError('Redirección de API rechazada')
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class FalError(RuntimeError):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


class FalClient:
    def __init__(self, key=''):
        self.key = key.strip()
        self.opener = urllib.request.build_opener(NoRedirect())

    def request(self, url, method='GET', body=None, authenticated=True, headers=None):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname not in ('api.fal.ai', 'queue.fal.run', 'rest.fal.ai', 'fal.ai'):
            raise ValueError('Destino de API no permitido')
        h = {'Accept': 'application/json', 'User-Agent': 'Nukify-GENAI/1'}
        if authenticated:
            if not self.key:
                raise ValueError('Configurá FAL_KEY o una clave de sesión')
            h['Authorization'] = 'Key ' + self.key
        if body is not None:
            body = json.dumps(body, allow_nan=False).encode()
            h['Content-Type'] = 'application/json'
        h.update(headers or {})
        try:
            with self.opener.open(urllib.request.Request(url, data=body, headers=h, method=method), timeout=60) as response:
                return json.loads(response.read(16 * 1024 * 1024))
        except urllib.error.HTTPError as exc:
            # Do not expose response bodies, which may echo keys, prompts or signed URLs.
            raise FalError(f'fal HTTP {exc.code}. Revisá la clave, permisos, saldo y parámetros.', exc.code) from None
        except (OSError, ValueError) as exc:
            if isinstance(exc, FalError):
                raise
            raise FalError('No se pudo confirmar la respuesta de fal. No se reenvía automáticamente.') from None

    def search(self, category, query='', cursor=None):
        params = dict(category=category, q=query, status='active', sort='relevant', limit=30)
        if cursor:
            params['cursor'] = cursor
        return self.request(API + '/models?' + urllib.parse.urlencode(params), authenticated=False)

    def schema(self, endpoint):
        return self.request('https://fal.ai/api/openapi/queue/openapi.json?' +
                            urllib.parse.urlencode({'endpoint_id': endpoint_id(endpoint)}), authenticated=False)

    def estimate(self, endpoint, units):
        endpoint_id(endpoint)
        if not math.isfinite(units) or units <= 0:
            raise ValueError('Unidades de facturación inválidas')
        prices = self.request(API + '/models/pricing?' + urllib.parse.urlencode({'endpoint_id': endpoint}))
        price = next(p for p in prices['prices'] if p['endpoint_id'] == endpoint)
        result = self.request(API + '/models/pricing/estimate', 'POST', {
            'estimate_type': 'unit_price', 'endpoints': {endpoint: {'unit_quantity': units}}})
        if not math.isfinite(result['total_cost']) or result['total_cost'] < 0:
            raise ValueError('Estimación inválida')
        return dict(result, unit=price['unit'], unit_price=price['unit_price'], units=units, at=now())

    def submit(self, endpoint, payload):
        return self.request(QUEUE + '/' + endpoint_id(endpoint), 'POST', payload,
                            headers={'X-Fal-No-Retry': '1', 'x-app-fal-disable-fallback': 'true'})

    def queue_request(self, url, method='GET'):
        p = urllib.parse.urlsplit(url)
        if p.scheme != 'https' or p.netloc != 'queue.fal.run' or '/requests/' not in p.path:
            raise ValueError('URL de seguimiento inválida')
        return self.request(url, method)

    def upload(self, path):
        path = Path(path)
        if path.stat().st_size > 512 * 1024 * 1024:
            raise ValueError('Archivo mayor a 512 MB: prepará un proxy más pequeño')
        mime = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        info = self.request('https://rest.fal.ai/storage/upload/initiate?storage_type=gcs', 'POST',
                            {'file_name': 'input' + path.suffix.lower(), 'content_type': mime})
        public_url(info['upload_url'])
        public_url(info['file_url'])
        with path.open('rb') as source:
            req = urllib.request.Request(info['upload_url'], data=source, method='PUT', headers={
                'Content-Type': mime, 'Content-Length': str(path.stat().st_size)})
            with self.opener.open(req, timeout=120) as response:
                response.read(1024)
        return info['file_url']

    def download(self, url, target):
        public_url(url)
        target = Path(target)
        temporary = target.with_suffix(target.suffix + '.part')
        try:
            with self.opener.open(url, timeout=120) as response, temporary.open('wb') as output:
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > 2 * 1024**3:
                        raise ValueError('Resultado mayor a 2 GB')
                    output.write(chunk)
            if not total:
                raise ValueError('Resultado vacío')
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        return str(target)


def resolve(schema, document):
    if '$ref' in schema:
        ref = schema['$ref']
        if not ref.startswith('#/'):
            raise ValueError('Referencia de schema externa no admitida')
        value = document
        for key in ref[2:].split('/'):
            value = value[key.replace('~1', '/').replace('~0', '~')]
        return dict(value, **{k: v for k, v in schema.items() if k != '$ref'})
    return schema


def input_schema(document):
    for value in document['paths'].values():
        if 'requestBody' in value.get('post', {}):
            return resolve(value['post']['requestBody']['content']['application/json']['schema'], document)
    raise ValueError('El modelo no publica un schema de entrada')


def field_schema(schema, document):
    schema = resolve(schema, document)
    choices = schema.get('anyOf', schema.get('oneOf', []))
    if choices:
        return dict(schema, **resolve(next((s for s in choices if s.get('type') != 'null'), choices[0]), document))
    return schema


def validate(value, schema, document, path='input', depth=0):
    """Validate the JSON Schema constraints used by the supported model forms."""
    if depth > 30:
        raise ValueError('Schema demasiado profundo')
    schema = resolve(schema, document)
    choices = schema.get('anyOf', schema.get('oneOf'))
    if choices:
        for choice in choices:
            try:
                validate(value, choice, document, path, depth + 1)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f'{path}: valor incompatible con el schema')
    for part in schema.get('allOf', []):
        validate(value, part, document, path, depth + 1)
    kind = schema.get('type')
    checks = {'string': isinstance(value, str), 'integer': type(value) is int,
              'number': type(value) in (int, float) and math.isfinite(value),
              'object': isinstance(value, dict), 'array': isinstance(value, list),
              'boolean': type(value) is bool, 'null': value is None}
    if kind and not any(checks.get(k, False) for k in (kind if isinstance(kind, list) else [kind])):
        raise ValueError(f'{path}: se esperaba {kind}')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(f'{path}: opción inválida')
    if isinstance(value, dict):
        for required in schema.get('required', []):
            if required not in value:
                raise ValueError(f'{path}: falta {required}')
        props = schema.get('properties', {})
        for key, child in value.items():
            if key in props:
                validate(child, props[key], document, path + '.' + key, depth + 1)
            elif schema.get('additionalProperties') is False:
                raise ValueError(f'{path}: campo desconocido {key}')
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', float('inf')):
            raise ValueError(f'{path}: cantidad de elementos inválida')
        for child in value:
            validate(child, schema.get('items', {}), document, path + '[]', depth + 1)
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or len(value) > schema.get('maxLength', float('inf')):
            raise ValueError(f'{path}: longitud inválida')
    if type(value) in (int, float):
        if not math.isfinite(value) or value < schema.get('minimum', -float('inf')) or value > schema.get('maximum', float('inf')):
            raise ValueError(f'{path}: fuera de rango')


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


class JobStore:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, spec, estimate):
        # UUID separates concurrent sessions; exclusive mkdir reserves the revision.
        slug = re.sub(r'[^\w-]+', '-', spec['asset']).strip('-')[:60] or 'asset'
        base = self.root / slug
        base.mkdir(exist_ok=True)
        version = 1
        while True:
            directory = base / f'v{version:04d}'
            try:
                directory.mkdir()
                break
            except FileExistsError:
                version += 1
        job = dict(id=uuid.uuid4().hex, version=version, directory=str(directory), spec=copy.deepcopy(spec),
                   estimate=copy.deepcopy(estimate), created=now(), state='PREPARING', outputs=[], events=[])
        self.save(job)
        return job

    def save(self, job):
        job['updated'] = now()
        path = Path(job['directory']) / 'job.json'
        # Credentials are intentionally never a member of the job/spec.
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps({k: v for k, v in job.items() if k != 'live_logs'}, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        temporary.replace(path)

    def list(self):
        jobs = []
        for path in self.root.glob('*/v*/job.json'):
            try:
                job = json.loads(path.read_text(encoding='utf-8'))
                job['directory'] = str(path.parent)
                jobs.append(job)
            except (OSError, ValueError):
                continue
        return sorted(jobs, key=lambda j: j['created'], reverse=True)


def output_files(result):
    files = result.get('images') or ([result['image']] if result.get('image') else [])
    if result.get('video'):
        files = [result['video']]
    if not files:
        raise ValueError('fal no devolvió imágenes ni video descargables')
    if not isinstance(files, list) or len(files) > 32:
        raise ValueError('Respuesta de medios inválida')
    return files
