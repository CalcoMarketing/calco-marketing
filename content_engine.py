#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALCO INDUSTRIA GRÁFICA — Motor de contenido
content_engine.py

QUÉ HACE
Genera el calendario editorial completo de un mes: publicaciones para
Instagram + Facebook y para LinkedIn, con copy listo para publicar,
hashtags, indicación de imagen y llamado a la acción rotado.

Además produce la lista de fotos y videos que hay que conseguir en el
taller, que es la única entrada humana que el sistema necesita — y le
avisa a Nicolás por mail apenas está lista, con el link directo.

CÓMO ESTÁ DISEÑADO
La estructura la calcula el código, no el modelo: las fechas, el reparto
de pilares según su peso, la rotación de CTA y la mezcla de hashtags son
deterministas. El modelo se ocupa solo de escribir. Eso hace que el
calendario sea consistente mes a mes y que el resultado sea auditable.

También lee el calendario del mes anterior, si existe, y le pasa al modelo
los ganchos ya usados para que no se repita.

USO
    # Con Anthropic (por defecto)
    export ANTHROPIC_API_KEY="sk-ant-..."
    python content_engine.py

    # Con DeepSeek
    export PROVEEDOR_IA="deepseek"
    export DEEPSEEK_API_KEY="sk-..."
    python content_engine.py

    python content_engine.py --mes 2026-09      # generar un mes específico
    python content_engine.py --dry-run          # sin llamar a la API

PROVEEDORES
El motor funciona igual con Anthropic o con DeepSeek. Se cambia con la
variable PROVEEDOR_IA, sin tocar el código. El resto del programa no sabe
qué modelo hay detrás.

AVISO A NICOLÁS POR MAIL (nuevo, Sesión 5)
Al terminar de generar el calendario, se envía un mail simple a Nicolás
con el link directo a lista-de-fotos.md del mes. Requiere estas variables
de entorno (secrets de GitHub):
    EMAIL_REMITENTE     la cuenta de Gmail que manda el aviso (ej: marketing@calco.uy)
    EMAIL_CLAVE_APP     contraseña de aplicación de esa cuenta (no la contraseña normal)
    NICOLAS_EMAIL       opcional, por defecto nastengo@smartier.software

Si faltan estas variables, el calendario se genera igual — el aviso por
mail es un extra, nunca bloquea la función principal del script.

SALIDA
    contenido/AAAA-MM/calendario.md      <- para copiar y pegar
    contenido/AAAA-MM/calendario.json    <- para el publicador automático
    contenido/AAAA-MM/lista-de-fotos.md  <- para Nicolás
