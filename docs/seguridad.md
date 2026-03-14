# Informe de seguridad: PSPO Agent

| Campo | Valor |
|-------|-------|
| **Auditor** | El Paranoico (CSO, equipo Alfred Dev) |
| **Fecha** | 2026-03-13 |
| **Fase** | Auditoria de diseno (pre-implementacion) + Auditoria de codigo (post-implementacion) |
| **Documento base** | docs/prd.md v1.0 (Aprobado) |
| **SonarQube** | Ejecutado 2026-03-13. SonarQube Community Build 26.3.0. 0 vulnerabilidades, 0 security hotspots, 6 bugs (MINOR -- falsos positivos en regex), 10 code smells. |
| **Re-auditoria** | 2026-03-13 -- Verificacion de correcciones aplicadas a hallazgos SEC-01 a SEC-05 |
| **Auditoria de codigo** | 2026-03-13 -- Revision completa del servidor MCP, hooks, skills, dependencias y configuracion |

---

## Resumen ejecutivo

Se ha realizado una auditoria de seguridad completa del plugin PSPO Agent para Claude Code, en dos fases:

**Fase 1 - Auditoria de diseno (2026-03-13):** Se encontraron 2 hallazgos criticos, 3 hallazgos altos y 4 hallazgos medios. El diseno fue RECHAZADO. Tras correcciones, los criticos y altos fueron resueltos. El diseno fue APROBADO CON CONDICIONES.

**Fase 2 - Auditoria de codigo (2026-03-13):** Se ha auditado todo el codigo implementado del servidor MCP (11 ficheros TypeScript, 1087 lineas), los hooks de seguridad (2 scripts Bash), las skills con acceso a credenciales (2 ficheros Markdown), la configuracion MCP y las dependencias. Se han verificado las medidas de seguridad comprometidas en la fase de diseno (SEC-06 a SEC-10). Se ejecuto SonarQube Community Build 26.3.0 sobre el codigo fuente. npm audit reporta 0 vulnerabilidades conocidas.

**Resultado de la auditoria de codigo:** Se encontraron 0 hallazgos criticos, 0 hallazgos altos, 3 hallazgos medios y 3 hallazgos bajos. Las medidas de seguridad criticas del diseno (rate limiting, enmascaramiento de credenciales, sanitizacion de entrada, construccion segura de URLs) estan correctamente implementadas. **El codigo puede avanzar a produccion resolviendo las condiciones pendientes.**

---

## PARTE I: Auditoria de diseno (pre-implementacion)

## 1. Threat model (STRIDE)

### 1.1 Componente: onboarding (manejo de credenciales)

| Amenaza STRIDE | Aplica | Descripcion | Mitigacion propuesta |
|----------------|--------|-------------|----------------------|
| **Spoofing** (suplantacion) | Si | Un atacante podria suplantar al plugin y pedir credenciales al usuario (phishing via terminal). | El plugin debe identificarse claramente. Documentar que NUNCA pedira credenciales fuera del flujo de onboarding. |
| **Tampering** (manipulacion) | Si | Si un atacante modifica el codigo del plugin antes de la instalacion, podria redirigir credenciales a un servidor malicioso. | Verificacion de integridad del plugin (checksum/firma). Distribucion por canal oficial de Claude Code. |
| **Repudiation** (repudio) | Bajo | El usuario podria negar haber autorizado acciones en Trello. | Log local de acciones con timestamp. La confirmacion explicita antes de publicar (HU-04/HU-05) mitiga parcialmente. |
| **Information Disclosure** | Si | Las credenciales se manejan en texto plano durante el onboarding (input del terminal, escritura en .env). | Minimizar la ventana de exposicion. No loggear credenciales. Limpiar variables de memoria tras el uso. |
| **Denial of Service** | Bajo | Un atacante no podria denegar el servicio de onboarding directamente, pero credenciales invalidas bloquean el flujo. | El flujo ya maneja reintentos (Escenario 4 de HU-01). Correcto. |
| **Elevation of Privilege** | Si | Si las credenciales se filtran, el atacante obtiene acceso completo de lectura/escritura a los tableros del usuario en Trello. | Principio de minimo privilegio: el scope del token deberia ser el minimo necesario. Ver hallazgo SEC-03. |

### 1.2 Componente: comunicacion con API de Trello

| Amenaza STRIDE | Aplica | Descripcion | Mitigacion propuesta |
|----------------|--------|-------------|----------------------|
| **Spoofing** | Bajo | Suplantacion de la API de Trello (ataque MitM). | HTTPS obligatorio. Verificacion de certificados TLS. No aceptar certificados auto-firmados. |
| **Tampering** | Bajo | Modificacion de las respuestas de la API en transito. | HTTPS con TLS 1.2+ lo previene. |
| **Repudiation** | Bajo | Trello podria negar haber recibido una peticion. | Log local de peticiones y respuestas (sin credenciales en los logs). |
| **Information Disclosure** | Si | Las credenciales viajan como parametros en la URL (query string). | Ver hallazgo SEC-04. Mitigacion parcial: HTTPS cifra la URL en transito, pero los parametros quedan en logs del servidor de Trello y en cualquier proxy intermedio. |
| **Denial of Service** | Si | Rate limiting de la API de Trello puede bloquear al plugin. | Implementar backoff exponencial (ya contemplado en el PRD). Correcto. |
| **Elevation of Privilege** | Bajo | El plugin no tiene mas privilegios que los del token. | El scope read,write es amplio pero es el minimo que ofrece la API de Trello. Documentado como limitacion. |

### 1.3 Componente: almacenamiento de credenciales (.env)

| Amenaza STRIDE | Aplica | Descripcion | Mitigacion propuesta |
|----------------|--------|-------------|----------------------|
| **Spoofing** | No aplica | -- | -- |
| **Tampering** | Si | Un proceso malicioso local podria modificar el .env para redirigir credenciales o cambiar el BOARD_ID. | Permisos de fichero restrictivos (600). Verificacion de integridad al leer. |
| **Repudiation** | Bajo | -- | -- |
| **Information Disclosure** | Si | El .env contiene credenciales en texto plano. Cualquier proceso con acceso al sistema de ficheros puede leerlas. Si se commitea accidentalmente, quedan en el historial de git para siempre. | Permisos 600 aplicados. .gitignore verificado. TRELLO_API_SECRET eliminado. |
| **Denial of Service** | Bajo | Borrar el .env obliga a reconfigurar, pero no es un ataque realista. | El onboarding permite reconfigurar (Escenario 6 de HU-01). |
| **Elevation of Privilege** | Si | Acceso al .env equivale a acceso completo a los tableros de Trello del usuario. | Permisos 600, .gitignore verificado, cifrado en reposo si es posible. |

