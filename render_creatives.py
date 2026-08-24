#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALCO INDUSTRIA GRÁFICA — Generador de creatividades de respaldo
render_creatives.py

QUÉ HACE
Para las publicaciones del calendario a las que TODAVÍA les falta el
archivo de medio (Nicolás no llegó a subir la foto pedida), genera una
imagen de respaldo automática:

  1. Busca la foto real del producto en calco.uy (la que ya está
     publicada en el catálogo — nunca una imagen inventada ni generada
     por IA).
  2. Le aplica una plantilla de marca simple (logo, franja inferior con
     el nombre y el sitio) usando HTML/CSS renderizado a PNG con
     Playwright.
  3. La deja en contenido/AAAA-MM/media/<id>.jpg, en el mismo lugar
     donde publisher.py espera encontrar la foto.

QUÉ NO HACE, A PROPÓSITO
- No genera nada para el pilar "produccion" (Detrás de la producción):
  esos posts piden explícitamente una foto nueva del taller, y usar una
  foto de catálogo ahí sería mostrar algo que no es lo que se anunció.
- No genera nada para los reels (formato "reel"): un video no se puede
  fabricar a partir de una foto fija sin que quede falso.
- No genera nada si la publicación ya tiene un archivo de medio real
  (Nicolás siempre tiene prioridad: si subió su foto, se usa esa).
- No inventa fotos con IA. Todo lo que produce este script sale de una
  fotografía real que ya está publicada en calco.uy.

CUÁNDO CORRE
Diario, un rato antes que publisher.py (para que el respaldo ya esté
listo si hace falta), vía GitHub Actions.

USO
    python render_creatives.py                     # hoy, mes actual
    python render_creatives.py --fecha 2026-09-02   # forzar una fecha
    python render_creatives.py --dry-run            # sin generar archivos
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("Falta la librería. Instalar con:  pip install requests")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Falta la librería. Instalar con:  pip install playwright")
    print("Y después:  playwright install chromium")
    sys.exit(1)

RAIZ = Path(__file__).parent
DIR_CONTENIDO = RAIZ / "contenido"
ARCHIVO_MARCA = RAIZ / "marca" / "sistema_de_marca.json"

# Pilares/formatos que este script NUNCA toca: necesitan una foto o
# video real y nuevo, no una imagen de catálogo reciclada.
PILARES_EXCLUIDOS = {"produccion"}
FORMATOS_EXCLUIDOS = {"reel"}

TIMEOUT_HTTP = 20


def cargar_marca():
    if not ARCHIVO_MARCA.exists():
        print(f"No se encontró {ARCHIVO_MARCA}")
        sys.exit(1)
    with open(ARCHIVO_MARCA, encoding="utf-8") as f:
        return json.load(f)


def cargar_calendario(anio_mes):
    ruta = DIR_CONTENIDO / anio_mes / "calendario.json"
    if not ruta.exists():
        print(f"No existe {ruta}. Nada que renderizar todavía.")
        sys.exit(0)  # no es un error: puede que el mes no se haya generado aún
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def ya_tiene_medio(anio_mes, pub_id):
    carpeta = DIR_CONTENIDO / anio_mes / "media"
    for ext in (".jpg", ".jpeg", ".png", ".mp4", ".mov"):
        if (carpeta / f"{pub_id}{ext}").exists():
            return True
    return False


def elegible_para_respaldo(pub):
    if pub.get("red") != "instagram_facebook":
        return False
    if pub.get("pilar") in PILARES_EXCLUIDOS:
        return False
    if pub.get("formato") in FORMATOS_EXCLUIDOS:
        return False
    if not pub.get("producto"):
        return False  # sin producto asociado no hay de dónde sacar la foto
    return True


HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CalcoBot/1.0)"}


def _descargar_bytes(url):
    resp = requests.get(url, timeout=TIMEOUT_HTTP, headers=HEADERS)
    resp.raise_for_status()
    return resp.content


def _es_pagina_de_categoria(url):
    """WooCommerce marca las categorías con /categoria-producto/ o
    /product-category/ en la URL. Si la URL configurada en
    sistema_de_marca.json es una de estas, NUNCA hay que usar su og:image
    directamente: es el banner genérico del sitio, no una foto de
    producto."""
    return "/categoria-producto/" in url or "/product-category/" in url


def _slug_de_categoria(url):
    return url.rstrip("/").split("/")[-1]


