<?php
/**
 * Plugin Name:  Calco – Datos Estructurados y GEO
 * Description:  Inyecta datos estructurados (Schema.org / JSON-LD) para posicionamiento en Google
 *               y en buscadores de IA (ChatGPT, Perplexity, Gemini). Detecta Yoast / Rank Math
 *               y no duplica lo que esos plugins ya emiten.
 * Version:      1.1.0
 * Author:       Departamento de Marketing – Calco Industria Gráfica
 *
 * INSTALACIÓN: subir este archivo a  wp-content/mu-plugins/
 * No requiere activación. Si la carpeta mu-plugins no existe, crearla.
 *
 * CHANGELOG
 * 1.1.0 (2026-08-19) — Corrección post-auditoría técnica:
 *   - producto(): @type "Product" sin offers/review/aggregateRating
 *     generaba error en Search Console. Cambiado a "Service", que no
 *     exige ninguno de esos tres campos y es más correcto para un
 *     modelo de "cotizar bajo presupuesto".
 *   - FAQPage: se mantiene el marcado (sigue siendo válido y puede
 *     ayudar a IA), pero AVISO: Google descontinuó por completo los
 *     rich results de FAQ en la Búsqueda el 7 de mayo de 2026. No va
 *     a generar snippet enriquecido en Google para ningún sitio.
 * 1.0.0 (2026-07-31) — Versión inicial.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class Calco_Datos_Estructurados {

	/* ---------------------------------------------------------------------
	 * DATOS DE LA EMPRESA
	 * Verificar estos valores antes de publicar. El código postal y el
	 * teléfono conviene confirmarlos contra la documentación oficial.
	 * ------------------------------------------------------------------ */
	const NOMBRE      = 'Calco Industria Gráfica';
	const SITIO       = 'https://calco.uy';
	const LOGO        = 'https://calco.uy/wp-content/uploads/2023/01/logo-calco.svg';
	const IMAGEN      = 'https://calco.uy/wp-content/uploads/2023/12/FONDOpantalla.jpg';
	const EMAIL       = 'info@calco.uy';
	const TELEFONO    = '+59893944783';
	const CALLE       = 'Ludwig Van Beethoven, Manzana 8 Solar 3';
	const LOCALIDAD   = 'San José de Carrasco';
	const DEPARTAMENTO = 'Canelones';
	const CODIGO_POSTAL = '15005'; // ← CONFIRMAR
	const PAIS        = 'UY';
	const LATITUD     = -34.8315019;
	const LONGITUD    = -56.0018320;
	const FUNDACION   = '2005';

	public static function init() {
		add_action( 'wp_head', array( __CLASS__, 'imprimir' ), 99 );
		add_action( 'init', array( __CLASS__, 'ruta_llms_txt' ) );
	}

	/* ------------------------------------------------------------------ */

	private static function otro_plugin_seo_activo() {
		return defined( 'WPSEO_VERSION' ) || defined( 'RANK_MATH_VERSION' ) || class_exists( 'RankMath' );
	}

	public static function imprimir() {
		$grafo = array();

		// LocalBusiness / PrintShop: siempre. Ningún plugin de SEO lo emite
		// con la especificidad de un negocio gráfico.
		$grafo[] = self::negocio();

		if ( function_exists( 'is_product' ) && is_product() ) {
			$producto = self::producto();
			if ( $producto ) {
				$grafo[] = $producto;
			}
		}

		if ( function_exists( 'is_product_category' ) && is_product_category() ) {
			$faq = self::faq_categoria();
			if ( $faq ) {
				$grafo[] = $faq;
			}
		}

		if ( is_front_page() ) {
			$faq = self::faq_general();
			if ( $faq ) {
				$grafo[] = $faq;
			}
		}

		if ( empty( $grafo ) ) {
			return;
		}

		$salida = array(
			'@context' => 'https://schema.org',
			'@graph'   => $grafo,
		);

		echo "\n<!-- Calco: datos estructurados -->\n";
		echo '<script type="application/ld+json">' . "\n";
		echo wp_json_encode( $salida, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT );
		echo "\n</script>\n";
	}

	/* ------------------------------------------------------------------
	 * NEGOCIO LOCAL
	 * ---------------------------------------------------------------- */
	private static function negocio() {
		return array(
			'@type'    => array( 'LocalBusiness', 'PrintShop', 'Organization' ),
			'@id'      => self::SITIO . '/#organizacion',
			'name'     => self::NOMBRE,
			'alternateName' => 'Calco',
			'url'      => self::SITIO,
			'logo'     => self::LOGO,
			'image'    => self::IMAGEN,
			'email'    => self::EMAIL,
			'telephone' => self::TELEFONO,
			'foundingDate' => self::FUNDACION,
			'description'  => 'Imprenta e industria gráfica en Uruguay. Producción de packaging y estuchería con troquelado propio, etiquetas en rollo y planas, papelería empresarial, libros y revistas, merchandising, gigantografías y señalética. Desarrollo a medida desde el diseño hasta la entrega.',
			'address'  => array(
				'@type'           => 'PostalAddress',
				'streetAddress'   => self::CALLE,
				'addressLocality' => self::LOCALIDAD,
				'addressRegion'   => self::DEPARTAMENTO,
				'postalCode'      => self::CODIGO_POSTAL,
				'addressCountry'  => self::PAIS,
			),
			'geo' => array(
				'@type'     => 'GeoCoordinates',
				'latitude'  => self::LATITUD,
				'longitude' => self::LONGITUD,
			),
			'areaServed' => array(
				'@type' => 'Country',
				'name'  => 'Uruguay',
			),
			'openingHoursSpecification' => array(
				array(
					'@type'     => 'OpeningHoursSpecification',
					'dayOfWeek' => array( 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday' ),
					'opens'     => '09:00',
					'closes'    => '17:00',
				),
			),
			'sameAs' => array(
				'https://www.instagram.com/calco.uy/',
				'https://www.facebook.com/GraficaCalco',
				'https://uy.linkedin.com/company/calco-industria-grafica',
				'https://www.youtube.com/@calcoindustriagrafica687',
			),
			'contactPoint' => array(
				array(
					'@type'             => 'ContactPoint',
					'contactType'       => 'Ventas y presupuestos',
					'telephone'         => self::TELEFONO,
					'email'             => self::EMAIL,
					'availableLanguage' => array( 'Spanish' ),
					'areaServed'        => 'UY',
				),
			),
			'hasOfferCatalog' => array(
				'@type'       => 'OfferCatalog',
				'name'        => 'Servicios de impresión',
				'itemListElement' => self::catalogo(),
			),
			'potentialAction' => array(
				'@type'  => 'Action',
				'name'   => 'Solicitar presupuesto',
				'target' => self::SITIO . '/solicitar-presupuesto/',
			),
		);
	}

	private static function catalogo() {
		$servicios = array(
			'Packaging y estuchería personalizada' => 'Estuches y cajas con desarrollo a medida y maquinaria de troquelado para cualquier cantidad.',
			'Etiquetas en rollo y planas'          => 'Etiquetas en bobina para botellas, latas y tarros, en diversos materiales, para aplicación manual o con etiquetadoras automáticas.',
			'Papelería empresarial y comercial'    => 'Cuadernos, blocs, carpetas, sobres y hojas membretadas.',
			'Libros, revistas y catálogos'         => 'Impresión editorial con distintos formatos, materiales y tipos de encuadernación.',
			'Merchandising y puntos de venta'      => 'Objetos de promoción y material para punto de venta.',
			'Gigantografías, señalética y arquigrafía' => 'Señalización y decoración de espacios interiores y exteriores.',
		);

		$salida = array();
		foreach ( $servicios as $nombre => $desc ) {
			$salida[] = array(
				'@type' => 'Offer',
				'itemOffered' => array(
					'@type'       => 'Service',
					'name'        => $nombre,
					'description' => $desc,
					'provider'    => array( '@id' => self::SITIO . '/#organizacion' ),
					'areaServed'  => array( '@type' => 'Country', 'name' => 'Uruguay' ),
				),
			);
		}
		return $salida;
	}

	/* ------------------------------------------------------------------
	 * PRODUCTO (WooCommerce, modelo por presupuesto)
	 *
	 * CORREGIDO 2026-08: se usaba @type "Product" sin "offers", "review" ni
	 * "aggregateRating". Google exige al menos uno de esos tres campos para
	 * validar un Product snippet; sin ellos, Search Console reporta el error
	 * "Either 'offers', 'review', or 'aggregateRating' should be specified".
	 * Como el modelo es "cotizar bajo presupuesto" (sin precio fijo), Product
	 * no es el tipo correcto: Google reserva Product/Offer para bienes con
	 * precio. Se usa "Service" en su lugar, que no exige ninguno de esos
	 * campos y describe mejor un trabajo de impresión a medida.
	 * ---------------------------------------------------------------- */
	private static function producto() {
		if ( ! function_exists( 'wc_get_product' ) ) {
			return null;
		}
		$p = wc_get_product( get_the_ID() );
		if ( ! $p ) {
			return null;
		}

		$imagen_id = $p->get_image_id();
		$imagen    = $imagen_id ? wp_get_attachment_image_url( $imagen_id, 'large' ) : self::IMAGEN;

		$categorias = wp_get_post_terms( $p->get_id(), 'product_cat', array( 'fields' => 'names' ) );

		$datos = array(
			'@type'       => 'Service',
			'@id'         => get_permalink( $p->get_id() ) . '#servicio',
			'name'        => $p->get_name(),
			'url'         => get_permalink( $p->get_id() ),
			'image'       => $imagen,
			'description' => wp_strip_all_tags( $p->get_short_description() ?: $p->get_description() ),
			'provider'    => array( '@id' => self::SITIO . '/#organizacion' ),
			'areaServed'  => array( '@type' => 'Country', 'name' => 'Uruguay' ),
		);

		if ( ! empty( $categorias ) && ! is_wp_error( $categorias ) ) {
			$datos['category'] = implode( ' > ', $categorias );
		}

		if ( $p->get_sku() ) {
			$datos['additionalProperty'][] = array(
				'@type' => 'PropertyValue',
				'name'  => 'SKU interno',
				'value' => $p->get_sku(),
			);
		}

		// Producción a pedido: no se declara precio. Se declara la vía de cotización.
		// "offers" con OfferCatalog sí se admite en Service sin disparar el
		// requisito de precio que exige Product/Offer.
		$datos['offers'] = array(
			'@type'         => 'Offer',
			'priceSpecification' => array(
				'@type'       => 'PriceSpecification',
				'description' => 'Precio a cotizar según cantidad, material y terminación',
			),
			'availability'  => 'https://schema.org/InStock',
			'url'           => self::SITIO . '/solicitar-presupuesto/',
		);

		$datos['additionalProperty'][] = array(
			'@type' => 'PropertyValue',
			'name'  => 'Modalidad de compra',
			'value' => 'Producción a pedido. Precio bajo presupuesto según cantidad, material y terminación.',
		);
		$datos['additionalProperty'][] = array(
			'@type' => 'PropertyValue',
			'name'  => 'Solicitud de presupuesto',
			'value' => self::SITIO . '/solicitar-presupuesto/',
		);

		return $datos;
	}

	/* ------------------------------------------------------------------
	 * PREGUNTAS FRECUENTES
	 * Todas las respuestas están basadas en información publicada en
	 * calco.uy. Revisar antes de publicar: son afirmaciones públicas.
	 * ---------------------------------------------------------------- */
	private static function mapa_faq() {
		return array(

			'etiquetas-en-rollos-y-plana' => array(
				'¿Qué tipo de etiquetas produce Calco Industria Gráfica?' =>
					'Producimos etiquetas en bobina y planas, personalizadas para botellas, latas y tarros, en diversos materiales. Se fabrican tanto para aplicación manual como para uso con etiquetadoras automáticas.',
				'¿Las etiquetas sirven para etiquetadoras automáticas?' =>
					'Sí. Las etiquetas en bobina se producen contemplando el paso, el sentido de salida y el diámetro de mandril que requiere cada equipo de etiquetado automático.',
				'¿Hay etiquetas aptas para contacto con alimentos?' =>
					'Sí. Trabajamos con materiales compatibles con el uso en alimentos y bebidas, con terminaciones adecuadas para ese tipo de producto.',
				'¿Cómo pido un presupuesto de etiquetas en Uruguay?' =>
					'Desde el catálogo en calco.uy se solicita el presupuesto en línea, o escribiendo a info@calco.uy. Estamos en San José de Carrasco, Canelones, y despachamos a todo el país.',
			),

			'estucheria-y-packaging' => array(
				'¿Calco fabrica packaging a medida?' =>
					'Sí. Contamos con formatos estándar y con un departamento de desarrollo a medida, con maquinaria especializada de troquelado, para cualquier cantidad.',
				'¿Hacen packaging para farmacia y cosmética?' =>
					'Sí. Producimos estuches con altos estándares de precisión y calidad, incluyendo prospectos plegados, para el rubro farmacéutico y cosmético.',
				'¿Producen cajas para delivery personalizadas?' =>
					'Sí. Fabricamos cajas de delivery autoarmables personalizadas con la marca del cliente, además de packaging e insumos para gastronomía.',
				'¿Cuál es la cantidad mínima de packaging?' =>
					'Trabajamos para cualquier cantidad. La tirada mínima conveniente depende del formato, el material y la terminación, y se define al cotizar.',
			),

			'libros-revistas-y-catalogos' => array(
				'¿Calco realiza el depósito legal en la Biblioteca Nacional?' =>
					'Sí, y lo realizamos en forma gratuita. Solo se solicita la entrega de 4 ejemplares.',
				'¿Qué opciones de encuadernación ofrecen para libros?' =>
					'Ofrecemos distintos tipos de papel, formatos —desde tamaño carta hasta formatos especiales— y terminaciones personalizadas, para elegir la combinación que mejor se adapte a cada obra.',
				'¿Imprimen revistas y catálogos de productos?' =>
					'Sí. Producimos revistas, catálogos y libros, eligiendo formato, material y tipo de encuadernación a medida de cada proyecto.',
			),

			'papeleria-empresarial-y-comercial' => array(
				'¿Qué incluye la papelería empresarial?' =>
					'Cuadernos, blocs, carpetas, sobres y hojas membretadas: los productos que forman la base de la identidad corporativa, con distintas terminaciones y materiales.',
				'¿Personalizan cuadernos con la marca de la empresa?' =>
					'Sí. Producimos cuadernos personalizados, incluyendo tapa dura, con la identidad visual de cada empresa.',
			),

			'gigantografias-senaletica-y-arquigrafia' => array(
				'¿Qué materiales usan para señalética en exteriores?' =>
					'Seleccionamos el material más adecuado según el destino, tanto para exteriores como para interiores, incluyendo carteles en sintra y otros soportes rígidos.',
				'¿Hacen decoración de espacios comerciales?' =>
					'Sí. Aplicamos diseño en arquitectura para señalización y decoración de espacios, con los materiales apropiados para cada ambiente.',
			),

			'alimentos-y-bebidas' => array(
				'¿Qué materiales usan para packaging y etiquetas de alimentos?' =>
					'Utilizamos materiales compatibles con el uso en alimentos, con terminaciones de calidad para que el producto se destaque en góndola.',
				'¿Producen etiquetas para bodegas y cervecerías?' =>
					'Sí. Producimos etiquetas en bobina para botellas, latas y tarros, en distintos materiales, aptas para aplicación manual o automática.',
			),
		);
	}

	private static function faq_categoria() {
		$term = get_queried_object();
		if ( ! $term || empty( $term->slug ) ) {
			return null;
		}
		$mapa = self::mapa_faq();
		if ( ! isset( $mapa[ $term->slug ] ) ) {
			return null;
		}
		return self::armar_faq( $mapa[ $term->slug ] );
	}

	private static function faq_general() {
		return self::armar_faq( array(
			'¿Dónde está ubicada Calco Industria Gráfica?' =>
				'En Ludwig Van Beethoven, Manzana 8 Solar 3, San José de Carrasco, Canelones, Uruguay. Atendemos de lunes a viernes de 09:00 a 17:00 y despachamos a todo el país.',
			'¿Qué produce Calco Industria Gráfica?' =>
				'Cubrimos necesidades de impresión desde una tarjeta hasta packaging de alta complejidad: estuchería y packaging con troquelado propio, etiquetas en rollo y planas, papelería empresarial, libros, revistas y catálogos, merchandising, gigantografías y señalética.',
			'¿Cómo solicito un presupuesto?' =>
				'Desde el catálogo en calco.uy se agregan los productos a la lista de presupuesto y se envía la solicitud en línea. También se puede escribir a info@calco.uy.',
			'¿Desde cuándo funciona Calco Industria Gráfica?' =>
				'Desde 2005, produciendo materiales gráficos para empresas y marcas en Uruguay.',
			'¿Se encargan del diseño además de la impresión?' =>
				'Sí. Podemos hacernos cargo desde el desarrollo y el diseño hasta la entrega en el domicilio del cliente.',
			'¿Hacen trabajos urgentes?' =>
				'Sí. Contamos con una línea de impresos urgentes para resolver trabajos con plazos ajustados.',
		) );
	}

	private static function armar_faq( array $preguntas ) {
		$items = array();
		foreach ( $preguntas as $q => $a ) {
			$items[] = array(
				'@type' => 'Question',
				'name'  => $q,
				'acceptedAnswer' => array(
					'@type' => 'Answer',
					'text'  => $a,
				),
			);
		}
		return array(
			'@type'      => 'FAQPage',
			'mainEntity' => $items,
		);
	}

	/* ------------------------------------------------------------------
	 * /llms.txt servido por WordPress
	 * Solo actúa si el archivo estático no existe en la raíz.
	 * ---------------------------------------------------------------- */
	public static function ruta_llms_txt() {
		$uri = isset( $_SERVER['REQUEST_URI'] ) ? strtok( $_SERVER['REQUEST_URI'], '?' ) : '';
		if ( '/llms.txt' !== $uri ) {
			return;
		}
		if ( file_exists( ABSPATH . 'llms.txt' ) ) {
			return; // el archivo estático manda
		}
		$archivo = __DIR__ . '/calco-llms.txt';
		if ( ! file_exists( $archivo ) ) {
			return;
		}
		header( 'Content-Type: text/plain; charset=utf-8' );
		header( 'Cache-Control: public, max-age=86400' );
		echo file_get_contents( $archivo ); // phpcs:ignore
		exit;
	}
}

Calco_Datos_Estructurados::init();
