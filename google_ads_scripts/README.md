# google_ads_scripts/

Cuatro scripts nativos de Google Ads (Google Ads Scripts). Corren dentro de la
propia cuenta de Google Ads, con su propio cron. **No requieren developer
token, servidor externo, ni GitHub Actions** — por eso están separados del
resto del sistema.

## Instalación (repetir para cada uno de los 4 archivos)

1. Entrar a Google Ads con `marketing@calco.uy`
2. Menú de la izquierda → **Herramientas y configuración** (ícono de llave)
3. Columna **"Acciones masivas"** → **Scripts**
4. Botón azul **"+"**
5. Borrar el contenido de ejemplo y pegar el archivo completo
6. Nombrar el script igual que el archivo (sin `.js`), por ejemplo:
   `revisar_terminos_busqueda`
7. Botón **"Vista previa"** (Preview) — corre en modo simulación, no aplica
   cambios reales. Revisar el log antes de continuar.
8. Si el log se ve razonable, **"Autorizar"**
9. Programar la ejecución (botón de reloj, "Frequency"):

| Script | Frecuencia | Hora sugerida |
|---|---|---|
| `revisar_terminos_busqueda.js` | Diario | 07:00 |
| `pausar_keywords_sin_conversion.js` | Semanal, lunes | 06:00 |
| `redistribuir_presupuesto.js` | Semanal, lunes | 06:30 |
| `migrar_puja_dia_21.js` | Diario | 07:30 |

Todas las horas en **America/Montevideo (GMT-03:00)**, la misma zona
horaria de la cuenta.

## Orden de instalación recomendado

Instalar en este orden, porque cada uno depende de que las campañas del
`calco-google-ads-plan.md` ya estén cargadas:

1. Cargar las 3 campañas del plan (C1, C2, C3) — paso manual, no es un script
2. `revisar_terminos_busqueda.js` — puede correr desde el día 1
3. `pausar_keywords_sin_conversion.js` — no hace nada hasta que alguna keyword
   llegue a 30 clics, así que no hay apuro en instalarlo antes del día 1
4. `redistribuir_presupuesto.js` — no actúa hasta que 2+ campañas tengan
   15+ conversiones cada una. Instalarlo desde el principio no hace daño.
5. `migrar_puja_dia_21.js` — instalarlo desde el día 1 para que quede
   vigilando; no va a migrar nada hasta el día 21 como mínimo.

## Salvaguardas ya incluidas en el código

- **`revisar_terminos_busqueda.js`** solo agrega negativas que coinciden con
  las categorías ya validadas en la auditoría (adhesivos, DIY, empleo,
  equipos, otros países, servicios que no ofrecemos). Términos ambiguos con
  clics y sin conversión quedan listados en el log para revisión humana, no
  se tocan solos.
- **`pausar_keywords_sin_conversion.js`** nunca toca la campaña de marca
  defensiva (`C3 - Marca defensiva`) y nunca deja un grupo de anuncios sin
  ninguna keyword activa. Pausa, no elimina — todo reversible.
- **`redistribuir_presupuesto.js`** nunca mueve más del 15% del presupuesto
  de una campaña por corrida, respeta pisos mínimos por campaña, exige 15+
  conversiones acumuladas antes de actuar, y nunca deja que la suma total
  supere el techo mensual de USD 325.
- **`migrar_puja_dia_21.js`** exige las dos condiciones (21+ días Y 15+
  conversiones) antes de migrar, y migra campaña por campaña según cuándo
  cada una las cumple — no todas el mismo día calendario.

## Si algo falla

Los cuatro scripts escriben su actividad en el **Log** de Scripts (visible
desde la misma pantalla donde se pegó el código) y los que aplican cambios
importantes mandan un mail a `marketing@calco.uy`. Si un script no corre,
Google Ads también manda un aviso automático por mail a la cuenta con el
error.

Si el cambio de estrategia de puja en `migrar_puja_dia_21.js` falla por un
cambio en la API de Scripts, el log lo va a decir explícitamente y el cambio
se hace manualmente en 2 clics: Campaña → Configuración → Puja → "Maximizar
conversiones".
