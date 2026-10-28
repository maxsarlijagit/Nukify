# Nukify: roadmap de producción

Plan propuesto: 27 de octubre de 2026. No implica funcionalidades implementadas.
Objetivo: completar planos de composición desde una aplicación independiente con
hábitos de trabajo familiares para usuarios de Nuke y motor Blender incluido.

## Punto de partida verificado

- Shell Qt, grafo vertical, propiedades, viewer float y motor Blender persistente.
- Siete tipos actuales: Read, Color (solo exposure), Blur, Transform limitado,
  Merge limitado, Mask elíptico y Write. No son todavía un catálogo de producción.
- Actualización automática, playback con cache, canales RGBA y comparación con B fijo.
- Instalador 0.4 compilado con Blender 4.5.14 LTS. Prueba de instalación pendiente.
- Pruebas sobre medios sintéticos; no hay aprobación de planos reales de producción.
- El contrato actual reduce la imagen a RGBA. Canales arbitrarios y AOVs requieren
  ampliar el modelo, transporte y evaluación, no solamente agregar botones.

## Cadencia y alcance

Sprints nominales de dos semanas de trabajo efectivo; son unidades de planificación,
no fechas comprometidas. Estimar capacidad al cerrar S0. Cada sprint termina con
build instalable, proyecto de ejemplo, pruebas de imagen y revisión de interacción.
S6, S7 y S9 contienen investigación: si el motor no satisface el contrato, dividir
el sprint y reestimar antes de prometer la herramienta. El conjunto inicial de
12 sprints representa unas 24 semanas nominales, con incertidumbre alta en tracking,
canales y 3D; no equivale a alcanzar paridad completa con Nuke.

