"""Build original 24x38 hunting maps and matching collision rows."""

from collections import deque
from pathlib import Path
import json
import random

from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MAPS_FILE = ROOT / "assets/expansion/maps.js"
WIDTH, HEIGHT, TILE = 24, 38, 32
SOURCE = Image.open(ROOT / "assets/expansion/graniteTrail-expanded.png").convert("RGB")
GRASS_TILE = SOURCE.crop((12*TILE, 7*TILE, 13*TILE, 8*TILE))
BUSH_TILE = SOURCE.crop((5*TILE, 4*TILE, 6*TILE, 5*TILE))


def remap(tile, colors):
    result = tile.copy()
    result.putdata([colors.get(pixel, pixel) for pixel in tile.getdata()])
    return result


GROUND = {
    "coast": GRASS_TILE,
    "sand": remap(GRASS_TILE, {(115,205,164):(229,211,157),(65,180,139):(198,174,119),(139,222,189):(252,236,185)}),
    "cave": remap(GRASS_TILE, {(115,205,164):(137,112,108),(65,180,139):(103,83,91),(139,222,189):(178,147,133)}),
    "snow": remap(GRASS_TILE, {(115,205,164):(223,243,237),(65,180,139):(167,209,215),(139,222,189):(251,255,245)}),
}
BUSH = {
    "coast": remap(BUSH_TILE, {(57,148,49):(34,137,110),(115,205,164):(115,205,164),(65,180,139):(48,170,138),(57,90,16):(21,92,87),(164,230,197):(160,228,181),(24,164,106):(82,195,153)}),
    "snow": remap(BUSH_TILE, {(57,148,49):(86,161,165),(115,205,164):(223,243,237),(65,180,139):(129,194,196),(57,90,16):(48,107,130),(164,230,197):(250,255,242),(24,164,106):(187,229,223)}),
}
BUSH_MASK = Image.new("L", (TILE, TILE))
BUSH_MASK.putdata([255 if bush != ground else 0 for bush,ground in zip(BUSH_TILE.getdata(), GRASS_TILE.getdata())])
FOREST_COLORS = {
    (57,148,49):(81,145,153),(131,213,98):(163,210,210),
    (189,255,139):(244,255,234),(115,205,164):(31,104,120),
    (57,90,16):(35,87,109),(65,180,139):(21,82,101),
    (139,222,189):(75,157,160),(24,164,106):(80,158,164),
    (115,98,98):(58,76,89),(65,57,49):(27,51,69),
}
SNOW_FOREST = remap(SOURCE, FOREST_COLORS)


def blank(fill):
    return [[fill for _ in range(WIDTH)] for _ in range(HEIGHT)]


def ellipse(grid, cx, cy, rx, ry, value):
    for y in range(HEIGHT):
        for x in range(WIDTH):
            jitter = (((x * 17 + y * 23) % 7) - 3) * .025
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1 + jitter:
                grid[y][x] = value


def rect(grid, x0, y0, x1, y1, value):
    for y in range(max(0, y0), min(HEIGHT, y1 + 1)):
        for x in range(max(0, x0), min(WIDTH, x1 + 1)):
            grid[y][x] = value


def exits(grid):
    # Every map joins the existing east-west route at its established y=9.5.
    for y in range(8, 12):
        for x in range(WIDTH):
            grid[y][x] = "."
    for y in (9, 10):
        for x in (0, 1, 2, 21, 22, 23):
            grid[y][x] = "."
    for y in range(HEIGHT):
        if y not in (9, 10):
            grid[y][0] = grid[y][WIDTH - 1] = "#"


def coast_boardwalk(x, y):
    return ((5<=x<=7 and 11<=y<=22) or (16<=x<=18 and 11<=y<=22)
            or (6<=x<=18 and 20<=y<=22) or (10<=x<=12 and 27<=y<=33)
            or (6<=x<=19 and 32<=y<=34))


def encounter_patches(grid, patches, excluded=None):
    # Route 1 uses broad, joined grass plots. Keep that shape while clipping
    # each plot to the walkable ground in these more irregular hunting maps.
    for x0,y0,x1,y1 in patches:
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                if 0<=x<WIDTH and 0<=y<HEIGHT and grid[y][x]=="." and not 8<=y<=11 and not (excluded and excluded(x,y)):
                    grid[y][x]="g"


