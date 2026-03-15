---
name: generate-stories
description: >
  Genera historias de usuario con criterios de aceptacion en formato Given/When/Then
  a partir del contexto del descubrimiento. Se encadena automaticamente despues de
  que el descubrimiento ha sido confirmado por el usuario.
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, Write, Edit
---

# /pspo-agent:generate-stories -- Generacion de historias de usuario

## Tu rol

Actuas como el agente `product-owner` durante esta skill. Generas historias de usuario profesionales con criterios de aceptacion completos a partir del contexto recogido durante el descubrimiento.

Delega el trabajo de generacion al agente `product-owner`.

## Prerequisito

Esta skill SOLO se ejecuta despues de que el descubrimiento este completo y el usuario haya confirmado los puntos clave. Si llegas aqui sin contexto de descubrimiento, redirige a `/pspo-agent:discovery`.

## Proceso de generacion

### Paso 1: Revisar el contexto del descubrimiento

Antes de generar, revisa:

1. **Contexto confirmado:** Los puntos clave que el usuario confirmo (usuario, problema, resultado, restricciones, fuera de alcance).
2. **Historias existentes:** Lee `docs/historias/` y `docs/backlog.md` si existen, para evitar duplicados y mantener coherencia en la numeracion.
3. **Configuracion:** Lee `settings.json` para los parametros de generacion (formato, escenarios minimos, tamano maximo).

### Paso 2: Identificar roles de usuario

Lista todos los roles de usuario mencionados durante el descubrimiento. Cada rol debe ser especifico:

- MAL: "usuario", "persona", "gente"
- BIEN: "comprador registrado", "administrador del sistema", "operador de soporte"

Si solo hay un rol, esta bien. Pero confirma que es el correcto y que es especifico.

### Paso 3: Descomponer en funcionalidades independientes

Divide la necesidad del usuario en funcionalidades que se pueden implementar y entregar por separado. Cada funcionalidad sera una historia de usuario.

Criterios para la descomposicion:
- Cada historia debe aportar valor por si sola (no "preparar la base de datos").
- Cada historia debe ser implementable en 3 dias o menos.
- Si una funcionalidad es demasiado grande, descomponla en historias mas pequenas.
- Ordena por prioridad: las historias que aportan mas valor al usuario van primero.

### Paso 4: Escribir las historias

Para cada funcionalidad, escribe una historia siguiendo este formato exacto:

```markdown
### HU-{XX}: {Titulo descriptivo breve}

**Historia de usuario:**

Como {rol especifico del usuario},
quiero {accion concreta que el usuario realiza},
para {beneficio medible que obtiene el usuario}.

**Criterios de aceptacion:**

ESCENARIO 1: {nombre descriptivo del escenario positivo}
Given {contexto inicial detallado}
  And {condicion adicional si aplica}
When {accion concreta del usuario}
Then {resultado esperado verificable}
  And {resultado adicional si aplica}

ESCENARIO 2: {nombre descriptivo del escenario negativo o de borde}
Given {contexto inicial}
When {accion del usuario con datos invalidos, error o caso de borde}
Then {comportamiento esperado ante la situacion}
  And {feedback claro al usuario}

{ESCENARIOS ADICIONALES si la historia lo requiere}

**Prioridad:** {Critica | Alta | Media | Baja}

**Notas:** {contexto adicional, dependencias con otras historias, restricciones tecnicas}
```

### Reglas de calidad de las historias

#### Sobre el formato "Como X, quiero Y, para Z"

- **X (rol):** NUNCA uses "usuario". Usa el rol especifico descubierto.
- **Y (accion):** Una accion concreta, en infinitivo. "registrarme con mi email", "filtrar productos por precio", "exportar el informe a PDF".
- **Z (beneficio):** Un beneficio medible o verificable. MAL: "para que funcione bien". BIEN: "para acceder a mi cuenta sin recordar una contrasena nueva".

#### Sobre los criterios de aceptacion

Los criterios de aceptacion NO son bullets de una frase. Cada escenario es un parrafo que explica:

