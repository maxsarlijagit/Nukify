# Repository structure / Estructura del repositorio

| Folder | Purpose / Propósito |
| --- | --- |
| `desktop/` | Desktop application: Qt UI and separate Blender worker / App Qt y worker Blender separado |
| `nukify/` | Original Blender addon prototype / Prototipo original del addon |
| `assets/` | App resources and synthetic fixtures / Recursos de la app y fixtures sintéticos |
| `examples/` | Self-contained editable demos / Demos editables autocontenidas |
| `tests/` | Automated checks, Qt checks and Blender checks / Pruebas automáticas, Qt y Blender |
| `scripts/` | Launch, packaging, fixture generation and audits / Inicio, empaquetado, fixtures y auditoría |
| `packaging/` | Installer configuration and release metadata / Configuración del instalador y versión |
| `docs/guides/` | User-facing guides / Guías de uso |
| `docs/development/` | Design and contributor reference / Referencias de diseño y desarrollo |
| `docs/planning/` | Roadmap and sprint records / Roadmap y registros de sprints |
| `docs/history/` | Earlier implementations and original proposal / Implementaciones previas y propuesta original |
| `docs/releases/` | Bilingual release notes / Notas bilingües de publicación |
| `docs/images/` | Documentation screenshots / Capturas de documentación |
| `agents/` | Instructions and contribution templates / Instrucciones y plantillas para agentes |
| `licenses/` | Dependency license notices / Licencias de dependencias |
| `.github/` | CI workflows / Automatización de CI |

## Local generated directories / Carpetas locales generadas

These remain ignored by Git and retain their build paths. Do not move an existing environment or installed runtime to reorganize source files.
Estas carpetas siguen ignoradas por Git y conservan las rutas usadas por el build. No muevas entornos ni runtimes instalados para ordenar fuentes.

| Folder | Contents / Contenido |
| --- | --- |
| `.buildenv/`, `.venv/` | Local Python environments / Entornos Python locales |
| `.tools/` | Local build tools / Herramientas locales |
| `build/`, `dist/` | Packaging intermediates / Intermedios de empaquetado |
| `releases/<version>/` | Installers and release bundles / Instaladores y paquetes |
| `sources/` | Downloaded dependency sources / Fuentes descargadas de dependencias |
| `validation/` | Local reports, logs and temporary verification scripts / Informes, logs y verificadores temporales |
| `renders/` | Generated render outputs / Salidas de render |

## Placement rules / Dónde guardar cada cosa

- Keep runnable demos under `examples/<name>/`, with relative media paths, a guide, provenance and checksums. / Guardá demos ejecutables en `examples/<nombre>/`, con rutas relativas, guía, procedencia y hashes.
- Keep user projects and private media outside the repository. / Conservá proyectos y medios privados fuera del repositorio.
- Put new user documentation in `docs/guides/`; add it to the [documentation index](README.md). / Agregá nuevas guías en `docs/guides/` y enlazalas desde el índice.
- Keep root launch/build entry points stable: `Start-Nukify.cmd`, `Start-Nukify.ps1`, `Build-Nukify.ps1`, requirements and contribution/license files. / Conservá estables los puntos de entrada, requisitos y archivos de contribución/licencias de la raíz.
- Keep the Qt UI and Blender execution in separate processes. This folder organization does not merge their runtimes. / Conservá UI Qt y ejecución Blender en procesos separados.
