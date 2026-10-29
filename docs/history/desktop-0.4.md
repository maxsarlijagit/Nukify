# Nukify 0.4.0 — instalación independiente

Ejecutar Nukify-Setup-0.4.0.exe. Instala para el usuario actual, sin administrador,
con acceso en Inicio y desinstalador. No necesita instalar Python ni Blender.
Incluye el motor Blender 4.5.14 LTS ya compilado (build 62c1db4208e8).
El motor se ejecuta en segundo plano desde engine/blender.exe, dentro de Nukify.
No usa ni modifica otras instalaciones de Blender. El instalador no descarga componentes.

Viewer arriba, nodos con conexiones verticales abajo y propiedades a la derecha.
Seleccionar Color1 y cambiar Exposure actualiza el viewer automáticamente con Live activo.
1 asigna el nodo seleccionado al viewer. Cache range prepara la secuencia demo de 48 cuadros;
Play o espacio reproduce. La velocidad sin cache depende de la composición y del equipo.
La barra incluye canales, exposición/gamma de visualización, sRGB/linear, zoom, proxy,
captura B, wipe y diferencia. La captura B es una imagen fija, no una segunda rama animada.

PROJECT contiene ancho/alto, First/Last y destino de exportación. Diagnostico muestra
el registro. Export EXR procesa el rango con el mismo motor incluido.
Los proyectos se guardan con Ctrl+S y se abren con Ctrl+O. Las imágenes externas se
referencian por ruta: trasladar un proyecto requiere trasladar/revincular sus medios.

Es un compositor en desarrollo con un subconjunto de nodos y controles inspirados en Nuke.
El proxy reduce la salida del viewer; actualmente el grafo se calcula a resolución completa.
No representa equivalencia completa con Nuke. Ver desktop-0.3.md en las fuentes para detalles.

Fuentes de Nukify y Blender incluidas en sources/. Licencia de Nukify: GPL-3.0-or-later.
Las licencias originales del motor están en engine/license/. THIRD_PARTY.md lista dependencias.
El desinstalador conserva proyectos, renders y cache del usuario fuera de la carpeta de instalación.
