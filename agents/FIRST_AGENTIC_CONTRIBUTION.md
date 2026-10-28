# First Agentic Contribution

Guía para hacer tu primera contribución a Nukify con un agente de programación. La persona define el resultado y revisa la entrega; el agente ayuda a explorar, implementar y verificar.

## 1. Elegí una tarea pequeña

Empezá con un error reproducible, un tooltip, una mejora de foco/atajo o una corrección de documentación. Describí qué sucede, qué debería suceder y cómo comprobarlo. Evitá usar «replicar todo Nuke» como primera tarea: no define un resultado revisable.

Abrí o vinculá un issue según [CONTRIBUTING.md](../CONTRIBUTING.md). No adjuntes medios privados; creá un ejemplo mínimo redistribuible.

## 2. Prepará tu copia

Si no tenés permisos de escritura, hacé un fork en GitHub y cloná tu fork. Si ya tenés una copia de trabajo, comprobá su estado antes de cambiar de rama.

```powershell
# Reemplazá TU_USUARIO por tu cuenta.
git clone https://github.com/TU_USUARIO/Nukify.git
cd Nukify
git switch -c docs/primera-contribucion
git status --short
```

Elegí un nombre de rama acorde a tu tarea. Para cambios de código prepará el entorno con [BUILDING.md](../BUILDING.md). Para editar documentación no necesitás descargar Blender ni compilar el instalador.

## 3. Dale un encargo concreto al agente

Copiá la [plantilla](TASK_TEMPLATE.md) o usá este ejemplo, reemplazando los campos:

```text
Trabajamos en mi copia de Nukify. Leé AGENTS.md y agents/INSTRUCTIONS.md.
Tarea: corregir [comportamiento] descrito en [issue].
Reproducción: [pasos y resultado actual].
Aceptación: [resultado observable].
Alcance: [archivos o área]; fuera de alcance: [exclusiones].
Primero revisá el estado Git y el código relevante. Explicá brevemente
el cambio previsto, implementalo y ejecutá las verificaciones adecuadas.
Preservá cambios ajenos. Entregá diff, comandos/resultados y límites.
En esta tarea no hagas push, merge ni publiques releases; revisaré el diff.
```

El límite de publicación de este ejemplo es una elección para tu primera contribución. Podés autorizar explícitamente otras acciones cuando corresponda. No hace falta repartir una tarea pequeña entre múltiples agentes.

## 4. Revisá la evidencia

- Leé el diff, no solamente el resumen del agente. Confirmá que resuelve el caso y no introduce cambios ajenos.
- Revisá qué comandos se ejecutaron, cuáles pasaron y cuáles se omitieron. Un comando sugerido no cuenta como ejecutado.
- Si cambia la UI, abrí la app y probá el flujo, teclado y tamaño de ventana. Si cambia imagen, pedí un render verificable con Blender.
- Si falta evidencia, pedí una corrección concreta antes de seguir. No copies credenciales ni logs privados en el chat o el PR.

## 5. Prepará el PR

```powershell
git diff --check
git diff
# Ejemplo para una tarea que solo cambió README.md; adaptá la lista exacta.
git add -- README.md
git diff --cached
# Con el entorno de desarrollo preparado:
.\.buildenv\Scripts\python.exe scripts/audit_publication.py
git commit -m "docs: aclarar primeros pasos"
git push -u origin HEAD
```

Si solo trabajaste en documentación y no creaste `.buildenv`, podés ejecutar la auditoría con `py -3.12 scripts/audit_publication.py`: usa la biblioteca estándar. No omitas la revisión del diff ni la auditoría porque la tarea sea pequeña.

Desde tu fork, abrí un PR hacia `maxsarlijagit/Nukify`, rama `main`. Usá la sección «Entrega» de la plantilla para describir cambios y evidencia. Esperá CI, revisá sus resultados y atendé los comentarios del mantenedor. No publiques una release para entregar un PR.

## Cuándo está terminada

La contribución está lista para revisión cuando cumple la aceptación, tiene un diff acotado, evidencia adecuada, documentación actualizada y limitaciones explícitas. «PR enviado», «PR integrado» y «versión publicada» son estados distintos: reportá el que realmente alcanzaste.