| Sprint | Objetivo y alcance | Criterio de salida |
| --- | --- | --- |
| S0 | Instalación y estabilidad: probar instalar, actualizar y desinstalar; arranque sin Blender/Python externos; autosave y recuperación; registro de errores; formatos de proyecto versionados. | Instalación en Windows limpio, composición demo y exportación; recuperación tras cierre inesperado; proyectos del usuario preservados. |
| S1 | Graph y ergonomía: contrato de mouse/teclado detallado abajo, barra de categorías, buscador Tab, multiselección, copy/paste, duplicar, bypass, Dot, Backdrop, conexiones editables, undo por gesto. | Crear y reorganizar un grafo de 30 nodos con teclado/mouse; guardar/reabrir conserva conexiones, posiciones y bypass; undo revierte cada gesto completo. |
| S2 | Contrato de imagen: alpha premultiplicado/straight, formato y data window, espacios de color OCIO, input/display/output separados, Read/Write robustos, diseño de canales nombrados. Probar EXR multilayer y capacidad de Blender antes de elegir puente adicional. | Roundtrip EXR con valores HDR, alpha y canales acordados preservados; display no altera export; configuración OCIO se guarda con el proyecto; canales no soportados producen un error explícito. |
| S3 | Composición 2D esencial: Constant, Grade, ColorCorrect, Multiply, Add, Clamp, Invert, Premult/Unpremult, Merge over/plus/multiply/screen/difference, Copy/Shuffle para canales acordados, Transform con pivote/rotación, Reformat, Crop, Blur, Dilate/Erode. | Componer foreground/background con bordes semitransparentes sin halos; fórmulas, orden A/B y filtros validados contra imágenes de referencia y tolerancias documentadas. |
| S4 | Animación y tiempo: parámetros animables, keyframes, interpolación constant/linear/Bezier, curve editor inicial, dope sheet, FrameHold, TimeOffset, Switch y remapeo temporal básico. | Animar transform y grade; scrub y export coinciden; guardar/reabrir conserva curvas; cambios invalidan los cuadros dependientes. |
| S5 | Roto y keying: Bezier en viewer, edición de puntos/tangentes, formas/layers, feather, invert, transform y animación; ChromaKey, LumaKey, Despill, limpieza de matte y EdgeBlur. | Completar un chroma real con garbage matte animado, pelo y motion blur; revisar alpha y RGB sobre fondos claros/oscuros durante toda la toma. |
| S6 | Tracker 2D: marcadores en viewer, patrón/búsqueda, forward/backward, stop, referencia, confianza, corrección manual y curvas. Exportar/enlazar a Transform, Stabilize y Roto. | Dos puntos recuperan traslación/rotación/escala en un clip controlado; reporte de error en píxeles; pérdidas y oclusiones visibles; un plano real queda aprobado. |
| S7 | Planar y reemplazos: investigación de seguimiento planar real; CornerPin de cuatro puntos, planar tracker si pasa la evaluación, perspectiva, estabilización/inversa, patch desde FrameHold. | Reemplazo de pantalla con perspectiva y oclusión, sin saltos al cambiar referencia; comparar esquinas contra ground truth y revisar deriva en toma real. |
| S8 | EXR de producción y acabado: ampliar AOVs, Cryptomatte cuando transporte/metadata lo permitan, operaciones por canal, ZDefocus, VectorBlur con convenciones explícitas, grano y regrain inicial. | Reconstruir un beauty desde AOVs y hacer una selección Cryptomatte verificable; conservar metadata necesaria; validar profundidad/vectores y export completo. |
| S9 | Integración 3D: escena Blender administrada por proyecto, cámara, Card, geometría, luces, RenderLayers y proyección; viewport de inspección. Investigación separada de camera solve, calibración y distorsión. | Integrar un elemento 3D en una toma, persistir escena/cámara y reproducir el render en otra instalación; solver solo se entrega si supera su prueba propia. |
| S10 | Rendimiento y entrega: profiling HD/4K, cache por dependencias, presupuestos de RAM/disco, proxy real y ROI donde el motor lo soporte, A/B de dos ramas animadas, render queue y reanudación. | Benchmarks repetibles con hardware/medios registrados; invalidación correcta; export cancelable/reanudable; errores y falta de espacio no corrompen proyecto ni resultados. |
| S11 | Beta de producción: correcciones, documentación, shortcuts finales, paquetes de medios, QA de instalación y regresión con artistas. | Tres planos reales completos: chroma, screen replacement y CG integration; apertura, edición, revisión y entrega EXR en otra máquina sin rutas del desarrollador. |

Dependencias principales: S0 → S1 → S2 → S3 → S4 → S5 → S6 → S7.
S8 requiere S2/S3; S9 requiere S2/S4 y el contrato de tracking si utiliza solve.
El profiling empieza en S0; S10 concentra las optimizaciones medidas, no posterga
la corrección de bloqueos de interfaz. Una herramienta incompleta no figura como lista.

## Mouse: contrato propuesto para S1

Es una propuesta de Nukify inspirada en hábitos de composición; no se afirma que
cada gesto coincida con todas las versiones o preferencias de Nuke.

| Contexto / gesto | Acción |
| --- | --- |
| Izquierdo sobre nodo | Seleccionar y mostrar propiedades; no cambiar el nodo conectado al viewer. |
| Shift + izquierdo sobre nodo | Agregar/quitar de la selección. |
| Izquierdo y arrastrar nodo | Mover toda la selección; un solo paso de undo al soltar. |
| Izquierdo sobre fondo | Limpiar selección; arrastrar dibuja rectángulo de selección. |
| Shift + rectángulo | Agregar a selección existente. |
| Doble clic izquierdo sobre nodo | Enfocar/abrir sus propiedades; Group entra al subgrafo cuando exista. |
| Izquierdo y arrastrar socket | Crear cable con previsualización y entradas compatibles resaltadas. |
| Soltar cable sobre entrada ocupada | Reemplazar conexión en una transacción reversible. |
| Arrastrar extremo de cable existente | Reconectar; soltar fuera cancela y conserva la conexión anterior. |
| Escape durante conexión o movimiento | Cancelar gesto y restaurar estado anterior. |
| Medio y arrastrar en graph | Pan, sin seleccionar/mover nodos. |
| Rueda en graph | Zoom centrado en cursor, con límites. |
| Derecho sobre fondo | Menú de creación, pegar, encuadrar y organización. |
| Derecho sobre nodo/cable | Acciones contextuales; desconectar explícitamente, bypass, duplicar, eliminar. |
| Arrastrar nodo sobre cable | Previsualizar inserción; confirmar al soltar solo con entrada/salida compatibles. |
| Izquierdo en viewer | Interactuar con la herramienta activa: seleccionar, roto, tracker o manipulador. |
| Medio y arrastrar en viewer | Pan independiente de herramienta activa; rueda para zoom. |

