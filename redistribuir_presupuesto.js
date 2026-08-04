# Configurar la conversión "Presupuesto_Enviado"
### Calco Industria Gráfica · procedimiento completo

**Página de conversión confirmada:**
`https://calco.uy/gracias-por-tu-solicitud/?cthx=gpls&order_id=8392`

Esa URL es el punto de anclaje de toda la medición. Solo se llega ahí después de
enviar una solicitud de presupuesto, así que una simple **vista de página**
alcanza como disparador. No hace falta detectar clics ni envíos de formulario.

El parámetro `order_id` es un bonus: sirve para que Google no cuente dos veces
la misma solicitud si el usuario recarga la página de gracias.

---

## BLOQUE 1 · Crear la acción de conversión en Google Ads

**Quién:** Juan (o Nicolás) · **Tiempo:** 5 min · **Dónde:** `ads.google.com/aw/conversions`

1. Botón azul **"+ Crear acción de conversión"**
2. Elegir **"Sitio web"**
3. Escribir el dominio `calco.uy` → **"Analizar"**
4. Google va a ofrecer detectar conversiones automáticamente.
   **Ignorar eso** y buscar el link **"+ Añadir una acción de conversión manualmente"**
5. Configurar exactamente así:

| Campo | Valor |
|---|---|
| Categoría de objetivo | **Enviar formulario de cliente potencial** |
| Nombre de la conversión | `Presupuesto_Enviado` |
| Valor | *No usar un valor para esta acción de conversión* |
| Recuento | **Una** (¡importante, ver nota abajo!) |
| Ventana de conversión post-clic | **30 días** |
| Ventana de conversión post-interacción con la vista | 1 día |
| Incluir en "Conversiones" | **Sí** |
| Optimización de acciones | **Principal** |
| Modelo de atribución | Basado en datos (o Último clic si no está disponible) |

6. **"Listo"** → **"Guardar y continuar"**
7. En la pantalla de configuración de la etiqueta, elegir **"Usar Google Tag Manager"**
8. **Anotar los dos valores que muestra:**
   - **ID de conversión:** `AW-XXXXXXXXX`
   - **Etiqueta de conversión:** `xxxxxxxxxxxxxxxxx`

Esos dos datos van al Bloque 2. No son secretos, se pueden pasar por mensaje.

> **Por qué "Recuento: Una" y no "Todas":** con "Todas", si un cliente pide
> presupuesto de 3 productos en visitas separadas, cuenta 3 conversiones y
> Google cree que rinde el triple de lo que rinde. Con "Una", cuenta un
> cliente potencial por clic en el anuncio. Para generación de leads, "Una"
> es siempre lo correcto. Este es exactamente el tipo de detalle que infla
> los reportes y arruina la optimización.

---

## BLOQUE 2 · Configurar Google Tag Manager

**Quién:** Nicolás · **Tiempo:** 15 min · **Dónde:** `tagmanager.google.com`

### 2.1 · Antes de tocar nada: verificar el estado del contenedor

Arriba a la derecha, mirar si el botón **"Enviar"** está en azul con cambios
pendientes. **Si hay cambios sin publicar de otra persona, no publicar nada
todavía** — hay que revisar primero qué son. Publicar cambios ajenos a ciegas
puede romper lo que sí funciona.

### 2.2 · Crear la variable del order_id

*Variables* → **"Nueva"** (en Variables definidas por el usuario)

| Campo | Valor |
|---|---|
| Nombre | `URL - order_id` |
| Tipo | **URL** |
| Tipo de componente | **Consulta** |
| Clave de consulta | `order_id` |

Guardar.

### 2.3 · Crear el activador

*Activadores* → **"Nuevo"**

| Campo | Valor |
|---|---|
| Nombre | `PV - Gracias Presupuesto` |
| Tipo | **Vista de página** |
| Se activa en | **Algunas vistas de página** |
| Condición | `Page Path` · **contiene** · `/gracias-por-tu-solicitud/` |

Guardar.

> Si `Page Path` no aparece en la lista de variables, hay que habilitarla:
> *Variables* → **"Configurar"** en Variables integradas → tildar **Page Path**.

### 2.4 · Etiqueta 1: Conversion Linker (LA MÁS OLVIDADA)

*Etiquetas* → **"Nueva"**

| Campo | Valor |
|---|---|
| Nombre | `Google Ads - Conversion Linker` |
| Tipo de etiqueta | **Vinculador de conversiones** |
| Activación | **All Pages** / Todas las páginas |

Guardar.

> **Por qué importa tanto:** sin el Conversion Linker, Google Ads pierde el
> rastro entre el clic en el anuncio y la conversión posterior. La conversión
> ocurre, la etiqueta dispara, pero Ads no sabe qué anuncio la generó — y
> entonces no puede optimizar. Es la causa número uno de conversiones
> "fantasma" que aparecen sin atribución. Si falta esta etiqueta, todo lo
> demás es decorativo.

### 2.5 · Etiqueta 2: la conversión de Google Ads

*Etiquetas* → **"Nueva"**

| Campo | Valor |
|---|---|
| Nombre | `Google Ads - Presupuesto Enviado` |
| Tipo de etiqueta | **Seguimiento de conversiones de Google Ads** |
| ID de conversión | *(el `AW-XXXXXXXXX` del Bloque 1)* |
| Etiqueta de conversión | *(la etiqueta del Bloque 1)* |
| ID de transacción | `{{URL - order_id}}` |
| Activación | `PV - Gracias Presupuesto` |

