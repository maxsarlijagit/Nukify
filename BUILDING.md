# Desarrollo y compilación (Windows x64)

## Requisitos

- Python 3.12 x64 para la interfaz; build probado con 3.12.10.
- Git, Blender **4.5.14 LTS**, Inno Setup 6.
- Qt/Python y dependencias fijadas en los archivos requirements.
- El worker usa Python 3.11 incluido en Blender. OpenEXR se carga en un proceso separado para evitar conflictos de DLL con Blender.

```powershell
git clone https://github.com/maxsarlijagit/Nukify.git
cd Nukify
py -3.12 -m venv .buildenv
.\.buildenv\Scripts\python.exe -m pip install -r requirements-build.txt

# Ajustar a la carpeta de Blender extraída en esta máquina.
$blenderDirectory = 'C:/Tools/Blender-4.5.14'
$env:NUKIFY_BLENDER = "$blenderDirectory/blender.exe"

# Descargar ruedas para el Python 3.11 del worker; no instala otra copia de NumPy.
.\.buildenv\Scripts\python.exe -m pip install --target desktop/vendor --only-binary=:all: --platform win_amd64 --python-version 311 --implementation cp --abi cp311 --no-deps -r requirements-worker.txt

.\.buildenv\Scripts\python.exe desktop/app.py
```

`desktop/vendor/` no se versiona. El ejecutable empaquetado siempre usa `engine/blender.exe`; `NUKIFY_BLENDER` solo configura la ejecución desde fuentes.

## Pruebas

```powershell
.\.buildenv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
.\.buildenv\Scripts\python.exe tests/ui_layout_090.py
& $env:NUKIFY_BLENDER --background --factory-startup --threads 4 --python-exit-code 1 --python tests/blender_nodes.py
```

La prueba OCIO requiere el config de Blender. Las pruebas de UI se ejecutan offscreen; el directorio `validation/` se crea localmente y no se publica en Git.

## Release

```powershell
New-Item -ItemType Directory -Force validation | Out-Null
# Commitear los archivos de fuente antes de compilar: el paquete registra el commit.
.\Build-Nukify.ps1 -BlenderDirectory $blenderDirectory -InnoCompiler 'C:/Program Files (x86)/Inno Setup 6/ISCC.exe'
```

El script hace un build limpio, descarga fuentes originales de Blender/Qt/PySide, copia avisos, incluye un ZIP del código propio y genera el instalador. `packaging/release.json` fija versión y SHA256 del Blender probado; una compilación diferente se rechaza explícitamente.

Los archivos salen en `releases/<version>/`. Mantener el directorio portable completo. No alcanza con copiar únicamente `Nukify.exe`.

Validar el ejecutable con `--advanced-test`, `--workflow-test`, `--sprints-test` y `--self-test`, cada uno seguido de una ruta JSON absoluta. Ejemplo:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
& .\releases\0.9.2\Nukify\Nukify.exe --self-test "$PWD/validation/regression.json"
```

Las DLL de Qt/PySide son dinámicas y están en `_internal/`. Los archivos de fuente incluidos permiten modificar/recompilar esos componentes; Nukify no impone verificaciones criptográficas sobre reemplazos de Qt. Consultar los README de cada archivo upstream para sus toolchains y opciones de compilación.
