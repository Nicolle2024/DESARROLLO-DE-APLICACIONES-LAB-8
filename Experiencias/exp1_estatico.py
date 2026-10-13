import os
import mimetypes
from http.server import BaseHTTPRequestHandler, HTTPServer

DIRECTORIO_BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "public"))


class ServidorEstaticoFortificado(BaseHTTPRequestHandler):
    def do_GET(self):
        ruta_cruda = self.path.split("?", 1)[0].lstrip("/")
        if not ruta_cruda:
            ruta_cruda = "index.html"

        ruta_resuelta = os.path.abspath(os.path.join(DIRECTORIO_BASE, ruta_cruda))

        if not ruta_resuelta.startswith(DIRECTORIO_BASE + os.sep) or not os.path.isfile(ruta_resuelta):
            self.send_error(404, "Recurso no encontrado o acceso estrictamente denegado.")
            return

        tipo_mime, _ = mimetypes.guess_type(ruta_resuelta)

        try:
            with open(ruta_resuelta, "rb") as archivo_fisico:
                contenido = archivo_fisico.read()

            self.send_response(200)
            self.send_header("Content-Type", tipo_mime or "application/octet-stream")
            self.send_header("Content-Length", str(len(contenido)))
            self.end_headers()
            self.wfile.write(contenido)
        except IOError:
            self.send_error(500, "Error del sistema al intentar acceder al archivo físico.")


if __name__ == "__main__":
    print("Servidor estático en http://localhost:8000  (Ctrl+C para detener)")
    HTTPServer(("localhost", 8000), ServidorEstaticoFortificado).serve_forever()