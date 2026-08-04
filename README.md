===============================================================================
CALCO INDUSTRIA GRAFICA - BITACORA DE MARKETING DIGITAL
Sesion 1 - Auditoria e infraestructura
Fecha: 31 de julio de 2026
===============================================================================

Documento de referencia interno. Contiene todos los identificadores, decisiones
estrategicas y tareas pendientes del proyecto. Guardar en el proyecto y
actualizar en cada sesion.

NO contiene contrasenas, tokens ni numeros de tarjeta. Esos datos nunca se
guardan en texto plano: van en la boveda de secretos de GitHub o en el gestor
de contrasenas de la empresa.


===============================================================================
1. DATOS MAESTROS DE LA EMPRESA
===============================================================================

Nombre comercial:      Calco Industria Grafica
Razon social:          CORTES CALOCA GERMAN
RUT:                   110241890016
En actividad desde:    2005
Direccion:             Ludwig Van Beethoven, Manzana 8 Solar 3
                       San Jose de Carrasco, Ciudad de la Costa
                       Canelones, Uruguay
Codigo postal:         15005 o 15002 -> PENDIENTE DE CONFIRMAR
Coordenadas:           -34.8315019, -56.0018320
Horario:               Lunes a viernes, 09:00 a 17:00. Fines de semana cerrado.
Telefono / WhatsApp:   093944783  (internacional: +59893944783)
Email general:         info@calco.uy
Email de marketing:    marketing@calco.uy
Sitio web:             https://calco.uy
Zona de servicio:      todo Uruguay


===============================================================================
2. IDENTIFICADORES TECNICOS
===============================================================================

META / FACEBOOK / INSTAGRAM
---------------------------
Portafolio empresarial A "Calco Industria Grafica" (con acento)
  ID:                  100736872634380
  Creado por:          German Cortes, 25 abril 2022
  Contiene:            Pagina de Facebook, Instagram, Pixel, cuenta publicitaria
  Verificacion:        SIN VERIFICAR
  2FA:                 en "Nadie" -> PENDIENTE cambiar a "Todos"

Portafolio empresarial B "Calco Industria Grafica" (sin acento)
  ID:                  915231621483370
  Creado por:          Juan Echizarto, 13 abril 2026
  Contiene:            WhatsApp Business API
  Verificacion:        VERIFICADA (17 julio 2026)
  2FA:                 en "Todos"

Pagina de Facebook:    Calco Industria Grafica
  ID:                  115509231136655
  URL:                 facebook.com/GraficaCalco
  Seguidores:          322
  Resenas:             0  -> oportunidad sin explotar

Pagina duplicada:      "CALCO" (Solar 4) - 131 seguidores
                       No borrar. Candidata a fusion. Backlog.

Instagram:             @calco.uy
  Seguidores:          2.664
  Mail asociado:       marketing@calco.uy
  Contrasena:          cambiada el 31/07/2026

Cuenta publicitaria:   Calco Industria Grafica
  ID:                  act_3265458220444226
  Moneda:              USD
  Zona horaria:        America/Montevideo
  Tarjeta:             Visa terminada en 0040
  Umbral de cobro:     USD 400 o dia 22 de cada mes
  Tope diario de Meta: USD 248 (limite de confianza, no propio)
  Historial:           15 campanas, todas desactivadas
  Gasto ultimos 60 d:  cero

Pixel / Conjunto de datos: "Pixel y API de conversiones WEB"
  ID:                  411002114762729
  Estado:              instalado en calco.uy via PixelYourSite
  API Conversiones:    YA CONFIGURADA (medicion server-side)
  Usuario del sistema: "Conversions API System User" ID 61555579386983

WhatsApp Business API
  WABA ID:             1702518370783837
  Estado:              Aprobada y verificada
  Moneda:              USD
  Zona horaria:        America/Montevideo
  Tarjeta:             Visa terminada en 0077
  Nota:                existe tambien una "Test WhatsApp Business Account"
                       (creada automaticamente, inofensiva)

GOOGLE
------
Google Ads
  ID de cliente:       347-799-5788
  Moneda:              USD
  Zona horaria:        (GMT-03:00) hora estandar de Uruguay
  Titular:             el jefe / dueno de la cuenta
  Acceso otorgado a:   marketing@calco.uy, nivel Administrador
  Etiqueta gtag:       NO INSTALADA en el sitio -> tarea pendiente critica

