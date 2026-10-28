# GENAI Studio · fal.ai

Sección experimental disponible desde el botón **GENAI** de la barra principal al ejecutar el código actualizado. El instalador 0.9.2 publicado antes de esta función no la incluye.

## Flujos disponibles

- Generar imágenes desde un prompt.
- Editar imágenes con referencias locales o URLs.
- Generar videos desde texto o una imagen.
- Editar videos con instrucciones y referencias, según el modelo.
- Seguir preparación, subida, cola, ejecución, descarga y creación de proxies.
- Guardar resultados en una biblioteca de versiones e incorporarlos al compositor con **Usar en graph**.

## Configurar y generar

1. Prepará el entorno de [BUILDING.md](../BUILDING.md), iniciá la app desde fuentes y abrí **GENAI → Conexión**.
2. Pegá tu propia clave de fal.ai. Se conserva únicamente en memoria durante esa sesión. También podés configurar `FAL_KEY` en el entorno antes de iniciar Nukify. No pegues la clave en un prompt, archivo de proyecto, issue o captura.
3. Para video, instalá FFmpeg por tu cuenta y agregalo al PATH o elegí su ejecutable en Conexión. No se descarga ni distribuye automáticamente.
4. En **Crear**, elegí el modo, el modelo, un nombre de asset y el prompt. Los campos de resolución, calidad, formato, duración, cantidad y seed dependen del schema del modelo. Las opciones adicionales están en **Opciones avanzadas**.
5. En campos de medios, usá **…** para elegir archivos. Los campos que admiten varias URLs usan una lista JSON. La marca `local:` indica un archivo local pendiente de preparación/subida; los campos de texto normales no se suben como archivos.
6. Elegí el proxy de entrada y el proxy de recepción. Ajustá las **unidades facturables manuales** consultando la ficha del modelo y presioná **Calcular costo**.
7. Revisá el costo, parámetros y medios. **Revisar y generar** muestra una confirmación antes de subir archivos y enviar una generación paga a tu cuenta de fal.

La clave no se guarda en los proyectos, preferencias o historial de trabajos. La ruta de FFmpeg es de sesión. Abrir GENAI no genera solicitudes pagas ni sube medios; buscar modelos y actualizar schemas son consultas al catálogo.

## Modelos destacados y descubrimiento

El catálogo inicial contiene 11 endpoints cuyos schemas públicos fueron consultados el **28 de octubre de 2026**:

| Familia | Modos incluidos |
| --- | --- |
| Google Nano Banana 2.1 | Generación y edición de imagen |
| Google Nano Banana Pro | Generación y edición de imagen |
| OpenAI GPT Image 2 | Generación y edición de imagen |
| MiniMax H3 Max | Texto a video e imagen a video |
| Kling 4 | Texto a video y edición de video |
| Kling O3 Pro | Edición de video |

La selección es orientativa; no es un ranking objetivo de calidad. **Buscar** consulta hasta 30 resultados activos de la categoría en el catálogo de fal; afiná el texto para encontrar otro modelo. **Actualizar schema** recupera sus campos actuales. Los modelos encontrados se conservan durante la sesión; los trabajos guardan el schema utilizado. Los campos complejos se editan como JSON. Un modelo descubierto puede requerir parámetros o formatos adicionales: revisá su ficha antes de usarlo. Los controles hacen validación básica del schema; la validación definitiva corresponde al servicio.

## Costos

La estimación consulta `/models/pricing` y `/models/pricing/estimate` con tu clave. Muestra moneda, precio base, unidad, cantidad manual y total estimado. No se presupone que una unidad sea una imagen o un segundo: depende del modelo.

**No calcula automáticamente los multiplicadores de resolución, duración, audio, tokens o calidad.** Ajustá la cantidad de unidades según la ficha. Por ejemplo, si el precio está expresado por segundo, cinco segundos requieren cinco unidades base, antes de los ajustes que indique ese modelo. El importe mostrado no es el cobro final ni un límite impuesto a fal. Si la consulta falla, generar queda deshabilitado. Cambiar parámetros invalida la estimación, que además vence a los cinco minutos.

La app no reenvía automáticamente una generación si se pierde la respuesta al envío. Un estado **UNKNOWN** requiere revisar el dashboard de fal antes de decidir otro envío. Esto evita convertir una desconexión en un segundo pedido cobrado.

