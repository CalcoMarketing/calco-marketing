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

# Palabras que no aportan al matcheo (ruido común en nombres de producto)
_RUIDO = {"de", "del", "la", "el", "los", "las", "para", "con", "y", "en",
          "personalizado", "personalizada", "personalizados", "personalizadas",
          "impreso", "impresa", "impresos", "impresas", "a", "medida"}


def _normalizar(texto):
    """Minúsculas, sin tildes ni puntuación, sin palabras de relleno."""
    t = texto.lower().strip()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return [w for w in t.split() if w not in _RUIDO and len(w) >= 3]


def _misma_palabra(a, b):
    """Compara por prefijo en vez de intentar reglas de plural, que en
    español fallan seguido (estuche/estuches, caja/cajas, rollo/rollos).
    Dos palabras se consideran la misma si una empieza con la otra y
    comparten al menos 4 caracteres: 'estuche' ≈ 'estuches',
    'caja' ≈ 'cajas', pero 'caja' ≠ 'cuaderno'."""
    if a == b:
        return True
    corta, larga = (a, b) if len(a) <= len(b) else (b, a)
    return len(corta) >= 4 and larga.startswith(corta)


def _puntaje_coincidencia(objeto_visual, nombre_producto):
    """Cuántas palabras significativas comparten el objeto que describe el
    post y el nombre del producto del catálogo. 0 = no tienen nada que ver."""
    pa = _normalizar(objeto_visual)
    pb = _normalizar(nombre_producto)
    if not pa or not pb:
        return 0
    return sum(1 for x in pa if any(_misma_palabra(x, y) for y in pb))


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


def _listar_productos_store_api(url_categoria):
    """Devuelve (lista_de_productos, error). Cada producto trae name e
    images, que es lo que hace falta para matchear y para la foto."""
    dominio = "/".join(url_categoria.split("/")[:3])
    slug = _slug_de_categoria(url_categoria)
    endpoint = f"{dominio}/wp-json/wc/store/v1/products?category={slug}&per_page=50"

    try:
        resp = requests.get(endpoint, timeout=TIMEOUT_HTTP, headers=HEADERS)
        resp.raise_for_status()
        productos = resp.json()
    except Exception as e:
        return None, f"Store API no disponible ({e})"

    if not isinstance(productos, list) or not productos:
        return None, "Store API respondió sin productos para esta categoría"

    return productos, None


def obtener_imagen_para_post(url_categoria, objeto_visual):
    """REGLA CENTRAL: solo devuelve una foto si el nombre del producto en
    el catálogo coincide con el objeto del que habla el post.

    Si el post dice "caja troquelada" y en el catálogo hay una "Caja
    display", coincide (comparten "caja") y se usa esa foto. Si en el
    catálogo solo hay bolsas, NO coincide y no se devuelve nada — es
    preferible no publicar a publicar una bolsa cuando el texto habla de
    cajas.

    Devuelve (bytes_imagen, nombre_producto, error)."""
    if not objeto_visual:
        return None, None, ("El post no declara qué objeto concreto muestra "
                            "(campo 'objeto_visual' vacío). No se arriesga "
                            "una foto que puede no corresponder.")

    productos, error = _listar_productos_store_api(url_categoria)
    if error:
        return None, None, error

    # Ranking por coincidencia de nombre
    con_puntaje = []
    for p in productos:
        nombre = p.get("name") or ""
        imagenes = p.get("images") or []
        if not nombre or not imagenes or not imagenes[0].get("src"):
            continue
        puntaje = _puntaje_coincidencia(objeto_visual, nombre)
        if puntaje > 0:
            con_puntaje.append((puntaje, nombre, imagenes[0]["src"]))

    if not con_puntaje:
        nombres = ", ".join(
            (p.get("name") or "?") for p in productos[:8]
        )
        return None, None, (
            f"Ningún producto del catálogo coincide con '{objeto_visual}'. "
            f"Productos disponibles en la categoría: {nombres}. "
            "No se genera imagen: publicar una foto que no corresponde al "
            "texto es peor que no publicar."
        )

    con_puntaje.sort(key=lambda x: -x[0])
    _, nombre_elegido, url_imagen = con_puntaje[0]

    try:
        return _descargar_bytes(url_imagen), nombre_elegido, None
    except Exception as e:
        return None, None, f"No se pudo descargar la foto de '{nombre_elegido}': {e}"


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
        objeto_visual = pub.get("objeto_visual", "")

        print(f"  El post habla de: '{objeto_visual or '(no declarado)'}'")
        print(f"  Buscando en el catálogo: {url_producto}")

        imagen_bytes, nombre_elegido, error = obtener_imagen_para_post(
            url_producto, objeto_visual
        )
        if error:
            print(f"  NO SE GENERA — {error}")
            continue

        print(f"  Coincidencia encontrada: «{nombre_elegido}»")

        if args.dry_run:
            print("  [dry-run] Se generaría la imagen con esa foto.")
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
        print(f"  Generada: {ruta_salida}")
        print(f"    Foto real de «{nombre_elegido}» del catálogo de calco.uy")

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
