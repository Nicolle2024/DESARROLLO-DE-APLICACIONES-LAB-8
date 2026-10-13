import json
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server


def endpoint_recepcion_estricta(environ, start_response):
    if environ.get("REQUEST_METHOD") not in ["POST", "PUT"]:
        start_response("405 Method Not Allowed", [("Content-Type", "application/json")])
        return [b'{"error": "Metodo transaccional bloqueado"}']

    try:
        tamano_buffer = int(environ.get("CONTENT_LENGTH", "0") or "0")
    except ValueError:
        tamano_buffer = 0
    if tamano_buffer <= 0:
        start_response("400 Bad Request", [("Content-Type", "application/json")])
        return [b'{"error": "Rechazo: Payload vacio (Zero Bytes)"}']

    cuerpo_bytes = environ["wsgi.input"].read(tamano_buffer)
    metadato_formato = environ.get("CONTENT_TYPE", "")

    try:
        if "application/json" in metadato_formato:
            dto_diccionario = json.loads(cuerpo_bytes.decode("utf-8"))
        elif "application/x-www-form-urlencoded" in metadato_formato:
            diccionario_listas = parse_qs(cuerpo_bytes.decode("utf-8"))
            dto_diccionario = {k: v[0] for k, v in diccionario_listas.items()}
        else:
            start_response("415 Unsupported Media Type", [("Content-Type", "application/json")])
            return [b'{"error": "El servidor exige formatos JSON o URL-Encoded"}']
    except (json.JSONDecodeError, ValueError):
        start_response("400 Bad Request", [("Content-Type", "application/json")])
        return [b'{"error": "Corrupcion detectada en el formato de transferencia"}']

    if not isinstance(dto_diccionario, dict):
        start_response("400 Bad Request", [("Content-Type", "application/json")])
        return [b'{"error": "Se esperaba un objeto con propiedades"}']

    llaves_obligatorias = {"identificador", "token_operacion", "comando"}
    llaves_faltantes = sorted(llaves_obligatorias - dto_diccionario.keys())
    if llaves_faltantes:
        start_response("400 Bad Request", [("Content-Type", "application/json")])
        mensaje = json.dumps({"error": "Violacion del esquema. Faltan propiedades", "faltantes": llaves_faltantes})
        return [mensaje.encode("utf-8")]

    respuesta_ok = json.dumps({"estado": "Payload estandarizado y auditado exitosamente", "datos": dto_diccionario})
    cuerpo = respuesta_ok.encode("utf-8")
    start_response("200 OK", [
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(cuerpo)))
    ])
    return [cuerpo]


if __name__ == "__main__":
    print("Receptor de payloads en http://localhost:8080  (Ctrl+C para detener)")
    make_server("", 8080, endpoint_recepcion_estricta).serve_forever()