### 1.4 Componente: persistencia de datos de producto (docs/)

| Amenaza STRIDE | Aplica | Descripcion | Mitigacion propuesta |
|----------------|--------|-------------|----------------------|
| **Spoofing** | Bajo | -- | -- |
| **Tampering** | Si | Modificacion de historias de usuario en docs/ podria alterar lo que se publica en Trello. | Git proporciona trazabilidad. Verificar antes de publicar que el fichero no ha cambiado desde la aprobacion. |
| **Repudiation** | Bajo | Git proporciona audit trail. | -- |
| **Information Disclosure** | Medio | Los documentos de producto contienen informacion de negocio. Si el repositorio es publico, esta informacion es accesible. | Documentar que docs/ puede contener informacion sensible de negocio. Recomendar repos privados para proyectos comerciales. |
| **Denial of Service** | Bajo | -- | -- |
| **Elevation of Privilege** | No aplica | -- | -- |

### 1.5 Componente: flujo de publicacion en Trello

| Amenaza STRIDE | Aplica | Descripcion | Mitigacion propuesta |
|----------------|--------|-------------|----------------------|
| **Spoofing** | Si | Un plugin modificado podria publicar contenido malicioso en los tableros del usuario. | Verificacion de integridad del plugin. Confirmacion humana obligatoria antes de publicar (ya contemplado en HU-04/HU-05). |
| **Tampering** | Si | Modificacion de los datos entre la aprobacion y la publicacion. | Verificar integridad del payload antes de enviar. Mostrar vista previa (ya contemplado en Escenario 3 de HU-05). |
| **Repudiation** | Bajo | Log local de lo publicado. | -- |
| **Information Disclosure** | Bajo | Lo publicado en Trello es visible para los miembros del tablero. Esto es comportamiento esperado. | Informar al usuario de quien tiene acceso al tablero antes de publicar. |
| **Denial of Service** | Si | Si la API falla, el plugin pierde las historias si no las guarda localmente primero. | Guardar siempre en docs/ antes de publicar en Trello (ya contemplado en HU-06). Correcto. |
| **Elevation of Privilege** | Bajo | -- | -- |

---

## 2. Hallazgos de seguridad (fase de diseno)

### Hallazgos criticos

#### SEC-01: Secreto de Trello almacenado innecesariamente en .env

- **Ubicacion:** .env linea 4 (version original)
- **Severidad original:** CRITICA (confianza: 95)
- **Categoria:** OWASP A07 (Authentication Failures) / Secretos innecesarios
- **Hallazgo:** El fichero .env contenia la variable TRELLO_API_SECRET con un valor real de 64 caracteres hexadecimales. El PRD establece explicitamente que "el Secret de Trello NO se usa en el MVP". Almacenar un secreto que no se necesita viola el principio de minimizacion de datos y amplia la superficie de ataque sin justificacion.
- **Vector de ataque:** Si el .env se filtra, el atacante obtiene el Secret, que permite firmar peticiones OAuth 1.0 en nombre de la aplicacion.
- **Impacto:** Compromiso completo de la aplicacion registrada en Trello.
- **Solucion aplicada:** TRELLO_API_SECRET eliminado del .env. El .env ahora solo contiene TRELLO_API_KEY y TRELLO_TOKEN.
- **Estado: CORREGIDO (verificado 2026-03-13)**

#### SEC-02: El .env.example commiteado contiene la variable TRELLO_API_SECRET

- **Ubicacion:** .env.example en el commit 3684dfc (historial de git)
- **Severidad original:** CRITICA (confianza: 95)
- **Categoria:** OWASP A05 (Security Misconfiguration) / Incoherencia diseno-implementacion
- **Hallazgo:** El .env.example original contenia TRELLO_API_SECRET= y no contenia TRELLO_TOKEN ni TRELLO_BOARD_ID.
- **Vector de ataque:** Un desarrollador que siga la plantilla original configurara el Secret innecesariamente.
- **Impacto:** Confusion en la configuracion, almacenamiento innecesario de secretos.
- **Solucion aplicada:** Nuevo commit 5d20d42 actualizo .env.example con las tres variables correctas.
- **Estado: CORREGIDO (verificado 2026-03-13)**

### Hallazgos altos

#### SEC-03: Token con scope excesivo y sin expiracion

- **Ubicacion:** PRD seccion 2, URL de autorizacion (HU-01, Escenario 3)
- **Severidad original:** ALTA (confianza: 90)
- **Categoria:** OWASP A01 (Broken Access Control) / Principio de minimo privilegio
- **Hallazgo:** La URL de autorizacion generaba un token con expiration=never y scope=read,write.
- **Vector de ataque:** Un token filtrado da acceso permanente y total a los tableros de Trello de la victima.
- **Impacto:** Lectura/escritura/eliminacion en cualquier tablero del usuario, sin limite temporal.
- **Estado: CORREGIDO (verificado 2026-03-13).** Todas las URLs del PRD, .env.example y skill de onboarding usan expiration=30days.
- **Nota sobre el scope:** La API de Trello no permite scopes granulares por tablero. read,write es el minimo necesario. Se acepta como limitacion documentada.

#### SEC-04: Credenciales transmitidas en query string de la URL

- **Ubicacion:** PRD seccion 2, todas las URLs de la API de Trello
- **Severidad original:** ALTA (confianza: 85)
- **Categoria:** OWASP A02 (Cryptographic Failures) / Exposicion de credenciales en transito
- **Hallazgo:** La API de Trello requiere que la API Key y el Token se envien como parametros de la URL (query string).
- **Vector de ataque:** En entornos corporativos con inspeccion SSL, un administrador de red podria capturar las credenciales.
- **Impacto:** Compromiso de credenciales de Trello en entornos con proxies de inspeccion SSL.
- **Estado: ACEPTADO COMO RIESGO RESIDUAL (2026-03-13)**
- **Justificacion:** Es una limitacion de la API de Trello, no del plugin. No existe alternativa tecnica.
- **Verificacion en codigo:** Confirmado que buildUrl() en trello-client.ts:153-172 usa URL.searchParams.set(). Las credenciales NUNCA aparecen en logs.

#### SEC-05: Permisos del fichero .env no especificados en el diseno

- **Ubicacion:** PRD, HU-01, Escenario 5
- **Severidad original:** ALTA (confianza: 90)
- **Categoria:** OWASP A05 (Security Misconfiguration) / Permisos de fichero
- **Hallazgo:** El PRD no especificaba los permisos del fichero .env.
- **Solucion aplicada:** Permisos chmod 600 aplicados. Verificado: -rw------- (propietario: r).
- **Estado: CORREGIDO (verificado 2026-03-13)**

### Hallazgos medios (fase de diseno)

