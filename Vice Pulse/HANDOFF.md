# Vice Pulse · Traspaso para Claude

**Corte del estado:** 23 de noviembre de 2026, hora de Nueva York.  
**Punto de partida:** usar la carpeta viva `vice-pulse/`. Conserva el código, los medios y el registro operativo. El ZIP de integración es una copia parcial anterior a la incorporación local de SEGA.

## 1. Objetivo y público

Vice Pulse es un proyecto de clips verticales en inglés para audiencias de TikTok, Instagram Reels y YouTube Shorts. Empezó con GTA VI y se amplió a campañas compatibles de creadores y gaming cuando hay material autorizado y la cuenta cumple el brief. El modelo de ingresos es presentar las publicaciones a Content Rewards y cobrar por vistas elegibles si la campaña las aprueba.

La meta es producir **dos clips distintos al día en total**, reutilizar cada pieza en las redes que autorice su campaña y automatizar la edición y la entrega todo lo que permitan las integraciones y las reglas. Presupuesto inicial **USD 0**. El operador del proyecto quiere delegar la edición y la operación técnica.

## 2. Estado actual

| Área | Estado al corte | Evidencia |
| --- | --- | --- |
| Edición y exportación | Implementadas. Whisper transcribe con tiempos por palabra. Ollama puntúa ventanas de 15–40 s. FFmpeg renderiza y Pillow compone el texto. También hay planes manuales para cortes precisos y duraciones distintas. | El 23 de noviembre pasaron 13 pruebas de aceptación y 5 pruebas con FFmpeg real. La ejecución completa Whisper → Ollama → dos exportaciones sigue sin verificarse en esta sesión. |
| Control de calidad | Implementado. El formato actual es MP4 vertical 1080 × 1920 a 30 fps con H.264 y AAC. Se comprueban decodificación, pistas y niveles de audio. | `media.py`, `quality.py`, `media_checks.py`. La revisión editorial y de derechos es un paso adicional. |
| Cloudinary y Buffer | Integraciones probadas con una subida real y dos borradores de Dylan en Instagram y TikTok. Las credenciales están configuradas en este Mac con permisos `0600`. | `state/integration-check.json`. Los dos borradores figuran como `draft`, sin fecha de envío ni URL pública. |
| Publicación real | YouTube publicó piezas de Bobby y Dylan por el editor nativo y Content Rewards confirmó recepción. El registro también contiene una publicación histórica de Bobby en Instagram cuyo envío a la campaña quedó bloqueado por el límite. TikTok tiene borradores, sin publicación confirmada en el registro revisado. | `state/vice.sqlite` y `edits/*-release.json`. |
| Automatización | La tarea «Operar Vice Pulse» está habilitada a las **12:30 y 20:30** en `America/New_York`. Una prueba manual ejecutó el prompt en la conversación. Sigue pendiente comprobar una ejecución programada desatendida con acceso al Mac y a la sesión de Content Rewards. | `state/scheduled-execution.json`, `state/automation-repair.json` y consulta de la tarea durante el traspaso. |
| Cobros | Hay acuses de recepción. Aprobación, vistas elegibles y pagos siguen sin confirmarse. | El registro diferencia la URL pública y el acuse. No se verificaron liquidaciones. |

**Registro operativo que debe conservarse**