Hacer los sockets y cables fáciles de seleccionar, separando el área de hit-test
del grosor visual. Nunca conectar por proximidad sin mostrar el destino. Un click
sin movimiento no crea un checkpoint. Validar ciclos y tipos antes de modificar
el grafo. Una conexión cancelada no deja cambios parciales ni un estado sucio.

## Shortcuts propuestos

Los comandos deben vivir en un registro único utilizado por menús, tooltips y
editor de atajos. Guardar preferencias por usuario, detectar conflictos y ofrecer
reset e import/export de preset. No ejecutar comandos de graph mientras se escribe
en un campo de texto, buscador o editor de expresiones.

| Atajo | Alcance | Comando |
| --- | --- | --- |
| Tab | Graph | Buscador de nodos en la posición del cursor, favoritos y recientes. |
| 1 / 2 | Graph | Conectar selección a viewer A / B; 2 solo cuando exista la rama B animada. |
| F | Panel activo | Encuadrar selección en graph o imagen en viewer. |
| Home | Graph | Encuadrar todo el grafo. |
| Ctrl+A | Graph | Seleccionar todos los nodos del nivel actual. |
| Ctrl+C / Ctrl+V | Graph | Copiar/pegar subgrafo con conexiones internas, IDs nuevos y offset. |
| Ctrl+D | Graph | Duplicar selección. |
| D | Graph | Alternar bypass en nodos que tengan un contrato de bypass válido. |
| Delete | Graph | Eliminar selección y conexiones incidentes de forma reversible. |
| Ctrl+Z / Ctrl+Shift+Z | Proyecto | Undo/redo de parámetros, nodos, cables, curvas y formas. |
| Ctrl+S / Ctrl+Shift+S / Ctrl+O | Aplicación | Guardar / guardar como / abrir. |
| Espacio | Graph o viewer | Maximizar/restaurar panel bajo cursor; cambiar comportamiento actual. |
| J / K / L | Viewer o timeline | Playback inverso / pausa / playback adelante, incorporado con soporte correspondiente. |
| Flecha izquierda/derecha | Viewer o timeline | Cuadro anterior/siguiente. |
| R / G / B / A | Viewer | Alternar canal; no dispara herramientas del graph. |
| Escape | Herramienta activa | Cancelar gesto; nunca cerrar el proyecto. |

Los atajos de nodos rápidos se asignan desde preferencias; ofrecer inicialmente
Read, Grade, Merge, Transform y Blur solo tras comprobar conflictos por contexto.
Mostrar los cambios respecto de 0.3 (especialmente Espacio) en notas de migración.
En laptops, ofrecer una alternativa configurable al botón medio para navegación.

## Barra de herramientas y propiedades

- Barra de creación por categorías: Image, Color, Channel, Merge, Filter,
  Transform, Time, Keyer, Draw, Tracking, 3D y Utilities. Menús con nombre,
  tooltip y atajo; solo herramientas realmente disponibles.
- Barra del viewer: canales/layers, transformación de display, exposure/gamma,
  zoom, overlays, proxy, A/B, wipe, ROI cuando esté implementado y estado de cache.
