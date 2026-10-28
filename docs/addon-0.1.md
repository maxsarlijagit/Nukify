# Nukify

Compositor open source basado en Blender, orientado a artistas que trabajan con grafos de composición y escenas 3D. Identidad propia, con workflows familiares para usuarios de Nuke.

## Estado: prototipo 0.1

Este repositorio contiene un complemento real para **Blender 4.5 LTS**, no un fork completo ni un reemplazo de Nuke. Usa el compositor nativo y guarda proyectos `.blend`. La interfaz sigue siendo la de Blender con un espacio y herramientas específicos.

Implementado:

- Espacio Nukify que duplica el espacio actual, configura el área principal como compositor y reutiliza el Outliner como editor de imagen cuando está disponible.
- Panel Nukify y menú de creación de nodos dentro de Shift+A.
- Read, Merge (Alpha Over), Color Balance, Blur, Transform, Keyer, Mask, Render Layers y Write.
- Tecla `1` para conectar la salida RGBA del nodo activo al Viewer, dentro del compositor.
- Cadena inicial Read → Color Balance → Viewer; conserva los nodos existentes. Si existe un Viewer, redirige su entrada.
- Write configurado para EXR de 32 bits en `//renders/`; requiere conectar entrada, revisar ruta y ejecutar render manualmente.

Los nombres Read, Merge y Write son etiquetas de workflow. No implican equivalencia matemática ni compatibilidad con scripts `.nk`. Color Balance no implementa Grade de Nuke.

## Abrir una sesión aislada

Desde PowerShell:

```powershell
cd F:\Proyectos\Nukify
.\Start-Nukify.ps1
```

Para otra instalación:

```powershell
.\Start-Nukify.ps1 -BlenderPath 'C:\ruta\blender.exe'
```

El launcher abre una sesión nueva con preferencias de fábrica y carga el complemento en memoria. No instala archivos en el perfil del usuario ni guarda sus preferencias. Cerrá esa sesión cuando termines. La apertura visual del espacio todavía requiere validación interactiva.

1. En el nodo Read, elegí una imagen con Open.
2. Ajustá Color Balance y seleccioná el nodo que quieras ver.
3. Presioná `1` o usá «Ver nodo seleccionado» en la pestaña Nukify de la barra lateral.
4. Usá el backdrop del compositor. Si usás el editor de imagen, seleccioná `Viewer Node` cuando esté disponible.
5. Agregá Render Layers para incorporar el render de la escena 3D; Blender mantiene sus herramientas de cámaras, geometría, materiales y luces.
6. Guardá el proyecto como `.blend`. Para volver a disponer de las herramientas Nukify, abrilo desde una sesión iniciada con el launcher.

## Verificación

```powershell
& 'G:\Blender\4.5\blender.exe' --background --factory-startup --python-exit-code 1 --python scripts\smoke.py
```

Validado en Blender 4.5.14 LTS: registro y desregistro, creación de los nueve tipos de nodo, preservación de nodos existentes, conexión al Viewer y configuración EXR. No se validaron todavía layout interactivo, render de imágenes, reproducción, resultados de color ni rendimiento con planos reales. No se declara soporte para Blender 5.x.

## Diseño y siguientes entregas

Ver [arquitectura y alcance](docs/architecture.md).

Código original de este repositorio bajo GPL-3.0-or-later (declaración SPDX). Antes de distribuir un paquete público, incluir el texto completo de la licencia y los avisos de las dependencias que se empaqueten. No se incluye Blender ni código, recursos gráficos o marcas de Foundry/Nuke.
