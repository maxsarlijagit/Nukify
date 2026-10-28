# Sistema de interfaz de Nukify 0.9

## Auditoría aplicada

La interfaz anterior usaba botones estirados, filas de ancho rígido, símbolos de fuente para transporte y panel de proyecto siempre visible. El inspector competía por altura con ajustes globales. Se reemplazaron estos patrones por barras adaptables, iconografía vectorial y separación en pestañas.

## Tokens y componentes

Implementación común: `desktop/ui_theme.py`.

| Token | Valor | Uso |
| --- | --- | --- |
| Fondo | #242424 | Aplicación y áreas secundarias |
| Panel | #303030 | Editores |
| Campo | #202020 | Entradas |
| Borde | #454545 | Separadores y campos |
| Texto | #dddddd | Lectura principal |
| Acento | #e6a34b | Foco, selección de nodo y pestaña |
| Activo | #365975 / #6095bf | Botones conmutados |
| Espacio | 4 / 8 px lógicos | Barras y formularios |
| Icono | 16 px lógicos, trazado 24×24 | Controles y categorías |

Los colores de categorías del graph se mantienen en registry.py. Se evita colorear superficies grandes con colores de categoría; la franja superior identifica el tipo.

## Comportamiento

`FlowLayout` conserva el orden de los controles y distribuye filas según el ancho disponible. No oculta comandos. Los controles se mantienen como widgets Qt nativos para conservar Tab, Enter, accesibilidad y señales existentes.

`decorate` aplica icono, nombre accesible, tooltip y tamaño compacto opcional. Reservar iconos sin texto para acciones inequívocas como transporte, reset y clave; acompañar acciones de archivo y categoría con texto. Los iconos tienen estado deshabilitado, fondo transparente y se vuelven a dibujar al cambiar tamaño.

Los formularios largos tienen scroll y búsqueda; WrapLongRows permite separar etiqueta/campo cuando no caben en una línea. Los presets modifican proporciones y siempre permiten volver a mostrar ambos editores. Guardar distribución es explícito y tolera preferencias dañadas sin impedir el arranque.

## Límites

Foco visible y nombres accesibles incluidos; no se ha completado una auditoría con lector de pantalla. DPI simulado a 150%, pendiente cambio físico entre monitores. No se añadieron animaciones decorativas al viewer ni al graph.