## Proxies y contenido recibido

- **Enviar Original:** sube el medio seleccionado sin reducirlo.
- **Enviar Proxy 512/1024/1920:** crea una copia con ese máximo de lado largo, sin ampliar. Imágenes en PNG; videos H.264/AAC con FFmpeg. Los proxies no son un intercambio HDR/EXR con color gestionado: prepará los medios de referencia de forma apropiada.
- **Recibir Proxy:** siempre descarga primero el original y calcula SHA256; después crea una copia local de revisión. No reduce el tamaño de descarga ni la tarifa del modelo.
- Los videos con FFmpeg disponible tienen previsualización local en frames a 12 fps, sin audio. **Abrir original** utiliza el reproductor del sistema para revisar el archivo completo con audio.
- **Preparar proxy local de esta versión** permite crear el proxy después de configurar FFmpeg, sin volver a generar ni descargar el original.
- **Usar en graph** crea un nodo `Read`. Para video extrae una secuencia PNG del original, con su cantidad de cuadros, y ajusta el rango del proyecto. No importa audio. La extracción puede ocupar bastante disco.

El módulo admite imágenes PNG/JPEG/WebP y videos MP4/MOV/WebM/MKV/AVI para preparación local. Otros tipos de referencia pueden enviarse por URL si el modelo los soporta. La subida local tiene un límite de 512 MB por archivo y la descarga de cada resultado de 2 GB. Las conversiones locales tienen un timeout de diez minutos. No hay instalación automática de codecs.

## Versiones y recuperación

Los trabajos se guardan bajo `%LOCALAPPDATA%/Nukify/genai/<asset>/v0001/`, `v0002/`, etc. Incluyen parámetros, schema, estimación, estado, request ID, rutas de seguimiento, eventos y hashes. Los originales y proxies quedan separados. El directorio es una biblioteca local compartida entre proyectos; cada trabajo registra el proyecto de origen. No lo subas a Git ni lo compartas sin revisar prompts y referencias.

**Reutilizar parámetros de esta versión** prepara una nueva solicitud y exige calcular el costo de nuevo. No promete reproducibilidad exacta, incluso con la misma seed. Los nodos importados conservan procedencia y versión; undo revierte la incorporación al graph sin borrar los medios.

**Pausar seguimiento** detiene la espera local; el trabajo remoto puede seguir y cobrar. **Reanudar seguimiento** usa el mismo request ID, incluso tras reiniciar Nukify, y no reenvía la generación. Si se interrumpió la descarga puede volver a descargar el resultado mientras fal lo conserve. **Cancelar en fal** solicita cancelación: no garantiza que un trabajo ya iniciado se detenga ni que no se cobre. Reanudá el seguimiento para comprobar el estado.

No cierres el proceso a la fuerza durante una operación. Si el programa se interrumpió al enviar y no llegó a guardar un request ID, revisá el dashboard de fal; no se intenta adivinar ni reenviar ese pedido.

## Validación y límites

La integración tiene pruebas locales con un proveedor simulado para generación, recepción, errores, recuperación, versionado, protección de credenciales e invalidación de cotizaciones, además de comprobaciones Qt. Estas pruebas **no equivalen a una generación real pagada**. Las consultas públicas de catálogo/schema sí se realizaron contra fal. La compatibilidad de inferencia, el cobro y la calidad final de cada modelo deben verificarse con una cuenta y un trabajo autorizado.

La validación local incluyó 67 pruebas aprobadas con Blender configurado, revisión visual a 1024/1440 px y escalado del 150%, conversión real de un video sintético de 48 cuadros y render de dos cuadros de su secuencia en Blender. La comparación con los PNG de entrada tuvo un error máximo de un nivel sobre 255. No se usaron medios de clientes ni generaciones pagas.

Fuentes de contratos: [cola de fal](https://fal.ai/docs/documentation/model-apis/inference/queue), [catálogo](https://fal.ai/docs/platform-apis/v1/models), [precios](https://fal.ai/docs/platform-apis/v1/models/pricing), [estimaciones](https://fal.ai/docs/platform-apis/v1/models/pricing/estimate) y [cliente oficial](https://github.com/fal-ai/fal/tree/main/projects/fal_client).
