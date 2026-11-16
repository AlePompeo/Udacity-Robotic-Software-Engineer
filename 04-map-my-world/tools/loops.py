"""Plot the optimized pose graph of an RTAB-Map database: neighbor links in grey, loop closures in red.

usage: loops.py <rtabmap.db> <output.png> <title>
"""
import sqlite3, zlib, sys, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
db, out, title = sys.argv[1:4]
c = sqlite3.connect(db)
ids = np.frombuffer(zlib.decompress(c.execute('select opt_ids from Admin').fetchone()[0]), dtype=np.int32)
P = np.frombuffer(zlib.decompress(c.execute('select opt_poses from Admin').fetchone()[0]), dtype=np.float32).reshape(-1, 12)
pos = {int(i): (p[3], p[7]) for i, p in zip(ids, P)}
links = c.execute('select from_id,to_id,type from Link').fetchall()
fig, ax = plt.subplots(figsize=(7, 9))
for f, t, ty in links:
    if ty == 0 and f in pos and t in pos: ax.plot(*zip(pos[f], pos[t]), color='0.55', lw=0.8)
nl = 0
for f, t, ty in links:
    if ty == 1 and f in pos and t in pos: ax.plot(*zip(pos[f], pos[t]), color='red', lw=1.0, alpha=0.8); nl += 1
xy = np.array(list(pos.values())); ax.plot(xy[0, 0], xy[0, 1], 'go', ms=9, label='start')
ax.plot([], [], color='0.55', label='neighbor links'); ax.plot([], [], color='red', label=f'loop closures ({nl})')
ax.set_aspect('equal'); ax.legend(loc='upper right'); ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]'); ax.set_title(title)
fig.tight_layout(); fig.savefig(out, dpi=120); print(len(pos), 'nodes', nl, 'loop links')
