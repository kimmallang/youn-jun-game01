"""Build four 32px-grid maps from the game's existing outdoor art."""
from pathlib import Path
import json
import random
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'expansion'
OUT.mkdir(parents=True, exist_ok=True)
route = Image.open(ROOT / 'assets/common/east-route.png').convert('RGB')
town = Image.open(ROOT / 'assets/common/north-town.png').convert('RGB')
T, W, H = 32, 24, 20

def tile(src, box):
    return src.crop(box)

grass = [tile(route, (256, 96, 288, 128)), tile(route, (320, 96, 352, 128)), tile(route, (256, 256, 288, 288)), tile(route, (320, 256, 352, 288))]
path = tile(route, (384, 400, 416, 432))
road_top = tile(route, (128, 288, 160, 304))
road_bottom = tile(route, (128, 336, 160, 352))
road_left = tile(route, (352, 384, 368, 416))
road_right = tile(route, (464, 384, 480, 416))
tall = tile(route, (448, 128, 480, 160))
tree = tile(route, (64, 128, 128, 224))
flower = tile(route, (96, 224, 128, 256))
cliff = tile(route, (64, 352, 96, 384))
center = tile(town, (64, 224, 224, 368))
mart = tile(town, (528, 224, 688, 368))
gym = tile(town, (272, 16, 496, 160))
tree_background = set(grass[0].getdata())
tree_mask = Image.new('L', tree.size)
tree_mask.putdata([0 if color in tree_background else 255 for color in tree.getdata()])
SIDE_TREE_Y = (-64, 0, 64, 128, 192, 352, 416, 480, 544)

def paint_side_trees(img, clear=False):
    for x in (0, 704):
        if clear:
            for y in (*range(0, 288, T), *range(352, 640, T)):
                img.paste(grass[0], (x, y))
                img.paste(grass[0], (x+T, y))
        # Keep the grass transparent when trees overlap. The final upper tree
        # ends at the road; the first lower tree starts below it.
        for y in SIDE_TREE_Y:
            img.paste(tree, (x, y), tree_mask)

def paint_tree_border(img):
    top_tree = town.crop((64, 0, 128, 64))
    for x in range(0, W*T, 64):
        img.paste(top_tree, (x, 0))
        img.paste(tree, (x, 544))
    paint_side_trees(img)

