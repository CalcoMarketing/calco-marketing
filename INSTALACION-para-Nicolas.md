# Instalación de datos estructurados y llms.txt
### Calco Industria Gráfica · para Nicolás

Dos archivos, dos pasos. Ninguno de los dos requiere tocar código de la web,
solo subir archivos por FTP o por el administrador de archivos del hosting.

---

## 1. Mu-plugin de WordPress: `calco-datos-estructurados.php`

**Qué hace:** agrega datos estructurados (JSON-LD) a cada página del sitio,
para que Google y los buscadores de IA entiendan mejor qué es Calco, qué
productos ofrece y cómo contactar. Detecta si Yoast o Rank Math ya están
instalados y no duplica nada de lo que esos plugins generan.

**Dónde va:** `wp-content/mu-plugins/calco-datos-estructurados.php`

**Pasos:**

1. Entrar por FTP o por el administrador de archivos del hosting (cPanel,
   Plesk, o el que use el hosting de calco.uy)
2. Ir a `wp-content/`
3. Si la carpeta `mu-plugins` **no existe**, crearla ahí mismo (mu-plugins
   se activa solo, no aparece en el listado de plugins de WordPress y no
   hace falta activarlo a mano — por eso se usa para esto)
4. Subir `calco-datos-estructurados.php` dentro de esa carpeta
5. Listo. No hay que activar nada en el panel de WordPress.

**Antes de dar por terminado**, revisar dos datos dentro del archivo que
convienen confirmarse (están marcados con comentarios `CONFIRMAR` cerca del
principio del archivo):
- El **código postal** (hoy dice `15005`, pero en la bitácora original quedó
  pendiente confirmar si es `15005` o `15002`)
- El **teléfono** y la **dirección**, por si cambiaron desde julio de 2026

**Verificación (5 minutos):**

1. Ir a [Google Rich Results Test](https://search.google.com/test/rich-results)
2. Pegar la URL de calco.uy y de al menos una página de producto
3. Confirmar que aparece el bloque de **Organization / LocalBusiness** sin
   errores
4. En la página de un producto, confirmar que aparece **Service** (no
   "Product") en los datos detectados — si en algún momento vuelve a
   aparecer "Product" sin oferta, avisar a Marketing: es el bug que ya se
   corrigió una vez

⚠️ **Nota importante sobre las FAQ:** el plugin también agrega preguntas
frecuentes (FAQPage) en la home y en las categorías de producto. Ese
marcado **no genera un resultado enriquecido en Google** — Google
discontinuó esa función para todos los sitios el 7 de mayo de 2026. Sigue
siendo información útil para el usuario y potencialmente para los
buscadores de IA, pero no hay que esperar ver el típico desplegable de
preguntas en los resultados de búsqueda de Google.

**Antes de que se indexe:** las preguntas y respuestas del archivo son
afirmaciones públicas y verificables sobre la empresa (depósito legal,
ubicación, horarios, qué se produce). Conviene que alguien de Marketing las
lea una vez antes de la primera indexación, por si algún dato cambió.

---

## 2. Archivo `llms.txt`

**Qué hace:** es el archivo que leen ChatGPT, Perplexity, Gemini y otros
asistentes de IA para entender rápido de qué trata el sitio, sin tener que
rastrear todas las páginas. Incluye la nota de desambiguación frente a
Calco Impresos y Calco Sport Adhesivos.

**Dónde va:** en la **raíz** del sitio, junto a donde vive `robots.txt`.

**Pasos:**

1. Por FTP o administrador de archivos, ir a la carpeta raíz del sitio
   (la misma donde está `wp-config.php`)
2. Subir el archivo `llms.txt` tal cual, sin cambiarle el nombre
3. Verificar que quedó accesible entrando en el navegador a
   `https://calco.uy/llms.txt` — tiene que mostrar el archivo como texto
   plano, no un error 404

**Si el hosting no permite subir archivos a la raíz** (pasa en algunos
hostings compartidos con WordPress), el mu-plugin del paso 1 ya tiene una
función de respaldo (`ruta_llms_txt()`) que sirve el contenido desde
`/llms.txt` igual, sin necesitar acceso a la raíz — pero solo funciona si
no existe ya un archivo físico con ese nombre, así que primero intentar
siempre subirlo directo.

---

## Orden recomendado

1. Mu-plugin primero (paso 1) — no depende de nada
2. `llms.txt` después (paso 2) — independiente, pero conviene hacerlo en la
   misma sesión para no olvidarlo
3. Avisar a Marketing cuando ambos estén verificados, para tildar la tarea
   en `memoria.md`

**Tiempo estimado total:** 15 a 20 minutos, la mayoría esperando que
Google Rich Results Test procese la verificación.
