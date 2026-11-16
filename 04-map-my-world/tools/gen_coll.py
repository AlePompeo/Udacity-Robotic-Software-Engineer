"""Turn the visual mesh of a COLLADA model into box collision shapes for an SDF model.

usage: gen_coll.py <model.dae> <output.xml>
Furniture becomes bounding boxes; a big room-sized volume becomes a rasterized footprint of its walls.
Paste the generated <collision> elements into the <link> of model.sdf.
"""
import sys, xml.etree.ElementTree as E, numpy as np
N = '{http://www.collada.org/2005/11/COLLADASchema}'
src, out = sys.argv[1], sys.argv[2]
root = E.parse(src).getroot()
scale = float(root.find(f'{N}asset/{N}unit').get('meter'))
geoms = {}
for g in root.iter(N + 'geometry'):
    m = g.find(N + 'mesh')
    verts = m.find(f'{N}vertices/{N}input').get('source')[1:]
    pos = None
    for s in m.findall(N + 'source'):
        if s.get('id') == verts:
            pos = np.array(s.find(N + 'float_array').text.split(), float).reshape(-1, 3)
    tris = []
    for t in m.findall(N + 'triangles'):
        off = len(t.findall(N + 'input'))
        p = np.array(t.find(N + 'p').text.split(), int)[::off]
        tris.append(p[:len(p) // 3 * 3].reshape(-1, 3))
    for t in m.findall(N + 'polylist'):
        off = len(t.findall(N + 'input'))
        vc = np.array(t.find(N + 'vcount').text.split(), int)
        p = np.array(t.find(N + 'p').text.split(), int)[::off]
        i = 0
        for c in vc:
            for k in range(1, c - 1): tris.append(np.array([[p[i], p[i + k], p[i + k + 1]]]))
            i += c
    if pos is not None and tris:
        geoms[g.get('id')] = (pos, np.concatenate(tris))
nodes = {n.get('id'): n for n in root.iter(N + 'node') if n.get('id')}
inst = []
def mat(n):
    m = n.find(N + 'matrix')
    return np.array(m.text.split(), float).reshape(4, 4) if m is not None else np.eye(4)
def walk(n, M):
    M = M @ mat(n)
    for ig in n.findall(N + 'instance_geometry'):
        gid = ig.get('url')[1:]
        if gid in geoms and n.get('id') != 'collision_node':
            P, T = geoms[gid]
            inst.append(((M[:3, :3] @ P.T).T + M[:3, 3]) * scale), inst.append(T)
    for inn in n.findall(N + 'instance_node'):
        t = nodes.get(inn.get('url')[1:])
        if t is not None: walk(t, M)
    for c in n.findall(N + 'node'): walk(c, M)
for vs in root.iter(N + 'visual_scene'):
    for n in vs.findall(N + 'node'): walk(n, np.eye(4))
rng = np.random.default_rng(0)
boxes = []; cells = set(); CS = 0.1
for W, T in zip(inst[0::2], inst[1::2]):
    lo, hi = W.min(0), W.max(0); d = hi - lo
    if hi[2] < 0.05 or lo[2] > 1.0 or max(d[0], d[1]) < 0.05: continue
    if d[0] * d[1] > 4.0 and d[2] > 1.0:
        a, b, c = W[T[:, 0]], W[T[:, 1]], W[T[:, 2]]
        area = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
        n = np.maximum(1, (area / (CS * CS / 4)).astype(int)).clip(max=4000)
        for k in range(len(T)):
            if area[k] < 1e-6: continue
            u = rng.random((n[k], 2)); f = u.sum(1) > 1; u[f] = 1 - u[f]
            P = a[k] + u[:, :1] * (b[k] - a[k]) + u[:, 1:] * (c[k] - a[k])
            P = P[(P[:, 2] > 0.05) & (P[:, 2] < 1.0)]
            for x, y in np.floor(P[:, :2] / CS).astype(int): cells.add((x, y))
        continue
    boxes.append(((lo + hi) / 2, d))
rows = {}
for x, y in cells: rows.setdefault(x, []).append(y)
for x, ys in rows.items():
    ys.sort(); s = p = ys[0]
    for y in ys[1:] + [None]:
        if y is not None and y == p + 1: p = y; continue
        boxes.append((np.array([(x + .5) * CS, (s + p + 1) / 2 * CS, 0.5]), np.array([CS, (p - s + 1) * CS, 1.0])))
        if y is not None: s = p = y
print(len(inst) // 2, 'geoms ->', len(boxes), 'boxes (', len(cells), 'cells )')
with open(out, 'w') as f:
    for i, (c, d) in enumerate(boxes):
        f.write(f'      <collision name="c{i}"><pose>{c[0]:.3f} {c[1]:.3f} {c[2]:.3f} 0 0 0</pose><geometry><box><size>{max(d[0],0.02):.3f} {max(d[1],0.02):.3f} {max(d[2],0.02):.3f}</size></box></geometry></collision>\n')
