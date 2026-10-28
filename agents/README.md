# Colaborar con agentes en Nukify

Esta carpeta permite que una persona trabaje con un asistente de programación sobre tareas concretas de Nukify. No requiere un proveedor específico ni instala un framework de agentes.

## Por dónde empezar

1. Leé las [instrucciones compartidas](INSTRUCTIONS.md).
2. Seguí la [guía First Agentic Contribution](FIRST_AGENTIC_CONTRIBUTION.md) para tu primera contribución asistida por un agente.
3. Copiá la [plantilla de tarea y entrega](TASK_TEMPLATE.md) en un issue o en el chat del agente.
4. Prepará el entorno con [BUILDING.md](../BUILDING.md) y seguí [CONTRIBUTING.md](../CONTRIBUTING.md) para enviar un PR.

El archivo [AGENTS.md](../AGENTS.md) de la raíz sirve como entrada para herramientas que admiten ese formato. Si tu herramienta no lo carga automáticamente, pedile que lea ese archivo y los documentos enlazados antes de trabajar. No asumas que una carpeta llamada `agents` se ejecuta o se carga sola.

## Responsabilidades

| Responsable | Trabajo |
| --- | --- |
| Colaborador humano | Define el problema, el alcance y la aceptación; revisa el diff y la experiencia de uso. |
| Agente de implementación | Inspecciona el código, propone un cambio acotado, implementa y verifica. |
| Revisor humano o agente | Comprueba regresiones, evidencia y límites sin dar por cierto el resumen del implementador. |
| Mantenedor | Revisa y decide la integración y publicación de versiones. |

Son roles de trabajo: un solo agente puede implementar y luego hacer una revisión separada del diff. Si se acuerda trabajo con varios agentes, asigná archivos o módulos distintos, un responsable de integración y una rama o worktree por tarea. Evitá ediciones simultáneas del mismo archivo.

La revisión humana sigue siendo necesaria antes de integrar una contribución. Una prueba automática aprobada no reemplaza la validación visual, de píxeles o de instalación cuando corresponda.
