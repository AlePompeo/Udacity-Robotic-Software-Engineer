"""Octagonal shell + orthogonal 3x3 room grid, built from plain wall boxes with exact junctions.

Junction rules (no columns, no overlapping volumes except the hidden mitre of the shell corners):
  * shell corners (135 degrees): both walls are lengthened by (T/2) * tan(22.5 deg), which makes the
    union of the two boxes coincide with the mitred corner;
  * interior walls stop on the face of the wall they meet (trim = T/2);
  * collinear pieces meet end to end.
"""
import math, os, sys
import xml.etree.ElementTree as ET

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "Project1_new", "model")
T, H = 0.15, 2.5
h = T / 2
DOOR_H, SILL, WIN_TOP = 2.0, 0.9, 2.1
MITRE = h * math.tan(math.radians(22.5))
MAT = "file://media/materials/scripts/gazebo.material"

CREAM = ("Gazebo/Grey", (0.92, 0.92, 0.96, 1))
TERRA = ("Gazebo/CeilingTiled", (0.90, 0.58, 0.32, 1))
SAND = ("Gazebo/Grey", (0.95, 0.88, 0.65, 1))

V = [(-5.5, -6), (5.5, -6), (8, -3.5), (8, 3.5), (5.5, 6), (-5.5, 6), (-8, 3.5), (-8, -3.5)]
WIN = 1.2
shell_ops = {
    0: [(2.7, WIN, "window"), (5.5, 3.0, "door"), (8.3, WIN, "window")],
    1: [(1.77, WIN, "window")],
    2: [(1.7, WIN, "window"), (5.3, WIN, "window")],
    3: [(1.77, WIN, "window")],
    4: [(3.0, WIN, "window"), (5.5, WIN, "window"), (8.0, WIN, "window")],
    5: [(1.77, WIN, "window")],
    6: [(1.7, WIN, "window"), (5.3, WIN, "window")],
    7: [(1.77, WIN, "window")],
}

# id, p1, p2, trim at p1, trim at p2, style, openings (centre along the wall measured from p1, width, kind)
walls = []
for i in range(8):
    walls.append((f"W{i+1}", V[i], V[(i + 1) % 8], -MITRE, -MITRE, CREAM, shell_ops[i]))

d14, d16 = 1.4, 1.6
for y, tag in ((-3, "S"), (3, "N")):
    walls.append((f"H{tag}W", (-8, y), (-4, y), h, 0, SAND, [(2.0, d14, "door")]))
    walls.append((f"H{tag}C", (-4, y), (4, y), 0, 0, TERRA, [(4.0, d16, "door")]))
    walls.append((f"H{tag}E", (4, y), (8, y), 0, h, SAND, [(2.0, d14, "door")]))
for x, tag in ((-4, "W"), (4, "E")):
    walls.append((f"V{tag}S", (x, -6), (x, -3), h, h, SAND, [(1.5, d14, "door")]))
    walls.append((f"V{tag}C", (x, -3), (x, 3), h, h, TERRA, [(3.0, d16, "door")]))
    walls.append((f"V{tag}N", (x, 3), (x, 6), h, h, SAND, [(1.5, d14, "door")]))


def sub(parent, tag, text=None, **attrs):
    e = ET.SubElement(parent, tag, attrs)
    if text is not None:
        e.text = text
    return e


def fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def build():
    sdf = ET.Element("sdf", version="1.7")
    model = sub(sdf, "model", name="Building")
    sub(model, "static", "true")
    sub(model, "pose", "0 0 0 0 0 0")
    n = -1
    segs_out = []
    for wid, (x1, y1), (x2, y2), t1, t2, (script, (r, g, b, a)), ops in walls:
        L = math.hypot(x2 - x1, y2 - y1)
        dx, dy = (x2 - x1) / L, (y2 - y1) / L
        yaw = math.atan2(dy, dx)
        lo, hi = t1, L - t2
        segs, cur = [], lo
        for s, wd, kind in sorted(ops):
            a0, b0 = s - wd / 2, s + wd / 2
            assert lo + 0.2 < a0 and b0 < hi - 0.2, (wid, s, wd, lo, hi)
            if a0 > cur:
                segs.append((cur, a0, 0, H))
            if kind == "door":
                segs.append((a0, b0, DOOR_H, H))
            else:
                segs += [(a0, b0, 0, SILL), (a0, b0, WIN_TOP, H)]
            cur = b0
        segs.append((cur, hi, 0, H))
        for s0, s1, z0, z1 in segs:
            n += 1
            mid = (s0 + s1) / 2
            zc, hh, ln = (z0 + z1) / 2, z1 - z0, s1 - s0
            link = sub(model, "link", name=f"Wall_{n}")
            sub(link, "pose", f"{fmt(x1 + dx * mid)} {fmt(y1 + dy * mid)} 0 0 0 {fmt(yaw)}")
            size = f"{fmt(ln)} {fmt(T)} {fmt(hh)}"
            col = sub(link, "collision", name=f"Wall_{n}_Collision")
            sub(col, "pose", f"0 0 {fmt(zc)} 0 0 0")
            sub(sub(sub(col, "geometry"), "box"), "size", size)
            vis = sub(link, "visual", name=f"Wall_{n}_Visual")
            sub(vis, "pose", f"0 0 {fmt(zc)} 0 0 0")
            sub(sub(sub(vis, "geometry"), "box"), "size", size)
            mat = sub(vis, "material")
            sc = sub(mat, "script")
            sub(sc, "uri", MAT)
            sub(sc, "name", script)
            sub(mat, "ambient", f"{r} {g} {b} {a}")
            sub(mat, "diffuse", f"{r} {g} {b} {a}")
            segs_out.append((wid, n))
    return sdf, n


sdf, count = build()
os.makedirs(os.path.join(OUT, "Building"), exist_ok=True)
tree = ET.ElementTree(sdf)
ET.indent(tree, space="  ")
tree.write(os.path.join(OUT, "Building", "model.sdf"), encoding="UTF-8", xml_declaration=True)

cfg = ET.Element("model")
sub(cfg, "name", "Building")
sub(cfg, "version", "1.0")
sub(cfg, "sdf", "model.sdf", version="1.7")
sub(cfg, "description", "Edificio a piano unico: guscio ottagonale smussato e griglia 3x3 di stanze con atrio centrale, porte e finestre.")
t2 = ET.ElementTree(cfg)
ET.indent(t2, space="  ")
t2.write(os.path.join(OUT, "Building", "model.config"), encoding="UTF-8", xml_declaration=True)
print("wall links:", count + 1, "| walls:", len(walls), "| mitre extension: %.4f m" % MITRE)
