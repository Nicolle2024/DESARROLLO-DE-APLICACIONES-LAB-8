import json
from http.server import BaseHTTPRequestHandler, HTTPServer

coleccion_usuarios = [
    {"id": 100, "nombre": "Linus Torvalds", "perfil": "SysAdmin"}
]


class EnrutadorAPI(BaseHTTPRequestHandler):

    def emitir_json(self, codigo_http, datos_diccionario):
        payload = json.dumps(datos_diccionario, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo_http)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/api/usuarios":
            self.emitir_json(200, {"estado": "ok", "total": len(coleccion_usuarios), "datos": coleccion_usuarios})
        else:
            self.emitir_json(404, {"error": "Endpoint no mapeado en la API"})

    def do_POST(self):
        if self.path == "/api/usuarios":
            try:
                longitud = int(self.headers.get("Content-Length", 0))
            except ValueError:
                return self.emitir_json(400, {"error": "Content-Length inválido"})
            if longitud > 1_000_000:
                return self.emitir_json(413, {"error": "Cuerpo demasiado grande"})

            bytes_recibidos = self.rfile.read(longitud)

            try:
                nuevo_registro = json.loads(bytes_recibidos.decode("utf-8"))
                if not isinstance(nuevo_registro, dict):
                    return self.emitir_json(400, {"error": "Se esperaba un objeto JSON"})

                nuevo_registro["id"] = coleccion_usuarios[-1]["id"] + 1 if coleccion_usuarios else 1
                coleccion_usuarios.append(nuevo_registro)
                self.emitir_json(201, {"estado": "creado", "datos": nuevo_registro})

            except (json.JSONDecodeError, UnicodeDecodeError):
                self.emitir_json(400, {"error": "El cuerpo de la petición debe ser JSON válido."})
        else:
            self.emitir_json(404, {"error": "Endpoint no mapeado en la API"})


if __name__ == "__main__":
    print("API REST en http://localhost:8000  (Ctrl+C para detener)")
    HTTPServer(("localhost", 8000), EnrutadorAPI).serve_forever()