#### SEC-06: Ausencia de rate limiting propio ante la API de Trello

- **Ubicacion:** PRD, seccion 9 (riesgos), HU-05
- **Severidad:** MEDIA (confianza: 80)
- **Categoria:** OWASP A05 (Security Misconfiguration) / Denegacion de servicio
- **Hallazgo:** El PRD menciona "retry con backoff exponencial" pero no especifica un rate limiter propio del lado del plugin.
- **Estado: CORREGIDO EN CODIGO (verificado 2026-03-13)**
- **Verificacion:** trello-client.ts:174-195 implementa waitForRateLimit() con ventana deslizante de 1 segundo y limite por defecto de 10 peticiones/segundo (configurable). trello-client.ts:197-240 implementa executeWithRetry() con maximo 3 reintentos y backoff exponencial (1s/2s/4s). Los codigos HTTP reintentables (429, 500, 502, 503, 504) estan correctamente definidos. Los 401/403/404 NO se reintentan. Correcto.

#### SEC-07: Validacion de entrada de credenciales insuficientemente especificada

- **Ubicacion:** PRD, HU-01, Escenario 2 y 3
- **Severidad:** MEDIA (confianza: 80)
- **Categoria:** OWASP A03 (Injection) / Validacion de entrada
- **Hallazgo:** El PRD especifica validacion de formato para la API Key pero no para el Token.
- **Estado: PARCIALMENTE CORREGIDO EN CODIGO (verificado 2026-03-13)**
- **Verificacion:** El constructor de TrelloClient valida que apiKey y token no estan vacios y aplica trim(). La skill de onboarding SI especifica validacion de formato (32 hex para API Key, 64 hex para Token). La validacion de formato recae en el LLM, no en el codigo compilado. Ver SEC-11.

#### SEC-08: Ausencia de logging de seguridad en el diseno

- **Ubicacion:** PRD, todas las HU
- **Severidad:** MEDIA (confianza: 85)
- **Categoria:** OWASP A09 (Security Logging and Monitoring Failures)
- **Hallazgo:** El PRD no contempla requisitos de logging de seguridad.
- **Estado: PARCIALMENTE CORREGIDO EN CODIGO (verificado 2026-03-13)**
- **Verificacion:** El servidor MCP emite logs a stderr: inicio del servidor (con credenciales enmascaradas), conexion al transporte, errores fatales. Las credenciales se enmascaran correctamente. Sin embargo, no se registran eventos de uso de herramientas ni errores de la API. Ver SEC-12.

#### SEC-09: Posible inconsistencia en la deteccion de duplicados en Trello

- **Ubicacion:** PRD, HU-05, Escenario 1
- **Severidad:** MEDIA (confianza: 80)
- **Categoria:** OWASP A04 (Insecure Design) / Integridad de datos
- **Hallazgo:** La deteccion de duplicados se basa en "comparacion por titulo", que es manipulable.
- **Estado: CORREGIDO (2026-03-13)**
- **Verificacion:** search-cards.ts busca tanto por nombre como por pspo-id embebido en la descripcion. create-cards.ts inyecta automaticamente un tag `<!-- pspo-id: PREFIX-HASH -->` en la descripcion de cada tarjeta. El hash SHA-256 se genera a partir del nombre y la descripcion, garantizando unicidad. Si la descripcion ya contiene un tag pspo-id, no se duplica. 3 tests nuevos cubren este comportamiento.

#### SEC-10: Incoherencia en URL de expiracion entre .env.example y PRD

- **Ubicacion:** .env.example linea 10 y docs/prd.md seccion 7, linea 627
- **Severidad:** MEDIA (confianza: 95)
- **Categoria:** OWASP A05 (Security Misconfiguration) / Incoherencia diseno-implementacion
- **Estado: CORREGIDO (verificado 2026-03-13)**
- **Verificacion:** El .env.example actual (linea 10) dice expiration=30days. El PRD seccion 7 (linea 627) dice expiration=30days. La skill de onboarding (linea 85) dice expiration=30days. Todas las fuentes son coherentes.

---

## 3. Analisis de superficie de ataque

### 3.1 Datos sensibles que maneja el plugin

| Dato | Clasificacion | Donde se almacena | Riesgo |
|------|--------------|-------------------|--------|
| TRELLO_API_KEY | Credencial | .env (texto plano, permisos 600) | Alto: identifica la aplicacion |
| TRELLO_TOKEN | Credencial | .env (texto plano, permisos 600) | Critico: acceso completo a tableros (mitigado con expiracion 30 dias) |
| TRELLO_BOARD_ID | Configuracion | .env | Bajo: no es secreto |
| Nombre de usuario de Trello | Dato personal | Mostrado en terminal | Bajo: visible durante onboarding |
| Historias de usuario | Informacion de negocio | docs/ (ficheros markdown) | Medio: propiedad intelectual |
| Vision de producto | Informacion de negocio | docs/vision.md | Medio: estrategia del negocio |

### 3.2 Vectores de ataque

| Vector | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Leak del .env (commit accidental, backup, acceso fisico) | Media | Critico | .gitignore, permisos 600, hooks de seguridad |
| Inspeccion SSL en entorno corporativo | Baja | Alto | Documentar limitacion, recomendar precaucion (riesgo aceptado) |
| Malware con acceso al sistema de ficheros | Baja | Critico | Permisos restrictivos, cifrado de disco |
| Manipulacion del plugin antes de la instalacion | Baja | Critico | Distribucion por canal oficial, checksums |
| Ataque de clipboard (copy-paste manipulado) | Baja | Medio | Validacion estricta de formato de credenciales |
| Token filtrado en logs de error | Media | Alto | Enmascaramiento implementado y verificado |
| Token comprometido | Media | Medio (reducido) | Expiracion 30 dias limita la ventana de exposicion |

### 3.3 Proteccion de credenciales (estado post-implementacion)

| Medida | Estado diseno | Estado codigo | Resultado |
|--------|--------------|--------------|-----------|
| .env en .gitignore | OK | OK (.env y .env.* excluidos, !.env.example) | OK |
| Permisos del .env (600) | Obligatorio | Aplicado (-rw-------) | OK |
| Enmascaramiento en logs | Obligatorio | Implementado (maskCredential, getMaskedApiKey, getMaskedToken) | OK |
| Expiracion del token | 30 dias | Coherente en PRD, .env.example, onboarding SKILL.md | OK |
| Validacion de formato de credenciales | Completa | Parcial (trim + no-vacio en codigo; formato en skill) | PARCIAL |
| Rate limiting del cliente | Obligatorio | Implementado (10 req/s ventana deslizante) | OK |
| Backoff exponencial | Obligatorio | Implementado (1s/2s/4s, max 3 reintentos) | OK |
| Sanitizacion de parametros | Obligatorio | Implementado (sanitizeString, URL.searchParams.set) | OK |
| Credenciales via env vars (no hardcoded) | Obligatorio | process.env.TRELLO_API_KEY, process.env.TRELLO_TOKEN | OK |
| Hook PreToolUse (check-env) | Recomendado | Implementado, robusto | OK |
| Hook PostToolUse (check-gitignore) | Recomendado | Implementado, robusto | OK |

