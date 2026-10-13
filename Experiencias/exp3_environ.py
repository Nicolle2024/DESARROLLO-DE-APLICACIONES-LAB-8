import json
from wsgiref.simple_server import make_server


def inspector_entorno_wsgi(environ, start_response):
    entorno_legible = {}
    for clave, valor in environ.items():
        if isinstance(valor, str):
            entorno_legible[clave] = valor

    texto_diagnostico = json.dumps(entorno_legible, indent=4)
    cuerpo_bytes = texto_diagnostico.encode("utf-8")

    start_response("200 OK", [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(cuerpo_bytes)))
    ])
    return [cuerpo_bytes]


if __name__ == "__main__":
    print("Inspector WSGI en http://localhost:8080  (Ctrl+C para detener)")
    make_server("127.0.0.1", 8080, inspector_entorno_wsgi).serve_forever()