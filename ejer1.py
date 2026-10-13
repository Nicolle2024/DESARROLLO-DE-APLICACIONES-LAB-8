"""
Ejercicio 1: Micro-Framework WSGI con Middleware de Seguridad por Token
y Deserializador Polimórfico (PEP 3333, solo biblioteca estándar).

Ejecución:
    python ejercicio1_wsgi.py

Pruebas con curl:
    # 401 (sin token)
    curl -i -X POST http://127.0.0.1:8080/api/inscripciones

    # 201 (JSON)
    curl -i -X POST http://127.0.0.1:8080/api/inscripciones \
      -H "Authorization: Bearer TOKEN_SECRETO_2026" \
      -H "Content-Type: application/json" \
      -d '{"dni":"12345678","correo_electronico":"a@b.com","programa_academico":"Ingenieria de Sistemas"}'

    # 201 (formulario clásico)
    curl -i -X POST http://127.0.0.1:8080/api/inscripciones \
      -H "Authorization: Bearer TOKEN_SECRETO_2026" \
      -d "dni=12345678&correo_electronico=a@b.com&programa_academico=Sistemas"

    # 400 (falta programa_academico)
    curl -i -X POST http://127.0.0.1:8080/api/inscripciones \
      -H "Authorization: Bearer TOKEN_SECRETO_2026" \
      -H "Content-Type: application/json" \
      -d '{"dni":"12345678","correo_electronico":"a@b.com"}'
"""

import hmac
import json
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

TOKEN_SECRETO = "Bearer TOKEN_SECRETO_2026"
RUTA_INSCRIPCIONES = "/api/inscripciones"
LLAVES_OBLIGATORIAS = ("dni", "correo_electronico", "programa_academico")
LIMITE_MAXIMO_PAYLOAD = 1024 * 1024  

def responder_json(start_response, estado, datos, cabeceras_extra=None):
    """Serializa `datos` a JSON/UTF-8, invoca start_response y retorna el iterable."""
    cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
    cabeceras = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(cuerpo))),
    ]
    if cabeceras_extra:
        cabeceras.extend(cabeceras_extra)
    start_response(estado, cabeceras)
    return [cuerpo]


class MiddlewareTokenSeguridad:
    """Intercepta toda petición; si el token no es válido hace short-circuit (401)."""

    def __init__(self, aplicacion_interna, token_esperado=TOKEN_SECRETO):
        self.aplicacion_interna = aplicacion_interna
        self.token_esperado = token_esperado

    def __call__(self, environ, start_response):
        token_recibido = environ.get("HTTP_AUTHORIZATION", "")

        valido = hmac.compare_digest(
            token_recibido.encode("utf-8"), self.token_esperado.encode("utf-8")
        )

        if not valido:
            mensaje = b"401 Unauthorized: token ausente o invalido. Use 'Authorization: Bearer <token>'."
            start_response(
                "401 Unauthorized",
                [
                    ("Content-Type", "text/plain; charset=utf-8"),
                    ("Content-Length", str(len(mensaje))),
                    ("WWW-Authenticate", "Bearer"),
                ],
            )
            return [mensaje]

        return self.aplicacion_interna(environ, start_response)


class ErrorIngesta(Exception):
    """Error controlado durante la ingesta (lleva su código HTTP)."""

    def __init__(self, estado, mensaje):
        super().__init__(mensaje)
        self.estado = estado
        self.mensaje = mensaje


def leer_cuerpo(environ):
    """Lectura estricta de wsgi.input limitada por CONTENT_LENGTH (evita hang-ups)."""
    try:
        longitud = int(environ.get("CONTENT_LENGTH", "0") or "0")
    except ValueError:
        raise ErrorIngesta("400 Bad Request", "CONTENT_LENGTH no es un entero valido.")

    if longitud <= 0:
        raise ErrorIngesta("400 Bad Request", "Payload vacio (Content-Length ausente o 0).")
    if longitud > LIMITE_MAXIMO_PAYLOAD:
        raise ErrorIngesta("413 Payload Too Large", "El cuerpo excede el limite permitido.")

    return environ["wsgi.input"].read(longitud)


def deserializar_payload(content_type, cuerpo_bytes):
    """Selecciona la estrategia de deserialización según Content-Type."""
    try:
        texto = cuerpo_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ErrorIngesta("400 Bad Request", "El cuerpo no es UTF-8 valido.")

    tipo = content_type.lower()

    if "application/json" in tipo:
        try:
            dto = json.loads(texto)
        except json.JSONDecodeError:
            raise ErrorIngesta("400 Bad Request", "JSON mal formado.")
        if not isinstance(dto, dict):
            raise ErrorIngesta("400 Bad Request", "El JSON debe ser un objeto (diccionario).")
        return dto

    if "application/x-www-form-urlencoded" in tipo:
        diccionario_listas = parse_qs(texto, keep_blank_values=True)
        return {k: v[0] for k, v in diccionario_listas.items()}

    raise ErrorIngesta(
        "415 Unsupported Media Type",
        "Content-Type debe ser application/json o application/x-www-form-urlencoded.",
    )


def validar_esquema(dto):
    """Lanza ErrorIngesta 400 en cuanto detecta una llave obligatoria ausente o vacía."""
    faltantes = [
        llave
        for llave in LLAVES_OBLIGATORIAS
        if llave not in dto or str(dto[llave]).strip() == ""
    ]
    if faltantes:
        raise ErrorIngesta(
            "400 Bad Request",
            f"Violacion del esquema. Parametros faltantes: {faltantes}",
        )


class AplicacionInscripciones:
    def __call__(self, environ, start_response):
        ruta = environ.get("PATH_INFO", "/")
        metodo = environ.get("REQUEST_METHOD", "GET")

        if ruta != RUTA_INSCRIPCIONES:
            return responder_json(
                start_response, "404 Not Found", {"error": f"Ruta no encontrada: {ruta}"}
            )

        if metodo != "POST":
            return responder_json(
                start_response,
                "405 Method Not Allowed",
                {"error": f"Metodo {metodo} no permitido. Use POST."},
                cabeceras_extra=[("Allow", "POST")],
            )

        try:
            cuerpo = leer_cuerpo(environ)
            dto = deserializar_payload(environ.get("CONTENT_TYPE", ""), cuerpo)
            validar_esquema(dto)
        except ErrorIngesta as e:
            return responder_json(start_response, e.estado, {"error": e.mensaje})

        return responder_json(
            start_response,
            "201 Created",
            {
                "estado": "Inscripcion registrada exitosamente",
                "datos": {k: dto[k] for k in LLAVES_OBLIGATORIAS},
            },
        )


app = MiddlewareTokenSeguridad(AplicacionInscripciones())

if __name__ == "__main__":
    puerto = 8080
    with make_server("127.0.0.1", puerto, app) as servidor:
        print(f"Servidor WSGI escuchando en http://127.0.0.1:{puerto}{RUTA_INSCRIPCIONES}")
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")