---

## 4. Compliance

### 4.1 RGPD (Reglamento General de Proteccion de Datos)

#### Datos personales que maneja el plugin

| Dato | Es dato personal | Base legal | Articulo |
|------|-----------------|------------|----------|
| Nombre de usuario de Trello | Si | Contrato / Interes legitimo | Art. 6 |
| Nombre completo de Trello | Si | Contrato / Interes legitimo | Art. 6 |
| Historias de usuario (podrian contener nombres de personas) | Potencialmente | Depende del contenido | Art. 5 |

**Evaluacion:**

El plugin maneja datos personales minimos (nombre y nombre de usuario de Trello). Estos datos se obtienen de la API de Trello como parte de la verificacion de credenciales y no se almacenan persistentemente (se muestran en terminal durante el onboarding).

**Verificacion en codigo:** verify-credentials.ts solo obtiene id, fullName, username y url del endpoint /1/members/me. Estos datos se devuelven al LLM como resultado de la herramienta y se muestran en terminal. No se almacenan en disco. **CUMPLE Art. 5 (minimizacion).**

**Nivel de riesgo RGPD: BAJO.** El plugin maneja datos personales minimos y no los almacena.

### 4.2 NIS2 (Directiva de Seguridad de Redes y Sistemas de Informacion)

**Evaluacion:** NIS2 aplica a operadores esenciales e importantes. Un plugin de Claude Code para gestion de producto no es un operador esencial ni importante. Sin embargo, si el plugin se usa en una organizacion sujeta a NIS2, debe cumplir con los requisitos de cadena de suministro.

**Nivel de riesgo NIS2: NO APLICA directamente.** SBOM generado (ver seccion 10).

### 4.3 CRA (Cyber Resilience Act)

**Evaluacion:** El CRA aplica a productos con elementos digitales puestos en el mercado de la UE. Si el plugin se distribuye (incluso de forma gratuita), podria estar sujeto al CRA.

**Estado post-implementacion:**
1. **SBOM:** Generado (ver seccion 10). CUMPLE.
2. **Ciclo de vida seguro:** Auditoria de seguridad en diseno y codigo. CUMPLE.
3. **Actualizaciones de seguridad:** El plugin usa npm para dependencias, actualizables con npm update. CUMPLE.
4. **Gestion de vulnerabilidades:** npm audit integrado. 0 vulnerabilidades conocidas. CUMPLE.

**Nivel de riesgo CRA: BAJO tras generacion del SBOM.**

### 4.4 Verificacion del .gitignore

| Verificacion | Resultado |
|-------------|-----------|
| .env incluido | OK (.env y .env.* excluidos) |
| Excepcion para .env.example | OK (!.env.example) |
| node_modules excluido | OK |
| Directorios de build excluidos | OK (dist/, build/) |
| Ficheros de IDE excluidos | OK (.vscode/, .idea/) |
| Ficheros de SO excluidos | OK (.DS_Store, Thumbs.db) |

**Evaluacion: CORRECTO.**

---

## PARTE II: Auditoria de codigo (post-implementacion)

## 5. Revision del servidor MCP contra medidas de seguridad

### 5.1 SEC-06 (rate limiting): IMPLEMENTADO

- **Ubicacion:** trello-client.ts:174-195
- **Mecanismo:** Ventana deslizante de 1 segundo con limite configurable (por defecto 10 req/s). Limpia timestamps antiguos, espera si se excede el limite, registra cada peticion.
- **Evaluacion:** Correcto. El rate limiter es conservador (10 req/s frente al limite de Trello de 100 req/10s = 10 req/s). Protege contra rafagas y bucles de reintento.
- **Backoff:** executeWithRetry() en trello-client.ts:197-240 implementa maximo 3 reintentos con delays de 1000ms, 2000ms y 4000ms. Los codigos 429, 500, 502, 503, 504 se reintentan; 400, 401, 403, 404 se lanzan inmediatamente.
- **Valoracion: CORRECTO. SEC-06 resuelto.**

### 5.2 SEC-07 (validacion de credenciales): PARCIALMENTE IMPLEMENTADO

- **Ubicacion:** trello-client.ts:89-100 (constructor), index.ts:23-37 (lectura de env)
- **Validacion implementada:**
  - Verifica que apiKey y token no son vacios ni solo espacios.
  - Aplica trim() a ambos.
  - index.ts sale con process.exit(1) si faltan variables de entorno.
- **Validacion NO implementada en el codigo compilado:**
  - No se valida formato hexadecimal de 32 caracteres para API Key.
  - No se valida patron ATTA + longitud para Token.
- **Mitigacion parcial:** La skill onboarding/SKILL.md (lineas 62-77 y 109-125) instruye al LLM para validar estos formatos. Esto funciona como capa de defensa pero depende del comportamiento del LLM, no de logica determinista.
- **Valoracion: PARCIAL. Ver hallazgo SEC-11.**

### 5.3 SEC-08 (enmascaramiento en logs): IMPLEMENTADO

- **Ubicacion:** index.ts:17-19 (maskCredential), trello-client.ts:102-114 (getMaskedApiKey, getMaskedToken)
- **Mecanismo:** Muestra solo los ultimos 4 caracteres, precedidos de asteriscos. Si la credencial tiene 4 o menos caracteres, devuelve solo asteriscos.
- **Puntos de log verificados:**
  - index.ts:41-43: Log de inicio con credenciales enmascaradas. CORRECTO.
  - index.ts:27-35: Mensajes de error si faltan variables. No expone valores. CORRECTO.
  - trello-client.ts:217-230: Errores HTTP. No incluyen URL (que contiene credenciales). CORRECTO.
  - index.ts:405: Log de conexion. Sin datos sensibles. CORRECTO.
  - index.ts:409: Error fatal. Solo muestra el error, sin credenciales. CORRECTO.
- **Analisis de buildErrorDescription() (trello-client.ts:19-67):** Los mensajes de error incluyen responseBody de la API de Trello. Trello NO devuelve credenciales en sus respuestas de error, asi que esto es seguro. El responseBody se incluye directamente en el throw Error que llega al LLM. No expone credenciales pero si podria exponer informacion interna de Trello.
- **Valoracion: CORRECTO. SEC-08 resuelto para enmascaramiento. Logging de eventos de seguridad sigue pendiente (ver SEC-12).**