"""

import argparse
import calendar
import json
import locale
import os
import re
import smtplib
import sys
from datetime import date, timedelta
from email.mime.text import MIMEText
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ---------------------------------------------------------------------------
# CAPA DE PROVEEDOR
# El resto del programa no sabe ni le importa qué IA está detrás.
# ---------------------------------------------------------------------------

def crear_cliente():
    """Devuelve (cliente, modelo, nombre_proveedor) según PROVEEDOR_IA."""
    if PROVEEDOR not in PROVEEDORES:
        print(f"Proveedor desconocido: '{PROVEEDOR}'.")
        print(f"Valores admitidos: {', '.join(PROVEEDORES)}")
        sys.exit(1)

    cfg = PROVEEDORES[PROVEEDOR]
    clave = os.environ.get(cfg["variable_clave"])

    if not clave:
        print(f"Falta la variable de entorno {cfg['variable_clave']}.")
        print(f"En local:  export {cfg['variable_clave']}='...'")
        print("En GitHub Actions se toma del secreto del repositorio.")
        sys.exit(1)

    if PROVEEDOR == "anthropic":
        if Anthropic is None:
            print("Falta la librería. Instalar con:  pip install anthropic")
            sys.exit(1)
        return Anthropic(api_key=clave), cfg["modelo"], PROVEEDOR

    if OpenAI is None:
        print("Falta la librería. Instalar con:  pip install openai")
        sys.exit(1)
    return OpenAI(api_key=clave, base_url=cfg["base_url"]), cfg["modelo"], PROVEEDOR


def pedir_texto(cliente, modelo, prompt):
    """
    Manda el prompt y devuelve el texto de la respuesta.
    Unifica las dos formas distintas de llamar que tiene cada proveedor.
    """
    if PROVEEDOR == "anthropic":
        r = cliente.messages.create(
            model=modelo,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in r.content if b.type == "text")

    r = cliente.chat.completions.create(
        model=modelo,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

# Proveedor de IA. Se define con la variable de entorno PROVEEDOR_IA.
# Valores admitidos: "anthropic" (por defecto) o "deepseek".
PROVEEDOR = os.environ.get("PROVEEDOR_IA", "anthropic").strip().lower()

PROVEEDORES = {
    "anthropic": {
        "modelo": "claude-sonnet-5",
        "variable_clave": "ANTHROPIC_API_KEY",
        "base_url": None,
    },
    "deepseek": {
        "modelo": "deepseek-chat",
        "variable_clave": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
    },
}

MAX_TOKENS = 16000
RAIZ = Path(__file__).parent
ARCHIVO_MARCA = RAIZ / "marca" / "sistema_de_marca.json"
DIR_CONTENIDO = RAIZ / "contenido"

# Repo público: se usa para armar el link directo que se le manda a
# Nicolás por mail. Si el repo cambiara de nombre/organización, actualizar
# solo acá.
REPO_GITHUB_URL = "https://github.com/CalcoMarketing/calco-marketing/blob/main"

DIAS_SEMANA = {
    "lunes": 0, "martes": 1, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6,
}

NOMBRE_MES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre",
    11: "noviembre", 12: "diciembre",
}

NOMBRE_DIA = {
    0: "lunes", 1: "martes", 2: "miércoles",
    3: "jueves", 4: "viernes", 5: "sábado", 6: "domingo",
}


# ---------------------------------------------------------------------------
# ESTRUCTURA (determinista, no la decide el modelo)
# ---------------------------------------------------------------------------

def cargar_marca():
    if not ARCHIVO_MARCA.exists():
        print(f"No se encontró {ARCHIVO_MARCA}")
        sys.exit(1)
    with open(ARCHIVO_MARCA, encoding="utf-8") as f:
        return json.load(f)


def fechas_del_mes(anio, mes, dias_nombre, desde_hoy=False):
    """Devuelve las fechas del mes que caen en los días de la semana pedidos."""
    objetivo = {DIAS_SEMANA[d] for d in dias_nombre}
    ultimo = calendar.monthrange(anio, mes)[1]
    hoy = date.today()
    fechas = []
    for dia in range(1, ultimo + 1):
        f = date(anio, mes, dia)
        if f.weekday() in objetivo:
            if desde_hoy and f <= hoy:
                continue
            fechas.append(f)
    return fechas


def repartir_pilares(pilares, cantidad):
    """
    Asigna un pilar a cada publicación respetando los pesos configurados,
    y los intercala para que no salgan dos iguales seguidos.
    """
    asignaciones = []
    for p in pilares:
        n = max(1, round(cantidad * p["peso"] / 100))
        asignaciones.extend([p["clave"]] * n)

    # Ajuste fino a la cantidad exacta
    while len(asignaciones) > cantidad:
        # saca del pilar más representado
        mas_comun = max(set(asignaciones), key=asignaciones.count)
        asignaciones.remove(mas_comun)
    while len(asignaciones) < cantidad:
        asignaciones.append(pilares[0]["clave"])

    # Intercalado: round-robin sobre los grupos para evitar repeticiones
    grupos = {}
    for a in asignaciones:
        grupos.setdefault(a, []).append(a)
    orden = sorted(grupos, key=lambda k: -len(grupos[k]))

    resultado = []
    while len(resultado) < cantidad:
        for clave in orden:
            if grupos[clave]:
                resultado.append(grupos[clave].pop())
                if len(resultado) == cantidad:
                    break
    return resultado


def armar_esqueleto(marca, anio, mes, desde_hoy=False):
    """Construye la grilla vacía: fecha, red, pilar, CTA, vertical sugerida."""
    cad = marca["cadencia"]
    pilares = marca["pilares"]
    ctas = marca["ctas"]
    verticales = [v["clave"] for v in marca["verticales"]]

    f_ig = fechas_del_mes(anio, mes, cad["instagram_facebook"], desde_hoy)
    f_li = fechas_del_mes(anio, mes, cad["linkedin"], desde_hoy)

    pilares_ig = repartir_pilares(pilares, len(f_ig))

    esqueleto_ig = []
    i_vertical = 0
    for i, (f, pilar) in enumerate(zip(f_ig, pilares_ig)):
        vertical = None
        if pilar == "vertical":
            vertical = verticales[i_vertical % len(verticales)]
            i_vertical += 1
        esqueleto_ig.append({
            "id": f"ig-{f.isoformat()}",
            "fecha": f.isoformat(),
            "dia_semana": NOMBRE_DIA[f.weekday()],
            "red": "instagram_facebook",
            "pilar": pilar,
            "vertical": vertical,
            "cta": ctas[i % len(ctas)],
            "formato": "reel" if pilar == "produccion" and i % 2 == 0 else "imagen",
            "hora": cad["hora_publicacion"],
        })

    esqueleto_li = []
    for i, f in enumerate(f_li):
        esqueleto_li.append({
            "id": f"li-{f.isoformat()}",
            "fecha": f.isoformat(),
            "dia_semana": NOMBRE_DIA[f.weekday()],
            "red": "linkedin",
            "pilar": "educativo" if i % 2 == 0 else "credibilidad",
            "vertical": None,
            "cta": "SIN_CTA",
            "formato": "texto",
            "hora": cad["hora_publicacion"],
        })

    return esqueleto_ig, esqueleto_li


def mezclar_hashtags(marca, pilar, vertical, producto_hint=None):
    h = marca["hashtags"]
    tags = list(h["base"]) + [h["geo"][0]]
    if producto_hint and producto_hint in h["producto"]:
        tags += h["producto"][producto_hint][:2]
    if vertical and vertical in h["vertical"]:
        tags += h["vertical"][vertical][:2]
    # completar hasta 9 sin duplicar
    for extra in h["geo"][1:] + h["producto"].get("packaging", []):
        if len(tags) >= 9:
            break
        if extra not in tags:
            tags.append(extra)
    return tags[:9]


# ---------------------------------------------------------------------------
# GENERACIÓN DE COPY
# ---------------------------------------------------------------------------

def ganchos_previos(anio, mes):
    """Lee el mes anterior para no repetir ganchos ni temas de producto."""
    m_prev = mes - 1 or 12
    a_prev = anio if mes > 1 else anio - 1
    prev = DIR_CONTENIDO / f"{a_prev}-{m_prev:02d}" / "calendario.json"
    if not prev.exists():
        return [], []
    try:
        with open(prev, encoding="utf-8") as f:
            data = json.load(f)
        pubs = data.get("publicaciones", [])
        ganchos = [p.get("gancho", "") for p in pubs if p.get("gancho")]
        productos = [p.get("producto", "") for p in pubs if p.get("producto")]
        return ganchos, productos
    except Exception:
        return [], []


def construir_prompt(marca, esqueleto, red, ganchos_usados, temas_usados_este_mes):
    pilares_txt = "\n".join(
        f"- {p['clave']}: {p['nombre']}. {p['objetivo']}" for p in marca["pilares"]
    )
    productos_txt = "\n".join(
        f"- {k}: {v['nombre']}. {v['detalle']}" for k, v in marca["productos"].items()
    )
    verticales_txt = "\n".join(
        f"- {v['clave']}: {v['nombre']}. {v['angulo']}" for v in marca["verticales"]
    )
    voz_txt = "\n".join(f"- {p}" for p in marca["voz"]["principios"])
    prohibido_txt = "\n".join(f"- {p}" for p in marca["voz"]["prohibido"])
    difs_txt = "\n".join(f"- {d}" for d in marca["diferenciales"])

    # Regla de certificación, calculada según los productos que toca esta
    # tanda. El certificado UNIT-ISO 9001 no cubre todos los rubros, y UNIT
    # prohíbe dar a entender un alcance mayor al real (instructivo CS/PI 016).
    cert = marca.get("certificacion")
    cert_txt = ""
    if cert:
        productos_tanda = {e.get("producto") for e in esqueleto if e.get("producto")}
        fuera = set(cert.get("productos_FUERA_del_alcance", []))
        toca_fuera = bool(productos_tanda & fuera)

        cert_txt = (
            "\n\nCÓMO NOMBRAR LA CERTIFICACIÓN (regla estricta, la controla el "
            "organismo certificador)\n"
            f"- Escribir siempre «{cert['formula_corta']}». Nunca «imprenta "
            "certificada», «calidad certificada» ni «certificados» a secas: "
            "UNIT exige que su nombre conste y esas formas ambiguas están "
            "expresamente prohibidas en su instructivo.\n"
            "- Nunca «certificados por ISO»: ISO no certifica empresas.\n"
            f"- Alcance real del certificado: {cert['alcance']} "
            "No se puede sugerir que cubre más que eso.\n"
            "- La certificación es de 2021; la empresa opera desde 2005. Son "
            "datos separados: nunca escribir «certificados desde 2005»."
        )
        if toca_fuera:
            cert_txt += (
                "\n- ATENCIÓN EN ESTA TANDA: hay publicaciones sobre productos "
                f"FUERA del alcance certificado ({', '.join(sorted(productos_tanda & fuera))}). "
                "En esas publicaciones NO menciones la certificación de ninguna "
                "forma."
            )


    if red == "linkedin":
        instruccion_red = (
            f"Audiencia: {marca['linkedin']['audiencia']}\n"
            f"Tono: {marca['linkedin']['tono']}\n"
            f"Cierre: {marca['linkedin']['cierre']}\n"
            "Largo: 120 a 200 palabras. Sin hashtags. Sin emojis."
        )
    else:
        instruccion_red = (
            "Instagram y Facebook, mismo copy para las dos.\n"
            "Largo: 50 a 110 palabras. Primera línea corta y con gancho: es lo "
            "único que se ve antes del 'ver más'.\n"
            "Máximo 2 emojis, y solo si aportan.\n"
            "NO escribas el CTA dentro del texto: el sistema lo agrega "
            "aparte, al final. Vos escribí solo el cuerpo, y cerralo con "
            "el argumento (un dato, una consecuencia práctica, una "
            "afirmación). Tampoco cierres con una pregunta al lector "
            "('¿Lo probamos?', '¿Hablamos?'): ese lugar ya lo ocupa el CTA."
        )

    evitar = ""
    if ganchos_usados:
        lista = "\n".join(f"- {g}" for g in ganchos_usados[:25])
        evitar = (
            "\n\nGANCHOS YA USADOS EN MESES ANTERIORES. No repetirlos ni "
            f"parafrasearlos:\n{lista}"
        )

    diversidad = ""
    if temas_usados_este_mes:
        conteo = {}
        for t in temas_usados_este_mes:
            conteo[t] = conteo.get(t, 0) + 1
        repetidos = [t for t, n in conteo.items() if n >= 1]
        if repetidos:
            lista_temas = ", ".join(sorted(repetidos))
            diversidad = (
                "\n\nDIVERSIDAD DE TEMA DENTRO DE ESTE MISMO MES. Ya se usaron "
                f"como tema principal: {lista_temas}. No repitas el mismo "
                "producto ni el mismo asunto de fondo (por ejemplo, si ya se "
                "habló del depósito legal, no lo vuelvas a usar como eje de "
                "otra publicación este mes, aunque cambies las palabras)."
            )

    grilla = json.dumps(esqueleto, ensure_ascii=False, indent=2)

    return f"""Sos el redactor de contenidos de {marca['empresa']['nombre']}, una {marca['empresa']['rubro']} en {marca['empresa']['ubicacion']}, en actividad desde {marca['empresa']['desde']}, que atiende {marca['empresa']['zona_servicio']}.

