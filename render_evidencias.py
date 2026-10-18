"""Hace imágenes legibles a partir de los registros HTTP y SQL guardados."""

import json
import textwrap
from pathlib import Path

from graphql import parse, print_ast
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidencias"
for old_image in EVIDENCE.glob("E*.png"):
    old_image.unlink()
document = parse((ROOT / "operaciones.graphql").read_text())
operations = {node.name.value: print_ast(node) for node in document.definitions if hasattr(node, "operation")}
fragment = next(print_ast(node) for node in document.definitions if getattr(node, "kind", "") == "fragment_definition")
font_path = next((path for path in (
    "/System/Library/Fonts/Menlo.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
) if Path(path).exists()), None)
font = ImageFont.truetype(font_path, 17) if font_path else ImageFont.load_default(size=17)
heading_font = ImageFont.truetype(font_path, 25) if font_path else ImageFont.load_default(size=25)


def add_record(lines, name, value):
    if isinstance(value, dict) and "operacion" in value and "respuesta" in value:
        lines.append(f"OPERACIÓN: {value['operacion']}")
        lines.extend(operations[value["operacion"]].splitlines())
        if "...DatosPermiso" in operations[value["operacion"]]:
            lines.extend(fragment.splitlines())
        lines.append("VARIABLES")
        lines.extend(json.dumps(value["variables"], ensure_ascii=False, indent=2).splitlines())
        lines.append("RESPUESTA HTTP GRAPHQL")
        lines.extend(json.dumps(value["respuesta"], ensure_ascii=False, indent=2).splitlines())
    elif isinstance(value, dict):
        for key, item in value.items():
            if key in ("operacion", "variables", "respuesta"):
                continue
            lines.append(f"--- {key.upper()} ---")
            add_record(lines, key, item)
    elif isinstance(value, list):
        for index, item in enumerate(value, 1):
            lines.append(f"--- REGISTRO {index} ---")
            add_record(lines, name, item)
    elif isinstance(value, str):
        lines.extend(value.splitlines() or ["(sin filas)"])
    else:
        lines.append(json.dumps(value, ensure_ascii=False))


def draw_pages(stem, data):
    lines = []
    add_record(lines, stem, data)
    wrapped = []
    for line in lines:
        expanded = line.expandtabs(4)
        wrapped.extend(textwrap.wrap(expanded, width=122, break_long_words=True,
                                     replace_whitespace=False, drop_whitespace=False) or [""])
    for page, start in enumerate(range(0, len(wrapped), 105), 1):
        current = wrapped[start:start + 105]
        image = Image.new("RGB", (1760, 2390), "#f8fafc")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1760, 82), fill="#10243a")
        draw.text((48, 22), f"{stem} · registro de ejecución · {page}", font=heading_font, fill="white")
        y = 112
        for line in current:
            color = "#124272" if line.startswith(("OPERACIÓN:", "VARIABLES", "RESPUESTA", "---")) else "#182330"
            draw.text((48, y), line, font=font, fill=color)
            y += 21
        draw.text((48, 2350), "Fuente: petición GraphQL y consulta MySQL guardadas en el JSON del mismo caso.",
                  font=font, fill="#52677a")
        image.save(EVIDENCE / f"{stem}_{page:02d}.png", optimize=True)


for path in sorted(EVIDENCE.glob("E*.json")):
    data = json.loads(path.read_text())
    if path.stem == "E06":
        for variant in data:
            draw_pages(f"E06_{variant['variante']}", variant)
    else:
        draw_pages(path.stem, data)

test_log = (EVIDENCE / "E07_test_mysql.txt").read_text()
summary = "\n".join(line for line in test_log.splitlines()
                    if line.startswith(("test_e07", "E07 MySQL:", "Ran 1 test", "OK")))
draw_pages("E07", {"prueba": "RUN_MYSQL_TESTS=1 python -m unittest tests/test_e07_mysql.py -v",
                   "resultado": summary,
                   "punto_de_fallo": "Después de Session.flush; antes de Session.commit. El test consulta desde otra sesión."})
