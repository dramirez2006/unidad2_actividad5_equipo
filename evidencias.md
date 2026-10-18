# Evidencias de la actividad 5

Las imágenes muestran los registros de peticiones HTTP a `/graphql` y consultas MySQL de este laboratorio, con el texto completo en los JSON del mismo caso. Se generaron a partir de respuestas ejecutadas, no de respuestas redactadas a mano. Los IDs corresponden a esta base: membresía de Ana 1, CAPTURISTA 3 y permisos `accounts.read` 3, `accounts.write` 4, `concepts.read` 5, `transactions.read` 7 y `transactions.write` 8. En otra instalación se deben consultar de nuevo. No se incluyen contraseñas, tokens ni hashes.

## E01. Punto de partida

- **Precondición:** matriz de actividad 4; CAPTURISTA en S0.
- **Operación y variables:** `PuntoDePartida`, `variables/E01_punto_partida.json`; además, consulta de relaciones de `comprobaciones.sql`.
- **Esperado:** cuatro roles, diez permisos y cuatro concesiones activas para CAPTURISTA.
- **Obtenido:** 4 roles, 10 permisos y las parejas de S0: `accounts.read`, `concepts.read`, `transactions.read`, `transactions.write`. `configuracion_inicial.json` registra los cuatro roles por códigos.
- **Regla demostrada:** la configuración se lee de las relaciones persistidas. Registro: `evidencias/E01.json`; imágenes `E01_01.png` y `E01_02.png`.

## E02. Catálogo

- **Precondición:** Ana tiene `roles.read`; los diez permisos del catálogo están activos.
- **Operación y variables:** `ExplorarCatalogo`, `CatalogoCompleto` y `CatalogoEnumInvalido`, con `variables/E02_catalogo.json`.
- **Esperado:** dos permisos para ACCOUNTS, dos para TRANSACTIONS, diez sin filtro y error de validación con PAYMENTS.
- **Obtenido:** alias `cuentas` y `movimientos` con dos códigos cada uno; diez sin filtro; GraphQL respondió `Value 'PAYMENTS' does not exist in 'PermissionResource' enum.` El fragmento `DatosPermiso` se utilizó en las consultas válidas.
- **Regla demostrada:** filtro por recurso y validación del enum. Registro: `evidencias/E02.json`; imágenes `E02_01.png` y `E02_02.png`.

## E03. Previsualización

- **Precondición:** CAPTURISTA en S0.
- **Operación y variables:** `RevisarConfiguracion`, `variables/E03_E04_S1.json`.
- **Esperado:** activar `accounts.write`, desactivar cero, conservar cuatro y terminar con cinco.
- **Obtenido:** exactamente esos grupos y `finalCount: 5`. La consulta SQL antes y después contiene los mismos IDs y estados, incluido el vínculo 27 de `accounts.write` inactivo.
- **Regla demostrada:** previsualizar solo lee y calcula. Registro: `evidencias/E03.json`; imágenes `E03_01.png` y `E03_02.png`.

## E04. Aplicación e idempotencia

- **Precondición:** CAPTURISTA en S0.
- **Operación y variables:** `AplicarConfiguracion` dos veces con `variables/E03_E04_S1.json`.
- **Esperado:** primera ejecución con `changed: true`; segunda con `changed: false`, sin activaciones ni desactivaciones y total cinco.
- **Obtenido:** coincide. La fila de `accounts.write` se reactivó con su ID anterior 27 y la segunda ejecución no creó otra pareja.
- **Regla demostrada:** aplicar la lista completa es idempotente. Registro: `evidencias/E04.json`; imágenes `E04_01.png` a `E04_03.png`.

## E05. Desactivar y reactivar

- **Precondición:** CAPTURISTA en S1.
- **Operación y variables:** `AplicarConfiguracion` con `variables/E05_E09_S0.json` y luego con `variables/E03_E04_S1.json`.
- **Esperado:** `accounts.write` inactivo y después activo sin perder la fila.
- **Obtenido:** la relación 27 pasó de `1` a `0` y volvió a `1`; `Permission.is_active` permaneció en `1` en los tres SELECT.
- **Regla demostrada:** desactivar una concesión no desactiva el permiso del catálogo. Registro: `evidencias/E05.json`; imágenes `E05_01.png` a `E05_03.png`.

## E06. Entradas inválidas

