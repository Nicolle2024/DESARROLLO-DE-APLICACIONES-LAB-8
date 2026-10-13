import json
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

base_de_datos = [{"id": i, "articulo": f"Item {i}", "valor": i * 10} for i in range(1, 101)]


def endpoint_inventario_paginado(environ, start_response):
    cadena_consulta = environ.get("QUERY_STRING", "")
    parametros_url = parse_qs(cadena_consulta)

    try:
        limite_elementos = int(parametros_url.get("limite", ["10"])[0])
        pagina_actual = int(parametros_url.get("pagina", ["1"])[0])
        if limite_elementos < 1 or pagina_actual < 1:
            raise ValueError("valores no positivos")
    except ValueError:
        estado, cuerpo = "400 Bad Request", {"error": "Paginación exige enteros positivos"}
    else:
        if limite_elementos > 50:
            limite_elementos = 50

        indice_desplazamiento = (pagina_actual - 1) * limite_elementos
        indice_corte = indice_desplazamiento + limite_elementos
        datos_cortados = base_de_datos[indice_desplazamiento:indice_corte]

        estado = "200 OK"
        cuerpo = {
            "meta": {"pagina": pagina_actual, "limite_real": limite_elementos, "total_items": len(base_de_datos)},
            "registros": datos_cortados
        }

    payload = json.dumps(cuerpo).encode("utf-8")
    start_response(estado, [
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(payload)))
    ])
    return [payload]


if __name__ == "__main__":
    print("Paginación en http://localhost:8080/?limite=15&pagina=2  (Ctrl+C para detener)")
    make_server("", 8080, endpoint_inventario_paginado).serve_forever()