VOZ DE MARCA
{voz_txt}

PROHIBIDO
{prohibido_txt}

DIFERENCIALES REALES (son los únicos hechos que podés afirmar sobre la empresa)
{difs_txt}{cert_txt}

PRODUCTOS
{productos_txt}

VERTICALES
{verticales_txt}

PILARES DE CONTENIDO
{pilares_txt}

NOTA DE DESAMBIGUACIÓN
{marca['desambiguacion']}

RED Y FORMATO
{instruccion_red}

REGLA CRÍTICA
No inventes datos que no estén en la lista de diferenciales o productos. Nada de plazos concretos en horas o días, cantidades mínimas, precios, nombres de certificaciones, ni nombres de clientes. Nunca cites números de ley, artículos o normativas específicas: si mencionás una obligación legal (como el depósito legal), describila en términos generales, sin número de ley, porque no está verificado y un dato legal incorrecto con el nombre de la empresa es un riesgo real. Si un texto necesitaría un dato así para funcionar, reformulalo para no necesitarlo.{evitar}{diversidad}

TAREA
Para cada publicación de la grilla, escribí el contenido. Respetá el pilar, el vertical y el CTA asignados.

GRILLA
{grilla}

FORMATO DE RESPUESTA
Devolvé únicamente un array JSON válido, sin texto antes ni después, sin bloques de código markdown. Un objeto por publicación, en el mismo orden que la grilla, con estas claves exactas:

