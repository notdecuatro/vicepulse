# Estado de Vice Pulse al 23 de noviembre de 2026

El programa de producción comparte dos conceptos diarios entre campañas. La edición técnica y el registro están probados; Cloudinary y Buffer ya superaron pruebas reales de subida y creación de borradores. La publicación integral automática en las tres redes sigue pendiente de validar.

## Ejecución

Desde esta carpeta, usar `.runtime/bin/python worker.py plan` para ver los bloqueos actuales sin descargar ni publicar. `worker.py draft` produce y prepara borradores cuando hay campaña, fuente y credenciales verificadas. `worker.py publish` exige revisión del archivo exacto y conserva además las comprobaciones de divulgación y entrega. La configuración se revalida cada día; no cambiar permisos o elegibilidad para saltar un bloqueo.

`vice.py`, `edit.py` y el coordinador comparten el mismo SQLite. No importar bases de datos de demostración ni ejecutar dos copias del proyecto con registros distintos. Un envío incierto se concilia; no se repite automáticamente.

## Resultado real

Se publicó https://youtube.com/shorts/2O0Qt2BfzNw en el canal Vice Pulse y Content Rewards confirmó recepción en la campaña de Dylan. Es el cupo 1 del 23 de noviembre. La promoción pagada nativa está activada. Aprobación y pago están pendientes.

Se conserva el borrador original `pilot/dylan-bank-v1.mp4`. El nuevo `pilot/dylan-bank-v2.mp4` dura 8,14 segundos: gancho separado, subtítulos recortados a la voz presente y nombre Lucia corregido. Se excluyó una frase con transcripciones contradictorias. Pasa el control técnico, pero aún requiere revisión editorial completa con audio y derechos acreditados antes de publicarse. La captura oficial completa está en `assets/dylan-day5-capture-2026-11-23.mp4`. No descargar otra vez la fuente disponible.

## Campañas

- Dylan: unido, con envío disponible; revalidar fin de la maratón antes del siguiente lote.
- Bobby: límite de clips alcanzado; conservar entregas anteriores.
- CNPL: unido y brief leído, pero falta acreditar cuenta de 30 días, historial deportivo y audiencia mínima de 50% Canadá/EE.UU. Mantener fuera de producción.

## Integraciones verificadas

El 23 de noviembre se comprobó que credentials.json contiene ambas credenciales y tiene permisos 0600. Buffer autenticó TikTok, Instagram y YouTube. Cloudinary aceptó una subida real de pilot/dylan-profile-v1.mp4. Se corrigió services.upload para usar el proxy HTTPS configurado cuando corresponde, manteniendo la verificación TLS.

Se crearon y consultaron dos borradores reales de ese clip en Buffer: Instagram y TikTok. Ambos devolvieron status draft, sentAt null y externalLink null. Los IDs están en state/integration-check.json y en los jobs del SQLite del cupo 1 del 23 de noviembre. No duplicar ni volver a publicar el YouTube existente. Estos borradores prueban el transporte por API; no sustituyen los controles de fuente, edición o divulgación nativa para publicación. La clave de Buffer termina en 98DF y vence el 22 de diciembre de 2026. No hay suscripciones contratadas.

La tarea existente sigue a las 12:30 y 20:30 de Nueva York. Su prueba inmediata ejecutó el prompt dentro de la conversación; esto no demuestra un ejecutor desatendido futuro. `state/scheduled-execution.json` conserva esa distinción.

## Pruebas

Trece pruebas de registro/coordinador y cinco regresiones FFmpeg reales pasaron. Incluyen límite global, varias campañas, reintentos, resultado remoto incierto, falta de elegibilidad, export general 1080x1920 y rechazo de silencio o audio ausente. Estas pruebas no acreditan retención, ingresos ni una publicación por API.

## Instagram temporalmente suspendido

Cuenta desactivada temporalmente por actividad sospechosa; Diego informó que ya presentó apelación. Pendiente de resolución. Instagram queda deshabilitado en todas las campañas y en la configuración predeterminada. No efectuar publicaciones, borradores nuevos, pruebas de acceso ni reconexiones a Instagram mientras esté pendiente. Conservar el borrador existente y su registro. YouTube y TikTok mantienen su configuración. Reanudar únicamente tras confirmar recuperación y revisar la cuenta.

## Correcciones y bloqueos comprobados en esta sesión

El plan conserva visibles los clips existentes aunque una campaña quede bloqueada. La comprobación de fuentes del plan no descarga archivos y exige fuente local autorizada. El render ya no reutiliza palabras de tramos eliminados en los subtítulos.

La fuente Dylan está descargada y registrada en campaigns/dylan.json; la evidencia está en campaigns/evidence/dylan-source.json. El brief permite edición y distribución propias, pero los derechos comerciales independientes de Rockstar y del audio siguen pendientes. La política pública de Rockstar cubre uso no comercial; no marcar esos campos como verificados.

El intento de consultar y crear una programación local falló con Codex app tool request failed. No se confirmó la creación de otra tarea. Se restauró activa la tarea original tras el intento, sin atribuirle acceso desatendido al Mac.

Tras el bloqueo inicial de revisión automática, Diego autorizó específicamente la adhesión a Chris Van Vliet. Se confirmó Joined y se leyó el documento de reglas. Exige cuenta de WWE/AEW/lucha libre y 40% de audiencia Tier 1; excluye gaming. Vice Pulse no acredita estos requisitos: permanece fuera de producción. Falta revisar requisitos globales y tutorial de Clip Summit. Detalle en campaigns/cvv-rules.md; configuración bloqueada en campaigns/cvv.json.