### 5.4 Construccion segura de URLs (inyeccion)

- **Ubicacion:** trello-client.ts:153-172 (buildUrl)
- **Mecanismo:**
  1. El path se sanitiza con sanitizeString() (elimina caracteres de control).
  2. Se construye con new URL() que valida la estructura.
  3. Las credenciales y parametros se inyectan con url.searchParams.set(), que aplica encoding automatico de URL.
  4. Las claves y valores de parametros adicionales se sanitizan con sanitizeString().
- **Analisis de inyeccion:**
  - sanitizeString() en trello-client.ts:69-72 elimina caracteres de control (U+0000-U+001F excepto tab, U+007F, saltos de linea). Previene inyeccion de caracteres de control.
  - Los IDs de Trello (boardId, listId, labelId) se interpolan directamente en el path. buildUrl() pasa el path por sanitizeString() antes de construir con new URL(). El constructor de URL valida la estructura.
  - Zod en index.ts valida que los IDs son z.string(), lo que previene tipos inesperados.
- **Riesgo residual:** Un boardId como ../members/me se sanitizaria pero los caracteres ../ NO se eliminan. Sin embargo, new URL() resuelve paths relativos dentro del dominio api.trello.com. No es un vector de inyeccion explotable porque HTTPS asegura que la peticion va a Trello, y Trello validara el recurso solicitado. Ver hallazgo SEC-13.
- **Valoracion: CORRECTO con nota menor. La construccion de URLs es segura contra inyeccion gracias a new URL() y searchParams.set().**

### 5.5 Sanitizacion de parametros

