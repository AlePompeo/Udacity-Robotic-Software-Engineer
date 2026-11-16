"""Count the loop closures of an RTAB-Map database that disagree with the odometry.

usage: badloops.py <rtabmap.db> [<more.db> ...]
Odometry is exact in the simulation, so a loop closure whose transform differs from the odometry
relative pose by more than 0.3 m or 10 degrees is a wrong one.
"""
import sqlite3, sys, numpy as np
def T(b):
    m = np.eye(4); m[:3, :] = np.frombuffer(b, dtype=np.float32).reshape(3, 4); return m
for db in sys.argv[1:]:
    c = sqlite3.connect(db)
    pose = {i: T(b) for i, b in c.execute('select id,pose from Node') if b is not None and len(b) == 48}
    res = []
    for f, t, ty, b in c.execute('select from_id,to_id,type,transform from Link where type=1'):
        if f not in pose or t not in pose or b is None or len(b) != 48: continue
        rel = np.linalg.inv(pose[f]) @ pose[t]; d = np.linalg.inv(rel) @ T(b)
        res.append((np.linalg.norm(d[:3, 3]), abs(np.degrees(np.arctan2(d[1, 0], d[0, 0])))))
    r = np.array(res) if res else np.zeros((0, 2))
    bad = int(((r[:, 0] > 0.3) | (r[:, 1] > 10)).sum())
    print('%s: closures %d | bad (>0.3 m or >10 deg) %d | median err %.3f m' % (db, len(r), bad, np.median(r[:, 0]) if len(r) else 0))