Google Business Profile
  Estado:              la ficha existe en Maps, sin reclamar ni optimizar
  Pendiente:           reclamar propiedad

REDES SOCIALES
--------------
Instagram:   https://www.instagram.com/calco.uy/
Facebook:    https://www.facebook.com/GraficaCalco
LinkedIn:    https://uy.linkedin.com/company/calco-industria-grafica  (198 seg.)
YouTube:     https://www.youtube.com/@calcoindustriagrafica687


===============================================================================
3. PERSONAS Y ROLES
===============================================================================

Juan Echizarto        marketing@calco.uy
                      Marketing. Acceso total al portafolio A y a la cuenta
                      publicitaria. Creador del portafolio B.
                      PENDIENTE: activarle el permiso de Finanzas.

Nicolas Astengo       nastengo@smartier.software
                      Empleado de Calco. Maneja redes sociales. Monto la API
                      de Conversiones del Pixel. Capacidad tecnica real.
                      Acceso total + Finanzas.
                      PENDIENTE: quitarle el permiso de Finanzas.
                      BACKLOG: migrar su mail a dominio @calco.uy.
                      Posible perfil duplicado: "Nico Nico"
                      nico_arg_esp@hotmail.com

German Cortes         germancortescaloca@gmail.com
                      Titular del RUT con el que la empresa esta verificada.
                      Creador del portafolio A. Inactivo.
                      NO ELIMINAR: su presencia respalda la verificacion.

El jefe               Dueno de la cuenta de Google Ads y de la tarjeta.
                      Aprueba el presupuesto mensual.

NUEVO REPARTO DE TAREAS ACORDADO
--------------------------------
Automatizado (sistema):
  - Redaccion de copys y calendario editorial
  - Diseno de piezas graficas
  - Programacion de publicaciones
  - Gestion de campanas y reportes

Nicolas (foco de mayor valor):
  1. Responder consultas de IG, Facebook y WhatsApp en menos de 2 horas
  2. Fotografiar y filmar la produccion (materia prima del contenido)
  3. Pedir resenas a clientes conformes
  4. Despliegue tecnico de lo que entrega Marketing

Juan / Marketing:
  - Estrategia, campanas, presupuesto, reportes al jefe


===============================================================================
4. AUDITORIA DEL SITIO calco.uy
===============================================================================

Plataforma:            WordPress + Elementor 4.1.2 + WooCommerce
Plugin SEO:            Yoast (detectado por metaetiquetas)
Modelo de conversion:  solicitud de presupuesto, NO venta directa con carrito
  -> la conversion a optimizar es el LEAD, no la compra

Instalado:             Pixel de Meta (PixelYourSite), LinkedIn Insight Tag
NO instalado:          etiqueta de Google (gtag) -> agujero critico

Activos reutilizables: 2 videos institucionales, catalogo con fotos de producto

ARQUITECTURA DEL CATALOGO
Por producto:
  /categoria-producto/estucheria-y-packaging/
  /categoria-producto/etiquetas-en-rollos-y-plana/
  /categoria-producto/puntos-de-venta-y-merchandising/
  /categoria-producto/gigantografias-senaletica-y-arquigrafia/
  /categoria-producto/papeleria-empresarial-y-comercial/
  /categoria-producto/libros-revistas-y-catalogos/
  /etiqueta-producto/urgente/

Por vertical:
  /categoria-producto/alimentos-y-bebidas/
  /categoria-producto/farmaceutica-y-cosmetica/
  /categoria-producto/quimicos-y-limpieza/
  /categoria-producto/congresos-y-eventos/
  /categoria-producto/gastronomia/
  /categoria-producto/tiendas-y-vestimenta/

Paginas clave:
  /shop/
  /solicitar-presupuesto/
  /por-que-elegir-calco/
  /sobre-nosotros/
  /contacto/