def build(key, kind, seed):
    rng = random.Random(seed)
    img = Image.new('RGB', (W*T, H*T))
    cells = [['.' for _ in range(W)] for _ in range(H)]
    road_cells = set()
    for y in range(H):
        for x in range(W):
            img.paste(grass[(x*7+y*13+seed)%len(grass)], (x*T,y*T))
    def block(x,y,w,h,mark='#'):
        for yy in range(y,y+h):
            for xx in range(x,x+w):
                if 0<=xx<W and 0<=yy<H: cells[yy][xx]=mark
    def pave(x,y,w,h):
        for yy in range(y,y+h):
            for xx in range(x,x+w):
                img.paste(path,(xx*T,yy*T)); cells[yy][xx]='.'; road_cells.add((xx,yy))
    def woods(x,y):
        img.paste(tree,(x*T,y*T)); block(x,y,2,3)
    # Both borders have a two-tile opening in the same row as the road.
    pave(0,9,24,2)
    if kind=='town':
        if key=='grayCity':
            pave(11,1,2,16); pave(2,15,20,2)
            img.paste(gym,(272,32)); block(8,1,7,5)
            img.paste(center,(96,352)); block(3,11,5,5)
            img.paste(mart,(512,352)); block(16,11,5,5)
            for x,y in [(3,2),(18,2),(3,6),(19,6),(9,12),(13,12)]: woods(x,y)
        else:
            pave(5,1,2,16); pave(17,2,2,15); pave(2,15,20,2)
            img.paste(gym,(80,32)); block(2,1,7,5)
            img.paste(center,(480,64)); block(15,2,5,5)
            img.paste(mart,(288,352)); block(9,11,5,5)
            # Blue water channels are fully blocked and bordered by stone.
            draw=ImageDraw.Draw(img)
            for x in range(10,15):
                for y in range(2,8):
                    draw.rectangle((x*T,y*T,x*T+31,y*T+31),fill='#4b9eb9')
                    draw.line((x*T+4,y*T+13,x*T+27,y*T+13),fill='#89d2d7',width=3)
                    block(x,y,1,1)
            for x,y in [(3,13),(20,13),(3,4),(20,4)]: img.paste(flower,(x*T,y*T))
        # Reapply the crossing so buildings and decorative water never cut it.
        pave(0,9,24,2)
    else:
        grass_patches = ([(4,3,6,4),(10,4,4,3),(15,3,6,4),
                          (3,12,7,4),(15,12,6,4)] if key=='graniteTrail'
                         else [(3,13,6,3),(15,3,6,4),(11,14,3,3)])
        for x0,y0,w,h in grass_patches:
            for y in range(y0,y0+h):
                for x in range(x0,x0+w):
                    if rng.random()>.08:
                        img.paste(tall,(x*T,y*T)); block(x,y,1,1,'g')
        for x,y in ([(3,2),(18,2),(3,14),(18,14)] if key=='graniteTrail' else [(4,2),(16,2),(4,14),(16,14)]): woods(x,y)
        for x,y in ([(9,2),(10,2),(11,2),(12,2),(13,2),(9,16),(10,16),(11,16)] if key=='graniteTrail' else [(9,4),(9,5),(9,6),(9,7),(14,12),(14,13),(14,14)]):
            img.paste(cliff,(x*T,y*T)); block(x,y,1,1)
        for x,y in [(5,7),(6,7),(17,7),(18,7),(7,16),(15,16)]: img.paste(flower,(x*T,y*T))
        pave(0,9,24,2)
    for y in range(H):
        if y not in (9,10): cells[y][0]=cells[y][1]=cells[y][22]=cells[y][23]='#'
    if key=='streamTrail':
        woods(22,9)
        block(22,9,2,2)
    paint_tree_border(img)
    # The gym is in front of the upper tree line, as in Pallet Town.
    if kind=='town':
        img.paste(gym,(272,32) if key=='grayCity' else (80,32))
    block(0,0,24,2); block(0,17,24,3)
    visible_roads={(x,y) for x,y in road_cells if cells[y][x]=='.'}
    for x,y in visible_roads:
        if y>0 and (x,y-1) not in road_cells: img.paste(road_top,(x*T,y*T))
        if y<H-1 and (x,y+1) not in road_cells: img.paste(road_bottom,(x*T,y*T+16))
        if x>0 and (x-1,y) not in road_cells: img.paste(road_left,(x*T,y*T))
        if x<W-1 and (x+1,y) not in road_cells: img.paste(road_right,(x*T+16,y*T))
    img.save(OUT / (key+'.png'))
    return [''.join(row) for row in cells]

names=[('grayCity','town',1),('graniteTrail','route',2),('blueCity','town',3),('streamTrail','route',4)]
maps={key:{'name':{'grayCity':'회색시티','graniteTrail':'돌산길','blueCity':'블루시티','streamTrail':'물가숲길'}[key], 'kind':kind,'rows':build(key,kind,seed), 'image':'assets/expansion/'+key+'.png','levels':{'graniteTrail':[5,10],'streamTrail':[10,15]}.get(key)} for key,kind,seed in names}
linked=route.copy()
# Replace the source side strips so their clipped trees do not show through.
paint_side_trees(linked, clear=True)
# Continue the existing road's top and bottom edges through both openings.
# Sampling inside the road avoids the thin green vertical seams at x=64/704.
linked.paste(route.crop((96,288,176,352)),(0,288))
linked.paste(route.crop((608,288,688,352)),(688,288))
# The south edge has no connected map: continue the fence and tree border.
linked.paste(route.crop((112,512,256,640)),(368,512))
linked.save(OUT/'east-route-linked.png')
(OUT/'maps.js').write_text('window.expansionMaps='+json.dumps(maps,ensure_ascii=False,separators=(',',':'))+';\n')

# Keep the original interior's pixel detail while giving each new gym its own palette.
for key, shadow, light in [('grayCity','#252d38','#d2c8ae'),('blueCity','#173b5d','#c4e9e8')]:
    for source, suffix in [('viridian-gym.png','gym'),('viridian-gym-leader.png','leader')]:
        original=Image.open(ROOT/'assets/common'/source).convert('RGBA')
        alpha=original.getchannel('A')
        tinted=ImageOps.colorize(ImageOps.grayscale(original),shadow,light).convert('RGBA')
        tinted.putalpha(alpha)
        tinted.save(OUT/f'{key}-{suffix}.png')
