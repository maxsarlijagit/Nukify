# Componentes externos y fuentes

El código propio de Nukify es GPL-3.0-or-later. Los componentes siguientes se distribuyen sin modificaciones, bajo sus licencias originales. El nombre del autor de Nukify no sustituye la autoría de estas bibliotecas.

| Componente | Versión de esta release | Licencia / avisos | Fuente |
| --- | --- | --- | --- |
| Blender | 4.5.14 LTS, build 62c1db4208e8 | GPL-3.0-or-later; componentes internos con avisos propios en engine/license | https://download.blender.org/source/blender-4.5.14.tar.xz |
| Qt Core, GUI, Network, Widgets (qtbase) | 6.8.3 | LGPL-3.0 / GPL según módulo; ver LICENSES y avisos incluidos | https://download.qt.io/archive/qt/6.8/6.8.3/submodules/qtbase-everywhere-src-6.8.3.tar.xz |
| Qt SVG | 6.8.3 | LGPL-3.0 / GPL; avisos incluidos | https://download.qt.io/archive/qt/6.8/6.8.3/submodules/qtsvg-everywhere-src-6.8.3.tar.xz |
| PySide6 Essentials / Shiboken | 6.8.3 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.8.3-src/pyside-setup-everywhere-src-6.8.3.tar.xz |
| CPython (interfaz) | 3.12.10 | PSF y avisos históricos; LICENSE.txt copiado | https://www.python.org/downloads/release/python-31210/ |
| NumPy | 2.2.6 | BSD-3-Clause y avisos de BLAS incluidos en la rueda | https://github.com/numpy/numpy/tree/v2.2.6 |
| Pillow | 11.3.0 | HPND y avisos de bibliotecas incluidas | https://github.com/python-pillow/Pillow/tree/11.3.0 |
| OpenCV Python headless | 4.11.0.86 | Apache-2.0 y LICENSE-3RD-PARTY.txt | https://github.com/opencv/opencv/tree/4.11.0 |
| OpenEXR Python | 3.3.5 | BSD-3-Clause | https://github.com/AcademySoftwareFoundation/openexr/tree/v3.3.5 |
| OpenColorIO Python | 2.4.2 | BSD-3-Clause | https://github.com/AcademySoftwareFoundation/OpenColorIO/tree/v2.4.2 |
| PyInstaller / bootloader | 6.22.3 | GPL con excepción del bootloader | https://pyinstaller.org/en/stable/license.html |

## Contenido del instalador

- `sources/`: archivos fuente originales de Blender, qtbase, qtsvg y PySide/Shiboken, más el código de Nukify correspondiente a la release.
- `sources/upstream-sources.json`: URL original y SHA256 de cada archivo fuente.
- `licenses/upstream/`: copias de textos de licencia y avisos extraídos de los archivos de Qt/PySide, incluidos los textos LGPL/GPL.
- `licenses/`: avisos de distribuciones Python del entorno de build y del worker, licencia CPython e inventario `python-components.json`.
- `engine/license/`: inventario y avisos originales de Blender y sus dependencias, incluido su Python y bibliotecas nativas.
- `_internal/desktop/vendor/cv2/`: avisos adicionales de OpenCV distribuidos por su rueda.

El inventario Python incluye herramientas de build; no afirma que todas se carguen en ejecución. Los archivos con licencias comerciales de Qt preservados en fuentes upstream no implican que Nukify se distribuya con una licencia comercial: se usa la distribución open source. Referencia oficial: https://doc.qt.io/qtforpython-6/licenses.html.

Qt/PySide se enlazan dinámicamente. Las DLL permanecen separadas dentro de `_internal/`, pueden reemplazarse por compilaciones compatibles y no hay restricción propia contra su modificación o depuración. Las instrucciones para reconstruir Nukify están en BUILDING.md; los archivos upstream conservan sus instrucciones originales.

Las fuentes originales también se publican junto al instalador como `Nukify-0.9.2-upstream-sources.zip`, para descargarlas sin instalar la aplicación. Las licencias originales completas prevalecen sobre este índice.
