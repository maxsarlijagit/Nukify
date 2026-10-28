# Nukify 0.3 — Live Viewer

Abrir `releases/0.3.0/Nukify/Nukify.exe` junto con su carpeta `_internal`. Sigue utilizando Blender 4.5 LTS instalado; no necesita Python instalado para ejecutar el paquete.

## Actualización automática

Live está activado al abrir. La demo se compone automáticamente. Los parámetros y conexiones actualizan el nodo asignado al Viewer después de una pausa de 140 ms. Un motor Blender persistente procesa una tarea por vez; si hay cambios mientras procesa, conserva el último pedido. Una respuesta atrasada no reemplaza el cuadro solicitado actualmente.

Seleccionar un nodo no cambia el Viewer: pulsar **1** en el grafo o **Asignar Viewer** para elegir qué salida mirar. Así se puede observar Merge mientras se ajusta Color. **Live OFF** suspende la actualización; el botón de asignación permite una evaluación manual.

## Playback

- Demo incluida: secuencia PNG de 48 cuadros con movimiento real, 24 fps por defecto.
- **Play/Pause**, paso anterior/siguiente, inicio/fin, **Loop**, selector de FPS y slider para scrubbing.
- **Espacio** reproduce/pausa cuando el foco está en el grafo o el canvas del Viewer.
- **First/Last** en el panel derecho definen el rango.
- **Cache range** prepara hasta 1000 cuadros del rango. Cuando falta un cuadro durante playback aparece Buffering; no se simula reproducción de cuadros inexistentes.
- Para medios propios, Read acepta `plate_####.exr` o `plate_####.png`; los números se resuelven según el frame.

La reproducción cacheada apunta al FPS elegido. La primera pasada depende de Blender y del material: actualización automática no significa garantía de 24 fps para cualquier grafo o resolución.

## Controles del Viewer

| Control | Comportamiento |
| --- | --- |
| RGB / R / G / B / A / Y / Matte | Canales, luminancia y overlay de matte; teclas R/G/B/A/Y sobre el canvas alternan el canal y RGB |
| sRGB / Linear | Transformación de visualización aplicada a los datos float |
| Exp / Gamma | Ajustes exclusivamente del Viewer; no modifican los nodos ni el EXR exportado |
| Checker | Fondo de transparencia |
| Fit / 1:1 / rueda | Encuadre y zoom; F encuadra el canvas |
| Arrastrar imagen | Pan |
| RGBA probe | Muestra coordenadas y valores scene-linear bajo el cursor |
| Capturar B | Congela el cuadro actual en un buffer de referencia |
| A / B snapshot / Wipe / Difference | Comparación con la captura B; requiere el mismo formato/proxy |
| Wipe slider | Posición de la separación A/B |
| Proxy Full / 1/2 / 1/4 | Reduce la imagen enviada al Viewer; predeterminado 1/2. El grafo se evalúa a su formato de trabajo y luego se reduce la salida. |
| Reset view | Restablece canales, exposición, gamma y encuadre |

Diseño inspirado en los controles de composición del [Viewer de Nuke](https://learn.foundry.com/nuke/content/reference_guide/image_nodes/viewer.html). No implementa todas sus opciones: no hay selección de AOVs arbitrarios, ACES configurable, deep, ROI de render ni viewport 3D. B es una captura fija, no un segundo grafo animado.

## Caché y motor

El caché usa un hash de los nodos necesarios, parámetros, conexiones, resolución, proxy, frame y fecha/tamaño de los medios. Mover un nodo visualmente no invalida el render. Editar un medio externamente se detecta al solicitar ese cuadro de nuevo.

Datos scene-linear RGBA de 32 bits; las transformaciones del Viewer son locales a Qt/NumPy. Caché de buffers en memoria: 192 MiB; imágenes de visualización: 64 MiB. Caché float en disco se recorta a aproximadamente 1 GiB al terminar tareas (puede superar temporalmente ese límite mientras se prepara un rango).

Exportar detiene el motor interactivo y ejecuta la exportación completa sin aplicar los ajustes del Viewer; después reinicia Live. Al cerrar la app se termina su motor de fondo.

## Identidad

Logo original en `assets/nukify-logo.png`: un nodo naranja sonriente con conectores turquesa, generado con la herramienta integrada de imágenes. Se utiliza en la cabecera, la ventana y el icono del ejecutable. El prompt está en `docs/logo-prompt.md`.

## Build y pruebas

Instalar `requirements-build.txt` en `.buildenv` y usar el comando de `Build-Nukify.ps1` (también puede ejecutarse Python directamente si PowerShell bloquea scripts). El build 0.3 se guarda en una carpeta separada para preservar la versión 0.2 y cualquier sesión abierta.

```powershell
.\.buildenv\Scripts\python.exe -m unittest discover -s tests -v
.\.buildenv\Scripts\python.exe tests/live_integration.py
.\.buildenv\Scripts\python.exe tests/live_window.py
```

`live_integration.py` comprueba un proceso persistente, descarte de pedidos intermedios, cache hit y píxeles de cuadros distintos. `live_window.py` comprueba cambio automático de parámetros sin Evaluar, persistencia de la salida Merge y playback con cuadros cacheados. Son pruebas sobre medios sintéticos; no validan rendimiento de planos de producción.