DIFERENCIALES IDENTIFICADOS (a explotar en toda la comunicacion)
  - Imprenta certificada
  - En actividad desde 2005 (mas de 20 anos)
  - Troquelado propio y departamento de desarrollo a medida
  - Linea de impresos urgentes (pagina construida y desaprovechada)
  - Deposito legal gratuito en Biblioteca Nacional para libros
  - Materiales aptos para contacto con alimentos
  - Se encargan del proceso completo, diseno incluido, con entrega a domicilio

DIAGNOSTICO DEL CONTENIDO ACTUAL
  Alcance organico: ~240 espectadores por publicacion sobre 322 seguidores
  en Facebook y 2.664 en Instagram (~7%).
  La estrategia de fondo (segmentar por vertical) es correcta.
  Falta volumen, formatos de video y distribucion pagada.

ERROR HISTORICO DETECTADO EN META
  Las 15 campanas anteriores se optimizaron para TRAFICO ("Clic en el enlace"),
  no para conversiones. Meta trajo gente que hace clic, no gente que cotiza.
  Correccion: campanas con objetivo Conversion sobre el evento Lead del Pixel.

COMPETIDORES CON NOMBRE PARECIDO (usar como negativas y desambiguar)
  - Calco Impresos (Mar Arabigo, Canelones)
  - Calco Sport Adhesivos (Montevideo)
  Nota: en Uruguay "calco" significa adhesivo o pegotin para autos.
  Nunca pujar por "calco" como palabra suelta.


===============================================================================
5. PRESUPUESTO Y REPARTO
===============================================================================

Presupuesto mensual total:   USD 500  (rango aprobado: USD 300 - 800)

  Google Ads - Busqueda      USD 325  (65%)
    C1 Productos Core        USD 6,50/dia   (~197/mes)
    C2 Urgentes              USD 2,70/dia   (~82/mes)
    C3 Marca defensiva       USD 1,50/dia   (~46/mes)

  Meta - Instagram+Facebook  USD 150  (30%)
    Retargeting sobre Pixel + prospeccion por verticales
    + click-to-WhatsApp

  Reserva de testeo          USD 25   (5%)

  LinkedIn pago              USD 0
    Decision: el CPC minimo de LinkedIn (USD 5-9) consume el presupuesto
    en dias. Se trabaja 100% organico.

PROYECCION HONESTA
  Mes 1 (calibracion):  10 - 25 presupuestos, costo por lead USD 13-30
  Mes 3 (optimizado):   25 - 60 presupuestos, costo por lead USD 6-13

  La variable que mas mueve estos numeros no es la publicidad: es el tiempo
  de respuesta. Con 25 presupuestos y 30% de cierre son 7-8 trabajos nuevos
  por mes. Si la respuesta demora 2 dias, ese 30% se cae a la mitad.


===============================================================================
6. DECISIONES ESTRATEGICAS TOMADAS
===============================================================================

1. La "casa" es el portafolio A, no el B.
   Aunque B tiene la verificacion, A tiene la pagina, el Instagram y limite
   de 5 cuentas publicitarias. La verificacion se puede volver a pedir; los
   activos con historial no se mueven facil.

2. No se fusionan los portafolios ni las WABA. No existe esa funcion en Meta.
   Se comparten activos via Socios (partner sharing): cero downtime, cero
   perdida de plantillas, cero reseteo de calidad del numero. Los scripts
   operan igual sobre activos compartidos.

3. No se crea cuenta publicitaria nueva en Meta ni cuenta nueva en Google Ads.
   Se usa el historial existente: el aprendizaje algoritmico acumulado es un
   activo. Cuentas duplicadas fragmentan datos y Google las penaliza.

4. Nunca usar "Promocionar publicacion" ni "Impulsar". No permite segmentar
   por industria, ni excluir clientes actuales, ni optimizar a conversion.
   Todo se construye como campanas reales en el Administrador de anuncios.

5. Fase 1 de Google Ads deja afuera Papeleria, Editorial y Merchandising.
   Con USD 325/mes, repartir entre 7 grupos impide que alguno junte datos
   suficientes para aprender. Entran en Fase 2.

6. Sin Display ni Performance Max en Fase 1. Con presupuesto chico se comen
   la inversion en impresiones basura.

7. Puja inicial: "Maximizar clics" con limite de CPC USD 0,45. A las 3 semanas,
   con 15-30 conversiones, migrar a "Maximizar conversiones". Arrancar en
   automatico sin datos hace que Google gaste rapido y mal.