def make_coast():
    g = blank(".")
    for shape in ((5, 4, 4, 3), (17, 4, 5, 3), (7, 15, 5, 3),
                  (18, 17, 4, 5), (4, 25, 4, 5), (13, 27, 5, 4),
                  (20, 31, 4, 5), (7, 34, 4, 3)):
        ellipse(g, *shape, "#")
    for x in range(WIDTH):
        g[0][x] = g[HEIGHT - 1][x] = "#"
    exits(g)
    # Timber boardwalks lead into two broad, explorable islands.
    rect(g, 5, 11, 7, 22, ".")
    rect(g, 6, 20, 18, 22, ".")
    rect(g, 16, 10, 18, 22, ".")
    rect(g, 10, 27, 12, 33, ".")
    rect(g, 6, 32, 19, 34, ".")
    encounter_patches(g, (
        (9,2,13,6),(2,7,6,7),(10,7,15,7),(2,12,6,16),(11,12,15,16),
        (1,17,3,20),(4,17,8,20),(9,17,15,19),(11,18,16,21),
        (18,21,22,25),(9,24,14,27),(1,29,7,34),(10,29,14,34),
        (16,31,20,35),(11,35,17,36),
    ), excluded=coast_boardwalk)
    return g


def make_cave():
    g = blank("#")
    for shape in ((6, 5, 5, 4), (17, 5, 5, 4), (6, 16, 5, 5),
                  (17, 17, 5, 5), (7, 28, 6, 6), (18, 29, 5, 6)):
        ellipse(g, *shape, ".")
    exits(g)
    for path in ((5, 11, 7, 18), (16, 11, 18, 18), (6, 19, 8, 30),
                 (16, 19, 18, 30), (7, 27, 19, 29), (7, 32, 19, 34)):
        rect(g, *path, ".")
    encounter_patches(g, (
        (3,3,8,6),(15,3,20,6),(3,13,8,17),(15,13,20,17),
        (5,18,9,20),(16,18,20,21),(6,24,11,28),(15,24,20,28),
        (4,30,8,33),(11,30,16,33),(18,30,21,33),
    ))
    return g


ICE_PONDS = ((6, 5, 3, 3), (17, 15, 4, 3), (5, 27, 3, 4), (19, 31, 3, 3))


def in_pond(x, y):
    return any(((x-cx)/rx)**2 + ((y-cy)/ry)**2 < 1 for cx,cy,rx,ry in ICE_PONDS)


def make_snow():
    g = blank(".")
    for shape in ICE_PONDS:
        ellipse(g, *shape, "#")
    for shape in ((11, 3, 3, 2), (3, 19, 2, 4), (21, 24, 2, 4),
                  (11, 35, 4, 2)):
        ellipse(g, *shape, "#")
    for x in range(WIDTH):
        for y in (0, 1, HEIGHT - 3, HEIGHT - 2, HEIGHT - 1):
            g[y][x] = "#"
    exits(g)
    # Leave a two-row opening between complete trees at the west entrance.
    for y in range(HEIGHT):
        for x in (0, 1, WIDTH-2, WIDTH-1):
            if x < 2 and y in (9, 10):
                continue
            g[y][x] = "#"
    for y in (9, 10):
        for x in (0, 1, 2, 3):
            g[y][x] = "."
    encounter_patches(g, (
        (3,3,7,6),(14,3,20,6),(10,5,14,7),(6,12,11,16),
        (11,15,14,19),(19,13,21,18),(6,19,11,23),(12,20,17,24),
        (15,25,20,28),(9,28,14,32),(3,30,7,34),
    ))
    return g


def validate(grid, name):
    assert len(grid) == HEIGHT and all(len(row) == WIDTH for row in grid)
    start = (1, 9)
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < WIDTH and 0 <= ny < HEIGHT and grid[ny][nx] != "#" and (nx,ny) not in seen:
                seen.add((nx,ny))
                queue.append((nx,ny))
    if name != "frostPass":
        assert (22, 9) in seen, f"{name}: disconnected exit"
    unreachable = [(x,y) for y in range(HEIGHT) for x in range(WIDTH) if grid[y][x] == "g" and (x,y) not in seen]
    for x,y in unreachable:
        grid[y][x] = "."
    remaining={(x,y) for y in range(HEIGHT) for x in range(WIDTH) if grid[y][x]=="g"}
    while remaining:
        patch={remaining.pop()}
        queue=deque(patch)
        while queue:
            x,y=queue.popleft()
            for neighbor in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    patch.add(neighbor)
                    queue.append(neighbor)
        if len(patch)<4:
            for x,y in patch:
                grid[y][x]="."
    minimum={"tidalMarsh":110,"moonCavern":180,"frostPass":180}.get(name,50)
    assert sum(cell == "g" for row in grid for cell in row)>=minimum, f"{name}: too few encounters"


