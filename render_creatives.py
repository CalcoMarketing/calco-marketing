#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALCO INDUSTRIA GRÁFICA — Generador de creatividades de respaldo
render_creatives.py

QUÉ HACE
Para las publicaciones del calendario a las que TODAVÍA les falta el
archivo de medio (Nicolás no llegó a subir la foto pedida), busca una
imagen de respaldo, en este orden de prioridad:

  1. Foto real subida por Nicolás (a Drive o al repo) — siempre gana si existe.
  2. Foto real del catálogo web (calco.uy) que coincida con el objeto del post.
  3. Imagen generada por IA (Google Gemini / "Nano Banana"), como último
     recurso cuando no hay foto real ni coincidencia de catálogo.

En los tres casos, la imagen se recorta a 1080x1080 y se deja en
contenido/AAAA-MM/media/<id>.jpg, donde publisher.py espera encontrarla.

SOBRE LA OPCIÓN 3 (IMÁGENES GENERADAS POR IA)
Desde la Sesión 5 (26/08/2026) se decidió permitir imágenes generadas por
IA para cualquier tipo de post, incluidos los que muestran producto o
proceso — reemplazando la restricción anterior. Es una decisión explícita
de negocio, no técnica: se prueba así y se evalúa el resultado.

Por prudencia, este script:
  - Registra en un manifiesto (media/fuentes_imagenes.json) qué fuente se
    usó para cada publicación (real / catalogo / ia), para poder revisar
    después qué tan seguido se recurre a IA y con qué resultado.
  - Sigue prefiriendo foto real o de catálogo por sobre IA cuando ambas
    están disponibles: la IA es el último recurso, no la opción por defecto.
  - Para productos con estructura técnica visible y compleja (packaging
    con troquelado abierto, por ejemplo), la calidad de la IA es más
    variable — ver pruebas de la Sesión 5. Conviene revisar esas
    publicaciones puntualmente antes de que el post salga (no hay chequeo
    automático de esto todavía).

QUÉ NO HACE, A PROPÓSITO
- No genera nada para el pilar "produccion" (Detrás de la producción):
  esos posts piden explícitamente una foto nueva del taller real.
- No genera nada para los reels (formato "reel"): un video no se puede
  fabricar a partir de una imagen fija sin que quede falso.
- No genera nada si la publicación ya tiene un archivo de medio real
  (Nicolás siempre tiene prioridad).

CUÁNDO CORRE
Diario, un rato antes que publisher.py (para que el respaldo ya esté
listo si hace falta), vía GitHub Actions.

CONFIGURACIÓN NUEVA REQUERIDA
GEMINI_API_KEY en GitHub Secrets (o variable de entorno local). Se saca
gratis en https://aistudio.google.com/apikey

USO
    python render_creatives.py                     # hoy, mes actual
    python render_creatives.py --fecha 2026-09-02   # forzar una fecha
    python render_creatives.py --dry-run            # sin generar archivos
    python render_creatives.py --sin-ia             # nunca usar IA (solo real/catálogo)
"""

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

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

# Búsqueda de fotos en Google Drive, para no pisar una foto real que ya
# se subió ahí. Si el módulo no está, se mira solo el repositorio.
try:
    import drive_fotos
except ImportError:
    class _SinDrive:
        @staticmethod
        def esta_configurado():
            return False
    drive_fotos = _SinDrive()

# Pilares/formatos que este script NUNCA toca: necesitan una foto o
# video real y nuevo, no una imagen de catálogo reciclada ni de IA.
PILARES_EXCLUIDOS = {"produccion"}
FORMATOS_EXCLUIDOS = {"reel"}

TIMEOUT_HTTP = 20

# Modelo de Gemini para generación de imágenes. Fijo acá, en un solo
# lugar, porque Google renombra estos modelos seguido.
MODELO_GEMINI_IMAGEN = "gemini-3.1-flash-image"


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
    """¿Ya existe la foto real de esta publicación?

    Mira primero en el repositorio y después en la carpeta de Drive. Si
    está en cualquiera de los dos, NO se genera imagen de respaldo: la
    foto real de Nicolás siempre tiene prioridad."""
    carpeta = DIR_CONTENIDO / anio_mes / "media"
    for ext in (".jpg", ".jpeg", ".png", ".mp4", ".mov"):
        if (carpeta / f"{pub_id}{ext}").exists():
            return True

    if drive_fotos.esta_configurado():
        file_id, nombre = drive_fotos.buscar_medio(pub_id)
        if file_id:
            print(f"    ({pub_id} ya tiene foto en Drive: {nombre})")
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
    español fallan seguido (estuche/estuches, caja/cajas, rollo/rollos)."""
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
    return "/categoria-producto/" in url or "/product-category/" in url


def _slug_de_categoria(url):
    return url.rstrip("/").split("/")[-1]


def _listar_productos_store_api(url_categoria):
    """Devuelve (lista_de_productos, error)."""
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


