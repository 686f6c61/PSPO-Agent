# Banco de preguntas de descubrimiento

Referencia para el agente product-owner. Las preguntas estan organizadas por categoria. No se usan todas: se seleccionan las mas relevantes segun el contexto del usuario.

## 1. Usuario y contexto

Objetivo: entender quien va a usar esto y en que situacion.

- Quien es el usuario principal de esta funcionalidad? (rol especifico: administrador, cliente final, operador...)
- Hay algun usuario secundario que tambien la use?
- En que contexto la usara? (desde el movil, en escritorio, en una oficina, en movimiento...)
- Con que frecuencia la usara? (una vez al dia, constantemente, de forma puntual...)
- Que nivel tecnico tiene el usuario? (experto, intermedio, sin conocimientos tecnicos)

## 2. Problema actual

Objetivo: entender el dolor real que se quiere resolver.

- Que problema concreto tiene el usuario hoy?
- Como resuelve este problema actualmente? (proceso manual, herramienta externa, no lo resuelve)
- Que consecuencias tiene no resolver este problema? (perdida de tiempo, errores, dinero, frustracion)
- Desde cuando tiene este problema? Ha intentado resolverlo antes?
- Cuanto tiempo o dinero pierde el usuario por este problema?

## 3. Resultado esperado

Objetivo: definir como sera el exito.

- Cuando esto funcione, que podra hacer el usuario que ahora no puede?
- Como sabras que esta funcionalidad es exitosa? (metrica concreta, comportamiento observable)
- Que mejora esperas? (ahorro de tiempo, reduccion de errores, nueva capacidad)
- Hay algun producto o herramienta que haga algo similar a lo que quieres? Que te gusta y que no de esa referencia?

## 4. Alcance y funcionalidades

Objetivo: definir que incluir y que no.

- Cuales son las funcionalidades imprescindibles para una primera version?
- Que funcionalidades serian deseables pero no criticas?
- Que queda explicitamente fuera de alcance?
- Si solo pudieras implementar una cosa, cual seria?
- Hay funcionalidades que dependan de otras? (hay un orden natural)

## 5. Restricciones tecnicas

Objetivo: identificar limitaciones del entorno.

- Hay alguna tecnologia o framework obligatorio?
- Hay integraciones con sistemas externos? (APIs, bases de datos, servicios de terceros)
- Hay restricciones de rendimiento? (tiempo de respuesta, volumen de datos)
- Hay requisitos de seguridad especiales? (autenticacion, cifrado, GDPR)
- Hay una infraestructura existente donde esto debe funcionar?

## 6. Restricciones de negocio

Objetivo: identificar limitaciones no tecnicas.

- Hay una fecha limite para la primera version?
- Cuanto tiempo de desarrollo estimas? (esto ayuda a calibrar el alcance)
- Hay presupuesto limitado que afecte a herramientas o servicios externos?
- Necesitas aprobacion de alguien antes de lanzar? (stakeholder, cliente, regulador)

## 7. Datos y contenido

Objetivo: entender que datos maneja la funcionalidad.

- Que datos necesita esta funcionalidad? (de entrada, de salida, almacenados)
- De donde vienen esos datos? (el usuario los introduce, vienen de una API, de una base de datos)
- Hay datos sensibles? (datos personales, financieros, medicos)
- Que volumen de datos se espera? (decenas, miles, millones)

## 8. Flujo de usuario

Objetivo: entender el recorrido del usuario.

- Cual es el primer paso que hace el usuario?
- Que opciones tiene en cada punto del flujo?
- Que pasa si algo sale mal? (error de entrada, fallo de red, dato inexistente)
- Hay pasos que requieran confirmacion del usuario?
- Como sabe el usuario que la operacion se ha completado con exito?

## Guia de seleccion de preguntas

| Situacion | Preguntas prioritarias | Total estimado |
|-----------|----------------------|----------------|
| Descripcion muy vaga ("quiero un chat") | Categorias 1, 2, 3, 4 | 6-8 preguntas |
| Descripcion media ("chat para soporte al cliente con tickets") | Categorias 2, 4, 5 | 4-5 preguntas |
| Descripcion detallada (incluye usuario, problema, restricciones) | Confirmar + categorias 4, 5 | 3 preguntas |
| Iteracion sobre historias existentes | Categorias 4, 8 | 2-3 preguntas |