def _imagen_desde_store_api(url_categoria):
    """Intento 1 (preferido): la API pública de WooCommerce Store API
    devuelve productos reales de la categoría, cada uno con su propia
    foto. Requiere que el sitio la tenga habilitada (viene activada por
    defecto en WooCommerce moderno, pero puede estar desactivada)."""
    dominio = "/".join(url_categoria.split("/")[:3])  # https://calco.uy
    slug = _slug_de_categoria(url_categoria)
    endpoint = f"{dominio}/wp-json/wc/store/v1/products?category={slug}&per_page=10"

    try:
        resp = requests.get(endpoint, timeout=TIMEOUT_HTTP, headers=HEADERS)
        resp.raise_for_status()
        productos = resp.json()
    except Exception as e:
        return None, f"Store API no disponible ({e})"

    if not isinstance(productos, list) or not productos:
        return None, "Store API respondió sin productos para esta categoría"

    for p in productos:
        imagenes = p.get("images") or []
        if imagenes and imagenes[0].get("src"):
            url_imagen = imagenes[0]["src"]
            try:
                return _descargar_bytes(url_imagen), None
            except Exception as e:
                continue  # probar el siguiente producto de la lista

    return None, "Ningún producto de la categoría tenía foto en la Store API"


def _imagen_desde_ficha_individual(url_categoria):
    """Intento 2 (respaldo): si la Store API no está disponible, se busca
    en el HTML de la página de categoría un link a una ficha de producto
    individual real (nunca se usa la imagen de la propia página de
    categoría, que es genérica), y se saca el og:image de esa ficha."""
    try:
        resp = requests.get(url_categoria, timeout=TIMEOUT_HTTP, headers=HEADERS)
        resp.raise_for_status()
    except Exception as e:
        return None, f"No se pudo abrir {url_categoria}: {e}"

    # Patrón típico de permalink de producto individual en WooCommerce.
    # Se descarta cualquier link que sea la propia página de categoría.
    candidatos = re.findall(
        r'href=["\']([^"\']*/producto/[^"\']+)["\']', resp.text, re.IGNORECASE
    )
    candidatos = [c for c in candidatos if c.rstrip("/") != url_categoria.rstrip("/")]

    if not candidatos:
        return None, ("No se encontró ningún link a una ficha de producto "
                       "individual dentro de la página de categoría")

    url_producto = urljoin(url_categoria, candidatos[0])

    try:
        resp_prod = requests.get(url_producto, timeout=TIMEOUT_HTTP, headers=HEADERS)
        resp_prod.raise_for_status()
    except Exception as e:
        return None, f"No se pudo abrir la ficha de producto {url_producto}: {e}"

    match = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        resp_prod.text, re.IGNORECASE
    ) or re.search(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        resp_prod.text, re.IGNORECASE
    )
    if not match:
        return None, f"No se encontró og:image en la ficha {url_producto}"

    url_imagen = urljoin(url_producto, match.group(1))
    try:
        return _descargar_bytes(url_imagen), None
    except Exception as e:
        return None, f"No se pudo descargar la imagen {url_imagen}: {e}"


def obtener_imagen_producto(url_configurada):
    """Punto de entrada único. IMPORTANTE: nunca devuelve la imagen de una
    página de categoría (sería el banner genérico del sitio, no una foto
    de producto real) — siempre busca la foto de un producto específico,
    por dos vías distintas, y si ninguna funciona, no devuelve nada en
    vez de arriesgarse a mostrar algo genérico o inventado."""
    if _es_pagina_de_categoria(url_configurada):
        imagen, error = _imagen_desde_store_api(url_configurada)
        if imagen:
            return imagen, None
        print(f"    (Store API falló: {error}. Probando respaldo...)")
        return _imagen_desde_ficha_individual(url_configurada)

    # Si la URL configurada ya es la ficha de un producto puntual (no una
    # categoría), se puede usar directamente su og:image.
    try:
        resp = requests.get(url_configurada, timeout=TIMEOUT_HTTP, headers=HEADERS)
        resp.raise_for_status()
    except Exception as e:
        return None, f"No se pudo abrir {url_configurada}: {e}"

    match = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        resp.text, re.IGNORECASE
    ) or re.search(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        resp.text, re.IGNORECASE
    )
    if not match:
        return None, f"No se encontró og:image en {url_configurada}"

    url_imagen = urljoin(url_configurada, match.group(1))
    try:
        return _descargar_bytes(url_imagen), None
    except Exception as e:
        return None, f"No se pudo descargar la imagen {url_imagen}: {e}"


