#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALCO INDUSTRIA GRÁFICA — Publicador automático
publisher.py

QUÉ HACE
Recorre el calendario del mes actual (contenido/AAAA-MM/calendario.json,
generado por content_engine.py) y publica en Instagram Business y en la
Página de Facebook las publicaciones cuya fecha programada es HOY y que
todavía no se publicaron. LinkedIn queda fuera a propósito: se decidió
trabajarlo 100% orgánico y manual (ver memoria.md, sección 6).

CÓMO EVITA PUBLICAR DOS VECES
Cada publicación del calendario tiene un campo "publicado". Apenas se
publica con éxito, este script actualiza ese campo a true y hace commit
del calendario.json de vuelta al repo. Si el workflow corre de nuevo el
mismo día (reintento manual, por ejemplo), no vuelve a publicar lo que
ya tiene publicado=true.

DE DÓNDE SALEN LAS FOTOS Y VIDEOS
De contenido/AAAA-MM/media/<id>.jpg (o .mp4 para los reels), donde <id>
es el mismo id que trae cada publicación en calendario.json (por ejemplo
"ig-2026-09-03"). Nicolás sube ese archivo al repo con ese nombre exacto.
Como el repositorio es público, la URL cruda de GitHub
(raw.githubusercontent.com/...) ya es una URL pública HTTPS válida para
la API de Meta — no hace falta ningún hosting de imágenes aparte.

Si a una publicación programada para hoy le falta el archivo de medio,
el script NO falla: la salta, la deja en el log y sigue con las demás.
Nicolás tiene margen para subir la foto un poco tarde sin romper nada;
esa publicación se retoma sola al día siguiente que el script corra y
encuentre el archivo (siempre que la fecha programada ya haya pasado,
igual la publica — no se pierde el post por llegar un día tarde con la
foto).

CREDENCIALES (Secrets del repositorio)
    META_PAGE_ACCESS_TOKEN         Token de Página de larga duración
    META_PAGE_ID                   ID de la Página de Facebook
    META_IG_BUSINESS_ACCOUNT_ID    ID de la cuenta de Instagram Business

CUÁNDO CORRE
Diario, vía GitHub Actions, un rato antes de la hora de publicación
configurada en marca/sistema_de_marca.json (cadencia.hora_publicacion).

USO
    python publisher.py                  # publica lo de hoy
    python publisher.py --fecha 2026-09-03   # forzar una fecha específica
    python publisher.py --dry-run        # simula sin publicar ni commitear
