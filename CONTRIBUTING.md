# Contribuir a Nukify

Gracias por contribuir. Esta versión es una beta técnica para Windows x64.

1. Abrí un issue que describa el problema o la propuesta. Para errores, indicá versión, pasos, resultado esperado, formato y un proyecto mínimo sin medios privados.
2. Prepará el entorno con [BUILDING.md](BUILDING.md), creá una rama y mantené los cambios acotados.
3. Corré las pruebas relevantes. Los cambios de compositor requieren comprobar píxeles mediante Blender; los cambios de UI deben revisarse a 1024 y 1440 px.
4. Enviá un pull request con descripción, validación y límites conocidos. No incluyas caches, renders privados, binarios de dependencias ni credenciales.

Las contribuciones se reciben bajo GPL-3.0-or-later. Conservá los avisos de terceros. Las imágenes de ejemplo deben ser propias o tener permisos de redistribución compatibles.

Estructura: `desktop/` contiene aplicación/motor; `tests/` pruebas; `scripts/` herramientas; `assets/` fixtures; `packaging/` release e instalador. `nukify/` conserva el prototipo del addon de Blender.
