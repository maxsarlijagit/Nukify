# Validación local 0.2 — 2026-10-27

- Sistema: Windows x64, Python de build 3.12.10.
- Runtime empaquetado: PySide6 Essentials/Shiboken 6.8.3.
- Motor externo: Blender 4.5.14 LTS, hash de build 62c1db4208e8.
- Blender.exe: firma Authenticode válida; SHA256 `362074A47FE6AC821A776B5B75D22DBF5157D47F676B65C7632CFBE2AAF3EB9D`.
- Nukify.exe: build local sin firma; SHA256 `B39742B7567BEC7A91DA27CBD3A6959E30CA98B7F3E4824C4FA0D2294F4F228F`.

## Ejecutado y observado

1. Cinco pruebas de grafo aprobadas: ciclos, tipos, medios faltantes, secuencias y orden.
2. Render en Blender de dos cuadros EXR RGBA float, 960×540. Verificación de color y alpha mediante lectura de píxeles en Blender.
3. Apertura real de `dist/Nukify/Nukify.exe`. Viewer arriba, propiedades a la derecha y grafo vertical abajo inspeccionados en pantalla.
4. Evaluar Viewer desde el botón del EXE: Blender ejecutado y resultado visible.
5. Exportar EXR desde el EXE: archivos persistidos en `C:\Users\user\Documents\Nukify Renders\render_8781dd0ca3da`.
6. Seleccionar Color1 y cambiar Exposure a 0.5 desde propiedades.
7. Guardar `validation/desktop-workflow.nukify`, abrirlo nuevamente y verificar Exposure=0.5 en la interfaz.
8. Reexportar desde ese proyecto reabierto: `C:\Users\user\Documents\Nukify Renders\render_099aaf989b1b`.

## Incidencia resuelta

El primer EXE con Qt global 6.11.2 falló al importar QtCore. Se reconstruyó en un venv sin paquetes globales, fijando Qt 6.8.3. El EXE corregido pasó apertura y ejecución real del motor Blender. No se modificó la política de ejecución de PowerShell.

## Límites

Prueba local con medios sintéticos, no un plano de producción ni un segundo equipo limpio. No se verificaron ACES, canales EXR arbitrarios, deep, playback o un viewport 3D integrado. Las conexiones verticales pertenecen a la interfaz Qt; Blender conserva su editor nativo.