- **22 de noviembre:** cupo 1, `bobby-dog-v2.mp4`, y cupo 2, `bobby-store-v3.mp4`. Ambos en YouTube con acuse. `bobby-store-v4.mp4` es otro render local. [Short de Bobby, cupo 1](https://youtube.com/shorts/Yk58VaZt6b8) · [Short de Bobby, cupo 2](https://youtube.com/shorts/vlkeXjDVZAw)
- **23 de noviembre:** cupo 1, `dylan-profile-v1.mp4`, publicado en YouTube con promoción pagada nativa y acuse. Los borradores de Instagram y TikTok pertenecen a ese mismo cupo. [Short de Dylan](https://youtube.com/shorts/2O0Qt2BfzNw)
- **23 de noviembre:** cupo 2 sin registrar. `pilot/dylan-bank-v2.mp4` es un candidato de 8,14 s que pasó el control técnico. El archivo `.review.json` indica aprobación editorial pendiente, incluida la escucha completa, y derechos comerciales pendientes. La toma original de Dylan ya está en `assets/`.

**Campañas conocidas**

| Campaña | Qué hacer con ella |
| --- | --- |
| **Dylan Page** | Adhesión y formulario comprobados. Revalidar fin de la maratón y saldo. La fuente está descargada y registrada. Quedan por acreditar los derechos comerciales sobre el gameplay y el audio. El brief exige a Dylan como protagonista, subtítulos en inglés y `#DylanPage`, y prohíbe marcas añadidas y voces o reacciones inventadas. |
| **Bobby Van Riper** | Adhesión y envíos históricos confirmados. Content Rewards mostró «Clip limit reached», sin fecha de reinicio indicada. Conservar las entregas y comprobar si vuelve a aceptar envíos de la cuenta. |
| **SEGA · STRANGER THAN HEAVEN** | Adhesión autorizada y confirmada el 23 de noviembre. Fuente oficial localizada en Frame.io, con proxy 1080p de 161,42 MB. Descarga y copia local del logo pendientes. Acreditar 50 % de audiencia de EE. UU./Canadá, confirmar el requisito de 0,5 % de interacción, resolver si hay aprobación previa y aclarar cómo incluir la mención de YouTube con la descripción obligatoria. Consultar `campaigns/sega-rules.md`. |
| **CNPL** | Adhesión confirmada. Producción bloqueada hasta acreditar una cuenta con al menos 30 días, historial de deportes y al menos 50 % de audiencia de Canadá/EE. UU. El pack oficial sigue pendiente. |
| **Chris Van Vliet** | Adhesión autorizada y brief leído. Fuera de producción: exige un canal de lucha libre, excluye gaming y pide 40 % de audiencia Tier 1. Faltan revisar requisitos globales y el tutorial de Clip Summit. |
| **GTA Clipper** | Candidato histórico documentado en `LEEME.md` y `campaign.example.json`. Confirmar vigencia, uso comercial del material y música, y autorización para Instagram si se retoma. |

## 3. Estructura de carpetas y archivos

```text
Vice Pulse/
├── HANDOFF.md                      Traspaso y punto de entrada para Claude.
├── ORGANIZACION.md                  Inventario general de los recursos del proyecto.
├── vice-pulse/                      Aplicación vigente. Ejecutar los comandos desde aquí.
│   ├── OPERACION.md                 Estado de operación e integraciones al 23 de noviembre.
│   ├── LEEME.md                     Histórico de pilotos y arranque. Algunos datos están desactualizados.
│   ├── vice.py                      CLI, licencias y hashes, producción, envíos y registro SQLite.
│   ├── worker.py                    Coordina los dos cupos y los modos plan, draft y publish.
│   ├── strategy.json                Prioridad de campañas, presupuesto y métricas del piloto.
│   ├── services.py                  Buffer GraphQL, subida firmada a Cloudinary y selección con Ollama.
│   ├── media.py                     Render, subtítulos, recuadros, overlays y normalización de audio.
│   ├── edit.py                      Render local con planes JSON, cortes y subtítulos revisados.
│   ├── quality.py                   Verifica proporción, resolución, códecs, decodificación y audio.
│   ├── acceptance.py                Pruebas de coordinación, registro y transporte simulado.
│   ├── media_checks.py              Pruebas de render con FFmpeg real y regresión de subtítulos.
│   ├── real_smoke.py                Prueba privada de Whisper, Ollama y render, con una aserción antigua.
│   ├── offline_demo.py              Genera MOV de muestra con material sintético.
│   ├── verify-mov.m                 Utilidad histórica Objective-C/AVFoundation para revisar MOV.
│   ├── setup-mac.command            Instalación con Homebrew, entorno Python y descarga de modelos.
│   ├── connect.command              Entrada oculta de las dos credenciales y guardado local.
│   ├── configure_local.py          Alternativa para introducir credenciales desde el navegador en loopback.
│   ├── configure.html              Formulario local servido por configure_local.py.
│   ├── campaign.example.json        Plantilla que se debe adaptar al brief y a las fuentes de cada campaña.
│   ├── campaign.json                Configuración predeterminada histórica de Bobby, sin fuentes registradas.
│   ├── campaigns/                  Bobby, Dylan, CNPL, CVV y SEGA, con sus configuraciones y notas.
│   │   └── evidence/                Evidencia de origen y derechos pendientes de la fuente Dylan.
│   ├── assets/                     Originales de Bobby y Dylan y overlays del piloto.
│   ├── edits/                      Planes, transcripciones con tiempos y fichas de publicación.
│   ├── pilot/                      MP4 del piloto, informes de calidad, revisiones y fotogramas.
│   ├── demo/                       MOV sintéticos de referencia.
│   ├── state/                      Registro y resultados operativos. Tratarlo como material privado.
│   │   ├── vice.sqlite              Cupos por fecha y publicaciones por red, con sus acuses.
│   │   ├── worker.lock              Bloqueo para coordinar ejecuciones sobre el mismo registro.
│   │   ├── worker-last-run.json      Plan o resultado más reciente guardado por el coordinador.
│   │   ├── integration-check.json   Evidencia de la subida y los borradores reales.
│   │   ├── platform-health.json      Incidencias de plataformas, incluida la pausa de Instagram.
│   │   └── scheduled-execution.json, automation-repair.json
│   │                                Prueba manual de la tarea e intentos de reparar la programación.
│   ├── checkpoints/                Copia histórica de archivos de la sesión de correcciones.
│   └── .runtime/                    Entorno virtual local. Recrear en el equipo de destino.
├── resources/                      Kit gráfico, candidatos de Twitch y audio de prueba de Whisper.
├── checkpoints/                    Copias de recuperación de código y SQLite del 22 y 23 de noviembre.
├── exports/                        ZIP de integración del 23 de noviembre, sin fuentes originales ni runtime.
└── archives/                       Paquete inicial, instaladores y copia del kit gráfico.
```

El entorno inspeccionado es una carpeta de trabajo sin repositorio Git detectado. Para adjuntar archivos a Claude, seleccionar el código, este documento y los medios necesarios. Excluir `credentials.json`, `.buffer-token.txt`, `.env*` y sesiones del navegador. Antes de compartir `state/`, `checkpoints/`, configuraciones reales, fichas de publicación o ZIP, revisar IDs de cuenta, URLs de proveedores, rutas personales y acuses. El ZIP local de integración incluye SQLite y referencias operativas. El registro original se conserva en el Mac para evitar duplicados.

## 4. Tecnologías y versiones

| Componente | Versión o configuración observada |
| --- | --- |
| Entorno | macOS ARM64, Homebrew 7.0.15, Python **3.11.18** en `.runtime`, SQLite **3.54.1** según ese intérprete. |
| Video y gráficos | FFmpeg y ffprobe **9.0.2**, Pillow **13.0.0**. Scripts de instalación escritos en Bash. |
| Transcripción | `openai-whisper` **20250625**, modelo predeterminado `base`, PyTorch **2.15.0**, NumPy **2.4.6**. La variable `WHISPER_MODEL` permite cambiar el modelo. |
| Selección | Cliente Ollama **0.40.17**, modelo configurado `qwen2.5:1.5b`, API local en `127.0.0.1:11434`. La versión del servidor en ejecución no se pudo verificar. `OLLAMA_MODEL` permite cambiar el modelo. |
| Almacenamiento y publicación | SDK Cloudinary **1.47.0** para subida firmada, Buffer GraphQL. No hay versión fijada de la API en el código. Entrega a Content Rewards mediante sesión web autenticada. |
| Herramientas auxiliares | `yt-dlp` **2026.10.26** instalado por el script. La descarga de fuentes configuradas en `vice.py` usa `urllib.request`, HTTPS y SHA-256. |

`setup-mac.command` fija la versión de `yt-dlp` y usa rangos para Cloudinary y Pillow. Homebrew y las dependencias transitivas pueden resolver versiones distintas al reinstalar.

## 5. Instalación y ejecución

1. **Usar la carpeta viva o preparar una copia de trabajo.** Desde la raíz, ejecutar `cd vice-pulse`. En otro Mac, recrear `.runtime/`. Para volver a operar con un respaldo, conservar una sola base operativa y conciliar los posts y borradores con Buffer y Content Rewards. Las rutas de los MP4 guardadas en SQLite son absolutas. Si se mueve el proyecto, revisarlas y comprobar los hashes antes de reanudar.
2. **Preparar las dependencias en macOS.** `bash setup-mac.command` instala Homebrew si falta y requiere red para herramientas y modelos. Su última prueba tiene una comprobación de resolución obsoleta. Para aislar la instalación de esa prueba, ejecutar los pasos siguientes con Homebrew disponible:

   ```bash
   brew install ffmpeg ollama python@3.11
   "$(brew --prefix python@3.11)/bin/python3.11" -m venv .runtime
   .runtime/bin/python -m pip install openai-whisper 'cloudinary>=1.44,<2' 'Pillow>=10,<14' 'yt-dlp==2026.10.26'
   brew services start ollama
   ollama pull qwen2.5:1.5b
   .runtime/bin/python -c 'import whisper; whisper.load_model("base")'
   ```

3. **Verificar las rutas locales sin publicar.**

   ```bash
   .runtime/bin/python vice.py doctor
   .runtime/bin/python acceptance.py
   .runtime/bin/python media_checks.py
   .runtime/bin/python worker.py plan
   ```

   `doctor` comprueba presencia de ejecutables, módulos y credenciales. `plan` lee el estado y escribe `state/worker-last-run.json`, sin descargar fuentes ni contactar plataformas. Devuelve código 2 si detecta bloqueos o errores. La comprobación de este traspaso ejecutó la lógica del plan en modo de solo lectura para preservar el registro anterior.
4. **Para reproducir una edición local**, usar `.runtime/bin/python edit.py edits/dylan-bank-v2.json` con la fuente local disponible. Escribe el MP4 y el informe de calidad. Comprobar un export existente con `.runtime/bin/python quality.py pilot/dylan-bank-v2.mp4`.
5. **Para integrar cuentas en un equipo nuevo**, guardar las credenciales directamente allí mediante `bash connect.command` o `.runtime/bin/python configure_local.py`. Asociar las cuentas de Buffer que estén autorizadas; `.runtime/bin/python vice.py accounts` consulta los canales y muestra sus IDs. La cuenta de Content Rewards necesita su propia sesión autenticada. Mantener Instagram deshabilitado mientras se resuelve la apelación.
6. **Para operar con material autorizado**, revalidar el brief, saldo, elegibilidad, permiso comercial, plataformas, sesión de entrega y aprobación previa de la campaña. Registrar el archivo local, su SHA-256 y la evidencia en `campaigns/<campaña>.json`. El coordinador exige que la fuente comercialmente autorizada ya esté disponible en disco. Usar primero `worker.py plan`. `worker.py draft` produce o reutiliza los cupos disponibles y crea borradores remotos. Para una prueba de un solo cupo tras revisar los mismos requisitos, el CLI acepta `vice.py produce --config campaigns/<campaña>.json --slot 1` y `vice.py draft --config campaigns/<campaña>.json --slot 1`, precedidos por `.runtime/bin/python`.
7. **Para publicar y registrar**, revisar el archivo exacto, aplicar la divulgación comercial nativa y comprobar URL pública y hora. El modo `worker.py publish` requiere un `.review.json` con `approved: true` y el SHA-256 del MP4, además de los controles de entrega. Las configuraciones actuales mantienen `native_disclosure_supported` en falso. Para la entrega patrocinada, usar el flujo nativo verificado y presentar cada URL en el formulario de Content Rewards dentro del plazo que marque la campaña. El flujo documentado usa 30 minutos. En `vice.py`, `sync` consulta los envíos de Buffer, `link` registra una publicación nativa sobre un job existente, y `record` guarda el acuse después de entregar el enlace. `register-edit` registra el MP4 de un plan en un cupo. Usar la fecha y la red correctas para conciliar registros históricos.

## 6. Decisiones tomadas y por qué

- **Priorizar campañas con brief, fuente autorizada y entrega disponible.** Dylan quedó primero en la estrategia local. Se abrieron alternativas porque Bobby alcanzó su límite. La adhesión a CNPL, CVV o SEGA por sí sola no habilita producir.
- **Mantener dos conceptos diarios compartidos entre campañas.** SQLite usa fecha y cupo como identidad del clip y añade la red como identidad de cada envío. Así se mantiene el límite global y se conserva un borrador o un envío incierto entre reinicios.
- **Usar edición propia con voz original cuando lo pide el brief.** Los pilotos posteriores conservaron audio original y combinaron cámara y gameplay cuando el encuadre lo pedía. Se conservaron tiempos por palabra para corregir subtítulos y excluir palabras de segmentos eliminados.
- **Separar pruebas de transporte, revisión editorial, publicación y cobro.** Se verificó Cloudinary y Buffer con borradores. Para YouTube se aplicó la promoción pagada desde el editor nativo. El acuse de Content Rewards se conserva por separado.
- **Pausar Instagram tras la desactivación temporal.** El operador ya presentó apelación. Se preservaron el borrador y los registros previos y se deshabilitó Instagram en las configuraciones. YouTube y TikTok siguen sujetos a los controles de cada campaña.
- **Medir un piloto de 14 días iniciado el 22 de noviembre.** `strategy.json` propone revisar en días 7 y 14 las vistas elegibles, retención, aprobaciones, cobros y minutos de operación para medir el resultado económico.

## 7. Problemas conocidos

- **El plan al corte no encuentra campaña lista para un nuevo clip.** Conserva el cupo 1 de Dylan y bloquea el cupo 2. Los bloqueos actuales están en la tabla de campañas. La sola disponibilidad del MP4 de Dylan no acredita los derechos de gameplay y audio.
- **La prueba local con Ollama está pendiente.** Este entorno devolvió `Operation not permitted` al consultar loopback. Además, `real_smoke.py` aún espera 720 × 1280, frente al renderer actual de 1080 × 1920. Corregir la aserción y ejecutar en una sesión del Mac con Ollama accesible. `real_smoke.py --audio <grabación>` permite usar una muestra propia si falta `say`.
- **La tarea programada aún no demuestra operación desatendida.** El intento de consultar y crear programación local devolvió `Codex app tool request failed`. La tarea original sigue habilitada. Hay que verificar un disparo real que pueda llegar al Mac, al registro y a Content Rewards.
- **Los controles difieren según el punto de entrada.** La revisión editorial por hash se exige desde `worker.py publish`. El comando directo `vice.py publish` aplica controles de fuente, canal y envío, pero no esa revisión editorial. Consolidar los controles antes de automatizar.
- **Un timeout puede dejar un job en `sending`.** Consultar Buffer primero y conciliar con `vice.py reconcile --slot N --network RED --post-id ID`, usando la campaña y la fecha correctas. Un borrador ya guardado se gestiona como el mismo post en Buffer. Un envío repetido puede duplicar publicaciones.
- **Documentación y respaldos de distintas fechas.** `LEEME.md` conserva notas previas a las credenciales y los archivos `*-results.txt` contienen conteos anteriores. Para el estado operativo, usar `OPERACION.md`, las configuraciones vigentes y el registro. El ZIP de integración local se inspeccionó. La copia remota del mismo nombre tiene el mismo tamaño declarado, pero una falla de DNS impidió comparar sus bytes.

## 8. Próximos pasos sugeridos

1. **Reanudar sobre el registro vigente.** Ejecutar el plan, comprobar el cupo de Dylan y localizar los borradores existentes. Mantener Instagram en pausa hasta confirmar la recuperación. Conservar los acuses y buscar aprobaciones o pagos en Content Rewards.
2. **Resolver una campaña para el siguiente cupo.** Confirmar vigencia y licencia comercial completa del fragmento de Dylan, o terminar la validación de SEGA con el material oficial, audiencia, logo y texto requerido. Si Dylan queda autorizado, escuchar y revisar `dylan-bank-v2.mp4` antes de aprobar su hash.
3. **Cerrar la prueba técnica.** Corregir la resolución esperada en `real_smoke.py` y ejecutar Whisper → Ollama → dos MP4 en el Mac. Unificar las reglas de publicación entre coordinador y CLI, y repetir las pruebas de duplicados y timeouts.
4. **Demostrar una ejecución integral desatendida.** Confirmar que un disparo programado procesa un cupo elegible, obtiene su URL pública, entrega dentro del plazo y registra el acuse sin duplicar. Si la divulgación nativa o el formulario siguen requiriendo intervención, identificar el paso concreto y el permiso necesario.
5. **Evaluar el piloto con datos reales.** Registrar por publicación vistas elegibles, retención, estados de aprobación, montos efectivamente cobrados y minutos de operación. Usar esas cifras en las revisiones de 7 y 14 días.

## 9. Instrucciones y preferencias del operador

- Comunicarse en español, con respuestas directas y concretas. Mantener en inglés el contenido de campaña cuando el brief lo exija.
- Priorizar la ejecución. Avanzar con verificaciones, pruebas y correcciones recuperables mientras exista trabajo autorizado. Pedir intervención solo si se necesita acceso, registro, autorización o verificación que el asistente no puede completar.
- Mantener presupuesto inicial de USD 0. No contratar suscripciones sin aprobación. Buscar edición automatizada y dos clips distintos por día entre todas las campañas.
- Mantener ordenada la carpeta Vice Pulse, con código operativo, medios, recursos, exportaciones y respaldos identificables.
- Basar cada estado en evidencia. Marcar los datos desconocidos como pendientes. Diferenciar borrador, publicación pública, recepción, aprobación y cobro.
- Mantener credenciales, datos de cuentas y sesiones fuera del traspaso. Cualquier cambio de elegibilidad, derechos o divulgación requiere la evidencia correspondiente.
