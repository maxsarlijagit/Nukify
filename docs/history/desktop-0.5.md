# Nukify 0.5 — Compositor Lab

Implementación funcional inicial de las áreas S0–S8. Mantiene Blender 4.5.14 LTS
como motor de composición y agrega OpenCV para tracking, OpenColorIO para display
y un proceso EXR aislado para evitar conflictos entre bibliotecas nativas.
No equivale a una certificación de los sprints para producción ni a paridad con Nuke.

## Instalar y probar

Ejecutar Nukify-Setup-0.5.0.exe. Instala por usuario y contiene Blender, Python y Qt;
no requiere seleccionar ejecutables ni descargar un motor. Abrir Nukify desde Inicio.
Proyecto → Ejemplos ofrece Composición, Chroma y roto, Tracking 2D, Planar y EXR/Cryptomatte.
Son medios sintéticos reproducibles, identificados como ejemplos técnicos.

- Live actualiza automáticamente la salida asignada al viewer al editar parámetros.
- Cache range prepara el rango; Play reproduce. El rendimiento de evaluación depende del plano.
- Proyecto → Color management permite cargar config OCIO y elegir display/view.
- Proyecto → Shortcuts configura los comandos del graph. Proyecto → Curvas muestra el dope sheet.
- Autosave cada 30 segundos guarda proyectos modificados en LocalAppData/Nukify/recovery-PID.nukify.
  Proyecto → Recuperar autosave permite abrirlos sin sobrescribir el original.
- Ctrl+S guarda, Ctrl+Shift+S guarda como, Ctrl+O abre; proyectos v1 migran a v2.

## Interacción

Izquierdo selecciona y arrastra nodos; sobre fondo hace selección rectangular.
Shift+clic alterna selección. Arrastrar entre sockets conecta/reconecta; se conserva
el método de click en salida y luego click en entrada. Escape cancela. Medio arrastra
la vista; rueda hace zoom. Derecho abre acciones contextuales y desconexión de cables.
Al arrastrar un nodo sobre un cable, el cable resaltado previsualiza la inserci?n;
soltar conecta ambas entradas en una operaci?n reversible. Tab busca nodos; F encuadra selección; Home encuadra todo; D hace bypass. Ctrl+C/V/D
copia, pega y duplica subgrafos. Una conexión o movimiento completo ocupa un undo.

Espacio maximiza/restaura graph o viewer. En viewer: J retrocede, K pausa, L avanza;
flechas cambian un cuadro; R/G/B/A/Y alternan canales. El botón Play sigue disponible.
Los atajos del graph no se ejecutan mientras se escribe en propiedades.

## Nodos

Image: Read, Constant y Write. Color: Exposure (Color histórico), Grade con gain/offset/gamma por canal,
ColorCorrect master/shadows/midtones/highlights, Multiply, Add, Clamp, Invert y ColorSpace. Channel: Premult,
Unpremult, Shuffle RGBA, Copy RGBA, AlphaMask y Cryptomatte. Merge: over, plus,
multiply, screen y difference, con mix y máscara. Filter: Blur, DilateErode de alpha,
EdgeBlur de alpha, ZDefocus, VectorBlur, Grain y Regrain. Transform: traslación,
rotación, escala y pivote; Crop, Reformat y CornerPin. Time: FrameHold, TimeOffset,
TimeRemap sin interpolación óptica y Switch. Draw: Mask, Roto y MaskCombine.
Tracking: Tracker2D y PlanarTracker. Utilities: Dot y Backdrop.

Grade aplica al RGB: normalizar black/white → lift/gain → multiply/offset → gamma
con signo, conservando alpha. Gain/offset/gamma tienen ajustes RGB adicionales; no reproduce todos los knobs de Nuke.
Las operaciones plus/multiply/screen/difference actúan también sobre alpha y mezclan
el resultado con B según mix. Los cambios de exposición/gamma del viewer no se exportan.
Trabajar con Premult/Unpremult explícitos al corregir imágenes con alpha.
DilateErode/EdgeBlur alteran alpha; no reconstruyen automáticamente colores de borde.
Regrain añade al RGB el residual (Plate − Clean) multiplicado por amount.

## Animación y roto

El diamante de cada parámetro numérico abre curvas y tabla de claves. Soporta constant,
linear, smooth y Bézier mediante pendientes de entrada/salida. Editar un parámetro
que ya tiene curva crea/reemplaza una clave en el cuadro actual. El dope sheet lista
los frames y permite abrir el editor con doble clic. No incluye todavía manipulación
gráfica de tangentes de curvas ni editor de expresiones.