8. Anuncios programados lunes a viernes 08:00-18:00. Cerrados fin de semana:
   pagar clics cuando nadie responde es tirar plata.

9. Campana de marca defensiva obligatoria por la existencia de Calco Impresos
   y Calco Sport Adhesivos. Clics a USD 0,05-0,15, el mejor retorno de la cuenta.

10. Los productos en datos estructurados van SIN precio declarado. El modelo
    es por presupuesto. Se declara "produccion a pedido" y se apunta a
    /solicitar-presupuesto/. Mas honesto y sin riesgo de sancion.

11. Las credenciales nunca se pegan en el chat. Van a GitHub Secrets o al
    gestor de contrasenas de la empresa. Las tarjetas las carga el titular
    directamente en Meta y Google.

12. Nunca mas contrasenas compartidas. Cada persona entra con su propio perfil
    y sus propios permisos.


===============================================================================
7. ENTREGABLES PRODUCIDOS EN ESTA SESION
===============================================================================

calco-google-ads-plan.md
  Plan completo: 3 campanas, 4 grupos de anuncios, keywords con concordancia
  definida, mas de 40 titulos y descripciones redactados, 80+ palabras clave
  negativas, extensiones, proyecciones y calendario de optimizacion.

calco-datos-estructurados.php
  Mu-plugin de WordPress. Inyecta JSON-LD: LocalBusiness/PrintShop con
  geolocalizacion, catalogo de servicios, esquema de Producto para WooCommerce
  y FAQPage por categoria. Detecta Yoast/Rank Math y no duplica.
  Instalar en wp-content/mu-plugins/

llms.txt
  Archivo que leen ChatGPT, Perplexity y Gemini para entender y citar a la
  empresa. Incluye nota de desambiguacion frente a Calco Impresos y Calco
  Sport Adhesivos. Subir a la raiz del sitio.

INSTALACION-para-Nicolas.md
  Instructivo paso a paso de los dos archivos anteriores, con verificacion
  en Google Rich Results Test.


===============================================================================
8. ESTADO DE TAREAS
===============================================================================

HECHO
  [x] Auditoria completa del sitio y de los activos digitales
  [x] Identificacion de los dos portafolios y de todos los IDs
  [x] Acceso confirmado a pagina, Instagram y Pixel
  [x] Segunda via de acceso al portafolio A (Juan Echizarto)
  [x] Confirmado: no hay fuga de presupuesto en Meta (0 gasto en 60 dias)
  [x] Cuenta publicitaria de Meta verificada: USD + Montevideo + tarjeta
  [x] Acceso de Administrador a Google Ads obtenido
  [x] Google Ads verificado: USD + GMT-03:00 Uruguay
  [x] Plan de campanas de Google Ads escrito
  [x] Paquete SEO/GEO escrito

PENDIENTE - BLOQUEA EL ARRANQUE
  [ ] Crear repositorio privado "calco-marketing" en GitHub
      github.com/signup con marketing@calco.uy
      Responsable: Nicolas o Juan
  [ ] Verificar si hay campanas activas gastando en Google Ads
  [ ] Verificar si existen conversiones configuradas en Google Ads
  [ ] Instalar la etiqueta de Google (gtag) en calco.uy
      Responsable: Nicolas
  [ ] Crear conversiones "Presupuesto_Enviado" y "Click_WhatsApp"
      Responsable: Nicolas

PENDIENTE - IMPORTANTE, NO BLOQUEA
  [ ] Instalar calco-datos-estructurados.php y llms.txt
      Responsable: Nicolas
  [ ] Revisar las preguntas frecuentes del plugin antes de que se indexen
      (son afirmaciones publicas verificables sobre la empresa)
  [ ] Activar permiso de Finanzas a Juan Echizarto
  [ ] Quitar permiso de Finanzas a Nicolas Astengo
  [ ] Poner limite de gasto de la cuenta de Meta en USD 600
  [ ] Activar 2FA en el portafolio A (pasar de "Nadie" a "Todos")
      Avisar antes a Nicolas: si no tiene 2FA propio, queda afuera
  [ ] Activar 2FA en la cuenta de Google de marketing@calco.uy
  [ ] Cruzar los dos portafolios como Socios
      En A: dar acceso a 915231621483370 (pagina, Instagram, Pixel)
      En B: asignar socio 100736872634380 sobre la WABA
  [ ] Reclamar y completar Google Business Profile
  [ ] Confirmar el codigo postal correcto (15005 o 15002)
  [ ] Confirmar que ambas tarjetas (Visa 0040 y Visa 0077) son de la empresa
  [ ] Responder los mensajes pendientes en Bandeja de entrada de Meta

