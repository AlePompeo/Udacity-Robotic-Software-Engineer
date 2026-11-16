import math, re, sys, collections
import numpy as np
import xml.etree.ElementTree as ET
from matplotlib.path import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

PROJ = sys.argv[1]
RES = 0.05
xs = np.arange(-9, 9, RES) + RES / 2
ys = np.arange(-7, 7, RES) + RES / 2
X, Y = np.meshgrid(xs, ys)
pts = np.column_stack([X.ravel(), Y.ravel()])


def rect(cx, cy, yaw, x0, x1, y0, y1):
    c, s = math.cos(yaw), math.sin(yaw)
    return [(cx + c * a - s * b, cy + s * a + c * b) for a, b in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]


def mask(poly):
    return Path(poly).contains_points(pts).reshape(X.shape)


# ---- walls (union of all boxes whose lower part is solid; doors keep only the lintel -> passable)
root = ET.parse(f"{PROJ}/model/Building/model.sdf").getroot()
walls = np.zeros(X.shape, bool)
wall_polys = []
for l in root.iter("link"):
    p = [float(v) for v in l.find("pose").text.split()]
    L, t, h = [float(x) for x in l.find("visual/geometry/box/size").text.split()]
    zc = float(l.find("visual/pose").text.split()[2])
    if zc - h / 2 > 1.0:       # lintel above a door/window: does not block a rover
        continue
    poly = rect(p[0], p[1], p[5], -L / 2, L / 2, -t / 2, t / 2)
    wall_polys.append(poly)
    walls |= mask(poly)

# ---- furniture footprints from the world file
FOOT = {
    "Plant": lambda x, y, a: [(x + 0.3 * math.cos(k * math.pi / 8), y + 0.3 * math.sin(k * math.pi / 8)) for k in range(16)],
    "Crate": lambda x, y, a: rect(x, y, a, -0.15, 0.15, -0.15, 0.15),
    "Rover": lambda x, y, a: rect(x, y, a, -0.27, 0.27, -0.21, 0.21),
    "Table": lambda x, y, a: rect(x, y, a, -0.75, 0.75, -0.4, 0.4),
    "Sofa": lambda x, y, a: rect(x, y, a, -0.8, 0.8, -0.35, 0.35),
    "Bookshelf": lambda x, y, a: rect(x, y, a, -0.45, 0.45, -0.4, 0.01),
}
world = open(f"{PROJ}/world/MyWorld.world").read()
items = []
for name, uri, x, y, yaw in re.findall(r"<name>(\w+)</name><uri>model://(\w+)</uri><pose>([-\d.]+) ([-\d.]+) [-\d.]+ [-\d.]+ [-\d.]+ ([-\d.]+)</pose>", world):
    if uri in FOOT:
        items.append((name, uri, float(x), float(y), float(yaw), FOOT[uri](float(x), float(y), float(yaw))))

problems = []
fm = {}
for name, uri, x, y, yaw, poly in items:
    m = mask(poly)
    fm[name] = m
    if (m & walls).any():
        problems.append(f"{name} ({uri}) tocca un muro ({int((m & walls).sum()) * RES * RES:.3f} m2)")
for (a, ma), (b, mb) in __import__("itertools").combinations(fm.items(), 2):
    if (ma & mb).any():
        problems.append(f"{a} e {b} si sovrappongono")

# ---- navigability: rover footprint ~ disc of radius 0.33 -> inflate every obstacle by it
R = 0.33
rc = int(math.ceil(R / RES))
offs = [(dy, dx) for dy in range(-rc, rc + 1) for dx in range(-rc, rc + 1) if (dx * dx + dy * dy) * RES * RES <= R * R]
obst = walls.copy()
for name, uri, x, y, yaw, poly in items:
    if uri != "Rover":
        obst |= fm[name]
inflated = np.zeros_like(obst)
for dy, dx in offs:
    inflated |= np.roll(np.roll(obst, dy, axis=0), dx, axis=1)
free = ~inflated


def cell(x, y):
    return int(round((y - ys[0]) / RES)), int(round((x - xs[0]) / RES))


rover1 = next((i for i in items if i[0] == "rover_1"), None)
start = cell(rover1[2], rover1[3])
seen = np.zeros_like(free)
dq = collections.deque([start])
seen[start] = True
while dq:
    r, c = dq.popleft()
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < free.shape[0] and 0 <= cc < free.shape[1] and free[rr, cc] and not seen[rr, cc]:
            seen[rr, cc] = True
            dq.append((rr, cc))

targets = {
    "atrio": (0, -2.0), "sala sud (ingresso)": (0, -4.6), "sala nord": (1.5, 4.2), "sala est": (5.5, 0.3), "sala ovest": (-5.5, 0.3),
    "angolo SE": (4.9, -5.2), "angolo NE": (4.9, 5.2), "angolo NW": (-4.9, 5.2), "angolo SW": (-4.9, -5.2),
    "esterno davanti all'ingresso": (0, -7.0 + 0.6),
}
rows = []
for k, (tx, ty) in targets.items():
    r, c = cell(tx, ty)
    ok = bool(seen[r, c]) if free[r, c] else None
    rows.append((k, tx, ty, "raggiungibile" if ok else ("occupato" if ok is None else "NON raggiungibile")))
for name, uri, x, y, yaw, poly in items:
    if uri == "Rover":
        r, c = cell(x, y)
        rows.append((name, x, y, "raggiungibile" if seen[r, c] else "NON raggiungibile"))

print(f"{PROJ}: mobili/ostacoli={len(items)} | problemi di contatto: {len(problems)}")
for p in problems:
    print("   !", p)
print("raggiungibilita' (rover con ingombro r=0.33 m):")
for k, x, y, s in rows:
    print(f"   {k:32s} ({x:5.1f},{y:5.1f})  {s}")

# ---- drawing
fig, ax = plt.subplots(figsize=(12, 9.5))
ax.imshow(seen, origin="lower", extent=(-9, 9, -7, 7), cmap="Greens", alpha=0.35)
for poly in wall_polys:
    ax.add_patch(Polygon(poly, closed=True, fc="#222", ec="#222", lw=0.3))
colr = {"Plant": "green", "Crate": "saddlebrown", "Rover": "red", "Table": "orange", "Sofa": "purple", "Bookshelf": "black"}
for name, uri, x, y, yaw, poly in items:
    ax.add_patch(Polygon(poly, closed=True, fc=colr[uri], ec="k", lw=0.5, alpha=0.8))
ax.set_aspect("equal"); ax.set_xlim(-9, 9); ax.set_ylim(-7, 7); ax.grid(alpha=.25)
ax.set_title("Layout: verde = zona raggiungibile da rover_1 (ingombro 0.33 m); mobili colorati")
fig.savefig(f"{sys.argv[2]}", dpi=100, bbox_inches="tight")
