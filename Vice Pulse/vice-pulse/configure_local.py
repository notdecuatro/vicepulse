"""One-use local credential setup. Binds to loopback and never logs submitted data."""
import json
import os
from pathlib import Path
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import tempfile
import threading
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent


def save_credentials(destination, supplied):
    if not isinstance(supplied, dict) or not supplied:
        raise ValueError('Faltan credenciales.')
    if set(supplied) - {'BUFFER_API_KEY', 'CLOUDINARY_URL'}:
        raise ValueError('Campo no permitido.')
    if any(not isinstance(v, str) or not v.strip() for v in supplied.values()):
        raise ValueError('Valor vacío o inválido.')
    if 'BUFFER_API_KEY' in supplied and (len(supplied['BUFFER_API_KEY']) < 20 or
                                        not supplied['BUFFER_API_KEY'].endswith('98DF')):
        raise ValueError('Se requiere la clave existente de Vice Pulse terminada en 98DF.')
    if 'CLOUDINARY_URL' in supplied:
        cloud = urlparse(supplied['CLOUDINARY_URL'])
        if cloud.scheme != 'cloudinary' or not all((cloud.username, cloud.password, cloud.hostname)):
            raise ValueError('Formato de Cloudinary inválido.')
    current = json.loads(destination.read_text()) if destination.exists() else {}
    current.update({k: v.strip() for k, v in supplied.items()})
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile('w', dir=destination.parent, delete=False) as out:
            temp_path = Path(out.name)
            os.fchmod(out.fileno(), 0o600)
            json.dump(current, out)
            out.flush()
            os.fsync(out.fileno())
        temp_path.replace(destination)
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


def main():
    csrf = secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, body, content_type='application/json'):
            raw = body.encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def allowed_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def do_GET(self):
            if not self.allowed_host() or self.path != '/':
                self.reply(404, '{}'); return
            html = (ROOT / 'configure.html').read_text().replace('__VICE_CSRF__', csrf)
            self.reply(200, html, 'text/html')

        def do_POST(self):
            origin = f'http://127.0.0.1:{self.server.server_port}'
            if not self.allowed_host() or self.path != '/save' or self.headers.get('Origin') != origin or not secrets.compare_digest(self.headers.get('X-Vice-CSRF', ''), csrf):
                self.reply(403, '{"message":"Solicitud no autorizada."}'); return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 10000:
                    raise ValueError('Tamaño inválido.')
                supplied = json.loads(self.rfile.read(length))
                save_credentials(ROOT / 'credentials.json', supplied)
            except (ValueError, OSError):
                self.reply(400, '{"message":"Revisa los valores. Usa la clave existente terminada en 98DF."}'); return
            self.reply(200, '{"message":"Conexión guardada en este Mac con permisos 0600. Puedes cerrar esta pestaña."}')
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        print(f'http://127.0.0.1:{server.server_port}/', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