1. **El contexto completo** (Given): no solo el estado, sino POR QUE el usuario esta en esa situacion. Que ha pasado antes.
2. **La accion concreta** (When): que hace exactamente el usuario, con que datos, en que interfaz.
3. **Las expectativas detalladas** (Then): que debe pasar, que debe ver, que debe sentir. Las expectativas son la parte mas importante.

INCORRECTO (demasiado escueto):
  Given: el usuario esta registrado
  When: hace login
  Then: ve el dashboard

CORRECTO (detallado):
  Given: el usuario tiene una cuenta activa con email confirmado y ha accedido
  al menos una vez en los ultimos 30 dias. Su sesion anterior caduco hace 2 horas.
  When: accede a la pagina de login, introduce su email y contrasena correctos,
  y pulsa el boton "Iniciar sesion".
  Then:
  - Se autentica en menos de 2 segundos (feedback visual de carga si supera 500ms).
  - Se redirige al dashboard con sus datos personalizados del ultimo acceso.
  - Se genera un token JWT con expiracion de 24 horas.
  - Se registra la fecha y hora del acceso en el log de actividad del usuario.
  - Si tiene notificaciones pendientes, se muestra un indicador en la cabecera.

Reglas adicionales:
- **Minimo 1 escenario positivo** (happy path): el flujo normal cuando todo va bien.
- **Minimo 1 escenario negativo**: que pasa cuando algo falla (datos invalidos, error de red, permiso denegado, recurso no encontrado).
- **Valores concretos:** MAL: "una cantidad valida". BIEN: "una cantidad entre 1 y 999".
- **Given:** Establece el contexto completo. El lector no tiene que adivinar nada.
- **When:** Una sola accion. Si necesitas dos "When", probablemente son dos escenarios.
- **Then:** Resultado observable y verificable. Nada de "funciona correctamente".

#### Sobre el tamano

- Si una historia parece mayor a 3 dias de trabajo, descomponla.
- Si necesitas mas de 5 escenarios de aceptacion, la historia probablemente es demasiado grande.
- Cada historia debe poder demostrarse en una review de sprint.

#### Sobre la independencia

- Cada historia se puede implementar sin esperar a que otra este terminada.
- Si hay dependencias, mencionarlas en las notas pero asegurate de que la historia tiene valor propio.
- Evita historias "infraestructurales" como "configurar la base de datos". Eso va dentro de la primera historia que necesite persistencia.

### Paso 5: Revisar la coherencia del conjunto

Antes de presentar las historias al usuario, revisa:

1. **Cobertura:** Las historias cubren toda la necesidad descrita en el descubrimiento? Falta algo?
2. **Coherencia:** Los roles son consistentes entre historias? Los terminos se usan igual?
3. **Orden:** La prioridad tiene sentido? La historia mas valiosa esta primera?
4. **Duplicados:** Hay solapamiento entre historias? Si dos historias comparten criterios de aceptacion, probablemente se pueden fusionar.
5. **Numeracion:** Si hay historias previas en `docs/historias/`, la numeracion continua desde el ultimo numero.

### Paso extra: Analisis de edge cases

Despues de generar los criterios de aceptacion basicos (escenarios positivos y negativos), analiza cada historia para detectar edge cases:

- **Limites de datos:** que pasa con strings vacios, valores nulos, numeros negativos, textos de 10000 caracteres?
- **Concurrencia:** que pasa si dos usuarios hacen la misma accion a la vez?
- **Estado inconsistente:** que pasa si el proceso se interrumpe a mitad (cierre del navegador, perdida de red)?
- **Permisos:** que pasa si un usuario sin permisos intenta acceder?
- **Integraciones:** que pasa si un servicio externo no responde?

Presenta los edge cases detectados al usuario:

```
He detectado {N} edge cases potenciales para esta historia:

| # | Edge case | Impacto | Sugiero cubrir? |
|---|-----------|---------|-----------------|
| 1 | Email con caracteres Unicode | Medio | Si |
| 2 | Timeout del servidor SMTP | Alto | Si |
| 3 | Registro simultaneo con mismo email | Bajo | No (MVP) |

Quieres que anadamos criterios de aceptacion para los edge cases marcados?
```

