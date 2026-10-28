# Nukify 0.9 — interfaz adaptable

Se mantiene el motor y los proyectos de 0.8. Esta entrega reorganiza la interfaz de composición con conceptos de editores compactos de Blender y una identidad propia.

- Tema gris neutro, acento cálido para acciones principales y foco, azul para estados activos.
- Iconos vectoriales propios para archivos, viewer, transporte, herramientas, categorías y keyframes. Se dibujan a la resolución de Qt; no dependen de emojis ni fuentes de iconos.
- Barras de herramientas que pasan a otra fila al reducir el ancho. Paleta de categorías con scroll vertical para acceder a todos los nodos en pantallas bajas.
- Inspector con pestañas Nodo / Proyecto. La segunda contiene formato, rango, carpeta de salida, diagnóstico y cancelación del proceso. Buscar parámetro filtra los controles del nodo; la cruz limpia el filtro.
- Botones de reset y keyframes compactos con tooltips. Los keyframes existentes se resaltan en dorado. Los controles activados, deshabilitados y con foco tienen estados diferenciados.
- Graph con grilla de puntos, nodos de esquinas suaves, franja de categoría y contorno de selección.
- Menú Espacio: Composición, Viewer amplio, Nodos amplios. Guardar distribución conserva las proporciones de los paneles para la siguiente apertura. No cambia el proyecto ni sus renders. El archivo de preferencias es `%LOCALAPPDATA%/Nukify/workspace.json`.

## Validación

Pruebas con la interfaz Qt real a 1440×940, 1280×800 y 1024×768, incluyendo escalado Qt de 150%, con una composición renderizada. Pruebas de búsqueda/limpieza, guardar/restaurar distribución e iconos en varios tamaños. Se conservan las regresiones de composición, roto, tracking, A/B y exportación.

El escalado al 150% se verificó con QT_SCALE_FACTOR; falta una sesión física con cambio de monitor/DPI. El wrapping mantiene los comandos accesibles pero aumenta la altura ocupada por las barras en ventanas angostas; usar Viewer amplio cuando el plano requiera más área.

No incluye docking libre ni persistencia de ventanas independientes. La navegación sigue usando los atajos configurados y la distribución viewer arriba / nodos abajo / propiedades a la derecha.

Funciones anteriores: [guía 0.8](desktop-0.8.md).
