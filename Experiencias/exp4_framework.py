from wsgiref.simple_server import make_server
from datetime import datetime


class NucleoWSGI:
    def __init__(self):
        self.mapa_enrutamiento = {}

    def registrar_endpoint(self, ruta_esperada):
        def envoltura_compilacion(funcion_controlador):
            self.mapa_enrutamiento[ruta_esperada] = funcion_controlador
            return funcion_controlador
        return envoltura_compilacion

    def __call__(self, environ, start_response):
        ruta_solicitada = environ.get("PATH_INFO", "/")

        if ruta_solicitada in self.mapa_enrutamiento:
            respuesta_texto = self.mapa_enrutamiento[ruta_solicitada](environ)
            estado = "200 OK"
        else:
            respuesta_texto = "Error 404: Endpoint huérfano o no implementado."
            estado = "404 Not Found"

        payload = respuesta_texto.encode("utf-8")
        start_response(estado, [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(payload)))
        ])
        return [payload]


class MiddlewareAuditoria:
    def __init__(self, aplicacion_interior):
        self.aplicacion_interior = aplicacion_interior

    def __call__(self, environ, start_response):
        verbo = environ.get("REQUEST_METHOD")
        uri = environ.get("PATH_INFO")
        print(f"[Capa de Seguridad] -> Intento de acceso: {verbo} a la ruta {uri}")
        return self.aplicacion_interior(environ, start_response)


app = NucleoWSGI()


@app.registrar_endpoint("/saludo")
def vista_saludo(environ):
    return "Micro-Framework funcionando mediante abstracción declarativa."


@app.registrar_endpoint("/hora")
def vista_hora(environ):
    return f"Hora del servidor: {datetime.now():%H:%M:%S}"


aplicacion_fortificada = MiddlewareAuditoria(app)

if __name__ == "__main__":
    print("Micro-framework en http://localhost:8080  (Ctrl+C para detener)")
    make_server("", 8080, aplicacion_fortificada).serve_forever()