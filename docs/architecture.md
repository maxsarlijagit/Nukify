# Arquitectura propuesta

> Documento inicial 0.1. La implementación Desktop 0.2 utiliza un shell Qt con grafo vertical y `.nukify` como fuente de verdad, compilado a nodos Blender. Ver [estado actual](desktop-0.2.md). La etapa de fork nativo no se ejecutó.

## Objetivo de producto

Abrir un plano, componer por nodos, integrar una escena 3D, revisar el resultado y exportar una secuencia desde una aplicación centrada en composición. Nukify tendrá identidad propia. La referencia a Nuke describe hábitos de trabajo y expectativas, no una promesa de clonación exacta.

## Decisión inicial

Validar los workflows mediante un complemento sobre Blender 4.5 LTS. Mantener las operaciones de imagen en el compositor nativo y la escena 3D en Blender evita construir un motor paralelo. Fijar esta versión para las primeras pruebas; migrar sólo con pruebas de API y de resultados de imagen.

Separar tres capas:

| Capa | Responsabilidad | Estado |
| --- | --- | --- |
| Herramientas Nukify, Python | Espacio, menús, atajos, presets y validación del proyecto | Prototipo inicial |
| Blender nativo | Grafo, evaluación de imagen, escenas, render, persistencia y gestión de color | Motor utilizado; cobertura por validar |
| Cambios de fuente Blender, C/C++ | Geometría visual del grafo, conexiones verticales, Viewer especializado y cambios profundos de evaluación | No implementado |

Un addon permite experimentar con controles y distribución de paneles. Una interfaz con nodos compactos, conectores superiores/inferiores y navegación idéntica al objetivo requiere evaluar cambios en el editor nativo. No asumir que Python puede reemplazar todo el editor o inyectar cualquier operación de imagen en su evaluador.

## Experiencia objetivo

- Viewer grande arriba a la izquierda, propiedades del nodo a la derecha, grafo abajo y timeline accesible.
- Acceso rápido a un espacio 3D para cámaras, geometría y proyecciones.
- Creación por búsqueda, conexión al Viewer con `1`, desconexión, bypass y organización del grafo.
- Flujo vertical, colores por categoría, etiquetas legibles, backdrops y grupos.
- Viewer con canales, zoom, exposición de visualización, pixel probe, región de interés y comparación A/B.

La distribución y los controles anteriores son objetivos, no capacidades ya terminadas. El prototipo usa un backdrop y un panel lateral sobre el editor estándar.

## Entregas y criterios de aceptación

### 1. Composición 2D utilizable

Read de secuencias y EXR; Merge con entradas A/B explícitas; transformaciones; máscaras; corrección de color; Write y rango de cuadros. Elegir y documentar convención de alpha. No presentar Color Balance como Grade.

Aceptación: abrir un plano real con alpha y una secuencia, componer foreground sobre background, guardar/reabrir y exportar EXR. Comparar valores de píxeles conocidos y comprobar bordes sin halos, rangos y nombres de archivo. Una prueba de creación de nodos no satisface esta entrega.

### 2. Interfaz de compositor

Validar primero layout, atajos y selección con artistas. Hacer un pequeño fork del editor nativo para probar orientación de sockets, nodos compactos y conexiones verticales. Conservar las modificaciones acotadas para poder incorporar actualizaciones de Blender.

Aceptación: completar un flujo Read → corrección → Merge → Viewer → Write con teclado, undo/redo y persistencia. Revisar comportamiento de los atajos fuera del compositor y dentro de grupos.

### 3. Integración 3D

Escena, cámara, geometría/card, luces, pases y Render Layers. Una escena Blender conectada al compositor es el primer nivel. Un grafo 3D con semántica equivalente a Scene/ScanlineRender es trabajo adicional.

Aceptación: integrar un elemento 3D en un plano, guardar cámara/escena y recomponer una secuencia reproducible con pases identificados.

### 4. Robustez para producción

Validar OCIO y configuraciones ACES, canales EXR arbitrarios, Cryptomatte, proxies, caché, invalidación por cuadro, errores de medios, recuperación de proyectos y render por lotes. Definir límites medidos de memoria y rendimiento con HD/4K.

No prometer de antemano equivalencia de deep compositing, multivista, RotoPaint, plugins OFX o importación `.nk`. Cada área necesita una investigación y un contrato independiente.

## Modelo de proyecto

Inicialmente `.blend` es la fuente de verdad. No duplicar el grafo en un JSON que pueda divergir. Metadatos específicos podrán versionarse como propiedades del proyecto cuando exista una necesidad real. Los nombres amigables son etiquetas; las operaciones mantienen identificadores nativos.

## Distribución

Primero launcher y addon; luego build independiente con identidad Nukify y una versión fijada de Blender. Publicar fuentes, instrucciones de compilación, licencias y avisos según los componentes distribuidos. Revisar la licencia exacta de la revisión elegida antes del empaquetado.

Referencias oficiales consultadas:

- https://www.blender.org/about/
- https://developer.blender.org/docs/license/
- https://www.blender.org/support/faq/
- https://docs.blender.org/manual/en/latest/editors/compositor.html

## Límite de la validación actual

El smoke test ejecutó operadores y creación de nodos en Blender 4.5.14 LTS sin render. La interfaz no fue inspeccionada visualmente y no se ejecutó una composición de un plano real. Antes de declarar una primera versión utilizable, completar la entrega 1 y validar el launcher en una sesión gráfica.
