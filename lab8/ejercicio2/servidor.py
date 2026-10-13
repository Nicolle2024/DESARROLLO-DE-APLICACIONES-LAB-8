import http.server
import json
import mimetypes
import os
from urllib.parse import urlparse, parse_qs

# ==============================
# CONFIGURACIÓN
# ==============================
# ==============================
# CONFIGURACIÓN (CORREGIDA)
# ==============================

HOST = "127.0.0.1"
PUERTO = 8080

# Reemplaza os.getcwd() por __file__ para usar la ruta real del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.abspath(os.path.join(BASE_DIR, "public"))


# ==============================
# DATOS EN MEMORIA (COLECCIÓN)
# ==============================
INVENTARIO = [
    {"id": 1, "nombre": "Laptop Lenovo", "categoria": "Computadoras", "stock": 15},
    {"id": 2, "nombre": "Mouse Logitech", "categoria": "Perifericos", "stock": 50},
    {"id": 3, "nombre": "Teclado mecanico", "categoria": "Perifericos", "stock": 30},
    {"id": 4, "nombre": "Monitor Samsung", "categoria": "Monitores", "stock": 20},
    {"id": 5, "nombre": "Laptop HP", "categoria": "Computadoras", "stock": 10}
]

# ==============================
# RESPUESTA JSON GENÉRICA
# ==============================
def enviar_json(handler, datos, estado=200):
    cuerpo = json.dumps(datos, ensure_ascii=False, indent=4).encode("utf-8")
    handler.send_response(estado)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(cuerpo)))
    handler.end_headers()
    handler.wfile.write(cuerpo)

# ==============================
# CONTROLADOR PRINCIPAL (HANDLER)
# ==============================
class MiServidor(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        url = urlparse(self.path)
        ruta = url.path

        # Endpoint analítico dinámico
        if ruta == "/api/inventario":
            self.api_inventario(url.query)
        # Enrutamiento de recursos estáticos
        else:
            self.archivo_estatico(ruta)

    # Motor de Filtrado, Búsqueda y Paginación
    def api_inventario(self, query_string):
        parametros = parse_qs(query_string)

        # Casteo y validación segura de 'limite'
        try:
            limite = int(parametros.get("limite", ["10"])[0])
        except ValueError:
            enviar_json(self, {"error": "El parámetro 'limite' debe ser un número entero."}, 400)
            return

        if limite <= 0 or limite > 100:
            enviar_json(self, {"error": "El parámetro 'limite' debe estar entre 1 y 100."}, 400)
            return

        # Casteo y validación segura de 'pagina'
        try:
            pagina = int(parametros.get("pagina", ["1"])[0])
        except ValueError:
            enviar_json(self, {"error": "El parámetro 'pagina' debe ser un número entero."}, 400)
            return

        if pagina <= 0:
            enviar_json(self, {"error": "La página debe ser mayor que 0."}, 400)
            return

        # Extracción del criterio de búsqueda (Filtro)
        filtro = parametros.get("filtro", [""])[0].lower()

        # Algoritmo de búsqueda parcial por coincidencia de texto
        if filtro:
            resultados_filtrados = []
            for producto in INVENTARIO:
                texto_busqueda = f"{producto['nombre']} {producto['categoria']}".lower()
                if filtro in texto_busqueda:
                    resultados_filtrados.append(producto)
        else:
            resultados_filtrados = INVENTARIO.copy()

        # Cálculo de particionamiento (Slicing con Offset / Limit)
        total = len(resultados_filtrados)
        offset = (pagina - 1) * limite
        resultados = resultados_filtrados[offset:offset + limite]
        total_paginas = (total + limite - 1) // limite if total > 0 else 0

        # Estructuración de la respuesta con Metadatos
        respuesta = {
            "datos": resultados,
            "paginacion": {
                "pagina": pagina,
                "limite": limite,
                "total_registros": total,
                "total_paginas": total_paginas
            },
            "filtro": filtro
        }
        enviar_json(self, respuesta, 200)

    # Gestor de Archivos Estáticos con Blindaje de Rutas
    def archivo_estatico(self, ruta):
        if ruta == "/":
            ruta = "/index.html"

        ruta_relativa = ruta.lstrip("/")
        ruta_absoluta = os.path.abspath(os.path.join(PUBLIC_DIR, ruta_relativa))

        # Validación perimetral estricta anti-Path Traversal
        try:
            ruta_comun = os.path.commonpath([PUBLIC_DIR, ruta_absoluta])
        except ValueError:
            self.send_error(403, "Acceso prohibido")
            return

        if ruta_comun != PUBLIC_DIR:
            self.send_error(403, "Ataque Path Traversal Bloqueado")
            return

        # Verificación física del recurso
        if not os.path.isfile(ruta_absoluta):
            self.send_error(404, "Archivo no encontrado")
            return

        # Inferencia dinámica del Content-Type
        content_type, _ = mimetypes.guess_type(ruta_absoluta)
        if content_type is None:
            content_type = "application/octet-stream"

        # Transmisión del flujo binario
        try:
            with open(ruta_absoluta, "rb") as archivo:
                contenido = archivo.read()

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(contenido)))
            self.end_headers()
            self.wfile.write(contenido)
        except OSError:
            self.send_error(500, "Error crítico al leer el archivo")

if __name__ == "__main__":
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    servidor = http.server.HTTPServer((HOST, PUERTO), MiServidor)

    print("====================================================")
    print(" SERVIDOR HTTP NATIVO E HÍBRIDO INICIADO")
    print("====================================================")
    print(f"📍 Interfaz web: http://{HOST}:{PUERTO}/")
    print(f"📍 Endpoint API: http://{HOST}:{PUERTO}/api/inventario")
    print(f"📁 Directorio Público Raíz: {PUBLIC_DIR}")
    print("====================================================")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Apagando servidor de baja potencia de manera segura...")
    finally:
        servidor.server_close()