def obtener_imagen_de_catalogo(url_categoria, objeto_visual):
    """REGLA CENTRAL: solo devuelve una foto si el nombre del producto en
    el catálogo coincide con TODAS las palabras significativas del objeto
    del que habla el post — no alcanza con compartir una palabra genérica.

    Por qué importa: 'caja troquelada' comparte la palabra 'caja' con
    'Caja para papas fritas', pero son productos completamente distintos.
    Exigir coincidencia total evita ese falso positivo — si no hay match
    completo, se prefiere no usar catálogo y dejar que el llamador intente
    con IA en vez de forzar una foto que no corresponde.

    Devuelve (bytes_imagen, nombre_producto, error)."""
    if not objeto_visual:
        return None, None, ("El post no declara qué objeto concreto muestra "
                            "(campo 'objeto_visual' vacío).")

    productos, error = _listar_productos_store_api(url_categoria)
    if error:
        return None, None, error

    palabras_objeto = _normalizar(objeto_visual)
    if not palabras_objeto:
        return None, None, (
            f"'{objeto_visual}' no tiene palabras significativas para comparar."
        )

    con_puntaje = []
    for p in productos:
        nombre = p.get("name") or ""
        imagenes = p.get("images") or []
        if not nombre or not imagenes or not imagenes[0].get("src"):
            continue
        puntaje = _puntaje_coincidencia(objeto_visual, nombre)
        # Coincidencia completa: TODAS las palabras del objeto_visual
        # tienen que aparecer en el nombre del producto. Una coincidencia
        # parcial (solo "caja" de "caja troquelada") no alcanza.
        if puntaje == len(palabras_objeto):
            con_puntaje.append((puntaje, nombre, imagenes[0]["src"]))

    if not con_puntaje:
        nombres = ", ".join((p.get("name") or "?") for p in productos[:8])
        return None, None, (
            f"Ningún producto del catálogo coincide completamente con "
            f"'{objeto_visual}' (se exige que coincidan todas sus palabras "
            f"significativas, no solo una). Productos disponibles en la "
            f"categoría: {nombres}."
        )

    con_puntaje.sort(key=lambda x: -x[0])
    _, nombre_elegido, url_imagen = con_puntaje[0]

    try:
        return _descargar_bytes(url_imagen), nombre_elegido, None
    except Exception as e:
        return None, None, f"No se pudo descargar la foto de '{nombre_elegido}': {e}"


# ---------------------------------------------------------------------
# GENERACIÓN CON IA (Google Gemini / "Nano Banana")
# ---------------------------------------------------------------------

def _armar_prompt_ia(objeto_visual, marca):
    """Arma el prompt para Gemini a partir del objeto_visual del post y
    los principios de voz/marca. Estilo fijo: foto de producto profesional,
    fondo neutro, sin texto ni logos inventados (el logo real se agrega,
    si corresponde, en un paso aparte — no confiar en que la IA lo dibuje
    bien)."""
    empresa = marca.get("empresa", {}).get("nombre", "la empresa")
    return (
        f"Professional product photography of {objeto_visual}, "
        f"for {empresa}, a graphic printing and packaging company. "
        "Clean white or neutral studio background, soft natural shadows, "
        "minimalist commercial product photography style, sharp focus, "
        "realistic materials and textures, no visible text, no logos, "
        "no brand names, square format for social media."
    )


def generar_imagen_ia(objeto_visual, marca):
    """Genera una imagen con Gemini a partir del objeto_visual del post.

    Devuelve (bytes_imagen, descripcion, error). No lanza excepciones:
    cualquier fallo (falta la key, error de red, respuesta vacía) se
    convierte en un error de texto para que el llamador decida no
    publicar en vez de romper la corrida completa."""
    if not objeto_visual:
        return None, None, "No hay 'objeto_visual' declarado: no se genera nada con IA."

    try:
        from google import genai
    except ImportError:
        return None, None, ("Falta la librería google-genai. Instalar con: "
                            "pip install google-genai")

    import os
    if not os.environ.get("GEMINI_API_KEY"):
        return None, None, "Falta la variable de entorno GEMINI_API_KEY."

    prompt = _armar_prompt_ia(objeto_visual, marca)

    try:
        client = genai.Client()  # lee GEMINI_API_KEY del entorno
        response = client.models.generate_content(
            model=MODELO_GEMINI_IMAGEN,
            contents=[prompt],
        )
    except Exception as e:
        return None, None, f"Error llamando a Gemini: {e}"

    try:
        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None) is not None:
                return part.inline_data.data, f"Generada por IA: {objeto_visual}", None
    except Exception as e:
        return None, None, f"Respuesta de Gemini sin imagen utilizable: {e}"

    return None, None, "Gemini no devolvió ninguna imagen en la respuesta."


# ---------------------------------------------------------------------
# RENDERIZADO (recorte + plantilla)
# ---------------------------------------------------------------------