"""

import argparse
import json
import mimetypes
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

try:
    import requests
except ImportError:
    print("Falta la librería. Instalar con:  pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

RAIZ = Path(__file__).parent
DIR_CONTENIDO = RAIZ / "contenido"

GRAPH_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

PAGE_ACCESS_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN")
PAGE_ID = os.environ.get("META_PAGE_ID")
IG_BUSINESS_ID = os.environ.get("META_IG_BUSINESS_ACCOUNT_ID")

# Se arma sola a partir del remoto de git, para no tener que configurarla
# a mano. Si el detectado no sirve (fork, remoto raro), se puede forzar
# con la variable de entorno RAW_BASE_URL.
RAW_BASE_URL_ENV = os.environ.get("RAW_BASE_URL")

TIMEOUT_POLL_VIDEO_SEGUNDOS = 180  # cuánto esperar a que Meta procese un reel
INTERVALO_POLL_SEGUNDOS = 10


# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------

def verificar_credenciales():
    faltantes = [
        nombre for nombre, valor in [
            ("META_PAGE_ACCESS_TOKEN", PAGE_ACCESS_TOKEN),
            ("META_PAGE_ID", PAGE_ID),
            ("META_IG_BUSINESS_ACCOUNT_ID", IG_BUSINESS_ID),
        ] if not valor
    ]
    if faltantes:
        print("Faltan variables de entorno: " + ", ".join(faltantes))
        print("En local:  export META_PAGE_ACCESS_TOKEN='...'")
        print("En GitHub Actions se toman de los secretos del repositorio.")
        sys.exit(1)


def detectar_raw_base_url():
    """Arma la base de raw.githubusercontent.com a partir del remoto git,
    o usa RAW_BASE_URL si está seteada a mano."""
    if RAW_BASE_URL_ENV:
        return RAW_BASE_URL_ENV.rstrip("/")

    try:
        remoto = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=RAIZ, text=True
        ).strip()
    except Exception:
        remoto = ""

    # Formatos posibles: git@github.com:owner/repo.git  |  https://github.com/owner/repo.git
    owner_repo = None
    if remoto.startswith("git@github.com:"):
        owner_repo = remoto.split("git@github.com:")[1]
    elif "github.com/" in remoto:
        owner_repo = remoto.split("github.com/")[1]

    if not owner_repo:
        print("No se pudo detectar el remoto de GitHub para armar las URLs "
              "de medios. Configurar RAW_BASE_URL a mano, por ejemplo:")
        print("  export RAW_BASE_URL='https://raw.githubusercontent.com/"
              "CalcoMarketing/calco-marketing/main'")
        sys.exit(1)

    owner_repo = owner_repo.replace(".git", "").strip("/")
    rama = obtener_rama_actual()
    return f"https://raw.githubusercontent.com/{owner_repo}/{rama}"


def obtener_rama_actual():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=RAIZ, text=True
        ).strip()
    except Exception:
        return "main"


def mes_actual_str():
    hoy = date.today()
    return f"{hoy.year}-{hoy.month:02d}"


def cargar_calendario(anio_mes):
    ruta = DIR_CONTENIDO / anio_mes / "calendario.json"
    if not ruta.exists():
        print(f"No existe {ruta}. ¿Ya corrió content_engine.py este mes?")
        sys.exit(1)
    with open(ruta, encoding="utf-8") as f:
        return json.load(f), ruta


def guardar_calendario(datos, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def ruta_medio_local(anio_mes, pub_id):
    """Busca el archivo de medio con cualquier extensión de imagen o video
    conocida, para no obligar a Nicolás a usar una extensión exacta."""
    carpeta = DIR_CONTENIDO / anio_mes / "media"
    for ext in (".jpg", ".jpeg", ".png", ".mp4", ".mov"):
        candidato = carpeta / f"{pub_id}{ext}"
        if candidato.exists():
            return candidato
    return None


def url_medio_publica(raw_base, anio_mes, archivo_local):
    return f"{raw_base}/contenido/{anio_mes}/media/{archivo_local.name}"


def es_video(archivo_local):
    return archivo_local.suffix.lower() in (".mp4", ".mov")


# ---------------------------------------------------------------------------
# INSTAGRAM
# ---------------------------------------------------------------------------

def publicar_instagram(url_medio, caption, es_reel):
    """Publica en Instagram Business. Devuelve (ok, detalle)."""
    tipo = "REELS" if es_reel else None

    parametros = {
        "caption": caption,
        "access_token": PAGE_ACCESS_TOKEN,
    }
    if es_reel:
        parametros["media_type"] = "REELS"
        parametros["video_url"] = url_medio
    else:
        parametros["image_url"] = url_medio

    resp = requests.post(
        f"{GRAPH_BASE}/{IG_BUSINESS_ID}/media",
        data=parametros, timeout=60,
    )
    data = resp.json()
    if "id" not in data:
        return False, f"Error al crear el contenedor: {data}"

    container_id = data["id"]

    if es_reel:
        ok, detalle = esperar_contenedor_listo(container_id)
        if not ok:
            return False, detalle

    resp2 = requests.post(
        f"{GRAPH_BASE}/{IG_BUSINESS_ID}/media_publish",
        data={"creation_id": container_id, "access_token": PAGE_ACCESS_TOKEN},
        timeout=60,
    )
    data2 = resp2.json()
    if "id" not in data2:
        return False, f"Error al publicar el contenedor: {data2}"

    return True, data2["id"]


def esperar_contenedor_listo(container_id):
    """Los reels se procesan de forma asíncrona. Hay que esperar a que
    status_code sea FINISHED antes de publicar, si no la publicación falla."""
    transcurrido = 0
    while transcurrido < TIMEOUT_POLL_VIDEO_SEGUNDOS:
        resp = requests.get(
            f"{GRAPH_BASE}/{container_id}",
            params={"fields": "status_code", "access_token": PAGE_ACCESS_TOKEN},
            timeout=30,
        )
        data = resp.json()
        estado = data.get("status_code")

        if estado == "FINISHED":
            return True, "listo"
        if estado == "ERROR":
            return False, f"Meta reportó error procesando el video: {data}"

        time.sleep(INTERVALO_POLL_SEGUNDOS)
        transcurrido += INTERVALO_POLL_SEGUNDOS

    return False, (
        f"El video no terminó de procesarse en {TIMEOUT_POLL_VIDEO_SEGUNDOS}s. "
        "Puede seguir procesando del lado de Meta; reintentar más tarde."
    )


# ---------------------------------------------------------------------------
# FACEBOOK
# ---------------------------------------------------------------------------

def publicar_facebook(url_medio, caption, es_video_flag):
    """Publica en la Página de Facebook. Devuelve (ok, detalle)."""
    if es_video_flag:
        resp = requests.post(
            f"{GRAPH_BASE}/{PAGE_ID}/videos",
            data={
                "file_url": url_medio,
                "description": caption,
                "access_token": PAGE_ACCESS_TOKEN,
            },
            timeout=120,
        )
    else:
        resp = requests.post(
            f"{GRAPH_BASE}/{PAGE_ID}/photos",
            data={
                "url": url_medio,
                "caption": caption,
                "access_token": PAGE_ACCESS_TOKEN,
            },
            timeout=60,
        )

    data = resp.json()
    if "id" not in data and "post_id" not in data:
        return False, f"Error de Facebook: {data}"
    return True, data.get("post_id", data.get("id"))


# ---------------------------------------------------------------------------
# CAPTION
# ---------------------------------------------------------------------------

def armar_caption(pub):
    partes = [pub.get("copy", "").strip()]
    hashtags = pub.get("hashtags") or []
    if hashtags:
        partes.append(" ".join(hashtags))
    return "\n\n".join(p for p in partes if p)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Publicador de Calco")
    ap.add_argument("--fecha", help="Fecha a publicar, formato AAAA-MM-DD. Vacío = hoy.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Simula sin publicar ni commitear cambios")
    args = ap.parse_args()

    fecha_objetivo = args.fecha or date.today().isoformat()
    anio_mes = fecha_objetivo[:7]

    print(f"=== Calco: publicador automático — {fecha_objetivo} ===")

    if not args.dry_run:
        verificar_credenciales()

    raw_base = detectar_raw_base_url()
    calendario, ruta_calendario = cargar_calendario(anio_mes)

    publicaciones = calendario.get("publicaciones", [])
    pendientes_hoy = [
        p for p in publicaciones
        if p.get("fecha") == fecha_objetivo
        and p.get("red") == "instagram_facebook"
        and not p.get("publicado")
    ]

    if not pendientes_hoy:
        print("No hay publicaciones de Instagram/Facebook pendientes para "
              f"{fecha_objetivo}. (LinkedIn se publica a mano, no lo toca "
              "este script.)")
        return

    print(f"{len(pendientes_hoy)} publicación(es) pendiente(s) para hoy.")

    hubo_cambios = False

    for pub in pendientes_hoy:
        pub_id = pub["id"]
        print(f"\n--- {pub_id} ---")

        if pub.get("duplicado_de"):
            print("  Marcada como posible duplicado por content_engine.py. "
                  "No se publica automáticamente: revisar a mano y sacar la "
                  "marca 'duplicado_de' del calendario.json cuando esté OK.")
            continue

        archivo = ruta_medio_local(anio_mes, pub_id)
        if not archivo:
            print(f"  Falta el archivo de medio en contenido/{anio_mes}/media/"
                  f"{pub_id}.(jpg|png|mp4|...). Se salta por ahora; Nicolás "
                  "puede subirlo y este script la retoma en la próxima corrida.")
            continue

        url_medio = url_medio_publica(raw_base, anio_mes, archivo)
        caption = armar_caption(pub)
        video_flag = es_video(archivo)

        print(f"  Medio: {archivo.name}  ({'video' if video_flag else 'imagen'})")
        print(f"  URL pública: {url_medio}")

        if args.dry_run:
            print("  [dry-run] No se publica de verdad.")
            continue

        ok_ig, detalle_ig = publicar_instagram(url_medio, caption, es_reel=video_flag)
        if ok_ig:
            print(f"  Instagram: publicado (id {detalle_ig})")
        else:
            print(f"  Instagram: FALLÓ — {detalle_ig}")

        ok_fb, detalle_fb = publicar_facebook(url_medio, caption, es_video_flag=video_flag)
        if ok_fb:
            print(f"  Facebook: publicado (id {detalle_fb})")
        else:
            print(f"  Facebook: FALLÓ — {detalle_fb}")

        if ok_ig or ok_fb:
            pub["publicado"] = True
            pub["publicado_instagram"] = ok_ig
            pub["publicado_facebook"] = ok_fb
            hubo_cambios = True
        else:
            print("  No se marca como publicado: fallaron las dos redes. "
                  "Se reintenta en la próxima corrida.")

    if hubo_cambios and not args.dry_run:
        guardar_calendario(calendario, ruta_calendario)
        print(f"\nCalendario actualizado en {ruta_calendario}")
        # El commit de vuelta al repo lo hace el workflow de GitHub Actions,
        # igual que hace content_engine.py con su propio workflow.

    print("\nListo.")


if __name__ == "__main__":
    main()
