# Unidad II · Actividad 5 · Configurar permisos con GraphQL

Entrega individual de Diego Ramírez Magaña. Implementación de las tres operaciones GraphQL, pruebas, investigación, registros SQL y organización de evidencias: Diego Ramírez Magaña. El proyecto base es el Sistema General de Ingresos de la actividad 4.

**Repositorio:** https://github.com/dramirez2006/unidad2_actividad5_equipo

## Contenido

- `ingresos/`: proyecto completo en FastAPI, Strawberry, SQLAlchemy y MySQL. Las tres operaciones nuevas están en `ingresos/app/schema.py`; las pruebas en `ingresos/tests/`.
- `operaciones.graphql` y `variables/`: documentos con nombre y JSON usados en GraphiQL.
- `configuracion_inicial.json`, `configuracion_final.json` y `comprobaciones.sql`: matriz por códigos y consultas de persistencia.
- `investigacion.md`: cuatro respuestas razonadas con fuentes oficiales.
- `evidencias.md` y `evidencias/`: E01-E10 con respuestas HTTP, estados SQL, salida de E07 e imágenes legibles de esos registros.
- `registrar_evidencias.py` y `render_evidencias.py`: guiones usados para repetir el registro y las imágenes.

## Preparar y ejecutar

Se necesita Python 3.12, Docker Desktop con Docker Compose y `curl`. Desde la carpeta de esta entrega:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-evidencias.txt
cd ingresos
docker compose up -d
cp .env.example .env
```

En `.env` se debe establecer una `SECRET_KEY` local de al menos 32 bytes y la URL de la base si no se usan los valores de demostración de `docker-compose.yml`. El archivo `.env` no se entrega. Con la base disponible:

```bash
../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8015
```

Abrir `http://127.0.0.1:8015/graphql` para GraphiQL. El arranque crea tablas nuevas y carga la matriz solo para roles sin filas en `role_permissions`. Una lista vacía guardada no se repone. La restricción única `(role_id, permission_id)` ya existía en el modelo y se comprobó en la base de laboratorio con `SHOW INDEX`. Si se usa una base antigua sin ese índice, debe añadirse mediante migración antes de probar; `create_all` no modifica tablas existentes.

## Datos de la práctica

Primero ejecutar las consultas de `comprobaciones.sql` para obtener los IDs reales. En la base usada para estas evidencias, Ana tiene membresía 1, CAPTURISTA es rol 3, ACCOUNTS.READ es permiso 3, ACCOUNTS.WRITE es 4, CONCEPTS.READ es 5, TRANSACTIONS.READ es 7 y TRANSACTIONS.WRITE es 8. Cuenta 3 y concepto 1 pertenecen a la empresa 1. Esos números son propios de esta base; hay que actualizar `variables/*.json` antes de repetir la práctica en otra. El archivo `configuracion_inicial.json` usa códigos precisamente para evitar depender de esos IDs.

Los cuatro roles y diez permisos se mantienen. La propuesta S0 de CAPTURISTA es `accounts.read`, `concepts.read`, `transactions.read`, `transactions.write`; S1 añade `accounts.write`. Se usa Ana como actor para las pruebas de configuración. `actorCompanyUserId` es un identificador de laboratorio y no prueba identidad por sí solo.

## Operaciones y variables

Pegar el contenido de `operaciones.graphql` en GraphiQL, seleccionar una operación por nombre y pegar el JSON indicado en el panel de variables. No se ejecutan todas las operaciones juntas.

| Caso | Operación | Variables |
| --- | --- | --- |
| E01 | `PuntoDePartida` | `E01_punto_partida.json` |
| E02 | `ExplorarCatalogo`, `CatalogoCompleto`, `CatalogoEnumInvalido` | `E02_catalogo.json` |
| E03 | `RevisarConfiguracion` | `E03_E04_S1.json` |
| E04 | `AplicarConfiguracion` dos veces | `E03_E04_S1.json` |
| E05 | `AplicarConfiguracion` S0 y S1 | `E05_E09_S0.json`, `E03_E04_S1.json` |
| E06 | `RevisarConfiguracion` y `AplicarConfiguracion` por variante | `E06_*.json` |
| E08 | `AplicarConfiguracion` con lista vacía; reinicio; `PuntoDePartida` | `E08_vacia.json`, `E01_punto_partida.json` |
| E09 | `AplicarConfiguracion` S0 | `E05_E09_S0.json` |
| E10 | `ContinuidadCuentas`, `ContinuidadMovimiento` | `E10_cuentas.json`, `E10_movimiento.json` |

E07 se ejecuta como prueba automatizada. Para E06, antes de la variante de rol inactivo se usa temporalmente `UPDATE roles SET is_active=0 WHERE code='CONSULTA'`; antes de permiso inactivo, `UPDATE permissions SET is_active=0 WHERE code='concepts.write'`. Se restaura cada estado a `1` inmediatamente después. Las consultas están anotadas en `comprobaciones.sql`.

## Pruebas y registros

Desde `ingresos/`:

```bash
../.venv/bin/python -m unittest discover -s tests -v
RUN_MYSQL_TESTS=1 ../.venv/bin/python -m unittest tests/test_e07_mysql.py -v
```

La primera orden usa SQLite temporal para las pruebas generales. La segunda usa MySQL local y provoca el error controlado de E07 después de `flush`; compara las mismas parejas e IDs desde otra sesión. No modifica la configuración final.

Volver a la carpeta raíz de la entrega. Para registrar E01-E06 y la primera parte de E08, con la API levantada y CAPTURISTA en S0:

```bash
.venv/bin/python registrar_evidencias.py --phase 1
```

Detener y volver a iniciar Uvicorn. Con cero concesiones activas de CAPTURISTA, ejecutar:

```bash
.venv/bin/python registrar_evidencias.py --phase 2
.venv/bin/python render_evidencias.py
```

Estas órdenes se ejecutan desde la carpeta raíz de la entrega. `registrar_evidencias.py` usa el contenedor local `actividad4_mysql` para los SELECT; toma las credenciales de demostración de las variables del propio contenedor y no las guarda en las evidencias. Para E10 genera un token de prueba en memoria mediante la función existente y lo envía solo en la petición; el archivo registra la respuesta sin token. La fase 2 restaura S0 y luego crea un movimiento ficticio de monto `15.50`, por lo que repetirla crea otro movimiento. Las imágenes se generan a partir de los JSON guardados; los archivos JSON contienen el registro completo.

No se incluyen entornos virtuales, cachés, `.env` ni credenciales reales. La entrega permanece en la configuración de catálogos y relaciones rol-permiso; no agrega asignaciones de roles a usuarios ni control de acceso del tema 2.