- **Precondición:** CAPTURISTA en S1. Para rol inactivo se desactivó temporalmente CONSULTA; para permiso inactivo, `concepts.write`. Cada estado se restauró al terminar su variante.
- **Operación y variables:** `RevisarConfiguracion` y `AplicarConfiguracion` para cada JSON `variables/E06_*.json`.
- **Esperado:** ambas operaciones informan un error descriptivo y ninguna cambia relaciones.
- **Obtenido:**

| Variante | Mensaje en ambas operaciones |
| --- | --- |
| Rol inexistente | El rol no existe o está inactivo. |
| Rol inactivo | El rol no existe o está inactivo. |
| ADMINISTRADOR | No se puede cambiar la lista de ADMINISTRADOR en esta práctica. |
| Permiso inexistente mezclado con válido | El permiso 999999 no existe o está inactivo. |
| Permiso inactivo | El permiso 6 no existe o está inactivo. |
| Permiso repetido | El ID de permiso 3 está repetido. |

En las seis variantes, la comparación SQL antes/después conserva las mismas parejas, IDs y estados. **Regla demostrada:** validación previa sin escrituras parciales. Registro: `evidencias/E06.json`; imágenes `E06_<variante>_01.png` y `E06_<variante>_02.png`.

## E07. Reversión después de `flush`

- **Precondición:** CAPTURISTA con su configuración activa; base MySQL disponible.
- **Operación y variables:** `RUN_MYSQL_TESTS=1 python -m unittest tests/test_e07_mysql.py -v`. El test crea una propuesta distinta e intercepta `Session.flush` para lanzar una excepción después del `flush` real y antes de `commit`.
- **Esperado:** error y rollback; una sesión nueva debe ver el estado anterior.
- **Obtenido:** la prueba pasó. Comparó las tuplas `(relacion_id, permission_id, is_active)` antes y después desde sesiones distintas, y fueron idénticas.
- **Regla demostrada:** la mutación no confirma una configuración parcial. Código en `ingresos/tests/test_e07_mysql.py`; salida `evidencias/E07_test_mysql.txt`; imagen `E07_01.png`.

## E08. Lista vacía y reinicio

- **Precondición:** CAPTURISTA en S1.
- **Operación y variables:** `AplicarConfiguracion` con `variables/E08_vacia.json`; se detuvo y volvió a arrancar Uvicorn; después se ejecutó `PuntoDePartida`.
- **Esperado:** cero concesiones activas antes y después del arranque, con filas inactivas conservadas; cuatro roles y diez permisos.
- **Obtenido:** la mutación devolvió `finalCount: 0`; las cinco filas de CAPTURISTA quedaron inactivas. Tras reiniciar, `rolePermissions` siguió vacío y los catálogos conservaron 4 y 10 registros.
- **Regla demostrada:** el arranque distingue una lista vacía deliberada de un rol nunca inicializado. Registros: `evidencias/E08_antes_reinicio.json` y `E08_despues_reinicio.json`; imágenes con esos mismos prefijos.

## E09. Restauración

- **Precondición:** CAPTURISTA vacío después del reinicio.
- **Operación y variables:** `AplicarConfiguracion` con `variables/E05_E09_S0.json`; SELECT de matriz activa y consulta de duplicados en `comprobaciones.sql`.
- **Esperado:** la matriz activa vuelve a `configuracion_inicial.json`; ninguna pareja duplicada.
- **Obtenido:** los códigos activos de los cuatro roles coinciden con el JSON inicial; la consulta de duplicados devolvió cero filas. `configuracion_final.json` registra ese estado.
- **Regla demostrada:** la prueba deja la configuración inicial restaurada. Registro: `evidencias/E09.json`; imagen `E09_01.png`.

## E10. Continuidad del proyecto

- **Precondición:** matriz restaurada; cuenta 3 y concepto 1 activos, vinculados y de la empresa 1; membresía de Ana 1.
- **Operación y variables:** `ContinuidadCuentas` con `variables/E10_cuentas.json` y `ContinuidadMovimiento` con `variables/E10_movimiento.json`. Para la segunda petición se generó en memoria un token de prueba con la función existente; no se guardó en archivos.
- **Esperado:** la consulta de cuentas funciona y el ingreso queda persistido con cuenta, concepto, empresa y monto válidos.
- **Obtenido:** movimiento 5, monto `15.50`, tipo INCOME, cuenta 3 y concepto 1 de empresa 1. El SELECT posterior encontró la fila.
- **Regla demostrada:** las operaciones financieras anteriores siguen funcionando. Registro: `evidencias/E10.json`; imagen `E10_01.png`.