def armar_html_plantilla(imagen_data_url, nombre_empresa, sitio):
    """Plantilla simple: la foto real de fondo, franja de marca abajo.
    Nada de texto inventado sobre el producto — solo el nombre y el sitio,
    que son datos ya verificados en el resto del sistema."""
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ width: 1080px; height: 1080px; overflow: hidden; font-family: Arial, sans-serif; }}
  .fondo {{
    width: 1080px; height: 1080px;
    background-image: url('{imagen_data_url}');
    background-size: cover;
    background-position: center;
    position: relative;
  }}
  .franja {{
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 140px;
    background: linear-gradient(0deg, rgba(0,0,0,0.75) 0%, rgba(0,0,0,0) 100%);
    display: flex;
    align-items: flex-end;
    padding: 24px 32px;
  }}
  .marca {{
    color: white;
    font-size: 28px;
    font-weight: bold;
  }}
  .sitio {{
    color: rgba(255,255,255,0.85);
    font-size: 18px;
    margin-left: auto;
  }}
  .fila {{
    display: flex;
    width: 100%;
    align-items: baseline;
  }}
</style>
</head>
<body>
  <div class="fondo">
    <div class="franja">
      <div class="fila">
        <div class="marca">{nombre_empresa}</div>
        <div class="sitio">{sitio}</div>
      </div>
    </div>
  </div>
</body>
</html>
"""


def renderizar(html, ruta_salida, navegador):
    import base64
    pagina = navegador.new_page(viewport={"width": 1080, "height": 1080})
    pagina.set_content(html)
    pagina.wait_for_timeout(200)  # margen para que la imagen de fondo termine de cargar
    pagina.screenshot(path=str(ruta_salida))
    pagina.close()


def main():
    ap = argparse.ArgumentParser(description="Generador de creatividades de respaldo")
    ap.add_argument("--fecha", help="Fecha a procesar, formato AAAA-MM-DD. Vacío = hoy.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Muestra qué haría, sin generar archivos")
    args = ap.parse_args()

    fecha_objetivo = args.fecha or date.today().isoformat()
    anio_mes = fecha_objetivo[:7]

    print(f"=== Calco: creatividades de respaldo — {fecha_objetivo} ===")

    marca = cargar_marca()
    calendario = cargar_calendario(anio_mes)
    productos = marca.get("productos", {})

    publicaciones = calendario.get("publicaciones", [])
    candidatas = [
        p for p in publicaciones
        if p.get("fecha") == fecha_objetivo and elegible_para_respaldo(p)
        and not ya_tiene_medio(anio_mes, p["id"])
    ]

    if not candidatas:
        print("No hay publicaciones que necesiten una imagen de respaldo hoy.")
        return

    print(f"{len(candidatas)} publicación(es) sin foto — evaluando respaldo automático.")

    carpeta_media = DIR_CONTENIDO / anio_mes / "media"
    if not args.dry_run:
        carpeta_media.mkdir(parents=True, exist_ok=True)

    navegador = None
    if not args.dry_run:
        playwright_ctx = sync_playwright().start()
        navegador = playwright_ctx.chromium.launch()

    generadas = 0

    for pub in candidatas:
        pub_id = pub["id"]
        clave_producto = pub["producto"]
        info_producto = productos.get(clave_producto)

        print(f"\n--- {pub_id} (producto: {clave_producto}) ---")

        if not info_producto or not info_producto.get("url"):
            print(f"  No hay URL configurada para el producto '{clave_producto}' "
                  f"en marca/sistema_de_marca.json. Se salta.")
            continue

        url_producto = info_producto["url"]
        print(f"  Buscando foto real en: {url_producto}")

        imagen_bytes, error = obtener_imagen_producto(url_producto)
        if error:
            print(f"  {error}. Se salta esta publicación (Nicolás puede subir "
                  "su propia foto cuando pueda).")
            continue

        if args.dry_run:
            print("  [dry-run] Se generaría una imagen de respaldo acá.")
            continue

        import base64
        mime = "image/jpeg"
        if imagen_bytes[:4] == b"\x89PNG":
            mime = "image/png"
        data_url = f"data:{mime};base64,{base64.b64encode(imagen_bytes).decode()}"

        html = armar_html_plantilla(
            data_url,
            marca["empresa"]["nombre"],
            marca["empresa"]["sitio"].replace("https://", "").replace("http://", ""),
        )

        ruta_salida = carpeta_media / f"{pub_id}.jpg"
        renderizar(html, ruta_salida, navegador)
        generadas += 1
        print(f"  Generada: {ruta_salida} (foto real de {url_producto}, con plantilla de marca)")

    if navegador:
        navegador.close()

    print(f"\nListo. {generadas} imagen(es) de respaldo generada(s).")
    if generadas:
        print("Recordatorio: si Nicolás sube su propia foto para el mismo id "
              "antes de que publisher.py corra, esa tiene prioridad — este "
              "script no la sobrescribe en corridas futuras porque ya "
              "detecta que el archivo existe.")


if __name__ == "__main__":
    main()