Si el usuario acepta, genera criterios de aceptacion adicionales para los edge cases seleccionados.
Si rechaza, documenta los edge cases conocidos como nota al final de la historia para futuras iteraciones.

### Paso extra: Estimacion rapida

Despues de los edge cases, pide al usuario una estimacion rapida por tallas para cada historia:

```
Estimacion rapida (t-shirt sizing):

  S = 1 dia | M = 2 dias | L = 3 dias | XL = 5 dias

Asigna una talla a cada historia:

  1. HU-XX: {titulo}
  2. HU-XX: {titulo}
  ...

Formato: "1=M 2=L 3=S" o "saltar" para estimar despues:
```

Si el usuario asigna tallas, incluyelas en la tabla de metadatos de cada fichero HU (campo Estimacion). Si elige saltar, deja el campo vacio y el sprint-plan o el publish lo pediran despues.

### Revision de estilo

Antes de presentar las historias al usuario, pasa todo el contenido generado por el agente `culture-guardian` para revision de estilo. El agente:
- Corrige acentos y enes (configuracion -> configuración, pequeno -> pequeño)
- Aplica tono profesional y detallista
- Verifica que los criterios de aceptacion son concretos y no genericos
- Lee aprendizajes previos del proyecto de la memoria de Claude Code

Solo despues de la revision de estilo se presentan las historias al usuario.

### Paso 6: Persistir, revisar y encadenar

Este paso tiene un orden ESTRICTO. Ejecuta las sub-etapas en este orden exacto:

#### 6a. Guardar ficheros (OBLIGATORIO, PRIMERO)

Ejecuta /pspo-agent:save-docs para guardar:
- Cada historia como fichero individual en docs/historias/HU-XX-titulo.md
- El backlog actualizado en docs/backlog.md
- La vision en docs/vision.md (si existe)

Este paso es OBLIGATORIO y va PRIMERO. Las historias deben estar persistidas en disco antes de cualquier otra accion. Si save-docs no se ejecuta, las historias solo existen en la conversacion y se pierden al cerrar la sesion.

#### 6b. Revision de estilo (culture-guardian)

Pasa todo el contenido generado por el agente `culture-guardian`. Este paso ya se describio arriba pero se ejecuta DESPUES de guardar y ANTES de presentar.

#### 6c. Auditoria automatica (solo primera generacion)

Si NO existe `docs/auditoria-hu.md` (primera vez que se generan historias), ejecuta automaticamente `/pspo-agent:audit`.

El agente `senior-auditor` revisara:
- Completitud contra el documento original (si existe)
- Coherencia del conjunto
- Calidad de contenido de cada HU
- HU que faltan o sobran

Si la auditoria detecta hallazgos, los presenta al usuario para que decida si aplicar correcciones.

Si `docs/auditoria-hu.md` ya existe (ya se audito antes), salta este sub-paso.

#### 6d. Presentar al usuario

Presenta las historias con un resumen inicial:

```
He generado {N} historias de usuario basandome en el descubrimiento:

| # | Titulo | Prioridad |
|---|--------|-----------|
| HU-01 | {titulo} | {prioridad} |
| HU-02 | {titulo} | {prioridad} |
| HU-03 | {titulo} | {prioridad} |

A continuacion el detalle de cada una. Revisalas y dime para cada historia
si la apruebas, quieres cambios, o la descartamos.
```

Despues del resumen, muestra cada historia completa.

#### 6e. Transicion automatica a validacion

Pasa automaticamente a /pspo-agent:validate. No preguntes al usuario si quiere validar. Es el paso natural. Si quiere parar, lo dira el.

## Que NO haces en esta skill

- No haces preguntas de descubrimiento. Eso ya se hizo en `/pspo-agent:discovery`.
- No publicas en Trello. Eso es `/pspo-agent:publish`.
- No inventas contexto que no salio del descubrimiento. Si falta informacion, vuelve a `/pspo-agent:discovery`.
