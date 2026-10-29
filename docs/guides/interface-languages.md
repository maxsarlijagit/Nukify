# Interface languages / Idiomas de la interfaz

## English

New profiles default to English, regardless of the Windows language. Open **Language / Idioma** in the top toolbar, choose **English** or **Español**, and save. Save your project and reopen Nukify to apply the selection. The dialog does not restart the app or interrupt renders, GENAI jobs, playback or unsaved work.

The preference lives in `%LOCALAPPDATA%/Nukify/preferences.json` as `"language": "en"` or `"language": "es"`. Missing, malformed and unsupported preferences fall back to English. Saving the language preserves other preferences.

Translation covers application controls, menus, viewer tools, inspector labels, composition/tracking/curve dialogs and GENAI controls. Technical node names, socket identifiers, enum values, provider model names and schemas, backend/provider logs, paths, prompts and project data remain in their original form. Language changes do not alter saved projects or shortcut preset keys. Native Windows file pickers follow Windows language settings.

This feature is included in the **0.10.1 installer**. After setting up the environment described in [BUILDING](../../BUILDING.md), launch the updated interface from the repository root:

```powershell
.\.buildenv\Scripts\python.exe desktop/app.py
```

Contributors: add UI text with `tr(...)` from `desktop/i18n.py`, and add its Spanish/English pair to `desktop/translations.py`. Format variables after translation; do not translate project keys or editable content. The catalog is imported as Python and packaged with the application, with no network service or extra dependency.

## Español

Los perfiles nuevos usan inglés, independientemente del idioma de Windows. Abrí **Language / Idioma** en la barra superior, elegí **English** o **Español** y guardá. Guardá tu proyecto y volvé a abrir Nukify para aplicar el idioma. El diálogo no reinicia la app ni interrumpe renders, trabajos GENAI, playback o cambios sin guardar.

La preferencia se guarda en `%LOCALAPPDATA%/Nukify/preferences.json`, con `"language": "en"` o `"language": "es"`. Si falta, está dañada o no es compatible, se usa inglés. Al guardar se conservan las demás preferencias.

Se traducen controles, menús, herramientas del viewer, etiquetas del inspector, diálogos de composición/tracking/curvas y controles GENAI. Los nombres técnicos de nodos, sockets, valores de opciones técnicas, modelos y schemas del proveedor, registros del motor/proveedor, rutas, prompts y datos de proyectos conservan su forma original. El idioma no modifica proyectos ni claves de presets de atajos. Los selectores nativos de archivos respetan el idioma de Windows.

La función está incluida en el **instalador 0.10.1**. Prepará el entorno siguiendo [BUILDING](../../BUILDING.md) y ejecutá el comando de arriba desde la raíz del repositorio.

Para contribuir, usá `tr(...)` de `desktop/i18n.py` y agregá el par español/inglés a `desktop/translations.py`. Aplicá las variables de formato después de traducir. No traduzcas claves de proyectos ni contenido editable.

## Validation / Validación

```powershell
.\.buildenv\Scripts\python.exe -m unittest discover -s tests -p test_i18n.py
.\.buildenv\Scripts\python.exe tests/ui_language_layout.py
$env:QT_SCALE_FACTOR = '1.5'
.\.buildenv\Scripts\python.exe tests/ui_language_layout.py
```

The visual check writes screenshots to `validation/` using an isolated temporary profile. / La revisión visual guarda capturas en `validation/` con un perfil temporal aislado.
