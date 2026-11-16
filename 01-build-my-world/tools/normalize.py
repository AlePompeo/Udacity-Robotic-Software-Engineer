import re, sys, os, glob, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xmlfmt import parse, emit, N, find

SRC, DST, WORLD_ORIG = sys.argv[1:4]
DECL = '<?xml version="1.0"?>'
MINE = {"Rover", "Crate", "Plant", "Sofa", "Rug", "Building"}   # file generati da me: versione SDF allineata a Gazebo 11
VER = "1.7"

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
log = []

def set_decl(root):
    root.children = [c for c in root.children if not (c.kind == "raw" and c.open.startswith("<?xml"))]
    root.children.insert(0, N("raw", DECL))

def set_version(open_tag, v):
    return re.sub(r"(version=)(['\"])[^'\"]*\2", lambda m: f"{m.group(1)}{m.group(2)}{v}{m.group(2)}", open_tag, count=1)

for d in sorted(glob.glob(f"{DST}/model/*/")):
    name = os.path.basename(d.rstrip("/"))
    # model.sdf
    p = d + "model.sdf"
    t = parse(open(p, encoding="utf-8").read())
    set_decl(t)
    sdf = find(t, "sdf")
    if name in MINE:
        sdf.open = set_version(sdf.open, VER)
    open(p, "w", encoding="utf-8").write(emit(t))
    # model.config
    p = d + "model.config"
    t = parse(open(p, encoding="utf-8").read())
    set_decl(t)
    if name in MINE:
        m = find(t, "model")
        for c in m.children:
            if c.name == "sdf":
                c.open = set_version(c.open, VER)
    open(p, "w", encoding="utf-8").write(emit(t))
    log.append(f"{name}: dichiarazione uniforme, rientro normalizzato" + (f", sdf {VER}" if name in MINE else ""))

# ---- world: start again from the file Gazebo saved, apply only the three intended edits
w = parse(open(WORLD_ORIG, encoding="utf-8").read())
sdf = find(w, "sdf")
world = find(sdf, "world")
building = next(c for c in world.children if c.name == "model" and "name='building'" in c.open)
new_links = [c for c in find(find(parse(open(f"{DST}/model/Building/model.sdf", encoding="utf-8").read()), "sdf"), "model").children if c.name == "link"]
def single(n):
    n.open = n.open.replace('"', "'")
    for c in n.children: single(c)
for l in new_links: single(l)
old = [c for c in building.children if c.name == "link"]
building.children = [c for c in building.children if c.name != "link"] + new_links
world.children = [c for c in world.children if c.name != "state"]
renamed = 0
for link in (n for n in iter_all(world)) if False else []:
    pass
def walk(n):
    yield n
    for c in n.children: yield from walk(c)
for link in (n for n in walk(world) if n.kind == "el" and n.name == "link"):
    seen = set()
    for c in link.children:
        if c.name in ("collision", "visual", "sensor"):
            nm = re.search(r"name='([^']*)'", c.open).group(1)
            if nm in seen:
                c.open = c.open.replace(f"name='{nm}'", f"name='{nm}_{c.name}'"); renamed += 1
            seen.add(nm)
open(f"{DST}/world/MyWorld.world", "w", encoding="utf-8").write(emit(w))
log.append(f"world: ripartito dal file salvato da Gazebo (apici singoli, nessuna intestazione); building {len(old)}->{len(new_links)} link, <state> rimosso, {renamed} nomi duplicati rinominati")
print("\n".join(log))
