# memoria.md
## Calco Industria Gráfica · Marketing Digital

> **Leer este archivo primero, en cada sesión nueva.** Es el contexto operativo del
> proyecto: quién es quién, qué está decidido, qué está pendiente y cuál es el
> próximo paso. El detalle histórico completo vive en `calco-bitacora-sesion-1.txt`.

**Última actualización:** 31 de julio de 2026 (Sesión 1)
**Estado general:** infraestructura resuelta · esperando GitHub para automatizar

---

## 1. El encargo

Actuar como **CMO autónomo y agencia de marketing digital integral** de Calco
Industria Gráfica. Posicionar la empresa en redes sociales (Instagram, Facebook,
LinkedIn), en Google y en buscadores de IA (ChatGPT, Perplexity, Gemini).
Ejecutar de forma autónoma, con código y automatización.

**Objetivo comercial:** generar solicitudes de presupuesto. El sitio no vende con
carrito: la conversión es el **lead**, no la compra.

---

## 2. Reglas de trabajo (acordadas, no se renegocian)

1. **Cero fricción.** No pedirle al cliente que redacte textos, elija colores ni
   apruebe copys. Las decisiones creativas y estratégicas las toma el sistema.
2. **Lo único que se le pregunta:** el presupuesto mensual de inversión.
3. **Instrucciones para principiante absoluto.** Si hace falta que entre a una
   plataforma, se le dice literalmente qué botón apretar.
4. **Reportes una vez al mes**, con métricas comprensibles: inversión, leads,
   costo por lead, ROI, alcance. Sin jerga.
5. **Las credenciales nunca se pegan en el chat.** Van a GitHub Secrets o al
   gestor de contraseñas de la empresa. Las tarjetas las carga el titular
   directamente en Meta y Google.
6. **Delegar lo técnico a Nicolás, no al dueño.** Tiene capacidad real: montó la
   API de Conversiones del Pixel.

---

## 3. Quién es quién

| Persona | Rol | Notas |
|---|---|---|
| **Juan Echizarto** (`marketing@calco.uy`) | Interlocutor principal. Marketing. | Acceso total al portafolio A. Creó el portafolio B. |
| **Nicolás Astengo** (`nastengo@smartier.software`) | Empleado. Redes + despliegue técnico. | Montó la API de Conversiones. Es el implementador. |
| **German Cortes** (`germancortescaloca@gmail.com`) | Titular del RUT. Inactivo. | **No eliminar:** respalda la verificación. |
| **El jefe** | Dueño de la cuenta de Google Ads y de la tarjeta. | Aprueba el presupuesto. |

---

## 4. La empresa en 10 líneas

- Imprenta e industria gráfica, en actividad **desde 2005**
- San José de Carrasco, Ciudad de la Costa, **Canelones**. Atiende **todo Uruguay**
- Lunes a viernes 09:00–17:00. **Cerrado fines de semana**
- WhatsApp/teléfono **093944783** · `info@calco.uy` · https://calco.uy
- **Produce:** packaging y estuchería con troquelado propio, etiquetas en rollo y
  planas, papelería empresarial, libros y revistas, merchandising,
  gigantografías y señalética. Línea de **impresos urgentes**
- **Verticales:** alimentos y bebidas, farmacia y cosmética, químicos y limpieza,
  gastronomía, tiendas y vestimenta, congresos y eventos
- **Diferenciales a explotar:** imprenta certificada · 20+ años · troquelado
  propio y desarrollo a medida · depósito legal gratis en Biblioteca Nacional ·
  materiales aptos para alimentos · proceso completo con entrega a domicilio
- **Ojo:** en Uruguay "calco" significa adhesivo para autos. Existen **Calco
  Impresos** y **Calco Sport Adhesivos**, que no son la empresa. Nunca pujar por
  "calco" como palabra suelta; siempre desambiguar

---

## 5. Identificadores (referencia rápida)

| Activo | ID |
|---|---|
| Portafolio A (página, IG, Pixel) — *la casa* | `100736872634380` |
| Portafolio B (WhatsApp API, verificado) | `915231621483370` |
| Página de Facebook | `115509231136655` |
| Cuenta publicitaria Meta · USD · Montevideo | `act_3265458220444226` |
| Pixel + API de Conversiones | `411002114762729` |
| Usuario del sistema (Conversions API) | `61555579386983` |
| WhatsApp Business API (aprobada) | `1702518370783837` |
| Google Ads · USD · GMT-03:00 Uruguay | `347-799-5788` |

Instagram **@calco.uy** (2.664 seg.) · Facebook (322 seg.) · LinkedIn (198 seg.)
· YouTube `@calcoindustriagrafica687`

---

## 6. Presupuesto

**USD 500/mes** (rango aprobado: 300–800)

| Canal | Monto | Nota |
|---|---|---|
| Google Ads – Búsqueda | USD 325 (65%) | 3 campañas: Core, Urgentes, Marca |
| Meta – IG + Facebook | USD 150 (30%) | Retargeting + verticales + click-to-WhatsApp |
| Reserva de testeo | USD 25 (5%) | |
| LinkedIn pago | USD 0 | CPC mínimo 5–9 USD: inviable. Solo orgánico |

