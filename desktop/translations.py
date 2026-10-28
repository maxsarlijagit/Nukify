# SPDX-License-Identifier: GPL-3.0-or-later
"""Spanish source labels and their English UI translations.

Keep format placeholders identical. Technical node names and enum values are
intentionally stable across languages for interchange and existing workflows.
"""
PAIRS = [tuple(line.split('|', 1)) for line in r'''
Ejemplos|Examples
Proyecto|Project
Inspeccionar 3D en Blender|Inspect 3D in Blender
Guardar distribucion|Save layout
Espacio|Workspace
VIEWER  /  sin evaluar     \u007c     Standard / sRGB|VIEWER  /  not evaluated     \u007c     Standard / sRGB
+ Nodo  [Tab]|+ Node  [Tab]
Encuadrar  [F]|Frame all  [F]
Nodo|Node
Buscar parametro...|Search parameters...
Filtrar los controles del nodo seleccionado|Filter controls of the selected node
Registro de Blender|Blender log
Diagnostico|Diagnostics
Cancelar proceso|Cancel process
Live: edita parametros. 1 asigna el Viewer. Play reproduce; Cache range prepara el rango.|Live: edit parameters. 1 assigns the Viewer. Play starts playback; Cache range prepares the range.
Distribucion guardada para la proxima apertura|Layout saved for the next launch
VIEWER  /  cambios pendientes de evaluar     \u007c     Standard / sRGB|VIEWER  /  changes awaiting evaluation     \u007c     Standard / sRGB
Proyecto modificado|Unsaved changes
Guardar cambios antes de continuar?|Save changes before continuing?
Abrir proyecto|Open project
{0}: clic en una entrada superior para conectar|{0}: click a top input to connect
Guardar proyecto|Save project
Guardado: {0}|Saved: {0}
VIEWER  /  evaluando {0} con Blender...|VIEWER  /  evaluating {0} with Blender...
Blender procesando · CPU · sin servicios externos|Blender processing · CPU · no external services
VIEWER  /  error al iniciar Blender|VIEWER  /  failed to start Blender
VIEWER  /  render fallido o cancelado · revisar registro|VIEWER  /  render failed or canceled · check log
Proceso sin resultado completo: {0}|Process did not complete: {0}
GENAI activo|GENAI active
Pausá el seguimiento GENAI y esperá la operación actual antes de cerrar.|Pause GENAI monitoring and wait for the current operation before closing.
Proceso activo|Process active
Cancela el proceso o espera a que termine antes de cerrar.|Cancel the process or wait for it to finish before closing.
Recuperar autosave|Recover autosave
frame, value, pi, sin/cos/abs/min/max/sqrt/clamp y ref("Nodo", "parametro"). Vacio elimina.|frame, value, pi, sin/cos/abs/min/max/sqrt/clamp and ref("Node", "parameter"). Leave empty to remove.
Imagen o primer cuadro|Image or first frame
Agregar clave en frame actual|Add key at current frame
Quitar fila seleccionada|Remove selected row
Asigna A y B con 1 y 2 antes de intercambiar|Assign A and B with 1 and 2 before swapping
Layers / canales|Layers / channels
Read de la rama A|Read from branch A
Fijar propiedades|Pin properties
Ver este nodo [1]|View this node [1]
Inspeccionar un Read EXR de la rama A. Usar seleccion cambia el pase del Read y afecta la composicion.|Inspect an EXR Read from branch A. Use selection changes the Read pass and affects the composition.
La rama A no contiene un Read EXR|Branch A does not contain an EXR Read
Selecciona un nodo para editarlo.|Select a node to edit it.
Quitar correccion de este frame|Remove correction at this frame
Inspeccionar EXR / canales|Inspect EXR / channels
Desenlazar animacion|Unlink animation
Editar en Viewer / datos|Edit in Viewer / data
Expresion matematica o referencia a otro nodo|Math expression or reference to another node
Curva y keyframes|Curve and keyframes
Elegir imagen / secuencia...|Choose image / sequence...
Iniciando motor...|Starting engine...
VIEWER / imagen anterior · error de evaluacion|VIEWER / previous image · evaluation error
Selecciona un nodo y pulsa 1|Select a node and press 1
Playback: define First y Last (al menos dos cuadros)|Playback: set First and Last (at least two frames)
Espera o cancela la exportacion antes de preparar cache|Wait for or cancel export before caching
Cache: el rango First/Last esta invertido|Cache: First/Last range is reversed
Cache range: maximo 1000 cuadros por tanda|Cache range: maximum 1000 frames per batch
Rango excede el presupuesto: aumenta cache o usa un proxy menor.|Range exceeds the budget: increase cache or use a smaller proxy.
Asigna Viewer A antes de preparar cache|Assign Viewer A before caching
Rango cacheado. Play listo.|Range cached. Ready for playback.
Canales RGBA / luminancia / overlay de matte|RGBA channels / luminance / matte overlay
Transformacion de visualizacion; no modifica Write|Display transform; does not modify Write
Exposicion del Viewer en stops; independiente de la composicion|Viewer exposure in stops; independent of the composition
Capturar B|Capture B
Congela el cuadro actual como referencia B|Freeze the current frame as reference B
Posicion del wipe A/B|A/B wipe position
B: sin captura|B: no snapshot
Promedio de muestras scene-linear, antes del display|Average scene-linear samples, before display transform
Formato|Format
Limite de formato y margen del 5%; no representa dataWindow EXR|Format boundary and 5% margin; does not represent EXR dataWindow
RGBA float · zoom con rueda · boton medio para pan|Float RGBA · wheel to zoom · middle button to pan
Configura OCIO desde Color management|Configure OCIO in Color management
Capturar B con el mismo formato/proxy|Capture B with the same format/proxy
Crear nodo|Create node
Buscar nodo...|Search nodes...
Crear nodo [Tab]|Create node [Tab]
Copiar|Copy
Pegar|Paste
Duplicar|Duplicate
Eliminar|Delete
Encuadrar|Frame selection
Desconectar|Disconnect
Soltar para insertar {0}: {1} → {2}.{3}|Release to insert {0}: {1} → {2}.{3}
Escala de tiempo|Time scale
Desplazamiento en frames|Frame offset
Elegir config OCIO|Choose OCIO config
Tracking: confianza y perdidas|Tracking: confidence and lost tracks
Analizando en segundo plano... Diagnostico muestra el progreso.|Analyzing in the background... Diagnostics shows progress.
Enlazar movimiento|Link motion
Enlazar|Link
Todavia no hay un analisis|No analysis yet
Canales y metadata de imagen|Image channels and metadata
Usar seleccion|Use selection
Resultado conservado en analysis; el nodo cambio durante el tracking.|Result kept in analysis; the node changed during tracking.
Tracking perdido: curvas anteriores conservadas. Abri Confianza / perdidas para corregir.|Tracking lost: previous curves preserved. Open Confidence / lost tracks to correct.
Capas|Layers
Nueva capa Bezier|New Bezier layer
Quitar capa activa|Remove active layer
Editar grupos / transformaciones|Edit groups / transforms
Grupos de roto|Roto groups
Viewer: click agrega puntos; arrastrar mueve; Shift arrastra tangente; Escape termina. Coordenadas normalizadas.|Viewer: click to add points; drag to move; Shift-drag for tangents; Escape to finish. Normalized coordinates.
Usar herramientas del Viewer|Use Viewer tools
Editar puntos en Viewer o editar los datos JSON.\nRoto: [x,y,inX,inY,outX,outY], origen inferior izquierdo.|Edit points in Viewer or edit JSON data.\nRoto: [x,y,inX,inY,outX,outY], bottom-left origin.
Carpeta donde crear el paquete|Folder for the package
Reanudar job.json|Resume job.json
Cache de disco|Disk cache
Presupuesto total A+B en MB|Total A+B budget in MB
B: sin asignar|B: unassigned
Shortcuts del Node Graph|Node Graph shortcuts
Importar shortcuts|Import shortcuts
Exportar shortcuts|Export shortcuts
Crear → seguir el proceso → revisar versiones → incorporar a composición|Create → monitor progress → review versions → import into composition
Crear|Create
Conexión|Connection
Clave de sesión; vacío usa FAL_KEY|Session key; leave empty to use FAL_KEY
Solo memoria. No se guarda en proyectos, preferencias ni historial.|Memory only. Not saved in projects, preferences or history.
API key propia|Your API key
La clave se usa en esta sesión. Para próximos inicios configurá FAL_KEY en tu entorno.|The key is used for this session. For future launches, set FAL_KEY in your environment.
Abrir claves de fal.ai|Open fal.ai keys
FFmpeg en PATH o ruta al ejecutable|FFmpeg in PATH or executable path
Elegir FFmpeg|Choose FFmpeg
Los proxies de video y la importación como secuencia requieren FFmpeg. Los originales se conservan siempre.|Video proxies and sequence import require FFmpeg. Originals are always preserved.
Buscar modelos en fal.ai…|Search models on fal.ai…
Buscar|Search
Destacados verificados · 28 oct 2026. La búsqueda consulta el catálogo actual.|Featured models verified · Oct 28, 2026. Search queries the current catalog.
Actualizar schema|Refresh schema
Ficha del modelo|Model details
Nombre del asset / shot|Asset / shot name
Describí el resultado y qué debe conservarse…|Describe the result and what should be preserved…
Opciones avanzadas|Advanced options
Medio a enviar|Media to send
Proxy recibido|Received proxy
Proxy = máximo del lado largo; no aumenta resolución. El proxy recibido se crea localmente y no reduce el cobro de fal.|Proxy = maximum long edge; no upscaling. Received proxies are created locally and do not reduce fal charges.
Cantidad de unidades facturables del modelo. Ajustar por duración, resolución y cantidad según su ficha.|Billable model units. Adjust for duration, resolution and quantity according to the model details.
Unidades (manual)|Units (manual)
Calcular costo|Estimate cost
Costo sin calcular|Cost not estimated
Revisar y generar|Review and generate
Reutilizar parámetros de esta versión|Reuse this version's parameters
Los resultados aparecerán aquí al completar la generación|Results will appear here when generation completes
Abrir original|Open original
Usar en graph|Use in graph
Preparar proxy local de esta versión|Prepare local proxy for this version
Elegí una versión para ver sus parámetros y estado|Select a version to view its parameters and status
Reanudar seguimiento|Resume monitoring
Pausar seguimiento|Pause monitoring
Cancelar en fal|Cancel on fal
Listo · no se envían medios hasta confirmar una generación|Ready · no media is sent until you confirm generation
Costo sin calcular · parámetros modificados|Cost not estimated · parameters changed
Medios de entrada|Input media
Consultando precio; no se envían medios ni se genera contenido|Fetching price; no media is sent and no content is generated
Parámetros recuperados. Calculá el costo para crear una nueva versión.|Parameters restored. Estimate cost to create a new version.
{0} · {1}\nRequest: {2}\nProyecto: {3}\nPrompt: {4}|{0} · {1}\nRequest: {2}\nProject: {3}\nPrompt: {4}
ASSET / VERSIONES|ASSET / VERSIONS
BIBLIOTECA  /  VERSIONES LOCALES|LIBRARY  /  LOCAL VERSIONS
Esperá a que termine la operación actual|Wait for the current operation to finish
Actualizá el schema del modelo antes de generar|Refresh the model schema before generating
Estimado: {0:.4f} {1} · {2:g} × {3:g} / {4}\nBase por unidades manuales. No ajusta calidad/duración automáticamente: revisá la ficha. No es un tope de gasto ni el cobro final.|Estimate: {0:.4f} {1} · {2:g} × {3:g} / {4}\nBased on manual units. Quality/duration are not adjusted automatically: check model details. This is neither a spending cap nor the final charge.
Precio consultado. Revisá unidades y parámetros antes de confirmar.|Price fetched. Review units and parameters before confirming.
Confirmar envío y costo|Confirm upload and cost
{0} modelos encontrados (máximo 30). Trending no garantiza calidad; consultá la ficha.|{0} models found (maximum 30). Trending does not guarantee quality; check model details.
Schema actualizado desde fal.ai|Schema refreshed from fal.ai
Sin request ID recuperable|No recoverable request ID
Los resultados ya están guardados|Results are already saved
Pausando al terminar la operación actual. El trabajo remoto puede continuar y cobrar.|Pausing after the current operation. The remote job may continue and incur charges.
Pausá primero el seguimiento y esperá a que termine la operación actual|Pause monitoring first and wait for the current operation to finish
Solicitar cancelación remota. Si ya está ejecutándose puede no cancelarse y generar cargos.|Request remote cancellation. A running job may not be canceled and may incur charges.
Sin resultados descargados para esta versión|No downloaded results for this version
Video guardado. Abrí el original o configurá FFmpeg para preparar una secuencia.|Video saved. Open the original or configure FFmpeg to prepare a sequence.
Nodo Read agregado al proyecto; original conservado|Read node added to project; original preserved
Pausá el seguimiento y esperá la operación actual antes de cerrar.|Pause monitoring and wait for the current operation before closing.
Seleccionar medios locales; se suben solo al confirmar|Select local media; uploaded only after confirmation
Cambió el proyecto; volvé a elegir Usar en graph|Project changed; choose Use in graph again
Abrir|Open
Guardar|Save
Asignar Viewer  [1]|Assign Viewer  [1]
Exportar EXR|Export EXR
Composicion|Composition
Chroma y roto|Chroma and roto
EXR y Cryptomatte|EXR and Cryptomatte
Integracion 3D|3D integration
Curvas y roto|Curves and roto
Curvas / Dope sheet|Curves / Dope sheet
Asignar Viewer B [2]|Assign Viewer B [2]
Desconectar B|Disconnect B
Reanudar render|Resume render
Recopilar proyecto y medios|Collect project and media
Presupuesto cache|Cache budget
Viewer amplio|Large Viewer
Nodos amplios|Large graph
Generar y editar imágenes / videos con fal.ai|Generate and edit images / videos with fal.ai
Primer frame|First frame
Frame anterior|Previous frame
Frame siguiente|Next frame
Ultimo frame|Last frame
Canales EXR|EXR channels
Layers / canales EXR|EXR layers / channels
Intercambiar A / B|Swap A / B
Importar preset|Import preset
Exportar preset|Export preset
Seleccionar todo|Select all
Encuadrar todo|Frame all
Maximizar panel|Maximize panel
Comando|Command
Atajo|Shortcut
Predeterminado|Default
Generar imagen|Generate image
Editar imagen|Edit image
Generar video|Generate video
Editar video|Edit video
Idioma / Language|Language / Idioma
Idioma de la interfaz|Interface language
El idioma se aplica al volver a abrir Nukify. Guardá tu proyecto antes de cerrar.|Language takes effect when you reopen Nukify. Save your project before closing.
Idioma guardado. Se aplicará al volver a abrir Nukify.|Language saved. It will apply when you reopen Nukify.
No se pudo guardar el idioma: {0}|Could not save language: {0}
Idioma guardado|Language saved
Aceptar|OK
Cancelar|Cancel
Cerrar|Close
Restaurar valores|Restore Defaults
Sí|Yes
No|No
Descartar|Discard
Aplicar|Apply
Ayuda|Help
Carpeta de salida|Output folder
Ancho|Width
Alto|Height
Primero|First
Último|Last
FOTOGRAMA|FRAME
GRAFO DE NODOS|NODE GRAPH
PROYECTO / FORMATO Y RANGO|PROJECT / FORMAT & RANGE
Reproducir|Play
Pausa|Pause
Bucle|Loop
Cachear rango|Cache range
Tiempo real ON|Live ON
Tiempo real OFF|Live OFF
Restablecer|Reset
Restablecer vista|Reset view
Ajustar|Fit
Gestión de color|Color management
Atajos|Shortcuts
Cola de render|Render queue
Reproducir proxy|Play proxy
Imagen a video|Image to video
Trabajo: |Job: 
Actualizando {0}...|Updating {0}...
Modelo: {0}\nEstimado: {1:.4f} {2}\nBase: {3:g} unidades de {4}. Puede variar con calidad/duración.\nArchivos locales a subir: {5}\nProxy de entrada: {6}\nSe enviarán el prompt y los medios elegidos a fal.ai usando tu cuenta.\nConfirmo que revisé las unidades facturables y autorizo este trabajo pago.|Model: {0}\nEstimate: {1:.4f} {2}\nBasis: {3:g} units of {4}. May vary with quality/duration.\nLocal files to upload: {5}\nInput proxy: {6}\nThe prompt and selected media will be sent to fal.ai using your account.\nI confirm that I reviewed the billable units and authorize this paid job.
Cargá el schema del modelo|Load the model schema
Escribí un prompt|Enter a prompt
Elegí al menos una imagen de entrada|Choose at least one input image
Elegí un video de entrada|Choose an input video
Configurá tu API key en Conexión o FAL_KEY|Set your API key in Connection or FAL_KEY
Calculá el costo nuevamente: parámetros cambiados o cotización vencida|Estimate cost again: parameters changed or quote expired
La operación falló. Revisá conexión, clave y configuración.|Operation failed. Check your connection, key and settings.
Formato de proyecto no compatible|Unsupported project format
Tipo de nodo no compatible|Unsupported node type
Conecta la escena y camara a RenderLayers para verla.|Connect the scene and camera to RenderLayers to view it.
Selecciona un nodo de imagen.|Select an image node.
Selecciona el nodo Write que queres exportar.|Select the Write node to export.
Hay un proceso activo. Espera o cancela.|A process is active. Wait or cancel it.
Falta el motor incluido. Reinstala Nukify para repararlo.|Bundled engine missing. Reinstall Nukify to repair it.
El rango First/Last esta invertido.|First/Last range is reversed.
Configura la carpeta Output.|Set the Output folder.
Selecciona Write y configura Output.|Select Write and set Output.
Rango invertido|Reversed range
Hay un render activo|A render is active
B requiere una imagen renderizada|B requires a rendered image
Agregar proyecto actual|Add current project
Quitar seleccionado|Remove selected
Iniciar / reanudar cola|Start / resume queue
Copiar claves|Copy keys
Pegar claves|Paste keys
Confianza / perdidas|Confidence / lost tracks
Corregir puntos en este frame|Correct points at this frame
Guardar correccion manual|Save manual correction
Editar zona de exclusion|Edit exclusion area
Analizar rango|Analyze range
Cancelar tracking|Cancel tracking
Crear Transform / CornerPin|Create Transform / CornerPin
Enlazar a nodo...|Link to node...
Editar en Viewer|Edit in Viewer
Terminar herramienta|Finish tool
(sin conectar)|(disconnected)
Parametro|Parameter
Estado|Status
Confianza|Confidence
Error FB px|FB error px
Agregar grupo|Add group
Quitar grupo|Remove group
Imagen|Image
Canal|Channel
Mezcla|Merge
Filtro|Filter
Transformación|Transform
Tiempo|Time
Dibujo|Draw
Utilidades|Utilities
Exposición|Exposure
Saturación|Saturation
Contraste|Contrast
Ganancia|Gain
Opacidad|Opacity
Rotación|Rotation
Escala|Scale
Ruta|Path
Etiqueta|Label
Tamaño|Size
Factor|Factor
Fotograma|Frame
Valor|Value
Pendiente de entrada|In slope
Pendiente de salida|Out slope
Activado|Enabled
Invertir|Invert
Completo|Full
Detener|Stop
VIEWER / exportacion terminada; Live actualiza la vista|VIEWER / export complete; Live updates the view
VIEWER / Live OFF · imagen anterior conservada|VIEWER / Live OFF · previous image preserved
EXR exportado|EXR exported
Evaluacion lista|Evaluation complete
Frame {0}: {1} \u007c A dorado, B azul|Frame {0}: {1} \u007c A gold, B blue
{0} en cache|{0} cached
sin cache|not cached
 · schema de fal| · fal schema
Requerido|Required
Opcional|Optional
Preset de shortcuts no compatible|Unsupported shortcut preset
Cada atajo debe ser texto|Each shortcut must be text
Hay atajos duplicados|Duplicate shortcuts
Preset invalido|Invalid preset
Version de preset no compatible|Unsupported preset version
Curva invalida|Invalid curve
Cantidad de claves invalida|Invalid key count
Clave invalida|Invalid key
Los frames deben ser enteros|Frames must be integers
Frames duplicados|Duplicate frames
Escala de tiempo debe ser positiva|Time scale must be positive
Lista de puntos invalida|Invalid point list
CornerPin requiere cuatro puntos|CornerPin requires four points
Hay un analisis activo. Espera o cancela.|Analysis is active. Wait or cancel it.
No se pudo iniciar el motor de analisis|Could not start the analysis engine
Defini tracking_path o conecta un Read directo para analizar.|Set tracking_path or connect a direct Read to analyze.
Primero analiza el rango.|Analyze the range first.
'''.strip().splitlines()]
PAIRS = [(a.replace(r'\u007c', '|').replace(r'\n', '\n'), b.replace(r'\u007c', '|').replace(r'\n', '\n')) for a, b in PAIRS]
