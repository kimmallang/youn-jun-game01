"""Extend the three short hunting maps with existing 32px project terrain."""

import json
import re
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "expansion"
INDEX = ROOT / "index.html"
TILE = 32
WIDTH = 24


def read_map_data():
    text = (ASSETS / "maps.js").read_text()
    return json.loads(text.split("window.expansionMaps=", 1)[1].split(";", 1)[0])


def route_rows():
    text = INDEX.read_text()
    match = re.search(r"const routeCollisionRows=\[(.*?)\];", text, re.S)
    return re.findall(r"'([.#gh]+)'", match.group(1))


def east_rows():
    rows = route_rows()[20:]
    rows[9] = ".." + rows[9][2:-2] + ".."
    rows[10] = ".." + rows[10][2:-2] + ".."
    for y in range(16, 20):
        rows[y] = "#" * WIDTH
    return rows


def replace_cells(row, first=11, last=15):
    return row[:first] + "." * (last - first) + row[last:]


def extend_rows(upper, lower, replace_road=False, extra_grass=()):
    rows = upper[:17] + ["##" + "." * 20 + "##"] * 3
    rows += ["##" + row[2:22] + "##" for row in lower[2:17]]
    rows += ["#" * WIDTH] * 3
    for y in [14, 15, 16, 20, 21, 22]:
        rows[y] = replace_cells(rows[y])
    # The lower clearing is a hunting area, not another route exit.
    if replace_road:
        rows[27] = rows[28] = "##" + "." * 20 + "##"
    for x0, x1, y0, y1 in extra_grass:
        for y in range(y0, y1):
            for x in range(x0, x1):
                assert rows[y][x] == "."
                rows[y] = rows[y][:x] + "g" + rows[y][x + 1 :]
    assert len(rows) == 38 and all(len(row) == WIDTH for row in rows)
    return rows


def extend_image(upper_path, lower_path, output_path, replace_road=False, extra_grass=()):
    upper = Image.open(upper_path).convert("RGB")
    lower = Image.open(lower_path).convert("RGB")
    assert upper.width == lower.width == WIDTH * TILE
    image = Image.new("RGB", (WIDTH * TILE, 38 * TILE))
    image.paste(upper.crop((0, 0, WIDTH * TILE, 17 * TILE)), (0, 0))

    # This open stretch bridges the original route and the new hunting clearing.
    for target_y, source_y in [(17, 7), (18, 8), (19, 7)]:
        band = upper.crop((0, source_y * TILE, WIDTH * TILE, (source_y + 1) * TILE))
        image.paste(band, (0, target_y * TILE))

    image.paste(lower.crop((0, 2 * TILE, WIDTH * TILE, 17 * TILE)), (0, 20 * TILE))
    image.paste(upper.crop((0, 17 * TILE, WIDTH * TILE, 20 * TILE)), (0, 35 * TILE))

    # Replace the copied east-west road with grass so it does not imply a closed exit.
    if replace_road:
        for target_y, source_y in [(27, 7), (28, 8)]:
            band = lower.crop((0, source_y * TILE, WIDTH * TILE, (source_y + 1) * TILE))
            image.paste(band, (0, target_y * TILE))

    grass = upper.crop((12 * TILE, 7 * TILE, 13 * TILE, 8 * TILE))
    for y in [14, 15, 16, 20, 21, 22]:
        for x in range(11, 15):
            image.paste(grass, (x * TILE, y * TILE))
    tall_grass = upper.crop((5 * TILE, 4 * TILE, 6 * TILE, 5 * TILE))
    for x0, x1, y0, y1 in extra_grass:
        for y in range(y0, y1):
            for x in range(x0, x1):
                image.paste(tall_grass, (x * TILE, y * TILE))
    image.save(output_path, optimize=True)


def main():
    maps = read_map_data()
    sources = {
        "eastRoute": (ASSETS / "east-route-linked.png", ROOT / "assets/common/15/15dcfb0ccaae7211d62365f30369226f8fd6d588b886f1c2dd50ddb08870469a.png", east_rows(), route_rows()),
        "graniteTrail": (ASSETS / "graniteTrail.png", ASSETS / "streamTrail.png", maps["graniteTrail"]["rows"][:20], maps["streamTrail"]["rows"][:20]),
        "streamTrail": (ASSETS / "streamTrail.png", ASSETS / "graniteTrail.png", maps["streamTrail"]["rows"][:20], maps["graniteTrail"]["rows"][:20]),
    }
    for key, (upper, lower, top_rows, lower_rows) in sources.items():
        filename = key + "-expanded.png"
        replace_road = key != "eastRoute"
        extra_grass = [(4, 9, 25, 28), (15, 20, 26, 30), (9, 13, 31, 33)] if key == "graniteTrail" else []
        extend_image(upper, lower, ASSETS / filename, replace_road, extra_grass)
        rows = extend_rows(top_rows, lower_rows, replace_road, extra_grass)
        if key == "eastRoute":
            east_expanded = rows
        else:
            maps[key]["rows"] = rows
            maps[key]["image"] = "assets/expansion/" + filename
    (ASSETS / "maps.js").write_text(
        "window.expansionMaps=" + json.dumps(maps, ensure_ascii=False, separators=(",", ":"))
        + ";window.eastRouteExpansionRows=" + json.dumps(east_expanded, separators=(",", ":")) + ";\n"
    )


if __name__ == "__main__":
    main()