def armar_html_plantilla(imagen_data_url):
    """La imagen (real, de catálogo, o generada por IA), recortada a
    cuadrado 1080x1080, sin nada encima."""
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ width: 1080px; height: 1080px; overflow: hidden; }}
  .fondo {{
    width: 1080px; height: 1080px;
    background-image: url('{imagen_data_url}');
    background-size: cover;
    background-position: center;
  }}
</style>
</head>
<body>
  <div class="fondo"></div>
</body>
</html>
"""


def renderizar(html, ruta_salida, navegador):
    pagina = navegador.new_page(viewport={"width": 1080, "height": 1080})
    pagina.set_content(html)
    pagina.wait_for_timeout(200)
    pagina.screenshot(path=str(ruta_salida))
    pagina.close()


# ---------------------------------------------------------------------
# MANIFIESTO DE FUENTES (para poder auditar después qué tan seguido se
# usó IA, y con qué resultado percibido)
# ---------------------------------------------------------------------

def _ruta_manifiesto(anio_mes):
    return DIR_CONTENIDO / anio_mes / "media" / "fuentes_imagenes.json"


def _registrar_fuente(anio_mes, pub_id, fuente, detalle):
    ruta = _ruta_manifiesto(anio_mes)
    datos = {}
    if ruta.exists():
        try:
            with open(ruta, encoding="utf-8") as f:
                datos = json.load(f)
        except Exception:
            datos = {}
    datos[pub_id] = {
        "fuente": fuente,  # "catalogo" | "ia"
        "detalle": detalle,
        "generado_el": datetime.now(timezone.utc).isoformat(),
    }
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser(description="Generador de creatividades de respaldo")
    ap.add_argument("--fecha", help="Fecha a procesar, formato AAAA-MM-DD. Vacío = hoy.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Muestra qué haría, sin generar archivos")
    ap.add_argument("--sin-ia", action="store_true",
                    help="Nunca generar con IA (solo foto real o catálogo)")
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
    generadas_por_ia = 0

    for pub in candidatas:
        pub_id = pub["id"]
        clave_producto = pub["producto"]
        info_producto = productos.get(clave_producto)
        objeto_visual = pub.get("objeto_visual", "")

        print(f"\n--- {pub_id} (producto: {clave_producto}) ---")
        print(f"  El post habla de: '{objeto_visual or '(no declarado)'}'")

        imagen_bytes = None
        nombre_elegido = None
        fuente = None

        # 1. Catálogo web (si hay URL configurada para el producto)
        if info_producto and info_producto.get("url"):
            url_producto = info_producto["url"]
            print(f"  Buscando en el catálogo: {url_producto}")
            imagen_bytes, nombre_elegido, error = obtener_imagen_de_catalogo(
                url_producto, objeto_visual
            )
            if imagen_bytes:
                fuente = "catalogo"
                print(f"  Coincidencia encontrada en catálogo: «{nombre_elegido}»")
            else:
                print(f"  Catálogo no sirvió — {error}")
        else:
            print(f"  No hay URL configurada para el producto '{clave_producto}'.")

        # 2. IA, solo si el catálogo no dio nada y no se pidió --sin-ia
        if not imagen_bytes and not args.sin_ia:
            print("  Intentando generar con IA (Gemini)...")
            imagen_bytes, nombre_elegido, error = generar_imagen_ia(objeto_visual, marca)
            if imagen_bytes:
                fuente = "ia"
                print(f"  Imagen generada por IA para: «{objeto_visual}»")
            else:
                print(f"  IA no generó nada — {error}")

        if not imagen_bytes:
            print("  NO SE GENERA — no hay foto de catálogo ni imagen de IA disponible.")
            continue

        if args.dry_run:
            print(f"  [dry-run] Se generaría la imagen (fuente: {fuente}).")
            continue

        import base64
        mime = "image/jpeg"
        if imagen_bytes[:4] == b"\x89PNG":
            mime = "image/png"
        data_url = f"data:{mime};base64,{base64.b64encode(imagen_bytes).decode()}"

        html = armar_html_plantilla(data_url)
        ruta_salida = carpeta_media / f"{pub_id}.jpg"
        renderizar(html, ruta_salida, navegador)
        generadas += 1
        if fuente == "ia":
            generadas_por_ia += 1

        _registrar_fuente(anio_mes, pub_id, fuente, nombre_elegido)

        print(f"  Generada: {ruta_salida} (fuente: {fuente})")

    if navegador:
        navegador.close()

    print(f"\nListo. {generadas} imagen(es) de respaldo generada(s), "
          f"{generadas_por_ia} de ellas con IA.")
    if generadas:
        print("Recordatorio: si Nicolás sube su propia foto para el mismo id "
              "antes de que publisher.py corra, esa tiene prioridad — este "
              "script no la sobrescribe en corridas futuras porque ya "
              "detecta que el archivo existe.")
        print(f"Detalle de fuentes usadas: {_ruta_manifiesto(anio_mes)}")


if __name__ == "__main__":
    main()
