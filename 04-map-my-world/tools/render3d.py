"""Render a point cloud exported with `rtabmap-export --cloud` as an oblique and a top view.

usage: render3d.py <cloud.ply> <output.png> <title>
Points below 6 cm (floor) and isolated points (fewer than 6 points in a 5 cm cell) are dropped.
"""
import sys, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
src, out, title = sys.argv[1:4]
b = open(src, 'rb').read(); h = b.index(b'end_header\n') + 11
n = int(b[:h].split(b'element vertex ')[1].split()[0])
d = np.frombuffer(b[h:h + n * 31], dtype=np.dtype([('p', '<f4', 3), ('n', '<f4', 3), ('c', 'u1', 3), ('k', '<f4')]))
p, c = d['p'], d['c'] / 255.0
k = np.floor(p / 0.05).astype(np.int64); _, inv, cnt = np.unique(k, axis=0, return_inverse=True, return_counts=True); dens = cnt[inv.ravel()]
m = (dens >= 6) & (p[:, 2] < 3.2) & (p[:, 2] > 0.06); p, c = p[m], c[m]
if len(p) > 300000: i = np.random.default_rng(0).choice(len(p), 300000, replace=False); p, c = p[i], c[i]
fig = plt.figure(figsize=(14, 7))
a = fig.add_subplot(121, projection='3d'); a.scatter(p[:, 0], p[:, 1], p[:, 2], c=c, s=1.0, linewidths=0)
a.view_init(elev=38, azim=-62); a.set_box_aspect((np.ptp(p[:, 0]), np.ptp(p[:, 1]), np.ptp(p[:, 2]) * 1.3)); a.set_title('Oblique view')
a2 = fig.add_subplot(122); order = np.argsort(p[:, 2]); a2.scatter(p[order, 0], p[order, 1], c=c[order], s=1.0, linewidths=0); a2.set_aspect('equal'); a2.set_title('Top view')
for x in (a, a2): x.set_xlabel('x [m]'); x.set_ylabel('y [m]')
fig.suptitle(title); fig.tight_layout(); fig.savefig(out, dpi=130)
