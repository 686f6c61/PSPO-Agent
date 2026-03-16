# Pasos detallados del onboarding

Este fichero complementa SKILL.md con instrucciones detalladas para cada paso del asistente de configuracion.

## Referencia rapida de URLs

| Recurso | URL |
|---------|-----|
| Crear Power-Up / obtener API Key | https://trello.com/power-ups/admin |
| Generar token manual | `https://trello.com/1/authorize?expiration=30days&name=PSPO+Agent&scope=read,write&response_type=token&key=<TU_API_KEY>` |
| Verificar conexion | `GET https://api.trello.com/1/members/me?key={KEY}&token={TOKEN}` |
| Listar tableros del usuario | `GET https://api.trello.com/1/members/me/boards?key={KEY}&token={TOKEN}` |

## Validaciones de formato

### API Key
- Longitud: exactamente 32 caracteres.
- Contenido: solo caracteres hexadecimales (0-9, a-f, A-F).
- Regex: `^[0-9a-fA-F]{32}$`
- Error comun: el usuario copia el Secret en vez de la API Key. El Secret tiene un formato diferente (mas largo).

### Token
- Longitud: minima 41 caracteres.
- Contenido: empieza por `ATTA` y luego solo caracteres alfanumericos.
- Regex: `^ATTA[a-zA-Z0-9]{37,}$`
- Error comun: el usuario copia una URL en vez del token, o copia el token cortado.

## Configuracion por defecto del tablero

### Columnas (listas)

Las columnas se crean en este orden (de izquierda a derecha en Trello):

| Posicion | Nombre | Proposito |
|----------|--------|-----------|
| 1 | Backlog | Historias de usuario priorizadas pendientes de sprint |
| 2 | Sprint activo | Historias comprometidas para la unica semana de sprint en curso |
| 3 | Bloqueada | Historias con dependencias confirmadas aun no resueltas |
| 4 | En progreso | Historias en desarrollo activo |
| 5 | En revision | Historias completadas pendientes de revision |
| 6 | Hecho | Historias completadas y verificadas |

### Etiquetas de prioridad

| Nombre | Color en Trello | Significado |
|--------|----------------|-------------|
| Critica | red | Bloquea el avance del proyecto. Resolver inmediatamente. |
| Alta | orange | Importante para el sprint activo. Prioridad de entrega. |
| Media | yellow | Necesaria pero no urgente. Puede esperar al siguiente sprint. |
| Baja | blue | Mejora menor o nice-to-have. Implementar cuando haya capacidad. |

## Gestion de errores durante el onboarding

### El usuario no puede acceder a trello.com/power-ups/admin

Posibles causas:
- No tiene cuenta de Trello -> Indicar que necesita crear una cuenta gratuita en trello.com primero.
- No tiene permisos de administrador en ningun workspace -> Necesita crear un workspace propio (gratuito).

### El token no se genera (la pagina de autorizacion da error)

Regla de seguridad general: la skill puede construir internamente la URL de autorizacion, pero NO debe mostrar en el chat la API key resuelta ni una URL que la contenga.

Posibles causas:
- La API Key es incorrecta -> Volver al paso 1.
- La sesion de Trello ha expirado -> Iniciar sesion de nuevo en Trello y volver a visitar la URL.
- El navegador bloquea popups -> Abrir la URL directamente en una pestana nueva.

### La verificacion de credenciales falla con 401

Posibles causas:
- API Key incorrecta -> Verificar que se copio del campo correcto.
- Token generado con una API Key diferente -> El token debe generarse con la URL que incluye la API Key correcta.
- Token expirado -> Si se configuro hace mas de 30 dias, regenerar.

### El tablero no se puede crear

Posibles causas:
- El usuario ha alcanzado el limite de tableros del plan gratuito (10 por workspace) -> Sugiere usar un tablero existente o eliminar alguno.
- Error de red temporal -> Reintentar.
