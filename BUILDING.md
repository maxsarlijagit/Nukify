# Desarrollo y compilación (Windows x64 y macOS Apple Silicon)

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
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Build-Nukify.ps1 -BlenderDirectory $blenderDirectory -InnoCompiler 'C:/Program Files (x86)/Inno Setup 6/ISCC.exe'
```

El comando permite ejecutar este script local en ese proceso de PowerShell, sin modificar la política persistente del sistema. El script hace un build limpio, descarga fuentes originales de Blender/Qt/PySide, copia avisos, incluye un ZIP del código propio y genera el instalador. `packaging/release.json` fija versión y SHA256 del Blender probado; una compilación diferente se rechaza explícitamente.

Los archivos salen en `releases/<version>/`. Mantener el directorio portable completo. No alcanza con copiar únicamente `Nukify.exe`.

Validar el ejecutable con `--advanced-test`, `--workflow-test`, `--sprints-test`, `--self-test` y `--genai-test`, cada uno seguido de una ruta JSON absoluta. La prueba GENAI es local, con un fixture sintético y red bloqueada; no valida inferencia paga. Ejemplo:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
& .\releases\0.10.0\Nukify\Nukify.exe --self-test "$PWD/validation/regression.json"
```

Las DLL de Qt/PySide son dinámicas y están en `_internal/`. Los archivos de fuente incluidos permiten modificar/recompilar esos componentes; Nukify no impone verificaciones criptográficas sobre reemplazos de Qt. Consultar los README de cada archivo upstream para sus toolchains y opciones de compilación.

## macOS Apple Silicon

Compilar nativamente en macOS 14+ con Python 3.12 arm64. No mezclar ruedas Windows con `desktop/vendor`: usar un checkout limpio o un directorio vendor exclusivo de esta plataforma.

```sh
python3.12 -m venv .buildenv
.buildenv/bin/python -m pip install -r requirements-build.txt
.buildenv/bin/python -m pip install --target desktop/vendor --only-binary=:all: --platform macosx_14_0_arm64 --python-version 311 --implementation cp --abi cp311 --no-deps -r requirements-worker.txt
# Para pruebas directas desde Python de UI:
.buildenv/bin/python -m pip install -r requirements-worker.txt
export NUKIFY_BLENDER='/Applications/Blender.app/Contents/MacOS/Blender'
QT_QPA_PLATFORM=offscreen .buildenv/bin/python -m unittest discover -s tests -p 'test_*.py'
QT_QPA_PLATFORM=offscreen .buildenv/bin/python tests/ui_layout_090.py
"$NUKIFY_BLENDER" --background --factory-startup --threads 4 --python-exit-code 1 --python tests/blender_nodes.py
```

Descargar el DMG oficial indicado en `packaging/macos.json` y verificar su SHA256 contra el archivo `.sha256` de Blender. Commitear los cambios antes de compilar; el script rechaza un árbol sucio para que el commit registrado corresponda a las fuentes distribuidas.

```sh
.buildenv/bin/python scripts/build_macos.py --blender-dmg /ruta/blender-4.5.14-macos-arm64.dmg
```

Genera `releases/0.11.2/macOS-arm64/Nukify.app`, un DMG con enlace a Aplicaciones, un ZIP y `SHA256SUMS-macOS-arm64.txt`. Incluye Blender, fuentes upstream/originales, fuentes de Nukify, avisos y manifiesto. El motor se copia sin alterar su estructura dentro de `Contents/Resources/engine/Blender.app`. El puente EXR usa el Python 3.11 privado de Blender en otro proceso.

El paquete usa firma ad-hoc: no sustituye Developer ID ni notarización. Para distribución notarizada se necesita la identidad y cuenta Apple del mantenedor. No hay compilación Intel validada.

Ejecutar las cinco suites del binario y la prueba de actualizaciones, cada una con ruta JSON absoluta:

```sh
QT_QPA_PLATFORM=offscreen releases/0.11.2/macOS-arm64/Nukify.app/Contents/MacOS/Nukify --self-test "$PWD/validation/mac-self-test.json"
# Repetir con --advanced-test, --workflow-test, --sprints-test, --genai-test y --updates-test.
codesign --verify --deep --strict releases/0.11.2/macOS-arm64/Nukify.app
hdiutil verify releases/0.11.2/macOS-arm64/Nukify-0.11.2-macOS-arm64.dmg
```

Antes de publicar, montar el DMG, copiar la app a un directorio temporal y repetir una suite desde esa copia. Conservar resultados en un archivo de validación junto a los binarios; no confundir esto con instalación validada en otra Mac limpia.
