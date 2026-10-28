# Nukify 0.7 — graph, viewer y cache

Entrega incremental de S12–S14 sobre 0.6. Blender 4.5.14 LTS sigue incluido y se
conservan proyectos v1/v2. No se afirma aprobación completa de producción.

## Graph y propiedades (S12)

- Sockets con área de selección más amplia y cables con hit-test independiente
  del grosor visible. El destino bajo el cursor se marca verde si admite la
  conexión y rojo si es incompatible o genera un ciclo. Escape cancela.
- Reconectar exactamente la misma entrada no agrega un undo vacío.
- Fijar propiedades conserva el panel de un nodo mientras se selecciona otro.
  Undo/redo vuelve a resolver el nodo por ID; no edita una copia antigua del grafo.
  Abrir otro proyecto limpia la fijación. Para volver a seguir la selección,
  desactivar Fijar propiedades.
- Reset restaura el valor por defecto y quita la curva del parámetro. Un undo
  recupera ambos. Los parámetros enlazados a tracking requieren desenlazar primero.
- Proyecto → Shortcuts permite importar/exportar presets JSON versionados.
  Los cambios importados se aplican con Guardar; Cancelar conserva la configuración.
  Se rechazan conflictos, comandos desconocidos y atajos reservados de archivos/undo.
- Las listas de conexiones de propiedades respetan tipos de imagen/escena/cámara.
  Eliminar una salida conectada a B desconecta esa referencia.

## Viewer (S13)

- Layers / canales EXR abre el inspector de un Read perteneciente a la rama A.
  Incluye canales, metadata, dataWindow y displayWindow. Usar selección modifica
  el pase del Read: afecta la composición, no es un cambio exclusivo de display.
- Intercambiar A/B es reversible con undo. Los controles A, B, Wipe y Difference
  mantienen su comportamiento de comparación sincronizada.
- Pixel, 3x3 y 9x9 calculan promedio RGBA y luminancia sobre float scene-linear,
  antes de exposure/gamma/display. El área de muestreo está expresada en píxeles
  del proxy; las coordenadas mostradas corresponden al formato completo.
- Formato muestra el límite de imagen y un margen del 5%. No es un overlay de
  dataWindow ni un control de ROI de render.
- Dos bandas debajo de la timeline muestran cache A (dorado) y B (azul).
  El tooltip identifica el cuadro y las ramas disponibles; click permite buscar
  ese cuadro. La exploración del cache es gradual y se pausa durante playback.
  Se exploran como máximo 1000 cuadros desde First; el resto se marca al evaluarse.

## Cache y rendimiento (S14)

- Cache range prepara las dos ramas conectadas, no solo A. Antes de empezar,
  calcula el espacio float del rango y pide un proxy menor o más presupuesto
  si no cabe. El presupuesto total A+B se configura desde Proyecto.
- Las firmas usan los valores evaluados de cada cuadro y las dependencias activas.
  Editar una clave futura conserva los cuadros que producen exactamente los
  mismos valores. Cambiar una rama independiente o mover nodos no invalida otra.
  Los enlaces de tracking y referencias de estabilización sí forman parte del cálculo.
- Los aciertos actualizan la antigüedad del cache de disco. Datos y metadata se
  publican mediante reemplazo de archivos temporales para evitar entradas parciales.
- Los resultados incluyen tiempos separados de construcción del grafo, render y
  lectura de píxeles. El benchmark HD/4K permanece sintético y reproducible.

Esto reduce renders innecesarios; no acelera por sí mismo una evaluación fría de
Blender. El cache sigue siendo por salida/cuadro: aún no guarda resultados de cada
nodo intermedio. Proxy interno, ROI y presupuestos configurables de memoria del
viewer quedan pendientes; se mantienen los límites de memoria de 0.6.

## Evidencia y límites

Prueba de 50 nodos con guardado/reapertura y undo/redo; reset de curvas con panel
fijado; presets y atajos inválidos; invalidación por dependencias; precarga real de
seis cuadros A y seis B; cambio de clave futura y regreso al cuadro conservado sin
enviar renders adicionales. Se repiten los flujos de 0.5 y 0.6 sobre el ejecutable.

La validación de interacción con artistas, sesiones prolongadas, EXR de producción
y otra máquina limpia sigue pendiente. No están cerrados todos los criterios del
roadmap S12–S14. Funciones previas: docs/desktop-0.5.md y docs/desktop-0.6.md.
