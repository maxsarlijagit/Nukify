# Nukify 0.6 — integración 3D y entrega

Versión funcional de los mecanismos S9–S11. Los criterios de beta con tres planos
reales y una segunda máquina siguen pendientes. Incluye Blender 4.5.14 LTS privado.

## Probar 3D

Proyecto → Ejemplos → Integracion 3D carga un cubo animado sobre un plate sintético.
La categoría 3D incluye Camera, Card, Geometry (cube/sphere/plane), Light, Project3D,
Scene y RenderLayers. Object y Object2 aceptan geometría; Camera y Scene tienen
conexiones tipadas. Scene admite dos objetos y una luz de área opcional.

Camera mira por su eje local -Z con Y arriba. Posiciones son unidades Blender;
rx/ry/rz son grados, lens milímetros. Light apunta inicialmente al origen y sus
rotaciones se aplican como ajustes sobre esa orientación. Card se encuentra en XY.
RenderLayers devuelve Image/Alpha/Depth/Normal y permite ajustar muestras Cycles CPU.
La escena se reconstruye con los parámetros y curvas de cada cuadro del proyecto.

Project3D conecta Object y Camera; texture_path proyecta una imagen mediante UV
Project. La cámara de proyección puede ser distinta de la cámara de render.
Las rutas de texturas son archivos individuales, no secuencias en esta versión.

Proyecto → Inspeccionar 3D en Blender genera una copia .blend con texturas empacadas
y abre el viewport de Blender incluido. Es una inspección externa: editar esa copia
no devuelve cambios al grafo. El proyecto .nukify conserva escena y cámara mediante
los nodos; composition.blend es una instantánea del último cuadro renderizado.
No incluye importación de geometría arbitraria, camera solve, calibración ni lens distortion.

## Comparación y cache

1 asigna la selección a A; 2 la asigna a B. Elegir B, Wipe o Difference en el viewer.
Ambas ramas se evalúan para el mismo cuadro antes de mostrar la comparación; B
puede ser otra salida animada. Proyecto → Desconectar B vuelve a un solo worker.
Capturar B mantiene la referencia fija cuando no hay una rama B conectada.

Hay como máximo dos workers persistentes de composición, uno por rama. El cache
usa parámetros, dependencias, cuadro, formato, proxy y cambios de medios. Proyecto
→ Presupuesto cache configura el total de disco A+B y lo guarda por usuario.
Las imágenes en memoria del viewer tienen límites independientes (192 MiB float y
64 MiB display, más los cuadros activos A/B). Un cuadro 4K float RGBA ocupa 126.6 MiB.
El proxy sigue reduciendo la salida: no promete acelerar todos los nodos internos.
ROI de evaluación y cache intermedio por nodo no están implementados.

## Render queue y reanudación

Proyecto → Render queue → Agregar proyecto actual toma una copia de parámetros,
conexiones y rango. Elegir Write si hay más de uno, y configurar Output. La cola
persiste por usuario. Iniciar / reanudar procesa los trabajos secuencialmente.
Cancelar conserva el trabajo pendiente; un fallo detiene la cola para revisarlo.

Cada trabajo tiene su carpeta con job.json, progress.json, EXR, previews y recibos
SHA256 por cuadro. Los archivos se renderizan en staging y se publican después de
terminar el cuadro. Proyecto → Reanudar render permite elegir job.json tras un cierre.
Solo se omiten cuadros con firma de parámetros/medios y hashes válidos. Un archivo
incompleto o alterado se vuelve a renderizar. No editar medios durante un render.
Se verifica espacio disponible antes de cada cuadro; la estimación no garantiza el
tamaño de un EXR multicapa arbitrario. La cola funciona en una instancia a la vez;
no es un gestor distribuido ni incluye bloqueo entre múltiples instancias.

## Proyecto portable

Proyecto → Recopilar proyecto y medios crea una carpeta nueva con project.nukify,
medios, rutas relativas y manifiesto SHA256. Incluye imágenes, secuencias, texturas,
fuentes de tracking y EXR conservados. Copiar la carpeta completa y abrir el proyecto
resuelve sus medios en la nueva ubicación. Output queda vacío para elegir destino.
Se recopilan todos los cuadros del patrón de secuencia. Las configuraciones OCIO
personalizadas se rechazan explícitamente porque pueden depender de LUTs y variables
externas: todavía requieren recopilación manual. No se afirma portabilidad de ellas.

## Validación

Pruebas de imagen 3D, proyección y pases; comparación A/B en cuadros consecutivos;
exportación con corrupción controlada y reanudación; cola de dos trabajos y render
desde medios reubicados. Además se repite la regresión de composición, tracking,
Cryptomatte y playback de 0.5. Los informes están en validation y en la entrega.

Benchmark sintético Constant → Grade → Blur, CPU cuatro hilos: tres mediciones por
formato con salida float completa. HD: 280–354 ms; 4K: 1473–1765 ms en este equipo.
Son tiempos de evaluación del fixture, no fps de playback ni rendimiento de un plano real.

Pendiente de aceptación: tres planos reales (chroma, reemplazo de pantalla, CG),
revisión de artista, memoria sostenida en planos largos y QA en Windows limpio.
Las funciones previas y sus límites se detallan en docs/history/desktop-0.5.md del código fuente.
