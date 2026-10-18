# Investigación breve: configuración de permisos

## 1. Identidad, permisos y autorización

Son momentos distintos del uso del sistema. Autenticar es comprobar quién entra: el servidor contrasta una credencial y, si corresponde, emite una sesión o un token. Configurar permisos es decidir qué puede hacer un puesto. Por ejemplo, el rol CAPTURISTA tiene `transactions.write` porque registra ingresos, pero no necesita `roles.write` para ese trabajo. Autorizar ocurre al atender una petición concreta: antes de guardar un movimiento, el servidor revisa que la membresía activa tenga el permiso necesario y que la cuenta pertenezca a su empresa. La consulta GraphQL solo describe qué se pide; la decisión se toma en el código que atiende la operación.

En las operaciones de esta actividad se manda `actorCompanyUserId` para probar esa revisión. El dato identifica una fila, pero cualquiera que abra GraphiQL puede escribir el número de otra membresía. Por eso no demuestra que la persona frente al navegador sea Ana. En producción habría que obtener la identidad de una credencial validada y vincularla con la membresía. El proyecto conserva su login previo; esta entrega no cambia ese mecanismo ni añade protección nueva a las rutas. Fuente usada: *Authorization*, GraphQL.

## 2. Pruebas que se pueden repetir

Poner nombre a una operación ayuda a localizar una respuesta. Separar las variables evita editar el texto GraphQL cada vez que cambian los IDs de una instalación. En `ExplorarCatalogo`, el alias `cuentas` distingue el resultado de ACCOUNTS del alias `movimientos` para TRANSACTIONS, aunque ambos consultan `permissionCatalog`. El fragmento `DatosPermiso` pide `id`, `code` y `name` en los dos grupos sin copiar la misma selección. Ninguno de esos recursos concede permisos; solamente vuelve la prueba más clara y repetible.

Otra operación propia del archivo es `RevisarConfiguracion`. Recibe la lista completa en `$input`, así que para probar S0 y S1 basta cambiar el JSON de variables. Guardar ese JSON también permite verificar después exactamente qué se envió. Al revisar una respuesta miro `data` y `errors`: un HTTP 200 no significa que la configuración se haya aceptado. Para demostrar escritura comparo además las filas de MySQL. Fuente usada: *Queries*, GraphQL.

## 3. Qué valida GraphQL y qué valida Python

El enum `PermissionResource` limita el filtro a cinco recursos conocidos. Si se escribe `PAYMENTS`, GraphQL rechaza el documento antes de llamar al resolver. El input `SetRolePermissionsInput` exige un `roleId` y una lista `permissionIds`; cada elemento debe ser no nulo. La notación `[ID!]!` prohíbe que la lista sea `null` y que contenga `null`, pero una lista sin elementos, `[]`, sigue siendo una lista válida. En este ejercicio `[]` tiene significado: retira todas las concesiones activas del rol elegido.

El tipo `ID` no sabe si la fila existe, está activa o aparece dos veces. Eso se comprueba en Python contra la base. Allí también se rechaza ADMINISTRADOR para estas dos operaciones, se valida que el rol siga activo y se verifica cada permiso antes de tocar la relación. Si mandamos dos veces el ID de `accounts.read`, el servidor devuelve un error en lugar de corregir silenciosamente la propuesta. El enum decide la forma aceptada por el esquema; el resolver decide si la propuesta tiene sentido para los datos actuales. Fuentes usadas: *Enums* e *Input types*, Strawberry GraphQL.

## 4. Confirmar todo y poder repetir

Atomicidad significa que la lista nueva se guarda completa o se revierte completa. Si CAPTURISTA debe ganar `accounts.write` y perder `concepts.read`, no debe quedar guardado solo el primer cambio si falla el segundo. La mutación calcula diferencias con una sesión, modifica las relaciones, hace `flush` y confirma una vez. Si ocurre una excepción, hace `rollback`. E07 provoca un fallo después de `flush` y comprueba desde otra sesión que se conserva el estado anterior.

Idempotencia responde otra pregunta: ¿qué pasa si se envía otra vez S1? En la primera aplicación cambia una relación; en la segunda no se crea ninguna pareja ni se modifica un estado, por lo que `changed` es `false`. Esto sirve cuando una persona repite una petición porque no vio la primera respuesta. Enviar varias mutaciones GraphQL juntas no crea por sí mismo una transacción común de MySQL: cada resolver puede confirmar sus propios cambios. La garantía de esta entrega está dentro de `setRolePermissions`, que administra una única confirmación para la lista completa. Fuente usada: *Transactions and Connection Management*, SQLAlchemy, y *Mutations*, GraphQL.

## Fuentes consultadas el 17 de octubre de 2026

- GraphQL, *Authorization*: https://graphql.org/learn/authorization/
- GraphQL, *Queries*: https://graphql.org/learn/queries/
- GraphQL, *Mutations*: https://graphql.org/learn/mutations/
- Strawberry GraphQL, *Enums*: https://strawberry.rocks/docs/types/enums
- Strawberry GraphQL, *Input types*: https://strawberry.rocks/docs/types/input-types
- SQLAlchemy, *Transactions and Connection Management*: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html