**Proyección:** mes 1 → 10-25 presupuestos (USD 13-30 c/u). Mes 3 → 25-60
presupuestos (USD 6-13 c/u). *La variable que más mueve estos números no es la
publicidad: es el tiempo de respuesta a la consulta.*

---

## 7. Decisiones cerradas (no reabrir sin motivo nuevo)

1. La casa es el **portafolio A**, no el B. Los activos con historial no se mueven.
2. **No se fusionan** portafolios ni WABA: esa función no existe en Meta. Se
   comparten activos vía **Socios** (partner sharing). Los scripts funcionan igual.
3. **No se crean cuentas nuevas** en Meta ni en Google Ads. El historial es un activo.
4. **Nunca "Promocionar publicación"** ni "Impulsar". Solo campañas reales.
5. **Fase 1 de Google Ads deja afuera** Papelería, Editorial y Merchandising.
   Con USD 325 repartir en 7 grupos impide que alguno aprenda.
6. **Sin Display ni Performance Max** en Fase 1.
7. Puja: **Maximizar clics con CPC máx USD 0,45** → a los 21 días, con 15-30
   conversiones, migrar a **Maximizar conversiones**.
8. Anuncios **lunes a viernes 08:00–18:00**.
9. **Campaña de marca defensiva obligatoria** por los dos homónimos.
10. Datos estructurados **sin precio declarado**: producción a pedido.
11. Meta se optimiza a **Conversión (evento Lead)**, nunca a Tráfico. Las 15
    campañas históricas fallaron justamente por eso.

---

## 8. Estado actual

**✅ Resuelto**
- Auditoría completa del sitio y de todos los activos digitales
- Portafolios, página, Instagram, Pixel y WABA identificados y bajo control
- Doble vía de acceso al portafolio A
- Meta: cuenta con historial, tarjeta, sin deuda, cero gasto en 60 días
- Google Ads: acceso de Administrador, USD, GMT-03:00 Uruguay
- Hallazgo favorable: **API de Conversiones server-side ya instalada**
- Entregados: plan de Google Ads, mu-plugin de datos estructurados, `llms.txt`,
  instructivo de instalación

**🔴 Bloquea el arranque**
- **Repositorio privado `calco-marketing` en GitHub** ← único bloqueo real
- Instalar la etiqueta de Google (gtag) en calco.uy
- Crear conversiones `Presupuesto_Enviado` y `Click_WhatsApp`
- Verificar si hay campañas activas o conversiones ya configuradas en Google Ads

**🟡 Importante, no bloquea**
- Instalar el mu-plugin y `llms.txt` · revisar las FAQ antes de que se indexen
- Permisos: dar Finanzas a Juan, quitarlas a Nicolás
- Límite de gasto de Meta en USD 600 · 2FA en portafolio A y en Google
- Cruzar los dos portafolios como Socios
- Reclamar Google Business Profile · confirmar código postal (15005 o 15002)
- Responder mensajes pendientes en Bandeja de entrada de Meta

**⚪ Backlog**
- Verificación de empresa para el portafolio A · fusionar página duplicada
  "CALCO" · migrar mail de Nicolás a `@calco.uy` · campaña de reseñas

---

## 9. Próxima entrega

Sistema de automatización completo, en cuanto exista el repositorio:

1. `content_engine.py` — calendario mensual: 20 posts IG/FB + 8 LinkedIn
2. `render_creatives.py` — plantillas HTML/CSS → PNG con Playwright
3. `publisher.py` — Meta Graph API vía GitHub Actions
4. `google_ads_scripts/` — optimización nativa, sin developer token
5. `seo_geo/` — 12 páginas escritas para ser citadas por IA
6. `monthly_report.py` — informe de una página al mail, día 1 de cada mes
7. `click_to_whatsapp` — campañas con destino WhatsApp

**Riesgo conocido:** la publicación automática en Instagram puede requerir
revisión de app por Meta (1–2 semanas). Plan B definido: carga en bloque en el
Planificador de Meta Business Suite. Mismo contenido, 10 min semanales de
Nicolás en vez de cero.

---

## 10. Archivos del proyecto

| Archivo | Qué es |
|---|---|
| `memoria.md` | **Este archivo.** Contexto operativo. Leer primero. |
| `calco-bitacora-sesion-1.txt` | Registro histórico detallado de la Sesión 1 |
| `calco-google-ads-plan.md` | Plan de campañas: keywords, copys, negativas |
| `calco-datos-estructurados.php` | Mu-plugin de WordPress (JSON-LD) |
| `llms.txt` | Archivo para buscadores de IA |
| `INSTALACION-para-Nicolas.md` | Instructivo de despliegue |

**Cómo mantener este archivo:** al cerrar cada sesión, actualizar la fecha, la
sección 8 (estado) y la 9 (próxima entrega). Las decisiones nuevas se agregan a
la sección 7. El detalle largo va a la bitácora, no acá: este archivo tiene que
poder leerse en dos minutos.
