# Instrucciones compartidas de trabajo

## Antes de editar

1. Confirmá carpeta, rama y estado con `Get-Location`, `git branch --show-current` y `git status --short`.
2. Leé el issue o pedido, [CONTRIBUTING.md](../CONTRIBUTING.md) y las instrucciones aplicables. Si hay cambios ajenos, preservalos; no hagas reset, limpieza o sobrescrituras para empezar.
3. Ubicá el comportamiento actual y sus pruebas. Usá búsquedas acotadas; evitá recorrer dependencias y renders generados.
4. Escribí un alcance breve con criterios verificables. Preguntá si falta una decisión que impida avanzar; resolvé detalles reversibles dentro de ese alcance.

## Mapa del proyecto

| Área | Puntos de entrada |
| --- | --- |
| Ventana, inspector y tema | `desktop/app.py`, `desktop/ui_theme.py` |
| Graph y catálogo de nodos | `desktop/model.py`, `desktop/registry.py`, `desktop/graph_tools.py` |
| Construcción y ejecución Blender | `desktop/builder.py`, `desktop/worker.py`, `desktop/runtime.py` |
| Viewer, actualización y cache | `desktop/viewer.py`, `desktop/live_engine.py`, `desktop/live_ui.py` |
| Animación, roto y tracking | `desktop/animation.py`, `desktop/expressions.py`, `desktop/roto.py`, `desktop/tracking.py` y sus UI |
| EXR y entrega | `desktop/exr_io.py`, `desktop/exr_bridge.py`, `desktop/delivery.py` |
| Pruebas y distribución | `tests/`, `scripts/`, `packaging/`, `.github/workflows/tests.yml` |

`nukify/` conserva el prototipo de addon de Blender; no lo confundas con la aplicación de escritorio actual. Este mapa orienta la búsqueda: verificá el código vigente antes de asumir responsabilidades exactas.

## Reglas de implementación

- La UI usa Python 3.12 y PySide6. El worker usa el Python 3.11 de Blender. Conservá esa separación y el aislamiento del puente EXR; no mezcles DLL o paquetes de ambos entornos.
- Desde fuentes, configurá Blender con `NUKIFY_BLENDER` según [BUILDING.md](../BUILDING.md). El ejecutable distribuido debe resolver su motor incluido. No agregues rutas personales absolutas al código.
- Ejecutá Blender en un proceso de trabajo independiente. No dependas de una sesión interactiva abierta ni cierres aplicaciones del usuario para hacer pruebas.
- Preservá compatibilidad de proyectos guardados. Si un cambio necesita migración, documentala y comprobá la carga de un proyecto anterior.
- En nodos, revisá entradas, tipos, conexiones, valores por defecto y errores; no confundas que un nodo aparezca en el catálogo con que su render funcione.
- En UI, seguí [el sistema de diseño](../docs/design-system.md): claridad de estados, tooltips, atajos y escalabilidad. Revisá foco y conflictos de teclado.
- Mantené las operaciones costosas fuera de la interacción de UI y verificá invalidación de cache cuando cambien parámetros o medios.
- Usá fixtures propios o redistribuibles. Conservá autoría, GPL-3.0-or-later y avisos de dependencias. No subas medios de clientes, secretos ni archivos `.env`.
- Evitá refactors ajenos al problema. Cambios de dependencias, builds públicos y releases requieren estar dentro del encargo.

## Validación proporcional

| Cambio | Evidencia esperada |
| --- | --- |
| Documentación | Diff, enlaces relativos válidos y comandos contrastados con el repositorio. No exige recompilar. |
| Lógica o graph | Pruebas relevantes y regresión para el comportamiento corregido; incluir casos inválidos si aplica. |
| UI o atajos | Pruebas Qt relevantes y revisión visual a 1024 y 1440 px; comprobar escalado y foco. |
| Nodos, imagen o EXR | Render real con Blender sobre fixture controlado y comprobación de píxeles/canales; no alcanza con mocks. |
| Viewer o playback | Cambiar parámetros, comprobar actualización e invalidación, recorrer frames y distinguir cache de cálculo real. |
| Empaquetado | Ejecutable con motor incluido y suites documentadas en BUILDING; verificar fuentes, avisos y manifiesto. |

Comandos base, desde la raíz y con el entorno ya preparado:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.buildenv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
.\.buildenv\Scripts\python.exe tests/ui_layout_090.py
# Solo si corresponde probar nodos y NUKIFY_BLENDER está configurado:
& $env:NUKIFY_BLENDER --background --factory-startup --threads 4 --python-exit-code 1 --python tests/blender_nodes.py
```

Para una revisión visual interactiva, quitá el modo offscreen de esa terminal con `Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue` antes de abrir la app. Consultá [BUILDING.md](../BUILDING.md) para preparación y pruebas del binario.

No instales dependencias ni ejecutes builds pesados solo por un cambio de texto. Informá pruebas omitidas y la razón; CI sin Blender no demuestra render, OCIO ni una instalación en otra PC. No afirmes calidad de producción con fixtures sintéticos.

## Entrega e integración

Revisá `git diff --check` y el diff completo. Agregá al índice solo los archivos de la tarea; antes de publicar ejecutá `scripts/audit_publication.py` con el Python del entorno. Este chequeo detecta algunos patrones y archivos indebidos, pero no reemplaza revisar el contenido.

El PR debe explicar problema, comportamiento resultante, validación ejecutada y límites. Adjuntá capturas reales si cambia la UI. No mezcles el cambio con actualizaciones de versión o binarios salvo que sea una tarea de release. No uses force push ni reemplaces tags/releases existentes para corregir una contribución.