BACKLOG - SIN URGENCIA
  [ ] Pedir verificacion de empresa para el portafolio A
      Antes: corregir razon social a CORTES CALOCA GERMAN y agregar el RUT
  [ ] Fusionar la pagina duplicada "CALCO" (131 seguidores)
  [ ] Migrar el mail de Nicolas a dominio @calco.uy
  [ ] Confirmar si "Nico Nico" es perfil duplicado y limpiarlo
  [ ] Campana automatizada de solicitud de resenas


===============================================================================
9. SISTEMA A CONSTRUIR (proxima sesion)
===============================================================================

1. content_engine.py
   Genera el calendario mensual completo: 20 posts para IG/FB + 8 para LinkedIn,
   via API de Anthropic, con reglas de marca definidas. Sin aprobacion manual.

2. render_creatives.py
   Sistema de plantillas HTML/CSS renderizadas a PNG con Playwright, usando
   las fotos de producto del propio sitio. Los 2 videos existentes se cortan
   en Reels verticales.

3. publisher.py
   Meta Graph API -> publica en Instagram Business y pagina de Facebook.
   Corre con GitHub Actions (gratis, cron incluido).
   RIESGO CONOCIDO: la publicacion automatica en Instagram puede requerir
   revision de app por parte de Meta, tramite de 1 a 2 semanas.
   PLAN B ya definido: carga en bloque en el Planificador de Meta Business
   Suite. Mismo contenido, 10 minutos semanales de Nicolas en vez de cero.

4. google_ads_scripts/
   Google Ads Scripts nativos (no requieren developer token ni servidor):
   - Diario: revisar terminos de busqueda y sumar negativas nuevas
   - Semanal: pausar keywords con mas de 30 clics y 0 conversiones
   - Semanal: redistribuir presupuesto hacia los grupos que convierten
   - Dia 21: migrar puja a "Maximizar conversiones"

5. seo_geo/
   Ya entregado en parte. Falta: 12 paginas de contenido orientadas a las
   preguntas que la gente le hace a la IA, escritas para ser citadas.

6. monthly_report.py
   Dia 1 de cada mes: cruza Meta Insights + Google Ads + GA4 y envia por mail
   una pagina con inversion, leads, costo por lead, ROI y alcance. Sin jerga.

7. click_to_whatsapp
   Campanas de Meta con destino WhatsApp aprovechando la WABA ya aprobada.
   En Uruguay el B2B se cierra por WhatsApp: costo por lead mas bajo que
   formulario.


===============================================================================
10. RIESGOS ABIERTOS
===============================================================================

1. El acceso al portafolio A depende en gran medida del login de Instagram,
   y ambas identidades (Instagram y perfil de Facebook) comparten el mismo
   mail marketing@calco.uy. Esa casilla es la llave maestra: si cae, cae todo.
   Mitigacion: 2FA en el mail + cruce de portafolios como socios.

2. La API de WhatsApp y la cuenta publicitaria dependen de dos tarjetas
   distintas. Si una vence o se rechaza, el servicio se corta sin aviso.

3. La cuenta de Google Ads pertenece al jefe. El acceso es delegado y
   revocable. Conviene, a futuro, que la titularidad quede a nombre de la
   empresa.

4. La verificacion de empresa vive solo en el portafolio B. Si se pierde
   el acceso a B, recuperar la verificacion son dias o semanas con
   documentacion legal.

5. Publicacion automatica en Instagram sujeta a revision de app por Meta.
   Plan B definido y sin impacto para el dueno.


===============================================================================
FIN DE LA BITACORA - Sesion 1 - 31/07/2026
Proxima sesion: entrega del sistema de automatizacion completo
Bloqueo actual: repositorio de GitHub
===============================================================================