Guardar.

### 2.6 · Probar ANTES de publicar

1. Botón **"Vista previa"** (arriba a la derecha)
2. Se abre el depurador y una ventana de calco.uy
3. **En esa ventana**, hacer una solicitud de presupuesto de prueba completa
4. Al llegar a `/gracias-por-tu-solicitud/`, en el panel del depurador verificar
   que aparezcan **disparadas** (Tags Fired):
   - `Google Ads - Conversion Linker`
   - `Google Ads - Presupuesto Enviado`
5. Si alguna quedó en "Tags Not Fired", revisar la condición del activador
   (el error más común: escribir la URL completa en vez de solo el path)

### 2.7 · Publicar

**"Enviar"** → Nombre de la versión: `Conversión Presupuesto - Google Ads` →
**"Publicar"**.

Sin este paso final, nada de lo anterior existe para el mundo real.

---

## BLOQUE 3 · Aprovechar la misma URL para Meta

**Quién:** Nicolás · **Tiempo:** 5 min · **Dónde:** WordPress → PixelYourSite

Esto resuelve el problema que detectamos en Meta: las 15 campañas históricas
optimizaban a tráfico porque **no había un evento de Lead configurado**. Ahora
sí lo podemos crear, con el mismo anclaje.

1. WordPress → **PixelYourSite** → pestaña **"Events"** (o "Eventos")
2. **"Add New Event"** / Añadir evento personalizado
3. Configurar:

| Campo | Valor |
|---|---|
| Nombre interno | `Presupuesto Solicitado` |
| Trigger / Condición | **URL contiene** `gracias-por-tu-solicitud` |
| Facebook Event | **Lead** |
| Parámetros | dejar los que vienen por defecto |

4. Guardar y publicar

**Verificar:** instalar la extensión de Chrome *Meta Pixel Helper*, hacer una
solicitud de prueba, y confirmar que en la página de gracias aparece el evento
**Lead** (no solo PageView).

Con esto el Pixel `411002114762729` empieza a acumular el evento Lead, que es
sobre el que van a optimizar las campañas nuevas de Meta.

---

## BLOQUE 4 · GA4 para reportería (opcional, no bloquea)

Solo cuando se recupere el acceso a la propiedad de GA4. No es urgente: la
conversión nativa del Bloque 1 ya mide lo que necesitamos.

1. GA4 → **Administrar** → **Eventos** → **"Crear evento"**
2. Nombre: `presupuesto_enviado`
3. Condición: `page_location` **contiene** `gracias-por-tu-solicitud`
4. Guardar → luego **Administrar** → **Eventos clave** → marcarlo como clave

---

## BLOQUE 5 · Limpieza en Google Ads (después de que el Bloque 1 mida)

**No hacer antes.** Si se degradan las señales actuales mientras la nueva
todavía no reporta datos, la campaña queda sin ninguna brújula y optimiza a
ciegas — peor que ahora.

Una vez que `Presupuesto_Enviado` registre sus primeras conversiones:

Pasar a **Secundaria** + *Incluido en objetivos de cuenta: No*

- `Local actions - Other engagements` (198 conv.)
- `Local actions - Directions` (74 conv.)
- `Local actions - Website visit` (13 conv.)
- `Clicks to call` (7 conv.)
- `Smart campaign map clicks to call`
- `Smart campaign ad clicks to call`
- `Calls from Smart Campaign Ads`

Se pueden degradar ya, sin esperar (son metas que el sitio no genera):

- `[afBc] Acción de compra de listados y anuncios de Google` (está Inactivo)
- `Carrito de la compra` (las dos versiones)
- `Tramitación de la compra` (las dos versiones)
- `www.calco.uy - GA4 (web) purchase`
- `Android installs (all other apps)` — no existe app de Calco

**Estado final buscado:** una sola acción en Principal — `Presupuesto_Enviado`.
Todo lo demás en Secundaria, visible en informes pero sin guiar la puja.

> **Nota sobre el carrito:** calco.uy **sí** tiene WooCommerce con `/cart/` y
> `/checkout/` activos. Las conversiones de compra están en cero, pero como la
> etiqueta tampoco funcionaba, no sabemos si es porque nadie compra o porque
> nadie lo medía. Se degradan por falta de datos, no por imposibilidad. Si
> resulta que el carrito vende, se reactivan y se evalúa una campaña de
> Shopping en Fase 2.

---

## Qué esperar después de publicar

- Las conversiones tardan **hasta 24 h** en aparecer en los informes de Ads
- La acción va a decir "Sin datos recientes" hasta la primera conversión real,
  y ahí pasa a **Activa**
- La campaña Smart entra en **re-aprendizaje de 3 a 7 días**. Es normal que el
  número de "conversiones" baje fuerte: dejan de contarse los 292 toques en la
  ficha de Maps y empiezan a contarse los presupuestos reales. **No es un
  empeoramiento: es el primer dato honesto que va a tener esta cuenta.**

## Orden de ejecución

1. Bloque 1 (Google Ads) — Juan
2. Bloque 2 (Tag Manager) — Nicolás
3. Bloque 3 (Meta) — Nicolás
4. Esperar 48 h y verificar que `Presupuesto_Enviado` registre datos
5. Bloque 5 (limpieza) — Juan
6. Recién entonces: cargar las campañas C1, C2 y C3 del plan