[
  {{
    "id": "el id de la grilla, igual",
    "gancho": "la primera línea, hasta 60 caracteres",
    "copy": "el texto completo de la publicación, con saltos de línea como \\n\\n",
    "producto": "la clave del producto principal mencionado, de la lista de PRODUCTOS",
    "objeto_visual": "el objeto físico concreto del que habla el texto, en 1 a 3 palabras, en singular y en minúscula (por ejemplo: 'caja troquelada', 'estuche', 'bolsa', 'etiqueta en rollo', 'cuaderno', 'libro'). Tiene que ser el objeto que el lector espera VER en la foto al leer este texto. Si el post no habla de un objeto físico puntual, poner cadena vacía.",
    "imagen": "descripción concreta de la foto o video que hay que conseguir en el taller, en una frase, redactada como instrucción para quien la va a tomar"
  }}
]
"""


def limpiar_json(texto):
    """Saca bloques de código si el modelo los agrega igual."""
    t = texto.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    inicio = t.find("[")
    fin = t.rfind("]")
    if inicio != -1 and fin != -1:
        t = t[inicio:fin + 1]
    return t


TAMANO_TANDA = 6  # publicaciones por llamado a la API. Chico a propósito:
                   # evita que una tanda grande se acerque al límite de
                   # tokens y quede un JSON cortado a mitad de camino.


def _llamar_api(cliente, modelo, prompt, intentos=2):
    """
    Un llamado a la API con reintento simple si el JSON viene incompleto.
    Devuelve (datos, error, fatal). Si fatal es True, no tiene sentido
    seguir intentando con las tandas siguientes: por ejemplo, cuando la
    cuenta se quedó sin saldo o la clave es inválida.
    """
    ultimo_texto = ""
    for intento in range(1, intentos + 1):
        try:
            texto = pedir_texto(cliente, modelo, prompt)
        except Exception as e:
            mensaje = str(e)
            fatal = any(t in mensaje.lower() for t in (
                "credit balance", "insufficient balance", "invalid x-api-key",
                "authentication", "permission", "quota", "invalid_api_key",
            ))
            return None, (mensaje, "error de API"), fatal

        ultimo_texto = texto
        try:
            return json.loads(limpiar_json(texto)), None, False
        except json.JSONDecodeError as e:
            if intento < intentos:
                print(f"    Tanda con JSON incompleto, reintentando ({intento}/{intentos})...")
                continue
            return None, (texto, e), False
    return None, (ultimo_texto, "sin datos"), False


def generar(cliente, modelo, marca, esqueleto, red, ganchos_usados, temas_usados_meses_previos):
    if not esqueleto:
        return []

    tandas = [esqueleto[i:i + TAMANO_TANDA] for i in range(0, len(esqueleto), TAMANO_TANDA)]
    print(f"  Generando {len(esqueleto)} publicaciones para {red} "
          f"en {len(tandas)} tanda(s) de hasta {TAMANO_TANDA}...")

    resultado = []
    ganchos_acumulados = list(ganchos_usados)
    # Temas de producto usados este mes, dentro de esta misma red. Arranca
    # con los de meses previos por si el modelo insiste en el mismo tema
    # apenas cambia el mes, pero lo que más pesa es lo que se va acumulando
    # tanda a tanda dentro de esta corrida.
    temas_este_mes = []

    for n, tanda in enumerate(tandas, 1):
        print(f"    Tanda {n}/{len(tandas)} ({len(tanda)} publicaciones)")
        prompt = construir_prompt(marca, tanda, red, ganchos_acumulados, temas_este_mes)
        datos, error, fatal = _llamar_api(cliente, modelo, prompt)

        if error is not None:
            texto, e = error
            fallo = DIR_CONTENIDO / f"_fallo_{red}_tanda{n}.txt"
            fallo.parent.mkdir(parents=True, exist_ok=True)
            fallo.write_text(str(texto), encoding="utf-8")
            print(f"    Tanda {n} falló. Detalle guardado en {fallo}")
            print(f"    Error: {e}")
            if fatal:
                print("    Error irrecuperable (saldo, clave o permisos).")
                print(f"    Se conserva lo generado hasta acá: {len(resultado)} publicaciones.")
                break
            continue

        resultado.extend(datos)
        # Los ganchos y los temas de esta tanda alimentan el prompt de la
        # siguiente, para que ni el gancho ni el tema de fondo se repitan
        # dentro del mismo mes.
        ganchos_acumulados.extend(d.get("gancho", "") for d in datos if d.get("gancho"))
        temas_este_mes.extend(d.get("producto", "") for d in datos if d.get("producto"))

    return resultado


# ---------------------------------------------------------------------------
# ESCRITURA
# ---------------------------------------------------------------------------

_PALABRAS_VACIAS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "que", "y", "es", "en", "a", "por", "para", "con", "tu", "te", "se",
    "no", "lo", "su", "al", "o", "si", "cómo", "qué", "cuál", "cuáles",
    "más", "muy", "también", "así", "eso", "esto", "esa", "ese", "esto",
}


def _normalizar(texto):
    """Simplifica un texto para comparar similitud, ignorando may/min,
    puntuación, espacios de más y palabras vacías (para no confundir dos
    ganchos por compartir 'qué', 'es', 'el', etc.)."""
    t = texto.lower().strip()
    t = re.sub(r"[¿?¡!.,:;\"']", "", t)
    t = re.sub(r"\s+", " ", t)
    palabras = [w for w in t.split() if w not in _PALABRAS_VACIAS]
    return " ".join(palabras) if palabras else t


def _son_parecidos(a, b, umbral=0.55):
    """
    Similitud simple por palabras compartidas. No hace falta una librería
    de NLP para esto: alcanza con detectar que dos ganchos son
    prácticamente el mismo texto, que es el patrón real que se vio en
    calendarios generados (mismo gancho, o casi el mismo, repetido dentro
    del mismo mes a pesar de la instrucción de no repetir).
    """
    pa, pb = set(_normalizar(a).split()), set(_normalizar(b).split())
    if not pa or not pb:
        return False
    interseccion = len(pa & pb)
    union = len(pa | pb)
    return (interseccion / union) >= umbral


def marcar_duplicados(pubs, ganchos_mes_anterior=None):
    """
    Verificación por código, no por instrucción al modelo: recorre las
    publicaciones ya generadas y, si dos ganchos son iguales o casi
    iguales, marca ambas con una advertencia visible. No depende de que
    el modelo haya respetado la instrucción de 'no repetir tema' — la
    detecta después, de forma determinista.

    Compara en dos direcciones:
    1. Dentro del mes que se está generando (como antes).
    2. Contra los ganchos del mes anterior, que es el caso que se detectó
       en la práctica: el modelo repite un gancho de hace 30 días aunque
       el prompt le diga explícitamente que no lo haga.
    """
    marcadas = 0

    # 1) Dentro del mismo mes
    for i, p in enumerate(pubs):
        for j, q in enumerate(pubs):
            if i >= j:
                continue
            g1, g2 = p.get("gancho", ""), q.get("gancho", "")
            if not g1 or not g2:
                continue
            if _normalizar(g1) == _normalizar(g2) or _son_parecidos(g1, g2):
                p["duplicado_de"] = q["id"]
                q["duplicado_de"] = p["id"]
                marcadas += 1

    # 2) Contra el mes anterior
    if ganchos_mes_anterior:
        for p in pubs:
            if p.get("duplicado_de"):
                continue  # ya marcada por el chequeo del mismo mes
            g1 = p.get("gancho", "")
            if not g1:
                continue
            for g2 in ganchos_mes_anterior:
                if _normalizar(g1) == _normalizar(g2) or _son_parecidos(g1, g2):
                    p["duplicado_de"] = "un post del mes anterior"
                    marcadas += 1
                    break

    if marcadas:
        print(f"  ATENCIÓN: {marcadas} publicación(es) con gancho igual o "
              f"muy parecido a otra (del mismo mes o del anterior). "
              f"Marcadas para revisión manual antes de publicar.")
    return pubs


# Si el gancho supera esta longitud, es sospechoso: el gancho es "la
# primera línea, hasta 60 caracteres" según la instrucción del prompt.
# Se deja margen (100) para no marcar ganchos un poco largos que están
# bien, y detectar el caso real que se vio en la práctica: el modelo
# vuelca el post ENTERO en el campo "gancho" y deja "copy" vacío.
LARGO_MAXIMO_GANCHO_NORMAL = 100


def marcar_copy_vacio(pubs):
    """
    Verificación por código de un desvío nuevo detectado en la Sesión 5:
    el modelo a veces devuelve el texto completo del post dentro del
    campo 'gancho' y deja 'copy' vacío. El JSON es válido — no lo
    detecta el parseo — pero el post sale con el cuerpo en blanco en
    calendario.md, en la lista de fotos y en el mail a Nicolás.

    Se detecta así: copy vacío (o casi) + gancho anormalmente largo.
    Se marca con 'copy_vacio': True para que quede visible en el
    markdown y quien revise el calendario antes de publicar lo vea y
    lo corrija a mano. No se intenta corregir solo (separar
    automáticamente gancho/copy es arriesgado: podría cortar mal una
    oración), es más seguro que una persona lo revise una vez detectado.
    """
    marcadas = 0
    for p in pubs:
        copy_texto = (p.get("copy") or "").strip()
        gancho = p.get("gancho") or ""
        if not copy_texto and len(gancho) > LARGO_MAXIMO_GANCHO_NORMAL:
            p["copy_vacio"] = True
            marcadas += 1

    if marcadas:
        print(f"  ATENCIÓN: {marcadas} publicación(es) con 'copy' vacío y "
              f"'gancho' sospechosamente largo — probablemente el modelo "
              f"volcó todo el texto en el campo equivocado. Revisar y "
              f"corregir a mano antes de publicar (buscar 'copy_vacio' en "
              f"calendario.md).")
    return pubs


def _quitar_cta_duplicado(copy_texto, cta):
    """El CTA lo agrega el sistema aparte, pero el modelo a veces lo
    escribe igual al final del cuerpo. Resultado: el mismo pedido dos
    veces seguidas, que suena insistente.

    Esta función lo detecta y lo saca del cuerpo. Es verificación por
    código, no una instrucción al modelo: no depende de que obedezca.

    Detecta dos casos:
    1. El CTA copiado literal o casi literal ("Contanos qué necesitás en
       los comentarios").
    2. Una variante reconocible del mismo pedido, comparando las
       palabras significativas del último párrafo contra las del CTA.
    """
    if not copy_texto or not cta or cta == "SIN_CTA":
        return copy_texto

    parrafos = [p for p in copy_texto.split("\n\n") if p.strip()]
    if len(parrafos) <= 1:
        return copy_texto  # no dejar el copy vacío

    ultimo = parrafos[-1].strip()

    # Palabras significativas del CTA, sin relleno ni puntuación
    def _clave(t):
        t = t.lower()
        t = re.sub(r"[^\wáéíóúñ\s]", " ", t)
        return {w for w in t.split()
                if w not in _PALABRAS_VACIAS and len(w) > 2}

    pal_cta = _clave(cta)
    pal_ult = _clave(ultimo)

    if not pal_cta or not pal_ult:
        return copy_texto

    # Cuántas palabras del CTA aparecen en el último párrafo
    compartidas = len(pal_cta & pal_ult)
    proporcion = compartidas / len(pal_cta)

    # Umbral alto y párrafo corto: es el CTA repetido, no un cierre que
    # casualmente comparte alguna palabra.
    es_duplicado = proporcion >= 0.6 and len(pal_ult) <= len(pal_cta) + 4

    if es_duplicado:
        return "\n\n".join(parrafos[:-1]).strip()

    return copy_texto


def fusionar(esqueleto, generado, marca):
    por_id = {g["id"]: g for g in generado}
    salida = []
    for e in esqueleto:
        g = por_id.get(e["id"])
        if not g:
            continue
        item = dict(e)
        copy_limpio = _quitar_cta_duplicado(g.get("copy", ""), e.get("cta", ""))
        item.update({
            "gancho": g.get("gancho", ""),
            "copy": copy_limpio,
            "producto": g.get("producto", ""),
            "objeto_visual": g.get("objeto_visual", ""),
            "imagen": g.get("imagen", ""),
        })
        if e["red"] == "instagram_facebook":
            item["hashtags"] = mezclar_hashtags(
                marca, e["pilar"], e.get("vertical"), g.get("producto")
            )
        else:
            item["hashtags"] = []
        salida.append(item)
    return salida


def escribir_markdown(pubs, anio, mes, ruta):
    duplicados = [p for p in pubs if p.get("duplicado_de")]
    vacios = [p for p in pubs if p.get("copy_vacio")]
    lineas = [
        f"# Calendario Editorial · {NOMBRE_MES[mes]} {anio}",
        f"## Calco Industria Gráfica",
        "",
        f"**Generado automáticamente** · {len(pubs)} publicaciones",
        "**Todo el copy está listo para copiar y pegar.**",
        "",
    ]

    if duplicados:
        lineas += [
            "> ⚠️ **REVISAR ANTES DE PUBLICAR:** se detectaron publicaciones "
            "con gancho igual o muy parecido dentro de este mes. Están "
            "marcadas más abajo con ⚠️. Elegir una y reescribir o "
            "descartar la otra antes de programar.",
            "",
        ]

    if vacios:
        lineas += [
            "> 🚨 **REVISAR ANTES DE PUBLICAR:** hay publicaciones con el "
            "texto vacío — el modelo volcó todo el contenido en el gancho "
            "por error. Están marcadas más abajo con 🚨. Hay que separar "
            "el texto a mano antes de usarlas.",
            "",
        ]

    lineas += ["---", ""]

    ig = [p for p in pubs if p["red"] == "instagram_facebook"]
    li = [p for p in pubs if p["red"] == "linkedin"]

    if ig:
        lineas += ["## Instagram + Facebook", ""]
        for p in ig:
            f = date.fromisoformat(p["fecha"])
            etiqueta = p["pilar"]
            if p.get("vertical"):
                etiqueta += f" · {p['vertical']}"
            alerta = " ⚠️ POSIBLE DUPLICADO" if p.get("duplicado_de") else ""
            alerta += " 🚨 TEXTO VACÍO — REVISAR" if p.get("copy_vacio") else ""
            lineas += [
                f"### 📅 {p['dia_semana'].capitalize()} {f.day} de {NOMBRE_MES[mes]} · {etiqueta}{alerta}",
                f"**Formato:** {p['formato']} · **Hora:** {p['hora']}",
                f"**Imagen a conseguir:** {p['imagen']}",
                "",
            ]
            if p.get("duplicado_de"):
                lineas += [
                    f"⚠️ *Se parece a la publicación `{p['duplicado_de']}` de este mismo mes. Revisar antes de programar.*",
                    "",
                ]
            if p.get("copy_vacio"):
                lineas += [
                    "🚨 *El texto de este post quedó vacío (probablemente volcado "
                    "por error dentro del gancho, más abajo). Separar el gancho "
                    "real del cuerpo a mano antes de usar este post.*",
                    "",
                ]
            for parrafo in p["copy"].split("\n\n"):
                lineas.append(f"> {parrafo.strip()}")
                lineas.append(">")
            lineas.pop()
            lineas += ["", "`" + " ".join(p["hashtags"]) + "`", "", "---", ""]

    if li:
        lineas += ["## LinkedIn", ""]
        for p in li:
            f = date.fromisoformat(p["fecha"])
            lineas += [
                f"### 📅 {p['dia_semana'].capitalize()} {f.day} de {NOMBRE_MES[mes]}",
                f"**Hora:** {p['hora']}",
                "",
            ]
            for parrafo in p["copy"].split("\n\n"):
                lineas.append(f"> {parrafo.strip()}")
                lineas.append(">")
            lineas.pop()
            lineas += ["", "---", ""]

    ruta.write_text("\n".join(lineas), encoding="utf-8")


def escribir_lista_fotos(pubs, anio, mes, ruta):
    ig = [p for p in pubs if p["red"] == "instagram_facebook"]
    lineas = [
        f"# Lista de fotos y videos · {NOMBRE_MES[mes]} {anio}",
        "## Para Nicolás",
        "",
        "Esto es lo único que el sistema no puede generar solo. Sin este material",
        "las piezas salen con fotos de catálogo y rinden la mitad.",
        "",
        "**Reglas:** luz natural o del taller, nunca flash. Vertical 9:16 para",
        "Reels e historias, cuadrado 1:1 para el feed. No hace falta que salgan",
        "perfectas: la textura real de una imprenta vende más que un render.",
        "",
        "---",
        "",
    ]
    for i, p in enumerate(ig, 1):
        f = date.fromisoformat(p["fecha"])
        tipo = "🎥 VIDEO" if p["formato"] == "reel" else "📷 FOTO"
        lineas.append(
            f"{i}. **{tipo}** — para publicar el {f.day}/{mes:02d} — {p['imagen']}"
        )
    lineas += ["", "---", "", "20 minutos de celular por semana en horario de producción alcanzan."]
    ruta.write_text("\n".join(lineas), encoding="utf-8")


# ---------------------------------------------------------------------------
# AVISO A NICOLÁS POR MAIL (nuevo, Sesión 5)
# ---------------------------------------------------------------------------

def avisar_a_nicolas(anio, mes, pubs_ig):
    """
    Manda un mail con el contenido COMPLETO del mes para Instagram/Facebook:
    para cada publicación, la fecha, qué foto o video hay que conseguir, y
    el texto entero del post — no solo la lista de fotos. Así Nicolás ve
    el contexto real de cada publicación, no una lista suelta de objetos
    para fotografiar sin saber para qué van.

    También incluye los links a calendario.md y lista-de-fotos.md por si
    prefiere verlo directamente en GitHub.

    Es un extra, no una función crítica: si faltan las variables de
    entorno o falla el envío, se avisa por consola pero NO se corta la
    generación del calendario. Perder el mail es mucho menos grave que
    perder el calendario entero por un problema de SMTP.
    """
    remitente = os.environ.get("EMAIL_REMITENTE")
    clave_app = os.environ.get("EMAIL_CLAVE_APP")
    destinatario = os.environ.get("NICOLAS_EMAIL", "nastengo@smartier.software")

    if not remitente or not clave_app:
        print("  (Aviso a Nicolás NO enviado: faltan los secrets "
              "EMAIL_REMITENTE y/o EMAIL_CLAVE_APP en GitHub.)")
        return

    anio_mes = f"{anio}-{mes:02d}"
    link_calendario = f"{REPO_GITHUB_URL}/contenido/{anio_mes}/calendario.md"
    link_fotos = f"{REPO_GITHUB_URL}/contenido/{anio_mes}/lista-de-fotos.md"

    asunto = f"Contenido de {NOMBRE_MES[mes]} — Calco ({len(pubs_ig)} publicaciones)"

    hay_problemas = any(p.get("duplicado_de") or p.get("copy_vacio") for p in pubs_ig)

    partes = [
        f"Hola Nicolás,\n",
        f"Ya está listo el calendario de {NOMBRE_MES[mes]} {anio} para "
        f"Instagram y Facebook: {len(pubs_ig)} publicaciones.\n",
    ]

    if hay_problemas:
        partes.append(
            "⚠ OJO: algunas publicaciones de abajo quedaron marcadas para "
            "revisar antes de publicar (texto duplicado o vacío). Están "
            "señaladas con ⚠ o 🚨 en su fecha correspondiente.\n"
        )

    partes += [
        "Abajo está el texto completo de cada una, con la foto o video que "
        "hay que conseguir para cada post. Si preferís verlo en GitHub:\n",
        f"  Calendario completo: {link_calendario}",
        f"  Solo la lista de fotos: {link_fotos}\n",
        "=" * 60,
    ]

    for p in sorted(pubs_ig, key=lambda x: x["fecha"]):
        f = date.fromisoformat(p["fecha"])
        tipo = "VIDEO" if p.get("formato") == "reel" else "FOTO"
        etiqueta = p.get("pilar", "")
        if p.get("vertical"):
            etiqueta += f" · {p['vertical']}"

        alerta = ""
        if p.get("duplicado_de"):
            alerta += " [⚠ POSIBLE DUPLICADO]"
        if p.get("copy_vacio"):
            alerta += " [🚨 TEXTO VACÍO — REVISAR ANTES DE USAR]"

        partes.append("")
        partes.append(f"{f.day}/{mes:02d} ({p.get('dia_semana', '')}) · {etiqueta}{alerta}")
        partes.append(f"[{tipo} A CONSEGUIR] {p.get('imagen', '')}")
        partes.append("")
        if p.get("copy_vacio"):
            partes.append(
                "[Este post quedó con el texto vacío — probablemente el "
                "sistema volcó todo por error en el título. Se necesita "
                "revisión manual antes de usar este post. El texto crudo, "
                "sin separar, quedó en el campo 'gancho':]"
            )
            partes.append(p.get("gancho", ""))
        else:
            partes.append(p.get("copy", "").strip())
        if p.get("duplicado_de"):
            partes.append("")
            partes.append(
                f"⚠ ATENCIÓN: este post se parece a {p['duplicado_de']} — "
                "revisar antes de programar, puede necesitar ajustes."
            )
        partes.append("")
        partes.append("-" * 60)

    partes.append("")
    partes.append(
        "Recordatorio: subí cada foto/video a la carpeta de Drive 'FOTOS "
        "PARA PUBLICAR' con el nombre del post (por ejemplo: "
        f"ig-{anio_mes}-02.jpg). El sistema las toma solas de ahí.\n"
    )
    partes.append("— Sistema de contenido de Calco (mensaje automático, no responder)")

    cuerpo = "\n".join(partes)

    msg = MIMEText(cuerpo, _charset="utf-8")
    msg["Subject"] = asunto
    msg["From"] = remitente
    msg["To"] = destinatario

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(remitente, clave_app)
            server.sendmail(remitente, [destinatario], msg.as_string())
        print(f"  Aviso completo enviado a Nicolás ({destinatario}).")
    except Exception as e:
        print(f"  No se pudo enviar el aviso a Nicolás: {e}")
        print("  (No es grave: el calendario y la lista de fotos ya están "
              "guardados igual. Avisarle manualmente esta vez.)")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def mes_siguiente():
    hoy = date.today()
    if hoy.month == 12:
        return hoy.year + 1, 1
    return hoy.year, hoy.month + 1


def main():
    ap = argparse.ArgumentParser(description="Motor de contenido de Calco")
    ap.add_argument("--mes", help="Mes a generar, formato AAAA-MM")
    ap.add_argument("--dry-run", action="store_true",
                    help="Muestra la grilla sin llamar a la API")
    ap.add_argument("--sin-aviso", action="store_true",
                    help="No enviar el mail de aviso a Nicolás")
    args = ap.parse_args()

    if args.mes:
        try:
            anio, mes = map(int, args.mes.split("-"))
        except ValueError:
            print("Formato de mes inválido. Usar AAAA-MM, por ejemplo 2026-09")
            sys.exit(1)
    else:
        anio, mes = mes_siguiente()

    marca = cargar_marca()
    hoy = date.today()
    desde_hoy = (anio == hoy.year and mes == hoy.month)

    print(f"Calendario de {NOMBRE_MES[mes]} {anio}")
    esq_ig, esq_li = armar_esqueleto(marca, anio, mes, desde_hoy)
    print(f"  Instagram + Facebook: {len(esq_ig)} publicaciones")
    print(f"  LinkedIn: {len(esq_li)} publicaciones")

    if args.dry_run:
        print("\nGrilla (sin generar copy):")
        for e in esq_ig + esq_li:
            v = f" / {e['vertical']}" if e.get("vertical") else ""
            print(f"  {e['fecha']} {e['red']:20} {e['pilar']}{v}")
        return

    cliente, modelo, proveedor = crear_cliente()
    print(f"  Proveedor: {proveedor} · modelo: {modelo}")

    ganchos_prev, temas_prev = ganchos_previos(anio, mes)
    if ganchos_prev:
        print(f"  {len(ganchos_prev)} ganchos previos cargados para no repetir")

    # Instagram/Facebook y LinkedIn comparten la lista de temas usados:
    # si el post de Instagram del día 7 habló del depósito legal, el de
    # LinkedIn del día 10 no debería volver sobre lo mismo.
    gen_ig = generar(cliente, modelo, marca, esq_ig, "instagram_facebook",
                      ganchos_prev, temas_prev)
    temas_tras_ig = temas_prev + [p.get("producto", "") for p in gen_ig if p.get("producto")]
    gen_li = generar(cliente, modelo, marca, esq_li, "linkedin",
                      ganchos_prev, temas_tras_ig)

    pubs = fusionar(esq_ig, gen_ig, marca) + fusionar(esq_li, gen_li, marca)

    if not pubs:
        print("No se generó ninguna publicación. Revisar el archivo de fallo.")
        sys.exit(1)

    pubs = marcar_duplicados(pubs, ganchos_mes_anterior=ganchos_prev)
    pubs = marcar_copy_vacio(pubs)

    destino = DIR_CONTENIDO / f"{anio}-{mes:02d}"
    destino.mkdir(parents=True, exist_ok=True)

    with open(destino / "calendario.json", "w", encoding="utf-8") as f:
        json.dump(
            {"anio": anio, "mes": mes, "publicaciones": pubs},
            f, ensure_ascii=False, indent=2
        )
    escribir_markdown(pubs, anio, mes, destino / "calendario.md")
    escribir_lista_fotos(pubs, anio, mes, destino / "lista-de-fotos.md")

    print(f"\nListo. {len(pubs)} publicaciones en {destino}/")
    print("  calendario.md      para copiar y pegar")
    print("  calendario.json    para el publicador automático")
    print("  lista-de-fotos.md  para Nicolás")

    if not args.sin_aviso:
        pubs_ig = [p for p in pubs if p["red"] == "instagram_facebook"]
        avisar_a_nicolas(anio, mes, pubs_ig)


if __name__ == "__main__":
    main()
