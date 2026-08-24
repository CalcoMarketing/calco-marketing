# Conectar las fotos de Drive con la publicación automática
### Calco Industria Gráfica

Con esto, Nicolás sube la foto a una carpeta de Drive desde el celular y
el sistema la publica solo. No hay que tocar GitHub.

**Esto se configura una sola vez.** Después funciona sin intervención.

**Quién lo hace:** alguien con acceso a Google Cloud Console con la
cuenta de Google de Calco. Toma unos 15 minutos.

---

## Qué se está armando

El sistema corre en GitHub, así que necesita una forma de leer la carpeta
de Drive por su cuenta, sin que nadie inicie sesión cada vez. Eso se
resuelve con una **cuenta de servicio**: un usuario de Google que no es
una persona, tiene su propio email, y al que se le comparte la carpeta
como se le compartiría a un compañero de trabajo.

La credencial de esa cuenta se guarda en los secretos del repositorio,
nunca en el código.

---

## Paso 1 · Crear el proyecto en Google Cloud

1. Entrar a [console.cloud.google.com](https://console.cloud.google.com)
   con la cuenta de Google de Calco
2. Arriba, en el selector de proyectos → **"Proyecto nuevo"**
3. Nombre: `calco-marketing` → **Crear**
4. Esperar a que termine y asegurarse de que quede seleccionado ese
   proyecto arriba

---

## Paso 2 · Habilitar la API de Drive

1. Menú (☰) → **APIs y servicios** → **Biblioteca**
2. Buscar **"Google Drive API"**
3. Clic en el resultado → botón **"Habilitar"**

Sin este paso, la cuenta de servicio existe pero no puede leer nada.

---

## Paso 3 · Crear la cuenta de servicio

1. Menú (☰) → **IAM y administración** → **Cuentas de servicio**
2. Arriba: **"+ Crear cuenta de servicio"**
3. Completar:
   - Nombre: `publicador-calco`
   - ID: se completa solo
   - Descripción: `Lee las fotos de Drive para publicar en redes`
4. **Crear y continuar**
5. En "Otorgar acceso a este proyecto": **saltear**, no hace falta ningún
   rol. La cuenta no necesita permisos sobre el proyecto, solo sobre la
   carpeta de Drive, y eso se da compartiendo la carpeta.
6. **Listo**

**Anotá el email que quedó creado.** Se ve así:

    publicador-calco@calco-marketing.iam.gserviceaccount.com

Lo vas a necesitar en el paso 5.

---

## Paso 4 · Descargar la credencial

1. En la lista de cuentas de servicio, clic en la que acabás de crear
2. Pestaña **"Claves"**
3. **"Agregar clave"** → **"Crear clave nueva"**
4. Tipo: **JSON** → **Crear**
5. Se descarga un archivo `.json` automáticamente

⚠️ **Ese archivo es una credencial.** Cualquiera que lo tenga puede leer
lo que esa cuenta pueda leer. No lo mandes por WhatsApp ni lo subas a
Drive. Se usa una vez, en el paso 6, y después se borra de la carpeta de
descargas.

---

## Paso 5 · Compartir la carpeta con la cuenta de servicio

Este es el paso que se olvida y hace que después no funcione.

1. Abrir la carpeta **"FOTOS PARA PUBLICAR"** en Drive
   (está dentro de `04_REDES SOCIALES`)
2. Botón **"Compartir"**
3. Pegar el email de la cuenta de servicio del paso 3
4. Permiso: **Lector** (alcanza; no necesita poder editar)
5. **Enviar**

Google puede avisar que ese email no tiene cuenta de Gmail. Es normal,
compartila igual.

---

## Paso 6 · Cargar la credencial en GitHub

1. Abrir el archivo `.json` descargado con el Bloc de notas
2. **Copiar todo el contenido**, desde la primera llave `{` hasta la
   última `}`
3. En GitHub: repo → **Settings** → **Secrets and variables** →
   **Actions**
4. **New repository secret**
   - Nombre: `GOOGLE_CREDENTIALS`
   - Valor: pegar todo el JSON
5. **Add secret**
6. Borrar el archivo `.json` de la carpeta de descargas

---

## Paso 7 · Probar

1. Subí una foto cualquiera a la carpeta de Drive, con nombre
   `ig-2026-09-04.jpg`
2. En GitHub: **Actions** → **"Publicar contenido diario"** →
   **Run workflow**
   - fecha: `2026-09-04`
   - tildar **"Simular sin publicar de verdad"**
3. Mirar el log del paso "Publicar"

**Tiene que decir:** `Foto tomada de Drive: ig-2026-09-04.jpg`

Si dice que no hay foto, revisá en este orden:
- El nombre del archivo, letra por letra
- Que la carpeta esté compartida con el email de la cuenta de servicio
- Que la API de Drive esté habilitada (paso 2)

---

## Cómo queda el flujo, ya funcionando

1. Marketing genera el calendario del mes (automático, día 25)
2. Nicolás recibe la lista de fotos a sacar
3. Nicolás saca las fotos y las sube a **FOTOS PARA PUBLICAR** con el
   nombre del post
4. El sistema publica solo, en la fecha que corresponde

Si una foto no está el día que toca, el sistema puede usar una de
catálogo como respaldo, o saltear la publicación. En cuanto la foto se
suba, la retoma.

---

## Si esto no se configura

No pasa nada grave: el sistema sigue funcionando como hasta ahora,
buscando las fotos en el repositorio de GitHub. Simplemente es más
incómodo para quien saca las fotos.
