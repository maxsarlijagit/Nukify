# Nukify Desktop 0.2

## Abrir y probar

Ejecutable: `F:\Proyectos\Nukify\dist\Nukify\Nukify.exe`.

Conservar la carpeta `_internal` junto al ejecutable. No hace falta Python para ejecutar este paquete. Blender no se incluye: se utiliza `G:\Blender\4.5\blender.exe` (4.5.14 LTS), configurable en el panel derecho. No usar Blender 5.x con este backend sin adaptar y probar su API.

1. Abrir Nukify.exe. La demo tiene dos imágenes técnicas locales, Color/Exposure, máscara elíptica, Merge y Write.
2. Seleccionar Merge1 y presionar **1** con el foco en el grafo, o usar **Evaluar Viewer** en la barra superior.
3. Seleccionar Color1, modificar Exposure en las propiedades y volver a evaluar Merge1. El Viewer indica cuando hay cambios pendientes.
4. Seleccionar Read1 o Read2 y usar **Abrir imagen** para reemplazar los medios. Para secuencias, escribir una ruta como `D:/shots/plate_####.exr` y elegir Frame.
5. Para conectar nodos, hacer clic en la salida inferior y luego en una entrada superior. También se pueden elegir entradas desde propiedades. Merge usa **A sobre B**; Mask modula Mix.
6. Agregar Blur o Transform desde **+ Nodo / Tab**, conectarlo y evaluar el resultado. **F** encuadra, rueda hace zoom, arrastre mueve nodos, Delete los elimina y Ctrl+Z deshace.
7. **Guardar / Ctrl+S** crea un proyecto `.nukify`; **Abrir / Ctrl+O** lo recupera. Los medios se referencian por ruta; no se copian dentro del proyecto.
8. Configurar Width/Height, First/Last y Output folder. **Exportar EXR** usa el único Write, o el Write seleccionado si hay varios. Cada exportación crea una subcarpeta nueva `render_<id>` para no pisar renders anteriores.

Cada exportación produce `comp_0001.exr`, etc. (RGBA float 32 bits), previews PNG con Standard/sRGB, `composition.blend`, el job JSON y un log. El `.blend` es el grafo compilado del último cuadro; las secuencias las administra Nukify y ese `.blend` contiene las imágenes resueltas del último cuadro. Para reexportar todo el rango, abrir el proyecto `.nukify`.

## Arquitectura actual

La versión 0.2 agrega una **interfaz Qt de escritorio**; no es un cambio en el editor nativo de Blender. Esto permite conexiones verdaderamente verticales y paneles propios sin compilar Blender. El backend ejecuta Blender instalado en un proceso separado y convierte el grafo en nodos nativos del compositor.

La fuente de verdad de esta interfaz es `.nukify` (JSON versionado). `composition.blend` es una salida derivada, no otro proyecto que deba sincronizarse en ambas direcciones. Esta decisión reemplaza la propuesta inicial de usar exclusivamente `.blend`.

El complemento anterior permanece en `nukify/` como experimento independiente. No ejecutarlo para abrir la nueva interfaz; usar el EXE. `Start-Nukify.ps1` se conserva como launcher del complemento original y requiere una política de PowerShell que permita scripts.

## Alcance real

- Evaluación explícita mediante botón o tecla 1; no hay reproducción ni composición interactiva por GPU.
- Read de archivos y patrones ####, exposición, blur, transform, máscara elíptica, alpha over y Write.
- Rango de exportación y selección manual del cuadro para previsualización.
- Deshacer/rehacer del grafo, parámetros y conexiones; guardado y reapertura.
- Visualización Standard/sRGB; no hay selector ACES, canales arbitrarios, deep o compatibilidad `.nk`.
- El shell no incluye todavía un viewport ni edición de escenas 3D. El motor usado es Blender, pero esa integración de interfaz está pendiente.
- Demo técnica sintética. La validación sobre un plano de producción real sigue pendiente.

## Build reproducible

Usar Python 3.12 y un entorno aislado sin paquetes globales:

```powershell
python -m venv .buildenv
.\.buildenv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.buildenv\Scripts\python.exe -m PyInstaller --clean --noconfirm --windowed --onedir --name Nukify --paths desktop --add-data 'desktop/worker.py;desktop' --add-data 'desktop/model.py;desktop' --add-data 'assets;assets' desktop/app.py
```

La primera compilación con el Qt global 6.11.2 produjo un error al cargar QtCore. El build corregido fija PySide6/Shiboken 6.8.3 en `.buildenv` y separa las rutas de DLL al lanzar Blender. No modifica las bibliotecas globales ni la política de scripts de Windows.

## Pruebas

```powershell
python -m unittest discover -s tests -v
python scripts/prepare_test_job.py
& 'G:\Blender\4.5\blender.exe' --background --factory-startup --threads 4 --python-exit-code 1 --python desktop/worker.py -- validation/render/job.json
& 'G:\Blender\4.5\blender.exe' --background --factory-startup --python-exit-code 1 --python tests/verify_render.py
```

Las pruebas del grafo cubren ciclos, tipos de conexión, medios faltantes, secuencias y orden de evaluación. La prueba de integración compone y exporta dos cuadros y comprueba dimensiones, float, color central, fondo y alpha del EXR.
