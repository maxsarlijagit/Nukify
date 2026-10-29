# Nukify 0.8 — curvas, roto y correcciones de tracking

Entrega incremental S15–S17. Incluye Blender 4.5.14 LTS y conserva lectura de proyectos anteriores. Abrir `Nukify.exe` del paquete completo o ejecutar el instalador; no requiere Python ni Blender externos.

## Probar el workflow

Proyecto → Ejemplos → Curvas y roto abre una composición animada con máscara en B. Seleccionar Roto y abrir su curva de shape_x: arrastrar claves o tangentes Bézier, seleccionar varias filas para mover varias claves, copiar/pegar claves y usar Retime. Guardar confirma la edición como una operación reversible; Cancelar descarta el diálogo. Escape durante un arrastre restaura ese arrastre.

El botón fx de cada parámetro numérico permite expresiones como `value + 15 * sin(frame * pi / 12)` o `ref("Constant1", "r") * 2`. Admite sin, cos, abs, min, max, sqrt y clamp, aritmética y referencias numéricas entre nodos. `value` representa el valor base o animado del propio parámetro. Vaciar fx elimina la expresión; Reset también elimina curva y expresión. Los ciclos se detectan por nodo: para valores del mismo nodo usar value, no ref. No admite Python arbitrario. Las referencias participan en el cache de cada cuadro.

## Roto y keying

Roto incorpora jerarquía de grupos con transformaciones, visibilidad y opacidad. Editar grupos permite definir id, parent, x/y, escala, rotación y opacidad. Asignar shape_group al id del grupo. Cada forma tiene shape_x/y/scale/rotation/opacity y shape_enabled; las propiedades numéricas de la forma admiten claves y expresiones. El editor de grupos no tiene controles propios de keyframes.

motion_samples entre 2 y 16 integra la máscara en varios subframes, usando shutter en unidades de cuadros y centrado en el cuadro actual. Aumenta el costo del render. Con 1 muestra conserva máscara sin blur temporal. No es motion blur general de imágenes o del render 3D.

ChromaKey agrega blur_pre/post, dilatación, feather, tolerancia/radio de bordes, despill_balance y selector de salida Image, Matte o Edges. Los controles se evalúan con el Keying de Blender.

## Tracking asistido

Analizar sigue usando LK 2D o homografía planar. Confianza / perdidas muestra resultados por cuadro; doble clic busca ese cuadro. Una pérdida conserva las curvas anteriores y guarda el intento fallido para revisión.

En un cuadro problemático: Corregir puntos en este frame, mover los puntos sobre el plate, Guardar correccion manual y volver a analizar. Tracker2D usa uno o dos puntos; PlanarTracker usa cuatro esquinas y vuelve a detectar features dentro del área corregida. Las correcciones aparecen como MANUAL, con confianza 1 por asignación del usuario, no por medición automática. Se pueden quitar por cuadro.

Editar zona de exclusion define un polígono fijo para ignorar features. Las ventanas de patrón/búsqueda se muestran al editar puntos. La recuperación es asistida: no hay detección automática de oclusiones ni búsqueda global de reaparición. Una pérdida detiene esa dirección; para saltos sucesivos hacen falta correcciones válidas. No es camera solve 3D.

## Validación y pendientes

Pruebas sintéticas de arrastre/cancelación de curvas, retiming de tangentes, expresiones y ciclos, invalidación de cache, grupos y blur de máscara, pérdida y recuperación manual 2D/planar y exclusión. Comprobación de píxeles reales mediante Blender, más regresiones del ejecutable.

Pendientes: revisión con artistas y planos reales, sesiones largas HD/4K, tracking de oclusiones automático, edición avanzada de grupos, tangentes ponderadas y validación en una segunda PC limpia. La entrega no certifica equivalencia funcional con Nuke ni cierra todos los criterios de producción.
