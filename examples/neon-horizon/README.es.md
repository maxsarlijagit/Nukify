# Neon Horizon · demo editable

[English](README.md) · [Español](README.es.md)

![Composición final renderizada en Nukify](preview.png)

Composición cyberpunk panorámica de **Max Sarlija**, creada con Nukify 0.10.1, dos imágenes generadas con GPT y 22 nodos editables. La imagen es un render real del motor Blender 4.5.14 incluido.

## Probarla

1. Instalá [Nukify 0.10.1 o posterior](https://github.com/maxsarlijagit/Nukify/releases).
2. Cloná el repositorio o usá **Code → Download ZIP** y extraelo. Conservá toda esta carpeta, incluyendo `media/`; descargar solamente el proyecto no alcanza.
3. Abrí Nukify, pulsá **Ctrl+O** y abrí `examples/neon-horizon/Neon_Horizon.nukify`.
4. Activá **Live** y cambiá un parámetro. Viewer A usa `Fine_Film_Grain`; Viewer B usa `City_Density` para comparar con el fondo.
5. Elegí una carpeta de salida con permisos de escritura antes de renderizar. Los medios usan rutas relativas y no se guarda una ruta personal de Blender ni de salida.

## Explorar el graph

- `Green_Key` y `Matte_Check`: chroma key, despill y revisión de alpha.
- `Unpremult_Edges`, `Hero_Light_Match`, `Premult_Edges`: tratamiento de bordes y ajuste de luz.
- `Hero_Placement`: posición y escala del personaje.
- `Contact_Shadow_Mask`, `Right_Boot_Shadow`, `Boot_Contact_Masks`: sombras de contacto separadas bajo las botas.
- `Hero_Over_City`, `Final_Film_Balance`, `Fine_Film_Grain`: merge, balance final y grano sutil.

`Hero_Saturation` y `Film_Contrast` son nodos ColorCorrect opcionales desactivados para conservar detalle en sombras. Activarlos cambia el aspecto entregado.

## Contenido y límites

Es una **imagen fija de 1920 × 804**, no un video ni una prueba de tracking o secuencias. El piso mojado no tiene un reflejo del personaje calculado físicamente; las sombras de contacto son aproximaciones artísticas. El hiperrealismo cinematográfico es la dirección visual, no una certificación de estudio. Sin afiliación con ILM ni DNEG.

Incluye ambos PNG originales y el preview. No necesitás API key ni solicitudes pagas para abrir y renderizar el proyecto. Se generaron exactamente dos imágenes con GPT en Codex y no se hicieron solicitudes a fal.ai. `provenance.json` registra hashes de los originales; `SHA256SUMS.txt` verifica proyecto e imágenes. Los EXR, archivos Blender de salida, cachés y ejecutables no se incluyen en Git: podés generarlos con un render local.

La app instalada y el viewer live se probaron durante la creación. Para publicar el ejemplo se validan dependencias del graph, resolución de medios y hashes; esto no implica una prueba en otra PC limpia.

Este ejemplo se distribuye con Nukify bajo [GPL-3.0-or-later](../../LICENSE), en la medida en que existan derechos aplicables a sus imágenes generadas por IA. Autor y composición: Max Sarlija. La procedencia de los medios está identificada arriba.