Roto: seleccionar points → Usar herramientas del Viewer. Click agrega un punto;
arrastrar mueve; Shift+arrastrar genera tangentes simétricas. Escape termina la edición.
Las coordenadas son normalizadas con origen inferior izquierdo. Cada nodo mantiene una lista de capas cerradas; Nueva capa Bezier y el selector
permiten editar cada una, con operaci?n max/add/subtract/intersect. Tambi?n se pueden
combinar nodos con MaskCombine. Feather e
invert están en propiedades. Keyframe points anima una forma conservando topología.
No hay todavía lista jerárquica de capas, open splines ni motion blur de roto.

## Tracking

Tracker2D analiza uno o dos puntos: traslación, rotación y escala. PlanarTracker
detecta features dentro de cuatro esquinas y estima homografía con RANSAC.
Ambos verifican correspondencias forward/backward y reportan pérdida; no aplican
resultados incompletos como si fueran correctos. No es un camera solver.

En los ejemplos, seleccionar el tracker y pulsar Analizar rango. tracking_path es
el plate analizado, mientras Image puede ser la imagen a mover. reference define
el cuadro de referencia. Se procesa a ambos lados de esa referencia, dentro de
First/Last. El formato del proyecto debe coincidir con el plate. Los avances quedan
en Diagnóstico; se puede cancelar. El análisis exitoso guarda curvas y un informe
de confianza. Si el nodo cambia durante el análisis, el resultado no lo sobrescribe.

Crear Transform / CornerPin genera un nodo editable con claves. Tracker2D ofrece
matchmove y stabilize; PlanarTracker ofrece cornerpin, matchmove y stabilize inverso; también se puede conectar su transformación a una máscara.
Corregir manualmente desde las curvas o volver a elegir puntos/referencia y analizar.
El seguimiento inicial usa ventana/pirámide fijas; no hay aún UI de patrón/búsqueda,
holdout animado, re-detección tras oclusión ni link vivo a un nodo destino.

## EXR, AOVs y Cryptomatte

Read → Inspeccionar EXR muestra pases, nombres de canales, data/display window y
metadata. Usar selección elige el pase/canal; un canal escalar se visualiza en RGB.
Cada Read puede extraer un AOV y se pueden recombinar en el grafo. Los pases nativos
de Blender conservan sockets de profundidad/vector para ZDefocus y VectorBlur.

Cryptomatte: elegir EXR, inspeccionar y seleccionar capa/objeto del manifest. La
extracción la ejecuta el compositor de Blender. El selector usa nombres del manifest;
no hay picker interactivo sobre el viewer. Exportar una máscara requiere conectarla
a Write o utilizarla en una composición.

Write exporta RGBA EXR float32 por defecto. Para conservar AOVs y metadata originales,
definir preserve_exr con la secuencia fuente y output_layer con el nombre de la capa
a reemplazar; vacío reemplaza R/G/B/A raíz. Se conservan los demás canales y el
dataWindow. El formato render debe coincidir con displayWindow. No usar esta opción
como una transformación implícita de todos los AOVs: solo reemplaza la capa indicada.

El puente adicional admite EXR flat de una parte, sin subsampling ni overscan fuera
de displayWindow. Rechaza formatos no cubiertos expresamente. Deep, multipart genérico,
propagación automática de todos los canales por cada nodo y color por canal arbitrario
siguen pendientes. Los canales de datos no deben recibir transforms de color.

## Límites de esta entrega

Los controles y nodos están implementados y se prueban con fixtures; la aprobación
de chroma/roto/tracking en tomas reales y la instalación en una segunda máquina limpia
siguen siendo criterios pendientes. El viewer B sigue siendo snapshot; proxy reduce
la salida, no todo el cálculo. No incluye S9 (3D), deep, OFX ni importación completa .nk.
Una configuración OCIO externa y sus LUTs deben acompañar al proyecto al trasladarlo.

## Build reproducible

Crear .buildenv con Python 3.12 y requirements-build.txt. El worker utiliza el Python
3.11 incluido en Blender; instalar requirements-worker.txt en desktop/vendor con
pip --target, --no-deps y wheels win_amd64 para CPython 3.11. No instalar esas ruedas
en el Python global ni dentro del motor del usuario. Ejecutar Build-Nukify.ps1 o sus
comandos equivalentes; ISCC está configurado en .tools/inno. El resultado queda en
releases/0.5.0, separado de versiones anteriores.

QA: unittest en tests/test_*.py; tests/live_integration.py, tests/live_window.py,
tests/ui_tracking.py; Blender ejecuta tests/blender_nodes.py y tests/blender_exr.py;
el Python incluido ejecuta tests/exr_roundtrip.py. Nukify.exe --self-test RUTA_JSON
prueba actualización automática, playback, guardado y dos cuadros EXR en un temporal.
