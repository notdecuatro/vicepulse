# Vice Pulse

## Piloto con Bobby Van Riper

La [campaña de Clipping Nation](https://contentrewards.com/c/campaigns/f583b069-ced7-49e5-9ed3-2d3a13d6df0c) aceptaba clips el 22 de noviembre de 2026. Vice Pulse quedó inscrito. Ese día quedaban $959 de presupuesto. La tarifa publicada era $1.50 por mil vistas elegibles en TikTok, Instagram Reels y YouTube Shorts, con un mínimo de 1,500 vistas y un máximo de $150 por publicación.

El [brief oficial](https://app.notion.com/p/Bobby-Van-Riper-GTA-VI-Clipping-Requirements-Guide-414582c82d8881d5b28bdd4235a1be82) pide material en inglés de los videos o directos de GTA VI de Bobby en Miami, con Bobby visible, un gancho inmediato, subtítulos legibles, `#bobbyvanriper` y su Twitch. El logo de la campaña es opcional. Mantener los likes visibles, el video público al menos 30 días y una tasa de interacción mínima del 1%. Se permite publicar el clip en las tres redes. La campaña exige al menos 40% de audiencia de EE. UU., Reino Unido, Canadá o Australia.

El enlace de cada publicación se presenta a Content Rewards dentro de los 30 minutos. Al llegar a 1,500 vistas, el [proceso de aprobación de Clipping Nation](https://app.notion.com/p/Clipping-Nation-Approval-Process-41a582c82d888181a892e48ccb233551) exige grabar desde un móvil la distribución geográfica del público de esa publicación y adjuntarla en un ticket del [Discord de Clipping Nation](https://discord.gg/DQyAcKa3nU). La grabación y el ticket forman parte del trabajo por publicación elegible.

`campaign.json` contiene los datos comprobados y el formato de Bobby. TikTok, Instagram y YouTube figuran conectados en Content Rewards y Buffer. La campaña mostró el formulario de entrega del enlace publicado, con plazo de 30 minutos. Los cuatro archivos MOV de la carpeta oficial son ejemplos que el brief reserva para referencia. Los [directos en Twitch](https://www.twitch.tv/bobby_vanriper/videos?filter=archives&sort=time) incluyen sesiones en Miami y partidas de GTA VI.

El [brief de la campaña](https://app.notion.com/p/Bobby-Van-Riper-GTA-VI-Clipping-Requirements-Guide-414582c82d8881d5b28bdd4235a1be82) identifica los directos como material de origen. El piloto se editó a partir de una descarga oficial de Twitch. Usa la cámara de Bobby y texto editorial sobre el momento del directo. El audio se generó para el piloto. La ficha de origen está junto al MP4 en `pilot/`.

Con la fuente autorizada y configurada, `.runtime/bin/python vice.py produce --slot 1` exporta un solo piloto. Revisar el gancho de los dos primeros segundos, los subtítulos, el aviso comercial y el llamado a seguir a Bobby antes de entregar. La prueba de 14 días comienza tras comprobar la publicación y el envío real a la campaña. Registrar por publicación las vistas elegibles, el estado del ticket, el pago y el tiempo de operación para calcular el ingreso neto por hora.

El 22 de noviembre se publicó el [primer Short de Vice Pulse](https://youtube.com/shorts/JVI00oM4tfM) con el aviso de promoción pagada y se entregó a la campaña dentro de los 30 minutos. Content Rewards confirmó la recepción. El clip comercial, su ficha de origen y los MP4 usados en la prueba privada están en `pilot/` y `demo/`.

## Estado del 22 de noviembre de 2026

Se exportaron dos muestras originales de 18 segundos con el render de producción. FFprobe confirmó MP4 vertical de 720 × 1280, H.264 y AAC con audio sintetizado. Son pruebas técnicas con texto y tiempos de referencia. Una muestra se cargó a Buffer y quedó guardada como borrador en TikTok, Instagram y YouTube. Buffer mostraba cero publicaciones en cola y cero enviadas después de guardar los tres borradores.

Pasaron siete pruebas de integración local con servicios simulados. Whisper transcribió audio real en inglés y devolvió marcas de tiempo. Ollama está instalado con el modelo `qwen2.5:1.5b` y escucha en el Mac. La sesión de trabajo bloqueó la llamada local al puerto de Ollama, de modo que la selección con ese modelo quedó pendiente de verificación. La prueba de Buffer se hizo en el navegador. La entrega automática a través de Cloudinary y la API de Buffer requiere sus credenciales.

## Arranque en el Mac

1. Ejecutar `setup-mac.command` en un Mac con red. Instala las herramientas gratuitas, descarga los modelos, prepara el entorno y ejecuta las pruebas. Se requiere acceso de macOS para instalar Homebrew si aún falta. `real_smoke.py` genera narración original, realiza transcripción y selección reales, exporta dos MP4 y comprueba sus pistas con ffprobe.
2. Conectar los perfiles de Vice Pulse en Buffer Free y en Content Rewards. Usar Instagram Business. Obtener la clave de Buffer desde [API settings](https://developers.buffer.com/guides/authentication.html) y la URL de conexión desde el panel de Cloudinary Free. Introducir ambas en `connect.command`. El archivo de credenciales se guarda solo en el Mac con permisos 0600.
3. Ejecutar `.runtime/bin/python vice.py accounts` y asociar los tres identificadores concretos a sus perfiles. La tarea programada debe conservar la sesión iniciada y el acceso a la base de datos local para presentar los enlaces.
4. El operador revisa el brief y sus archivos, copia `campaign.example.json` a `campaign.json` y completa los campos verificados. El ejemplo corresponde a GTA Clipper. Para otra campaña, cambiar el anuncio, hashtags, logotipo y fuentes según el brief. Guardar la licencia o los términos que cubran el material utilizado en `assets`. Calcular el SHA-256 del vídeo con `shasum -a 256`. El campo opcional `source_url` permite descargar el archivo desde una URL HTTPS autorizada cuando ya se identificó su hash. Los permisos por plataforma y el saldo deben corresponder al día en curso. Para una pista sin música de terceros, documentar también quién autoriza la voz y el audio restante.
5. Ejecutar `.runtime/bin/python vice.py produce`. Se generan hasta dos clips nuevos de 15 a 40 segundos por fecha de Nueva York. Se conserva el encuadre completo del original en el lienzo vertical. Las dos salidas usan la misma licencia vigente. Si se agota el material o se pierde acceso, el lote queda incompleto hasta resolver la causa.
6. Para la primera prueba externa ejecutar `.runtime/bin/python vice.py draft --slot 1` y comprobar los borradores en cada canal autorizado. El código utiliza la API oficial de Buffer y subida firmada con el SDK de Cloudinary. Abrir cada borrador y comprobar imagen, audio, texto, derechos y etiqueta comercial. En la campaña patrocinada hay que verificar la etiqueta en el editor nativo. El campo `native_disclosure_supported` parte desactivado. No habilitarlo basándose en un texto “Ad” en el vídeo o la descripción.
7. Con la sesión de Content Rewards preparada, publicar la primera pieza autorizada, verificar su URL real y presentar cada publicación desde la cuenta verificada a esa campaña dentro de 30 minutos. Si requiere aprobación previa, enviar primero el borrador a la marca y obtener su aprobación. `vice.py sync` recupera enlaces, estados y fechas de Buffer. Para publicación nativa separada, comprobar el perfil, la URL y la hora real y usar `vice.py link --slot 1 --network youtube --url URL --sent-at FECHA_ISO_CON_ZONA`. Registrar la referencia real de la solicitud con `vice.py record --slot 1 --network youtube --receipt REFERENCIA`. Estos dos comandos actualizan el registro local. El envío a Content Rewards se realiza con el formulario de la sesión autenticada. Verificar que la solicitud aparezca en Submissions. La aprobación y el cobro son resultados posteriores.
8. Tras la prueba real, completar el segundo clip. Para campañas que admitan expresamente publicación automática y cuyos requisitos estén cubiertos, `vice.py publish --slot 1` envía el MP4 por Buffer directamente. Para borradores existentes, publicar ese mismo borrador. Un timeout ambiguo conserva el estado `sending`. Localizar primero el post en Buffer y usar `vice.py reconcile --slot 1 --network youtube --post-id ID`. Si el proveedor confirma que no se creó, resolver el registro antes de volver a intentar. Conservar `state` entre ejecuciones.

## Campañas e integraciones revisadas

- [Maratón de Dylan Page](https://contentrewards.com/c/campaigns/39753a1a-f1f3-491b-a8f6-0cfee0af0c97). La página aceptaba clips y nombraba TikTok, Instagram y YouTube. Pide mostrar a Dylan y usar #DylanPage. Termina al acabar la maratón. Tres materiales se desbloquean después de la adhesión.
- [GTA Clipper](https://contentrewards.com/c/campaigns/686f6547-172e-4b76-99be-c26eabd5a2cf). La ficha mostraba $0.50 por mil vistas elegibles, mínimo $5 y máximo $200 por vídeo. El brief público menciona TikTok y YouTube Shorts. Confirmar Instagram por escrito antes de contar con esa red. Usar el logo oficial durante todo el clip.
- [Política de Rockstar](https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material). La política pública para aficionados cubre uso no comercial. Verificar el alcance comercial del material exacto y de la música con el titular o con la licencia que aporte la campaña.
- [Buffer Free](https://buffer.com/pricing) admite tres canales y diez publicaciones pendientes por canal. [Cloudinary Free](https://cloudinary.com/pricing) ofrece 25 créditos mensuales. Usar planes gratuitos.
- [Conexión de cuentas](https://help.contentrewards.com/en/articles/16746780-connect-your-social-accounts) y [presentación de un vídeo](https://help.contentrewards.com/en/articles/15319814-submit-a-video). Cada enlace requiere una cuenta conectada y una entrega dentro del plazo. La tarea de seguimiento necesita una sesión disponible para ejecutar ese paso.


## Relanzamiento del 22 de noviembre

La versión `pilot/bobby-dog-v2.mp4` usa la fuente original de 1920 × 1080 recuperada en Descargas. Conserva el audio original y muestra cámara y juego en dos paneles. El corte revisado dura 15.51 segundos y exporta 1080 × 1920, H.264 y AAC. El audio medido es −15.92 LUFS y −1.45 dBTP.

YouTube confirmó la publicación pública en https://youtube.com/shorts/Yk58VaZt6b8 y Content Rewards confirmó la recepción del enlace. Los ajustes nativos incluyen promoción pagada y público general. El registro está en `edits/bobby-dog-release.json`.

Para reproducir esta edición desde la carpeta del proyecto, ejecutar `.runtime/bin/python edit.py edits/bobby-dog.json`. El plan contiene los cortes y los recuadros de cámara y juego. La transcripción conserva tiempos de palabras y correcciones revisadas. Este comando solo exporta. La publicación de este lanzamiento se hizo en YouTube Studio.

El renderer acepta recuadros por fuente a través de `sources[].layout` para la producción automática. Los análisis nuevos usan una caché distinta con tiempos de palabras. El renderer rechaza una pista ausente o con volumen medio inferior a −50 dB.

La automatización completa sigue pendiente. Este proyecto local carece de BUFFER_API_KEY y CLOUDINARY_URL, `campaign.json` conserva su lista de fuentes vacía y no hay un servicio programado activo verificado. En este relanzamiento se publicó una pieza en YouTube. Instagram y TikTok quedan pendientes.

## Continuación y dos campañas

El programa acepta `--config campaigns/bobby.json` o `--config campaigns/dylan.json`. Los slots 1 y 2 comparten el registro diario para conservar el límite total entre campañas. Una edición terminada se incorpora con `.runtime/bin/python vice.py register-edit --slot 2 --plan edits/bobby-store.json`. El registro valida las pistas y rechaza reutilizar el mismo slot con otro archivo. Registrar una edición conserva las comprobaciones de autorización que se ejecutan antes del envío por API.

`media.py` y `edit.py` admiten `brand_overlay` en el plan. Los overlays oficiales están en assets/overlay-1.png y assets/overlay-2.png. El morado se usa en la segunda edición y está situado debajo del panel de cámara. Se volvió a transcribir el fragmento con contexto del nombre Cuffem y se revisó su montaje.

La segunda pieza se publicó en https://youtube.com/shorts/vlkeXjDVZAw y Content Rewards confirmó la recepción del enlace en esta sesión. Audio medido −17.05 LUFS, pico verdadero −1.75 dBTP. Los registros locales están en edits/bobby-store-release.json y state/vice.sqlite. Se preservan por separado las URLs, la recepción y cualquier futura aprobación o pago.

La campaña de Dylan Page está unida. Acepta material de su maratón iniciado el 19 de noviembre y exige que Dylan sea protagonista durante el clip, subtítulos y textos en inglés, #DylanPage y ediciones propias. Prohíbe marcas añadidas, reacciones o voces inventadas y publicaciones de colaboración. Se configuró campaigns/dylan.json para conservar sus requisitos. Faltan material local concreto y su revisión antes de producir para esa campaña. El saldo consultado fue $4,920 y cambia con el tiempo.

La tarea Operar Vice Pulse se reactivó a las 12:30 y 20:30 America/New_York. La programación está confirmada. La publicación mediante las APIs de Buffer y Cloudinary sigue pendiente de credenciales y prueba real.