def pixel(draw, x, y, color, w=4, h=4):
    draw.rectangle((x, y, x+w-1, y+h-1), fill=color)


def paste_ground(image, key, px, py, seed):
    image.paste(ImageChops.offset(GROUND[key], (seed % 4) * 2, ((seed // 3) % 4) * 2), (px, py))


def neighbors(grid, x, y, cell):
    return {
        direction: 0 <= x+dx < WIDTH and 0 <= y+dy < HEIGHT and grid[y+dy][x+dx] == cell
        for direction, dx, dy in (("left",-1,0),("right",1,0),("up",0,-1),("down",0,1))
    }


def painter_coast(image, draw, grid, x, y, cell, seed):
    px,py=x*TILE,y*TILE
    water=neighbors(grid,x,y,"#")
    if cell=="#":
        land={k:not v for k,v in water.items()}
        draw.rectangle((px,py,px+31,py+31),fill="#237995")
        r=random.Random(seed+614)
        for _ in range(10):
            ox,oy=r.randrange(0,16)*2,r.randrange(0,16)*2
            color=r.choice(("#2d87a0","#1c6b8a","#338fa2","#236e8e"))
            pixel(draw,px+ox,py+oy,color,r.choice((2,4,6)),2)
        for i in range(3):
            ox=((seed*3+i*11)%13)*2
            oy=((seed+i*7)%13)*2+2
            pixel(draw,px+ox,py+oy+2,"#185e80",10,2)
            pixel(draw,px+ox+2,py+oy,"#77cfc9",10,2)
            pixel(draw,px+ox+6,py+oy-2,"#a5e4d0",4,2)
        for direction,present in land.items():
            if not present: continue
            if direction=="left": edge=(px,py,px+5,py+31)
            elif direction=="right": edge=(px+26,py,px+31,py+31)
            elif direction=="up": edge=(px,py,px+31,py+5)
            else: edge=(px,py+26,px+31,py+31)
            draw.rectangle(edge,fill="#4eb1b6")
            for i in range(0,32,8):
                if direction in ("left","right"):
                    ex=px+(2 if direction=="left" else 28)
                    pixel(draw,ex,py+i,"#b1e7d2",4,2)
                else:
                    ey=py+(2 if direction=="up" else 28)
                    pixel(draw,px+i,ey,"#b1e7d2",4,2)
        return
    bridge=coast_boardwalk(x,y)
    if bridge:
        draw.rectangle((px,py,px+31,py+31),fill="#ab8456")
        for oy in (0,15,30):
            pixel(draw,px,py+oy,"#584b46",32,2)
            pixel(draw,px,py+oy+2,"#dfb678",32,2)
        for ox,oy in ((4,7),(20,10),(11,23),(27,24)):
            pixel(draw,px+ox,py+oy,"#805e46",6,2)
            pixel(draw,px+ox+2,py+oy-2,"#e5c68d",4,2)
        for ox in (2,28):
            for oy in (7,23):pixel(draw,px+ox,py+oy,"#4d4850",2,2)
    else:
        near_water=any(water.values())
        paste_ground(image,"sand" if near_water or 8<=y<=11 else "coast",px,py,seed)
        for direction,present in water.items():
            if not present:continue
            if direction=="left":
                pixel(draw,px,py,"#ead9a3",4,32)
                for oy in (2,10,18,26):pixel(draw,px+4,py+oy,"#f6e8b9",2,4)
            elif direction=="right":
                pixel(draw,px+28,py,"#ead9a3",4,32)
                for oy in (0,8,16,24):pixel(draw,px+26,py+oy,"#f6e8b9",2,4)
            elif direction=="up":
                pixel(draw,px,py,"#ead9a3",32,4)
                for ox in (2,10,18,26):pixel(draw,px+ox,py+4,"#f6e8b9",4,2)
            else:
                pixel(draw,px,py+28,"#ead9a3",32,4)
                for ox in (0,8,16,24):pixel(draw,px+ox,py+26,"#f6e8b9",4,2)
        if cell=="g":
            image.paste(BUSH["coast"],(px,py),BUSH_MASK)
            for ox,top in ((7,7),(18,4),(25,12)):
                pixel(draw,px+ox,py+top,"#b9ae70",2,11)
                pixel(draw,px+ox+2,py+top+2,"#efe1a3",2,5)


def painter_cave(image, draw, grid, x, y, cell, seed):
    px,py=x*TILE,y*TILE
    if cell=="#":
        draw.rectangle((px,py,px+31,py+31),fill="#3b384b")
        r=random.Random(seed+415)
        for i in range(8):
            ox,oy=r.randrange(0,14)*2,r.randrange(0,14)*2
            width,height=r.choice(((6,4),(10,4),(4,8),(8,6)))
            color=r.choice(("#4b485c","#575066","#333242","#655b6d"))
            pixel(draw,px+ox,py+oy,color,width,height)
            if i%3==0:pixel(draw,px+ox,py+oy,"#7b7080",max(2,width-4),2)
        floor=neighbors(grid,x,y,".")
        crystals=neighbors(grid,x,y,"g")
        if floor["down"] or crystals["down"]:
            pixel(draw,px,py+25,"#252a3a",32,7)
            for ox in (0,8,18,26):pixel(draw,px+ox,py+25,"#857589",6,2)
        if floor["up"] or crystals["up"]:
            pixel(draw,px,py,"#292e3d",32,4)
        return
    paste_ground(image,"cave",px,py,seed)
    r=random.Random(seed+773)
    for _ in range(5):
        ox,oy=r.randrange(0,15)*2,r.randrange(0,15)*2
        pixel(draw,px+ox,py+oy,r.choice(("#715d69","#c0a193","#796a72")),r.choice((2,4)),2)
    if neighbors(grid,x,y,"#")["up"]:
        pixel(draw,px,py,"#655365",32,4)
        pixel(draw,px,py+4,"#ad8f88",32,2)
    if cell=="g":
        for ox,oy,height in ((3,13,16),(15,5,24),(25,16,12)):
            tip=(px+ox+4,py+oy)
            draw.polygon((px+ox-2,py+oy+height-1,*tip,px+ox+10,py+oy+height-1),fill="#2c4054")
            draw.polygon((px+ox,py+oy+height-4,px+ox+4,py+oy+3,px+ox+4,py+oy+height-4),fill="#63b9c3")
            draw.polygon((px+ox+4,py+oy+3,px+ox+8,py+oy+height-4,px+ox+4,py+oy+height-4),fill="#267f9c")
            pixel(draw,px+ox+4,py+oy+5,"#dcf6df",2,7)
            pixel(draw,px+ox+1,py+oy+height-2,"#b5dbd1",8,2)


def painter_snow(image, draw, grid, x, y, cell, seed):
    px,py=x*TILE,y*TILE
    if cell=="#" and (x in (0,1,WIDTH-2,WIDTH-1) or y in (0,1,HEIGHT-3,HEIGHT-2,HEIGHT-1)) and not in_pond(x,y):
        if y>=HEIGHT-3 or x in (0, 1):
            # The bottom forest is three rows tall; its snow-capped crowns
            # begin at row 35. The source west edge has a complete tree
            # ending above and starting below the route entrance.
            source_y=py
        elif x in (WIDTH-2, WIDTH-1) and 1<=y<HEIGHT-3:
            # The east edge has no exit, so repeat whole tree pairs there.
            source_y=(4 if y%2 else 5)*TILE
        else:
            source_y=py
        image.paste(SNOW_FOREST.crop((px,source_y,px+32,source_y+32)),(px,py))
        return
    if cell=="#" and in_pond(x,y):
        draw.rectangle((px,py,px+31,py+31),fill="#74b9c7")
        r=random.Random(seed+308)
        for _ in range(8):
            ox,oy=r.randrange(0,15)*2,r.randrange(0,15)*2
            pixel(draw,px+ox,py+oy,r.choice(("#83c9d1","#5eafbf","#9fd8db")),r.choice((4,6,8)),2)
        for ox,oy in ((2,7),(17,18)):
            pixel(draw,px+ox,py+oy,"#d5f4eb",10,2)
            pixel(draw,px+ox+6,py+oy+2,"#428da8",10,2)
        return
    paste_ground(image,"snow",px,py,seed)
    if cell=="#":
        # A joined rock face, with snow only at its exposed upper edge.
        # Adjacent blocked cells share the same wall instead of drawing
        # separate cone-shaped half trees in every tile.
        draw.rectangle((px,py,px+31,py+31),fill="#688f9d")
        r=random.Random(seed+914)
        for _ in range(7):
            ox,oy=r.randrange(0,16)*2,r.randrange(0,16)*2
            pixel(draw,px+ox,py+oy,r.choice(("#547e91","#82a8ae","#467486")),r.choice((4,6,8)),2)
        adjacent=neighbors(grid,x,y,"#")
        if not adjacent["up"]:
            pixel(draw,px,py,"#e2f5ec",32,8)
            for ox in (2,10,18,26):
                pixel(draw,px+ox,py+8,"#b8dfe0",4,2+(ox%4))
            pixel(draw,px+4,py+2,"#ffffff",14,2)
        if not adjacent["down"]:
            pixel(draw,px,py+28,"#345d77",32,4)
            pixel(draw,px+4,py+26,"#9bc5c9",24,2)
        if not adjacent["left"]:
            pixel(draw,px,py,"#426f83",4,32)
        if not adjacent["right"]:
            pixel(draw,px+28,py,"#8eb9bf",4,32)
        return
    r=random.Random(seed+117)
    for _ in range(4):
        ox,oy=r.randrange(0,15)*2,r.randrange(0,15)*2
        pixel(draw,px+ox,py+oy,r.choice(("#f9fff3","#b8dce0","#e9fbf4")),2,2)
    if cell=="g":
        # Dense frost grass makes each encounter plot visible as a single bed.
        image.paste(BUSH["snow"],(px,py),BUSH_MASK)
        for ox in (3,13,24):
            pixel(draw,px+ox,py+5,"#f7fff1",4,2)


def render(grid, theme, path):
    image = Image.new("RGB",(WIDTH*TILE,HEIGHT*TILE))
    draw = ImageDraw.Draw(image)
    painter = {"coast":painter_coast,"cave":painter_cave,"snow":painter_snow}[theme]
    for y,row in enumerate(grid):
        for x,cell in enumerate(row):
            painter(image,draw,grid,x,y,cell,(x*37+y*71)%101)
    image.save(path)


def main():
    raw = MAPS_FILE.read_text()
    prefix, east = raw.split(";window.eastRouteExpansionRows=",1)
    maps = json.loads(prefix.split("=",1)[1])
    # Open the previously closed edge of 물가숲길 for the new coastal route.
    stream = maps["streamTrail"]
    for y in (9, 10):
        stream["rows"][y] = stream["rows"][y][:22] + ".."
    stream_image = Image.open(ROOT / stream["image"])
    for y in (9, 10):
        for x in (22, 23):
            stream_image.paste(stream_image.crop(((x-2)*TILE,y*TILE,(x-1)*TILE,(y+1)*TILE)),(x*TILE,y*TILE))
    stream_image.save(ROOT / stream["image"])
    additions = (
        ("tidalMarsh","해안 물길","coast",make_coast,[38,78],"갈대밭 · 수변 포켓몬","물가의 갈대밭을 탐색해 봐. 서쪽은 물가숲길, 동쪽은 달빛 동굴이야."),
        ("moonCavern","달빛 동굴","cave",make_cave,[40,85],"수정 군락 · 동굴 포켓몬","빛나는 수정 사이에 야생 포켓몬이 있어. 서쪽은 해안 물길, 동쪽은 서리 고개야."),
        ("frostPass","서리 고개","snow",make_snow,[43,100],"눈더미 · 얼음 포켓몬","눈더미를 탐색해 봐. 얼어붙은 연못은 지나갈 수 없고 서쪽 길은 동굴로 이어져."),
    )
    for key,name,theme,build,levels,hint,guidance in additions:
        grid=build()
        validate(grid,key)
        filename=f"assets/expansion/{key}.png"
        render(grid,theme,ROOT/filename)
        maps[key]={"name":name,"kind":"route","rows":["".join(row) for row in grid],"image":filename,"levels":levels,"hint":hint,"guidance":guidance}
        print(key, "encounter tiles",sum(cell == "g" for row in grid for cell in row))
    MAPS_FILE.write_text("window.expansionMaps="+json.dumps(maps,ensure_ascii=False,separators=(",",":"))+";window.eastRouteExpansionRows="+east)


if __name__ == "__main__":
    main()