- Barra contextual de Roto: selección, Bezier, formas, puntos, feather y overlays.
- Barra contextual de Tracking: crear track, patrón/búsqueda, referencia,
  forward/backward, stop, confianza y enlace/export de movimiento.
- Propiedades: paneles fijables, valores por defecto, reset individual,
  indicador de animación, keyframes, unidades, límites y errores locales legibles.
- Separar transporte de playback de controles de tracking. Cancelar un track
  no debe pausar o descartar silenciosamente una exportación independiente.

## Decisiones de ingeniería que condicionan el plan

1. Mantener Qt como interfaz y Blender incluido como motor. El proyecto .nukify
   continúa siendo la fuente de verdad; archivos .blend son recursos o artefactos
   administrados. El documento architecture.md de 0.1 es histórico.
2. Sustituir INPUTS/DEFAULTS y lógica dispersa por registro de nodos versionados:
   sockets tipados, parámetros, unidades, animación, evaluator, controles y migración.
3. No llamar Grade a Exposure ni PlanarTracker a un CornerPin animado. Cada nombre
   tiene un contrato de imagen/movimiento probado; diferencias quedan documentadas.
4. Unificar espacio de coordenadas: píxeles, origen, aspect ratio, formato y proxy.
   Formas, tracks, overlays y render deben usar la misma transformación.
5. Tracking usa trabajos cancelables y persistencia de tracks. La automatización del
   Movie Clip Editor y su dependencia de contexto/UI se investiga antes de integrar;
   disponer del algoritmo en Blender no garantiza acceso desde el worker headless.
6. Un plane track derivado de puntos no equivale automáticamente a un solver planar
   robusto. Evaluar calidad, deriva y coste; cualquier dependencia adicional se fija,
   licencia, empaqueta y prueba antes de incorporarla.
7. Frames EXR, AOVs, metadata y transformaciones OCIO requieren pruebas de fidelidad
   de extremo a extremo. Evaluar una biblioteca de I/O adicional solo si el puente
   de Blender no cumple; no descartar canales silenciosamente.

## Definición de terminado y material de QA

Cada nodo nuevo necesita valores de referencia, alpha/HDR, parámetros extremos,
frame animado cuando corresponda, persistencia, undo y comparación viewer/export.
Cada herramienta interactiva se prueba con mouse, teclado, cancelación, diferentes
zooms/proxies, foco en campos de texto y restauración después de abrir el proyecto.

Preparar fixtures sintéticas con ground truth y tres planos propios/autorizados:
chroma con pelo y blur, pantalla con perspectiva/oclusión y toma para integración CG.
Registrar resolución, FPS, rango, configuración de color, hardware y versión del motor.
Para tracking medir error por frame y deriva; fijar umbrales por fixture antes de
desarrollar (objetivo inicial del fixture 2D limpio: error mediano ≤1 píxel a resolución
nativa, separado de la aprobación visual en planos difíciles).
No confundir fps de playback cacheado con velocidad de evaluación de la composición.

Fuera de la primera beta: deep compositing, compatibilidad completa .nk, OFX genérico,
paridad de keyers propietarios, paint avanzado completo, multi-view estéreo y render
farm distribuida. Se planifican después de validar el flujo principal.

## Referencias de diseño

- [Viewer de Nuke](https://learn.foundry.com/nuke/content/reference_guide/image_nodes/viewer.html)
- [Tracker de Nuke](https://learn.foundry.com/nuke/content/reference_guide/transform_nodes/tracker.html)
- [Aplicación de datos de tracking](https://modosdk.foundry.com/nuke/content/comp_environment/tracking_stabilizing/applying_tracking_data.html)
- [Compositor de Blender 4.5](https://developer.blender.org/docs/release_notes/4.5/compositor/)

Estas referencias orientan los workflows. El alcance y los criterios anteriores
son decisiones propuestas para Nukify, no garantías de equivalencia entre motores.