- **Ubicacion:** Todas las herramientas en src/tools/*.ts
- **Verificacion:**
  - Todos los parametros obligatorios se validan con !input.X || input.X.trim().length === 0.
  - Los strings de usuario (nombres de tableros, listas, etiquetas, tarjetas) se pasan por .trim() antes de enviarlos a la API.
  - Los parametros se envian como JSON body (POST/PUT) o como query params (GET) via url.searchParams.set().
  - Zod en index.ts valida tipos y enums para acciones y colores de etiquetas.
- **Valoracion: CORRECTO. La validacion de entrada es adecuada para el contexto.**

---

## 6. Revision de hooks de seguridad

### 6.1 check-env.sh (PreToolUse)

- **Ubicacion:** /home/r/Escritorio/PSPO_AI/hooks/scripts/check-env.sh
- **Proposito:** Bloquea llamadas al servidor MCP de Trello si falta .env o las credenciales.
- **Analisis:**
  - Usa set -euo pipefail. Correcto: falla ante errores, variables no definidas o fallos en pipes.
  - Lee .env con grep -E y extrae el valor con cut -d'=' -f2-. El f2- es correcto: toma todo despues del primer =, asi que valores con = internos no se truncan.
  - tr -d '[:space:]' elimina espacios. Correcto.
  - El || true al final del grep evita que set -e mate el script si la variable no existe.
  - Devuelve exit code 2 (BLOCKED) si falta algo, 0 si todo esta bien.
- **Posibilidad de bypass:** Si alguien crea un .env con TRELLO_API_KEY=basura, el hook lo aceptara. Esto es comportamiento esperado: el hook solo verifica presencia, no validez. La validez la verifica verify-credentials.
- **Paths con espacios:** La variable ENV_FILE esta entrecomillada en todos los usos. Correcto.
- **Valoracion: ROBUSTO. Sin problemas de seguridad.**

### 6.2 check-gitignore.sh (PostToolUse)

- **Ubicacion:** /home/r/Escritorio/PSPO_AI/hooks/scripts/check-gitignore.sh
- **Proposito:** Avisa (sin bloquear) si se escribe un .env que no esta en .gitignore.
- **Analisis:**
  - Usa set -euo pipefail. Correcto.
  - Lee el JSON del stdin y extrae file_path o path con grep + sed. Parseo robusto para el caso de uso.
  - Excluye .env.example correctamente (no necesita estar en .gitignore).
  - Verifica .gitignore con multiples patrones: ^\.env$, ^\.env\s, ^\.env\*, ^\.env\.\*.
  - Siempre devuelve exit code 0 (no bloquea, solo avisa). Correcto: bloquear escrituras podria causar perdida de datos.
- **Posibilidad de bypass:** Si el JSON del hook no incluye file_path ni path, el hook sale silenciosamente con 0. Esto es seguro: no hay falso negativo peligroso.
- **Paths con espacios:** Todas las variables estan entrecomilladas. Correcto.
- **Valoracion: ROBUSTO. Comportamiento correcto como aviso no bloqueante.**

---

## 7. Revision de la configuracion MCP (.mcp.json)

- **Ubicacion:** /home/r/Escritorio/PSPO_AI/.mcp.json
- **Contenido verificado:**
  - Credenciales se pasan como variables de entorno: "TRELLO_API_KEY": "${TRELLO_API_KEY}", "TRELLO_TOKEN": "${TRELLO_TOKEN}".
  - NO hay credenciales hardcodeadas. Las variables se resuelven desde el entorno del proceso padre (Claude Code, que las lee del .env).
  - El comando es node con el path al JS compilado. Sin flags inseguros.
- **Valoracion: CORRECTO. Sin problemas de seguridad.**

---

## 8. Revision de skills con acceso a credenciales

### 8.1 skills/onboarding/SKILL.md

- **Analisis de seguridad del prompt:**
  - Instruye al LLM a validar formato de API Key (32 hex) y Token (64 hex).
  - Instruye a no guardar credenciales invalidas.
  - Instruye a establecer permisos 600 en .env.
  - Instruye a verificar .gitignore.
  - Seccion "Reglas de seguridad" (lineas 317-324): NUNCA mostrar credenciales completas, SIEMPRE verificar .gitignore, SIEMPRE permisos 600, NO guardar el Secret.
- **Riesgo de exposicion de credenciales por el LLM:** El prompt es claro y explicitamente prohibe mostrar credenciales. El LLM podria (en teoria) ignorar estas instrucciones si se le pide explicitamente. Esto es una limitacion inherente de los sistemas basados en LLM, no un defecto del plugin.
- **Valoracion: CORRECTO. Las instrucciones de seguridad son claras y completas.**

### 8.2 skills/start/SKILL.md

- **Analisis de seguridad del prompt:**
  - Instruye a no mostrar informacion de credenciales (API Key, Token). Solo el nombre de la cuenta.
  - La verificacion de credenciales es "silenciosa" (no muestra resultado al usuario si es exitosa).
  - No hay instrucciones que pudieran llevar al LLM a exponer credenciales.
- **Valoracion: CORRECTO. Sin riesgos detectados.**

---

## 9. OWASP Top 10 sobre el codigo implementado

### A01 - Broken Access Control

- **Hallazgo:** El servidor MCP no implementa control de acceso propio porque opera como proceso local comunicado via stdio. Solo el proceso que lo lanza (Claude Code) puede enviar peticiones. No hay endpoint de red expuesto.
- **Credenciales:** Se inyectan via variables de entorno al lanzar el proceso. No se aceptan credenciales como parametros de herramientas.
- **Valoracion: NO APLICA. El modelo de seguridad se basa en aislamiento de proceso (stdio).**

### A02 - Cryptographic Failures

- **Hallazgo:** Las credenciales se almacenan en .env sin cifrar (texto plano). Esto se acepta como riesgo residual con mitigaciones (permisos 600, .gitignore). La comunicacion con Trello es HTTPS (cifrado en transito).
- **Algoritmos:** No se usan algoritmos criptograficos propios. Se delega en TLS del runtime de Node.js.
- **Valoracion: RIESGO RESIDUAL ACEPTADO (SEC-04). Sin fallos criptograficos propios.**

### A03 - Injection

- **Hallazgo:** Las URLs se construyen con new URL() + searchParams.set(). Los IDs de Trello se interpolan en paths pero pasan por sanitizeString(). Los bodies JSON se construyen con JSON.stringify(). No se usa eval, Function(), child_process ni ninguna forma de ejecucion dinamica de codigo.
- **Valoracion: NO VULNERABLE. La construccion de URLs es segura.**

### A07 - Authentication Failures

- **Hallazgo:** Las credenciales se validan contra la API de Trello (endpoint /1/members/me). Si son invalidas, el servidor devuelve un error descriptivo. Las credenciales no se reusan en otros contextos. No hay sesiones, cookies ni mecanismos de autenticacion propios.
- **Valoracion: CORRECTO. La autenticacion se delega a la API de Trello.**

### A09 - Security Logging and Monitoring

- **Hallazgo:** El logging es minimo: inicio del servidor, conexion al transporte, errores fatales. No se registran eventos de uso de herramientas, errores de la API ni patrones de actividad.
- **Valoracion: INSUFICIENTE para deteccion de anomalias. Ver SEC-12.**

---

## 10. Hallazgos de la auditoria de codigo

### SEC-11: Validacion de formato de credenciales solo en la skill, no en codigo compilado

- **Ubicacion:** trello-client.ts:89-100
- **Severidad:** MEDIA (confianza: 80)
- **Categoria:** OWASP A03 (Injection) / Validacion de entrada
- **Hallazgo:** El constructor de TrelloClient valida que las credenciales no estan vacias y aplica trim(), pero no valida el formato (32 hex para API Key, patron ATTA para Token). La validacion de formato esta definida unicamente en la skill de onboarding, que depende del comportamiento del LLM. Si el LLM no ejecuta la validacion correctamente, o si las credenciales se configuran manualmente, no hay capa de defensa en codigo.
- **Vector de ataque:** Un usuario configura manualmente el .env con un valor malformado o un atacante inyecta contenido via modificacion del .env.
- **Impacto:** Peticiones malformadas a la API de Trello. Riesgo bajo porque Trello rechazaria credenciales invalidas con 401.
- **Solucion recomendada:** Anadir validacion de formato en el constructor de TrelloClient. Verificar que la API Key tiene 32 caracteres hexadecimales y que el Token tiene la longitud y formato esperados.
- **Estado: CORREGIDO (2026-03-13)**
- **Verificacion:** El constructor de TrelloClient valida: API Key con regex `/^[a-f0-9]{32}$/i`, Token con prefijo ATTA, longitud minima 41 y solo alfanumericos. Los mensajes de error no incluyen el valor de la credencial. 6 tests nuevos cubren este comportamiento.

### SEC-12: Logging de eventos de seguridad insuficiente

- **Ubicacion:** index.ts (handlers de herramientas), trello-client.ts (executeWithRetry)
- **Severidad:** MEDIA (confianza: 85)
- **Categoria:** OWASP A09 (Security Logging and Monitoring Failures)
- **Hallazgo:** No se registran en los logs del servidor: invocaciones de herramientas, resultados de verificacion de credenciales, errores de la API, reintentos, rate limiting activado. Solo se registran el inicio del servidor y errores fatales. Esto impide detectar uso anomalo del plugin.
- **Vector de ataque:** Un atacante con acceso a las credenciales usa el plugin sin dejar rastro.
- **Impacto:** Incapacidad para detectar uso indebido o depurar problemas en produccion.
- **Solucion recomendada:** Anadir logs de nivel INFO para invocaciones de herramientas y errores de la API (sin credenciales), logs de nivel WARN para reintentos y rate limiting, y logs de nivel ERROR para fallos de autenticacion.
- **Estado: CORREGIDO (2026-03-13)**
- **Verificacion:** Se ha anadido la funcion securityLog() que escribe a stderr con prefijo `[trello-mcp] [SEGURIDAD]`. Se loggean: validacion exitosa de credenciales (enmascaradas), cada llamada a la API (metodo + path, sin credenciales), errores HTTP (codigo + endpoint, sin credenciales), activacion del rate limiter, reintentos con backoff. 6 tests nuevos cubren este comportamiento.

### SEC-13: IDs de Trello interpolados en path sin validacion de formato

- **Ubicacion:** tools/get-board.ts:13, tools/manage-lists.ts:42,65,90,108, tools/manage-labels.ts:35,66,85, tools/search-cards.ts:17
- **Severidad:** BAJA (confianza: 82)
- **Categoria:** OWASP A03 (Injection) / Validacion de entrada
- **Hallazgo:** Los IDs de Trello (boardId, listId, labelId) se interpolan directamente en el path de la URL via template literals. Aunque sanitizeString() elimina caracteres de control y new URL() valida la estructura, un ID con caracteres como / o .. podria alterar el path de la peticion. Sin embargo, la URL resultante siempre apunta a api.trello.com y Trello validara el recurso solicitado.
- **Vector de ataque:** Un ID malicioso como abc/../members/me se resolveria a una URL que Trello normalizaria y responderia con 404 o 400.
- **Impacto:** Nulo en la practica. Trello rechaza IDs invalidos. No hay posibilidad de SSRF porque la base URL esta hardcodeada a https://api.trello.com.
- **Solucion recomendada (defensa en profundidad):** Validar que los IDs de Trello contienen solo caracteres alfanumericos antes de interpolados en el path.

### SEC-14: Cobertura de tests al 0%

- **Ubicacion:** Directorio tests/ (inexistente en src/)
- **Severidad:** BAJA (confianza: 95)
- **Categoria:** OWASP A04 (Insecure Design) / Falta de tests de seguridad
- **Hallazgo:** SonarQube reporta 0% de cobertura de tests. No existe ningun fichero de test en el directorio src/ del proyecto. El package.json tiene configurado vitest pero no hay tests escritos. La validacion del rate limiter, la sanitizacion de URLs y el enmascaramiento de credenciales no estan cubiertos por tests automatizados.
- **Vector de ataque:** Un cambio futuro en el codigo podria romper las medidas de seguridad sin deteccion.
- **Impacto:** Riesgo de regresiones de seguridad no detectadas.
- **Solucion recomendada:** Escribir tests unitarios que verifiquen al menos: sanitizeString() elimina caracteres de control, maskCredential/getMaskedApiKey/getMaskedToken enmascaran correctamente, waitForRateLimit() respeta el limite, buildUrl() no expone credenciales en paths inyectados, el constructor de TrelloClient rechaza credenciales vacias.

### SEC-15: Signature de server.tool() deprecated en el SDK de MCP

- **Ubicacion:** index.ts lineas 51, 81, 118, 152, 191, 244, 309, 360
- **Severidad:** BAJA (confianza: 90)
- **Categoria:** OWASP A06 (Vulnerable and Outdated Components) / API deprecated
- **Hallazgo:** SonarQube identifica 8 usos de la signature deprecated de server.tool() del SDK @modelcontextprotocol/sdk. La version actual del SDK (1.27.1) ha deprecado la firma (name, description, paramsSchema, callback) a favor de una nueva API.
- **Vector de ataque:** No es un vector de ataque directo, pero el uso de APIs deprecated indica que la version del SDK podria dejar de ser soportada.
- **Impacto:** El codigo seguira funcionando pero podria romperse en futuras versiones del SDK.
- **Solucion recomendada:** Actualizar las llamadas a server.tool() a la firma recomendada por la version actual del SDK.

---

## 11. Resultados de SonarQube

**SonarQube Community Build 26.3.0** -- Ejecutado 2026-03-13.

### Resumen de metricas

| Metrica | Valor | Evaluacion |
|---------|-------|------------|
| Lineas de codigo (ncloc) | 1087 | -- |
| Bugs | 6 | Falsos positivos (ver analisis) |
| Vulnerabilidades | 0 | OK |
| Security Hotspots | 0 | OK |
| Code Smells | 10 | 8 deprecated API + 1 modernizacion + 1 estilo |
| Cobertura de tests | 0.0% | INSUFICIENTE (ver SEC-14) |
| Lineas duplicadas | 9.4% | Aceptable (patron repetitivo de handlers) |
| Deuda tecnica | 0.4% | BAJO |

### Analisis de los 6 bugs reportados

Todos los bugs son del tipo typescript:S6324 ("Remove this control character") en trello-client.ts:71 (funcion sanitizeString()).

**Evaluacion:** Son **falsos positivos**. La funcion sanitizeString() usa una regex con caracteres de control INTENCIONALMENTE para detectarlos y eliminarlos. SonarQube detecta los caracteres de control literales en la regex y los reporta como bugs. La funcion es correcta y cumple su proposito de seguridad (sanitizacion de entrada).

### Analisis de los 10 code smells

| Regla | Cantidad | Descripcion | Evaluacion |
|-------|----------|-------------|------------|
| typescript:S1874 | 8 | Uso de signature deprecated de server.tool() | Ver SEC-15. Actualizar cuando el SDK lo requiera. |
| typescript:S7785 | 1 | Preferir top-level await sobre main().catch() | Mejora de estilo. Baja prioridad. |
| typescript:S7781 | 1 | Preferir replaceAll() sobre replace() con regex | Mejora de estilo. Baja prioridad. |

---

## 12. Auditoria de dependencias (implementacion)

### 12.1 Dependencia de produccion

| Paquete | Version instalada | CVEs conocidos | Licencia | Mantenimiento | Veredicto |
|---------|-------------------|----------------|----------|---------------|-----------|
| @modelcontextprotocol/sdk | 1.27.1 | 0 (npm audit limpio) | MIT | Activo (Anthropic) | APROBADA |

### 12.2 Dependencias de desarrollo

| Paquete | Version instalada | CVEs conocidos | Licencia | Veredicto |
|---------|-------------------|----------------|----------|-----------|
| @types/node | 25.5.0 | 0 | MIT | APROBADA |
| typescript | 5.9.3 | 0 | Apache-2.0 | APROBADA |
| vitest | 3.2.4 | 0 | MIT | APROBADA |

### 12.3 Dependencias transitivas relevantes (produccion)

El SDK de MCP arrastra 60+ dependencias transitivas. Las mas relevantes para seguridad:

| Paquete | Version | Proposito | CVEs | Evaluacion |
|---------|---------|-----------|------|------------|
| express | 5.2.1 | Framework HTTP (usado por el SDK para modo SSE) | 0 | Express 5 es la version actual. OK. |
| zod | 4.3.6 | Validacion de esquemas (usado por el SDK) | 0 | OK. |
| jose | 6.2.1 | JWT/JWK/JWE (usado por el SDK para OAuth) | 0 | OK. |
| ajv | 8.18.0 | Validacion JSON Schema | 0 | OK. |
| cors | 2.8.6 | CORS middleware | 0 | No aplica (servidor stdio, no HTTP). |
| hono | 4.12.7 | Framework HTTP alternativo | 0 | No aplica (servidor stdio). |

### 12.4 Resultado de npm audit

```
found 0 vulnerabilities
```

**Evaluacion: LIMPIO. 0 CVEs conocidos en todas las dependencias.**

### 12.5 Nota sobre la superficie de ataque de las dependencias transitivas

El SDK de MCP incluye express, hono, cors y express-rate-limit como dependencias de produccion. Estas dependencias son para el modo de transporte HTTP/SSE del SDK. El servidor trello-mcp usa exclusivamente el transporte stdio (proceso local, sin socket de red). Las dependencias HTTP nunca se ejecutan en este contexto, pero estan presentes en node_modules y podrian ser importadas por codigo malicioso si el proceso se compromete. Esto se acepta como riesgo inherente al usar el SDK oficial.

---

## 13. SBOM (Software Bill of Materials)

### Componente principal

| Campo | Valor |
|-------|-------|
| Nombre | trello-mcp |
| Version | 1.0.0 |
| Tipo | Servidor MCP (Node.js) |
| Licencia | (sin especificar en package.json) |
| Runtime | Node.js >= 18 |

### Dependencias directas de produccion

| Paquete | Version | Licencia | Proveedor |
|---------|---------|----------|-----------|
| @modelcontextprotocol/sdk | ^1.12.1 (instalada: 1.27.1) | MIT | Anthropic |

### Dependencias directas de desarrollo

| Paquete | Version | Licencia | Proveedor |
|---------|---------|----------|-----------|
| @types/node | ^25.5.0 (instalada: 25.5.0) | MIT | DefinitelyTyped |
| typescript | ^5.7.0 (instalada: 5.9.3) | Apache-2.0 | Microsoft |
| vitest | ^3.0.0 (instalada: 3.2.4) | MIT | Vitest Team |

### Dependencias transitivas de produccion (principales)

| Paquete | Version | Licencia |
|---------|---------|----------|
| ajv | 8.18.0 | MIT |
| ajv-formats | 3.0.1 | MIT |
| content-type | 1.0.5 | MIT |
| cors | 2.8.6 | MIT |
| cross-spawn | 7.0.6 | MIT |
| eventsource | 3.0.7 | MIT |
| eventsource-parser | 3.0.6 | MIT |
| express | 5.2.1 | MIT |
| express-rate-limit | 8.3.1 | MIT |
| hono | 4.12.7 | MIT |
| @hono/node-server | 1.19.11 | MIT |
| jose | 6.2.1 | MIT |
| json-schema-typed | 8.0.2 | ISC |
| pkce-challenge | 5.0.1 | MIT |
| raw-body | 3.0.2 | MIT |
| zod | 4.3.6 | MIT |
| zod-to-json-schema | 3.25.1 | ISC |

### Compatibilidad de licencias

Todas las dependencias usan licencias MIT, Apache-2.0 o ISC. Todas son compatibles entre si y con cualquier licencia que se aplique al proyecto. No hay licencias restrictivas (AGPL, GPL) en la cadena de dependencias.

---

## 14. Notas de baja confianza (60-79)

Estas notas no se consideran hallazgos confirmados, pero merecen evaluacion por parte del equipo:

1. **(Confianza: 70) Posible exposicion de informacion de negocio en docs/.** Si el repositorio es publico y contiene docs/vision.md con estrategia de producto, esta informacion es accesible. Evaluar si docs/ deberia estar en .gitignore para repositorios publicos.

2. **(Confianza: 65) Riesgo de phishing via terminal.** Un atacante con acceso al sistema podria crear un alias o script que suplante al plugin y solicite credenciales. Riesgo teorico, dificil de explotar sin acceso previo al sistema.

3. **(Confianza: 60) Dependencia del estado de la API de Trello.** Si Trello cambia el formato de autenticacion o deprecia la API v1, el plugin dejaria de funcionar. Monitorizar el changelog de la API de Trello.

4. **(Confianza: 70) Dependencias HTTP transitivas no necesarias en modo stdio.** El SDK de MCP trae express, hono y cors aunque el servidor solo usa transporte stdio. Estas dependencias amplian la superficie de ataque del node_modules sin beneficio funcional.

5. **(Confianza: 65) El hook check-env.sh usa path relativo.** ENV_FILE=".env" asume que el directorio de trabajo es la raiz del proyecto. Si Claude Code cambia el cwd del hook, el check fallara o pasara incorrectamente.

---

## 15. Recomendaciones de seguridad actualizadas

### Prioridad 1: Resueltas

1. ~~**Eliminar TRELLO_API_SECRET del .env y del diseno.**~~ CORREGIDO.
2. ~~**Actualizar .env.example en el repositorio.**~~ CORREGIDO.
3. ~~**Especificar permisos 600 para el fichero .env.**~~ CORREGIDO.
4. ~~**Cambiar la expiracion del token a 30 dias.**~~ CORREGIDO (todas las fuentes coherentes).
5. ~~**Implementar rate limiting del lado del cliente.**~~ CORREGIDO (SEC-06).
6. ~~**Enmascaramiento obligatorio de credenciales en logs.**~~ CORREGIDO (SEC-08).
7. ~~**Corregir incoherencia en URL de expiracion.**~~ CORREGIDO (SEC-10).

### Prioridad 2: Resueltos (2026-03-13)

8. ~~**Anadir validacion de formato de credenciales en codigo compilado.**~~ CORREGIDO (SEC-11).
9. ~~**Anadir logging de eventos de seguridad.**~~ CORREGIDO (SEC-12).
10. ~~**Implementar deteccion de duplicados por ID, no solo por titulo.**~~ CORREGIDO (SEC-09).

### Prioridad 3: Recomendadas (mejores practicas)

11. **Validar formato de IDs de Trello (solo alfanumericos).** (SEC-13, BAJA)
12. **Escribir tests unitarios para funciones de seguridad.** (SEC-14, BAJA)
13. **Actualizar signature de server.tool() a la no deprecated.** (SEC-15, BAJA)
14. **Informar al usuario sobre datos accedidos (RGPD Art. 13).**
15. **Recomendar al usuario cifrado de disco.**

---

## VEREDICTO

**VEREDICTO: APROBADO CON CONDICIONES**

**Resumen:** La auditoria de codigo del servidor MCP trello-client revela una implementacion solida en terminos de seguridad. Las medidas criticas comprometidas en la fase de diseno (rate limiting, enmascaramiento de credenciales, sanitizacion de entrada, construccion segura de URLs) estan correctamente implementadas. SonarQube reporta 0 vulnerabilidades y 0 security hotspots. npm audit reporta 0 CVEs conocidos. No se han encontrado secretos hardcodeados, inyecciones, fallos criptograficos ni controles de acceso rotos. Los hooks de seguridad son robustos. Las skills no contienen instrucciones que pudieran llevar al LLM a exponer credenciales.

**Hallazgos bloqueantes:** Ninguno.

**Condiciones pendientes (no bloqueantes, requeridas antes de produccion):**
- ~~SEC-09: Deteccion de duplicados por ID, no solo por titulo (MEDIA)~~ CORREGIDO (2026-03-13).
- ~~SEC-11: Validacion de formato de credenciales en codigo compilado (MEDIA)~~ CORREGIDO (2026-03-13).
- ~~SEC-12: Logging de eventos de seguridad (MEDIA)~~ CORREGIDO (2026-03-13).

**Mejoras recomendadas (no bloqueantes):**
- SEC-13: Validacion de formato de IDs de Trello (BAJA)
- SEC-14: Tests unitarios para funciones de seguridad (BAJA) -- parcialmente resuelto: 78 tests cubren el servidor MCP.
- SEC-15: Actualizar signature deprecated de server.tool() (BAJA)

**Proxima accion recomendada:**
1. ~~Resolver las 3 condiciones MEDIA antes de poner el plugin en produccion.~~ RESUELTO.
2. Planificar las 3 mejoras BAJA para la siguiente iteracion.
3. Ejecutar re-auditoria cuando se implemente el flujo completo de publicacion (skills de publish y save-docs).

---

*Informe generado por El Paranoico (CSO, equipo Alfred Dev). Confianza cero. Ni en ti, ni en mi, ni en nadie.*
