"""Registra respuestas reales de GraphQL y estados SQL del laboratorio local."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from graphql import parse, print_ast

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "ingresos"))
from app.security import create_access_token
DOCUMENT = parse((ROOT / "operaciones.graphql").read_text())
OPERATIONS = {node.name.value: node for node in DOCUMENT.definitions if hasattr(node, "operation")}
FRAGMENT = next(node for node in DOCUMENT.definitions if getattr(node, "kind", "") == "fragment_definition")
SQL_RELATIONS = """SELECT rp.id, r.code, p.code, rp.is_active, p.is_active
FROM role_permissions rp JOIN roles r ON r.id=rp.role_id
JOIN permissions p ON p.id=rp.permission_id ORDER BY r.code,p.code"""


def sql(statement):
    result = subprocess.run(
        ["docker", "exec", "actividad4_mysql", "sh", "-c",
         'MYSQL_PWD="$MYSQL_PASSWORD" mysql -u"$MYSQL_USER" "$MYSQL_DATABASE" -N -e "$1"',
         "_", statement], capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def execute(name, variables_file, token=None):
    operation = print_ast(OPERATIONS[name])
    if "...DatosPermiso" in operation:
        operation += "\n" + print_ast(FRAGMENT)
    variables = json.loads((ROOT / "variables" / variables_file).read_text())
    request = {"query": operation, "operationName": name, "variables": variables}
    command = ["curl", "-sS", "http://127.0.0.1:8015/graphql", "-H", "Content-Type: application/json",
               "--data-binary", json.dumps(request, ensure_ascii=False)]
    if token:
        command.extend(["-H", f"Authorization: Bearer {token}"])
    response = subprocess.run(
        command,
        capture_output=True, text=True, check=True,
    )
    return {"operacion": name, "variables": variables,
            "respuesta": json.loads(response.stdout)}


def save(name, content):
    (ROOT / "evidencias" / f"{name}.json").write_text(
        json.dumps(content, indent=2, ensure_ascii=False) + "\n"
    )


def must_succeed(result):
    if result["respuesta"].get("errors"):
        raise AssertionError(result)


def must_fail(result):
    if not result["respuesta"].get("errors"):
        raise AssertionError(result)


def first_phase():
    start = {"sql": sql(SQL_RELATIONS), "graphql": execute("PuntoDePartida", "E01_punto_partida.json")}
    must_succeed(start["graphql"])
    save("E01", start)

    catalog = [execute("ExplorarCatalogo", "E02_catalogo.json"),
               execute("CatalogoCompleto", "E02_catalogo.json"),
               execute("CatalogoEnumInvalido", "E02_catalogo.json")]
    for result in catalog[:2]:
        must_succeed(result)
    must_fail(catalog[2])
    save("E02", catalog)

    before = sql(SQL_RELATIONS)
    preview = execute("RevisarConfiguracion", "E03_E04_S1.json")
    must_succeed(preview)
    after = sql(SQL_RELATIONS)
    assert before == after
    save("E03", {"sql_antes": before, "graphql": preview, "sql_despues": after})

    before = sql(SQL_RELATIONS)
    first = execute("AplicarConfiguracion", "E03_E04_S1.json")
    second = execute("AplicarConfiguracion", "E03_E04_S1.json")
    must_succeed(first)
    must_succeed(second)
    after = sql(SQL_RELATIONS)
    save("E04", {"sql_antes": before, "primera": first, "segunda": second, "sql_despues": after})

    before = sql(SQL_RELATIONS)
    remove = execute("AplicarConfiguracion", "E05_E09_S0.json")
    middle = sql(SQL_RELATIONS)
    restore = execute("AplicarConfiguracion", "E03_E04_S1.json")
    after = sql(SQL_RELATIONS)
    must_succeed(remove)
    must_succeed(restore)
    save("E05", {"sql_antes": before, "retiro": remove, "sql_retirado": middle,
                 "reactivacion": restore, "sql_reactivado": after})

    variants = [
        ("rol_inexistente", "E06_rol_inexistente.json", None),
        ("rol_inactivo", "E06_rol_inactivo.json", "UPDATE roles SET is_active=0 WHERE code='CONSULTA'"),
        ("administrador", "E06_administrador.json", None),
        ("permiso_inexistente", "E06_permiso_inexistente.json", None),
        ("permiso_inactivo", "E06_permiso_inactivo.json", "UPDATE permissions SET is_active=0 WHERE code='concepts.write'"),
        ("permiso_repetido", "E06_permiso_repetido.json", None),
    ]
    recorded = []
    for name, variables, preparation in variants:
        if preparation:
            sql(preparation)
        try:
            before = sql(SQL_RELATIONS)
            preview = execute("RevisarConfiguracion", variables)
            apply = execute("AplicarConfiguracion", variables)
            after = sql(SQL_RELATIONS)
            must_fail(preview)
            must_fail(apply)
            assert before == after
            recorded.append({"variante": name, "preparacion": preparation, "sql_antes": before,
                             "preview": preview, "aplicacion": apply, "sql_despues": after})
        finally:
            if name == "rol_inactivo":
                sql("UPDATE roles SET is_active=1 WHERE code='CONSULTA'")
            if name == "permiso_inactivo":
                sql("UPDATE permissions SET is_active=1 WHERE code='concepts.write'")
    save("E06", recorded)

    before = sql(SQL_RELATIONS)
    empty = execute("AplicarConfiguracion", "E08_vacia.json")
    must_succeed(empty)
    after = sql(SQL_RELATIONS)
    save("E08_antes_reinicio", {"sql_antes": before, "graphql": empty, "sql_despues": after})
    print("Fase 1 completa. Reinicia uvicorn y ejecuta --phase 2.")


def second_phase():
    start = sql(SQL_RELATIONS)
    current = execute("PuntoDePartida", "E01_punto_partida.json")
    must_succeed(current)
    assert current["respuesta"]["data"]["rolePermissions"] == []
    save("E08_despues_reinicio", {"sql": start, "graphql": current})

    restored = execute("AplicarConfiguracion", "E05_E09_S0.json")
    must_succeed(restored)
    final = sql(SQL_RELATIONS)
    duplicates = sql("SELECT role_id,permission_id,COUNT(*) FROM role_permissions GROUP BY role_id,permission_id HAVING COUNT(*)>1")
    assert not duplicates
    save("E09", {"graphql": restored, "sql_final": final, "duplicados": duplicates})

    accounts = execute("ContinuidadCuentas", "E10_cuentas.json")
    actor_id = int(json.loads((ROOT / "variables" / "E10_movimiento.json").read_text())["actor"])
    user_id = int(sql(f"SELECT user_id FROM company_users WHERE id={actor_id}"))
    movement = execute("ContinuidadMovimiento", "E10_movimiento.json", create_access_token(user_id))
    must_succeed(accounts)
    must_succeed(movement)
    transaction_id = movement["respuesta"]["data"]["createTransaction"]["id"]
    stored = sql(f"SELECT t.id,t.amount,a.company_id,t.account_id,t.concept_id FROM transactions t JOIN accounts a ON a.id=t.account_id WHERE t.id={int(transaction_id)}")
    save("E10", {"cuentas": accounts, "movimiento": movement, "sql_movimiento": stored,
                 "nota": "Token de prueba generado en memoria con el mecanismo existente; no se guardó."})
    print("Fase 2 completa.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", type=int, choices=(1, 2), required=True)
    arguments = parser.parse_args()
    (ROOT / "evidencias").mkdir(exist_ok=True)
    (first_phase if arguments.phase == 1 else second_phase)()
