#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALCO INDUSTRIA GRÁFICA — Fotos desde Google Drive
drive_fotos.py

QUÉ HACE
Busca las fotos y videos de cada publicación en la carpeta de Drive
"FOTOS PARA PUBLICAR", en vez de exigir que estén en el repositorio.

POR QUÉ
Subir archivos a GitHub no es cómodo para quien saca las fotos con el
celular. Con esto, Nicolás sube la foto a una carpeta de Drive con el
nombre del post (ig-2026-09-04.jpg) y el sistema la encuentra sola.

CÓMO SE AUTENTICA
Con una cuenta de servicio de Google. La credencial JSON va en el secreto
GOOGLE_CREDENTIALS del repositorio; nunca en el código.

La carpeta de Drive tiene que estar compartida con el email de esa cuenta
de servicio (con permiso de lector alcanza).

CONFIGURACIÓN
    GOOGLE_CREDENTIALS   JSON de la cuenta de servicio (secreto)
    DRIVE_FOLDER_ID      ID de la carpeta "FOTOS PARA PUBLICAR"

SI NO ESTÁ CONFIGURADO
No falla: devuelve None y el sistema sigue funcionando con las fotos que
haya en el repositorio, como antes. Esto es a propósito, para que la
publicación no se caiga si alguien revoca la credencial.
"""

import io
import json
import os
import sys

EXTENSIONES = (".jpg", ".jpeg", ".png", ".mp4", ".mov")

# ID de la carpeta "FOTOS PARA PUBLICAR" dentro de 04_REDES SOCIALES.
# Se puede sobrescribir con la variable de entorno DRIVE_FOLDER_ID.
CARPETA_POR_DEFECTO = "1cQeUR7eUkEzjUsQMj0jltRTE6X9YK1yX"


def _cliente_drive():
    """Devuelve el cliente de Drive, o None si no está configurado.

    Devolver None en vez de fallar es intencional: si la credencial no
    está puesta o venció, el sistema sigue publicando con las fotos del
    repositorio en vez de cortarse por completo."""
    credenciales_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not credenciales_json:
        return None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        print("    (Faltan las librerías de Google. Instalar con: "
              "pip install google-api-python-client google-auth)")
        return None

    try:
        info = json.loads(credenciales_json)
        cred = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        return build("drive", "v3", credentials=cred, cache_discovery=False)
    except Exception as e:
        print(f"    (No se pudo autenticar contra Drive: {e})")
        return None


def buscar_medio(pub_id, servicio=None):
    """Busca en la carpeta de Drive un archivo cuyo nombre sea el id de la
    publicación con cualquiera de las extensiones aceptadas.

    Devuelve (file_id, nombre_archivo) o (None, None) si no está."""
    servicio = servicio or _cliente_drive()
    if not servicio:
        return None, None

    carpeta = os.environ.get("DRIVE_FOLDER_ID", CARPETA_POR_DEFECTO)

    # Se piden todos los archivos de la carpeta que empiecen con el id.
    # Comparar después en Python evita depender de cómo Drive interpreta
    # la extensión en la consulta.
    consulta = (f"'{carpeta}' in parents and trashed = false "
                f"and name contains '{pub_id}'")

    try:
        resp = servicio.files().list(
            q=consulta,
            fields="files(id, name, mimeType)",
            pageSize=20,
        ).execute()
    except Exception as e:
        print(f"    (Error consultando Drive: {e})")
        return None, None

    archivos = resp.get("files", [])
    nombres_validos = {f"{pub_id}{ext}" for ext in EXTENSIONES}

    for f in archivos:
        if f["name"].lower() in {n.lower() for n in nombres_validos}:
            return f["id"], f["name"]

    return None, None


def descargar(file_id, ruta_destino, servicio=None):
    """Descarga un archivo de Drive al disco local.
    Devuelve True si salió bien."""
    servicio = servicio or _cliente_drive()
    if not servicio:
        return False

    try:
        from googleapiclient.http import MediaIoBaseDownload
    except ImportError:
        return False

    try:
        pedido = servicio.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        bajada = MediaIoBaseDownload(buffer, pedido)
        terminado = False
        while not terminado:
            _, terminado = bajada.next_chunk()

        ruta_destino.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta_destino, "wb") as f:
            f.write(buffer.getvalue())
        return True
    except Exception as e:
        print(f"    (Error descargando de Drive: {e})")
        return False


def esta_configurado():
    """Para que los scripts puedan avisar en el log si Drive está activo."""
    return bool(os.environ.get("GOOGLE_CREDENTIALS"))


if __name__ == "__main__":
    # Prueba manual:  python drive_fotos.py ig-2026-09-04
    if len(sys.argv) < 2:
        print("Uso: python drive_fotos.py <id-de-publicacion>")
        sys.exit(1)

    pub_id = sys.argv[1]
    if not esta_configurado():
        print("GOOGLE_CREDENTIALS no está configurado.")
        sys.exit(1)

    fid, nombre = buscar_medio(pub_id)
    if fid:
        print(f"Encontrado en Drive: {nombre} (id {fid})")
    else:
        print(f"No hay ningún archivo llamado {pub_id}.(jpg|png|mp4|...) "
              "en la carpeta de Drive.")
