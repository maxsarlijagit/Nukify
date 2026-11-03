# Actualizaciones de Nukify

Nukify consulta las releases públicas de `maxsarlijagit/Nukify` en segundo plano,
unos segundos después de abrir la aplicación y como máximo una vez cada 24 horas.
La consulta no necesita cuenta ni token de GitHub. Si no hay conexión, el arranque
y la composición continúan normalmente; la búsqueda manual informa el error.

En **Proyecto → Actualizaciones** podés ver la versión instalada, buscar ahora,
desactivar la búsqueda automática o elegir si incluir versiones beta.
Las betas están habilitadas inicialmente porque Nukify se distribuye como beta.
Las versiones estables también participan en ese canal; nunca se ofrece bajar de versión.

Cuando hay una versión superior con instalador compatible, el aviso muestra la
versión actual, la nueva y las notas de la release en texto. Podés ver la release
en GitHub, posponerla o ignorar esa versión. La búsqueda manual vuelve a mostrar
una versión ignorada. El aviso no descarga ni instala por sí solo.

**Descargar actualización** guarda el instalador en `%LOCALAPPDATA%/Nukify/updates`.
El tamaño y SHA256 se comprueban contra los metadatos del asset publicado en GitHub.
Cerrar el aviso cancela la descarga y elimina el archivo parcial. Una vez verificado,
**Instalar y cerrar Nukify** vuelve a verificar el archivo y solicita el cierre
normal: permite guardar o cancelar y respeta los bloqueos por procesos activos.
Si se acepta, abre el asistente de instalación de Windows sin forzar reinicios.
Completá el asistente y volvé a abrir Nukify. No es una instalación silenciosa.

Las preferencias se guardan en `%LOCALAPPDATA%/Nukify/updates.json`. Las pruebas
integradas no consultan GitHub automáticamente. El código de composición y el
worker de Blender no participan en el sistema de actualizaciones.

## Publicación compatible

- La versión de fuentes se obtiene de `packaging/release.json`; la instalación
  usa el campo `app` del `release.json` junto al ejecutable. El título ya no lleva
  una versión fija en el código de la interfaz.
- Crear una release publicada con tag `vMAJOR.MINOR.PATCH` (también se admiten
  sufijos `-alpha.N`, `-beta.N`, `-rc.N`) y completar sus notas de cambios.
- Adjuntar `Nukify-Setup-VERSION.exe`. Debe estar completamente subido y tener
  `size` y `digest` SHA256 en la API de GitHub. Una release incompleta o sin hash
  no se ofrece como actualización instalable.
- Se consideran las 100 releases más recientes de la API y se elige la versión
  mayor del canal seleccionado. Los borradores no participan.
- El SHA256 detecta corrupción; confía en la publicación del repositorio y no
  reemplaza una firma Authenticode del editor.
- Esta función requiere distribuir un nuevo ejecutable que la incluya. Las
  instalaciones anteriores no adquieren el actualizador sin esa actualización inicial.

Validación local:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.buildenv\Scripts\python.exe -m unittest discover -s tests -p 'test_update*.py'
```
