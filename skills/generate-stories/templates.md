# Plantillas y ejemplos de historias de usuario

Referencia para el agente product-owner durante la generacion de historias.

## Plantilla base

```markdown
### HU-XX: Titulo descriptivo breve

**Historia de usuario:**

Como [rol especifico del usuario],
quiero [accion concreta que el usuario realiza],
para [beneficio medible que obtiene el usuario].

**Criterios de aceptacion:**

ESCENARIO 1: [nombre descriptivo del escenario positivo]
Given [contexto inicial detallado]
  And [condicion adicional si aplica]
When [accion concreta del usuario]
Then [resultado esperado verificable]
  And [resultado adicional si aplica]

ESCENARIO 2: [nombre descriptivo del escenario negativo]
Given [contexto inicial]
When [accion del usuario con datos invalidos o condicion de error]
Then [comportamiento esperado ante la situacion]
  And [feedback claro al usuario]

**Prioridad:** [Critica | Alta | Media | Baja]

**Notas:** [contexto adicional, dependencias, restricciones]
```

## Ejemplo completo: sistema de notificaciones

### HU-01: Suscripcion a notificaciones por email

**Historia de usuario:**

Como comprador registrado en la tienda online,
quiero suscribirme a notificaciones de bajada de precio de un producto,
para recibir un aviso cuando el producto que me interesa este mas barato.

**Criterios de aceptacion:**

ESCENARIO 1: Suscripcion exitosa a un producto disponible
Given el comprador ha iniciado sesion en la tienda
  And esta viendo la pagina de detalle del producto "Auriculares BT-500" con precio 89.99 EUR
When pulsa el boton "Avisarme si baja de precio"
Then el sistema registra la suscripcion para ese producto y ese comprador
  And muestra un mensaje de confirmacion: "Te avisaremos si el precio de Auriculares BT-500 baja"
  And el boton cambia a "Dejar de seguir precio"

ESCENARIO 2: Intento de suscripcion sin sesion iniciada
Given el comprador NO ha iniciado sesion
  And esta viendo la pagina de detalle de un producto
When pulsa el boton "Avisarme si baja de precio"
Then el sistema redirige a la pagina de inicio de sesion
  And tras iniciar sesion, completa la suscripcion automaticamente
  And muestra el mensaje de confirmacion

ESCENARIO 3: Suscripcion duplicada al mismo producto
Given el comprador ya esta suscrito a notificaciones del producto "Auriculares BT-500"
When pulsa el boton "Avisarme si baja de precio" en el mismo producto
Then el sistema muestra: "Ya estas suscrito a las notificaciones de precio de este producto"
  And no crea una suscripcion duplicada

**Prioridad:** Alta

**Notas:** Depende de que el sistema de precios tenga historico. La notificacion por email se implementa en HU-02.

---

### HU-02: Envio de notificacion cuando el precio baja

**Historia de usuario:**

Como comprador suscrito a notificaciones de precio,
quiero recibir un email cuando el precio del producto baje,
para poder comprarlo en el momento mas conveniente sin estar revisando la tienda constantemente.

**Criterios de aceptacion:**

ESCENARIO 1: Notificacion por bajada de precio
Given el comprador "Ana Garcia" esta suscrito a notificaciones del producto "Auriculares BT-500"
  And el precio actual es 89.99 EUR
When el precio del producto cambia a 69.99 EUR
Then el sistema envia un email a la direccion registrada del comprador
  And el email incluye: nombre del producto, precio anterior (89.99 EUR), precio nuevo (69.99 EUR) y enlace directo al producto
  And el asunto del email es: "El precio de Auriculares BT-500 ha bajado a 69.99 EUR"

ESCENARIO 2: El precio sube (no notificar)
Given el comprador esta suscrito a notificaciones del producto "Auriculares BT-500"
  And el precio actual es 89.99 EUR
When el precio cambia a 99.99 EUR
Then el sistema NO envia ninguna notificacion
  And la suscripcion sigue activa

ESCENARIO 3: Error en el envio del email
Given el sistema detecta una bajada de precio para un producto con suscriptores
When intenta enviar el email y el servicio de correo devuelve un error
Then el sistema registra el error en el log
  And marca el envio como pendiente para reintento
  And reintenta el envio en los proximos 30 minutos (maximo 3 intentos)

**Prioridad:** Alta

**Notas:** Requiere integracion con un servicio de email transaccional (ej: SendGrid, SES). El reintento se implementa con una cola de mensajes.

## Anti-patrones: historias mal escritas

### Anti-patron 1: Rol generico

MAL:
```
Como usuario, quiero buscar productos, para encontrar lo que necesito.
```

BIEN:
```
Como comprador no registrado que visita la tienda por primera vez,
quiero buscar productos por nombre o categoria,
para encontrar rapidamente lo que busco sin tener que navegar por toda la tienda.
```

### Anti-patron 2: Accion vaga

MAL:
```
Como administrador, quiero gestionar los pedidos, para que todo funcione bien.
```

BIEN:
```
Como operador de logistica del almacen,
quiero filtrar los pedidos pendientes de envio por fecha de compra,
para preparar primero los pedidos mas antiguos y cumplir los plazos de entrega.
```

### Anti-patron 3: Beneficio no medible

MAL:
```
Como cliente, quiero que la pagina sea rapida, para tener mejor experiencia.
```

BIEN:
```
Como comprador que navega desde el movil con conexion 4G,
quiero que la pagina de listado de productos cargue en menos de 2 segundos,
para no abandonar la compra por lentitud de carga.
```

### Anti-patron 4: Criterio de aceptacion vago

MAL:
```
Given el usuario esta en la pagina
When hace la accion
Then funciona correctamente
```

BIEN:
```
Given el comprador esta en la pagina de checkout con 3 productos en el carrito
  And el total es 149.97 EUR
When introduce un codigo de descuento valido "VERANO20" (20% de descuento)
Then el precio total se actualiza a 119.98 EUR
  And se muestra el detalle del descuento: "-29.99 EUR (codigo VERANO20)"
  And el codigo aparece como aplicado con opcion de eliminarlo
```

### Anti-patron 5: Historia demasiado grande

MAL:
```
Como administrador, quiero un panel de gestion completo con usuarios, productos,
pedidos, informes y configuracion del sistema, para gestionar toda la tienda.
```

Esto son al menos 5 historias separadas. Descomponer en: gestion de usuarios, gestion de productos, gestion de pedidos, informes y configuracion.
