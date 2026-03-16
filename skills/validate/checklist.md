# Checklist de calidad de historias de usuario

El agente product-owner usa esta checklist internamente antes de presentar cada historia al usuario. Si una historia no cumple algun criterio, se corrige antes de presentarla.

## Formato de la historia

| Criterio | Verificacion |
|----------|-------------|
| Tiene formato "Como X, quiero Y, para Z" | El rol (X), la accion (Y) y el beneficio (Z) estan presentes |
| El rol es especifico | No es "usuario", "persona" ni "gente". Es un rol concreto |
| La accion es concreta | Usa un verbo en infinitivo que describe una accion observable |
| El beneficio es medible | Se puede verificar si se ha conseguido o no |

## Criterios de aceptacion

| Criterio | Verificacion |
|----------|-------------|
| Formato Given/When/Then | Cada escenario sigue la estructura correcta |
| Al menos 1 escenario positivo | Hay un happy path completo |
| Al menos 1 escenario negativo | Hay un caso de error, entrada invalida o caso de borde |
| Valores concretos | No hay "datos validos", "una cantidad correcta", "funciona bien" |
| Given establece el contexto completo | El lector no tiene que adivinar precondiciones |
| When tiene una sola accion | Si hay dos acciones, son dos escenarios |
| Then tiene resultados verificables | Se puede comprobar objetivamente si se cumple |

## Independencia

| Criterio | Verificacion |
|----------|-------------|
| Se puede implementar sola | No requiere que otra historia este terminada para entregar valor |
| No comparte criterios con otra historia | Si dos historias tienen criterios iguales, hay solapamiento |

## Tamano

| Criterio | Verificacion |
|----------|-------------|
| Estimable en 16 h efectivas o menos | Si parece mayor, hay que descomponer |
| Menos de 6 escenarios de aceptacion | Si necesita mas, probablemente es demasiado grande |
| Se puede demostrar en una review | El resultado es observable y demostrable |

## Prioridad

| Criterio | Verificacion |
|----------|-------------|
| La prioridad es explicita | Tiene una de: Critica, Alta, Media, Baja |
| La prioridad es coherente | Las historias con mas valor para el usuario tienen mayor prioridad |
| El orden es logico | No hay historias "Baja" antes de "Critica" sin justificacion |

## Coherencia del conjunto

| Criterio | Verificacion |
|----------|-------------|
| Los roles son consistentes | El mismo rol se llama igual en todas las historias |
| Los terminos se usan igual | No se mezclan "producto/articulo", "cliente/comprador" sin razon |
| No hay huecos funcionales | La necesidad del descubrimiento esta cubierta completamente |
| No hay duplicados | Ninguna historia es un subconjunto de otra |
