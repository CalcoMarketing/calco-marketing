# Configurar la publicación automática (Instagram + Facebook)
### Calco Industria Gráfica · `publisher.py`

`publisher.py` ya está escrito y el workflow de GitHub Actions ya está
programado para correr todos los días a las 09:15 (Montevideo). Lo único
que falta es cargar 3 secretos en el repositorio y confirmar el modo de
acceso de la app de Meta. Esto lo hace **Nicolás**, una sola vez.

---

## Paso 0 · Confirmar el modo de acceso (2 minutos, antes que nada)

Como la app y la cuenta de Instagram de Calco van a pertenecer a la misma
organización, se puede publicar en **modo Standard Access, sin pasar por
App Review de Meta**. Confirmar esto en
[developers.facebook.com](https://developers.facebook.com) → la app de
Calco → **Instagram** → verificar que la cuenta de Instagram aparece
listada con un rol (admin/desarrollador) en esa misma app. Si es así, no
hace falta ningún trámite de revisión — se puede seguir directo al paso 1.

---

## Paso 1 · Conseguir un token de Página de larga duración

**Dónde:** [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer)

1. Seleccionar la app de Calco arriba a la derecha
2. **"Get Token" → "Get Page Access Token"**
3. Elegir la Página de Facebook de Calco (`GraficaCalco`)
4. Tildar estos permisos antes de generar:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `instagram_business_basic`
   - `instagram_business_content_publish`
5. Generar el token

**Este token dura 1-2 horas.** Para que dure ~60 días, hay que canjearlo:

```
GET https://graph.facebook.com/v21.0/oauth/access_token
    ?grant_type=fb_exchange_token
    &client_id=<APP_ID>
    &client_secret=<APP_SECRET>
    &fb_exchange_token=<EL_TOKEN_DE_CORTA_DURACION>
```

`APP_ID` y `APP_SECRET` están en la configuración de la app, en
developers.facebook.com. El resultado de este llamado es el token que
va al secreto `META_PAGE_ACCESS_TOKEN`.

⚠️ **Recordatorio:** este token vence cada ~60 días. Hay que repetir este
paso periódicamente — si `publisher.py` empieza a fallar de golpe con
error de autenticación, es casi siempre por esto.

---

## Paso 2 · Conseguir los dos IDs

**ID de la Página** (`META_PAGE_ID`): ya está en `memoria.md` —
`115509231136655`.

**ID de la cuenta de Instagram Business** (`META_IG_BUSINESS_ACCOUNT_ID`):

```
GET https://graph.facebook.com/v21.0/{META_PAGE_ID}
    ?fields=instagram_business_account
    &access_token={EL_TOKEN_DEL_PASO_1}
```

La respuesta trae un `id` adentro de `instagram_business_account` — ese
es el valor.

---

## Paso 3 · Cargar los 3 secretos en GitHub

1. En el repo → **Settings → Secrets and variables → Actions**
2. **New repository secret**, repetir 3 veces:

| Nombre exacto | Valor |
|---|---|
| `META_PAGE_ACCESS_TOKEN` | el token de larga duración del Paso 1 |
| `META_PAGE_ID` | `115509231136655` |
| `META_IG_BUSINESS_ACCOUNT_ID` | el que salió en el Paso 2 |

---

## Paso 4 · Probar sin publicar de verdad

Pestaña **Actions** → **Publicar contenido diario** → **Run workflow** →
tildar **dry_run: true** → **Run workflow**.

Revisar el log: tiene que decir qué publicaciones encontró para hoy y si
les falta el archivo de medio, sin publicar nada real. Si dice "No hay
publicaciones... pendientes para (fecha)", es normal si hoy no hay nada
programado en el calendario del mes — probar de nuevo forzando una fecha
que sí tenga contenido programado (campo `fecha` del `run workflow`).

---

## Paso 5 · Subir las fotos (tarea semanal de Nicolás, sin fecha de vencimiento)

Por cada publicación programada, subir el archivo a
`contenido/AAAA-MM/media/` con el **mismo id** que tiene en
`calendario.md` o `calendario.json` (por ejemplo `ig-2026-09-03.jpg`).
Extensiones aceptadas: `.jpg`, `.jpeg`, `.png` para fotos, `.mp4` o `.mov`
para reels.

Si el archivo no está subido el día que le toca publicarse, el script no
falla ni se rompe: la salta, avisa en el log, y la publica al día
siguiente en cuanto encuentre el archivo — aunque la fecha original ya
haya pasado.

---

## Qué NO automatiza esto

- **LinkedIn sigue siendo manual**, tal como se decidió: se publica a mano
  desde la página de empresa, martes y jueves. El script ni lo intenta.
- **No genera las imágenes.** `render_creatives.py` (plantillas → PNG)
  todavía no está escrito — hoy las fotos las saca Nicolás con el celular,
  siguiendo `lista-de-fotos.md`.
