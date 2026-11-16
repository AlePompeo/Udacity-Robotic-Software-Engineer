import sys, math, itertools, numpy as np, xml.etree.ElementTree as ET
from matplotlib.path import Path
path = sys.argv[1]
root = ET.parse(path).getroot()
RES = 0.01
xs = np.arange(-8.4, 8.4, RES); ys = np.arange(-6.4, 6.4, RES)
X, Y = np.meshgrid(xs, ys)
pts = np.column_stack([X.ravel(), Y.ravel()])
walls, colmask = [], np.zeros(X.shape, bool)
for l in root.iter("link"):
    p = [float(v) for v in l.find("pose").text.split()]
    v = l.find("visual"); g = v.find("geometry"); zc = float(v.find("pose").text.split()[2])
    if g.find("box") is not None:
        L, t, h = [float(x) for x in g.find("box/size").text.split()]
        L, t = L - 0.004, t - 0.004
        c, s = math.cos(p[5]), math.sin(p[5])
        poly = [(p[0]+c*a-s*b, p[1]+s*a+c*b) for a, b in [(-L/2,-t/2),(L/2,-t/2),(L/2,t/2),(-L/2,t/2)]]
        m = Path(poly).contains_points(pts).reshape(X.shape)
        amb = v.find("material/ambient").text
        walls.append((l.get("name"), m, zc-h/2, zc+h/2, amb))
    else:
        r = float(g.find("cylinder/radius").text)
        colmask |= (X-p[0])**2 + (Y-p[1])**2 <= r*r
n = 0; tot = 0; out = 0; worst = 0; worst_pair = None
zf = 0
for (na, ma, a0, a1, ca), (nb, mb, b0, b1, cb) in itertools.combinations(walls, 2):
    if min(a1, b1) - max(a0, b0) <= 1e-6: continue
    inter = ma & mb
    k = int(inter.sum())
    if k == 0: continue
    n += 1; tot += k
    ko = int((inter & ~colmask).sum()); out += ko
    if ca != cb and abs(a1 - b1) < 1e-3: zf += int((inter & ~colmask).sum())
    if ko > worst: worst, worst_pair = ko, (na, nb)
a = RES*RES
print(f"{path}: muri={len(walls)} | coppie sovrapposte={n}, area={tot*a:.4f} m2 | fuori dalle colonne={out*a:.4f} m2 (max {worst*a:.4f} m2 {worst_pair})\n  sfarfallio (facce superiori coplanari, colori diversi, fuori colonne): {zf*a:.4f} m2")
