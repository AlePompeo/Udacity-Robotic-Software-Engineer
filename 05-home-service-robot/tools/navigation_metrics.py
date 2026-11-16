"""Measure how well the robot drives: path length, total rotation, time below 0.05 m/s, global plans.

usage: python3 navigation_metrics.py      (while the robot moves; stop it with Ctrl+C to print the result)
It listens to /odom and /move_base/NavfnROS/plan.
"""
import math, signal, sys, time
import rospy
from actionlib_msgs.msg import GoalStatusArray
from nav_msgs.msg import Odometry, Path
rospy.init_node('hsr_metrics')
d = {'t': None, 'p': None, 'yaw': None, 'len': 0.0, 'rot': 0.0, 'slow': 0.0, 'plans': 0, 'tr': []}
def on_odom(m):
    t = m.header.stamp.to_sec(); p = m.pose.pose.position; q = m.pose.pose.orientation
    yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
    if d['t'] is not None and t > d['t']:
        step = math.hypot(p.x - d['p'][0], p.y - d['p'][1]); dyaw = abs(math.atan2(math.sin(yaw - d['yaw']), math.cos(yaw - d['yaw'])))
        if step < 1.0:
            d['len'] += step; d['rot'] += dyaw
            if step / (t - d['t']) < 0.05: d['slow'] += t - d['t']
        if len(d['tr']) == 0 or t - d['tr'][-1][0] > 5: d['tr'].append((t, p.x, p.y))
    d['t'], d['p'], d['yaw'] = t, (p.x, p.y), yaw
rospy.Subscriber('/odom', Odometry, on_odom)
rospy.Subscriber('/move_base/NavfnROS/plan', Path, lambda m: d.__setitem__('plans', d['plans'] + 1))
def summary():
    print('METRICS path %.1f m | total rotation %.1f turns | time below 0.05 m/s %.0f s | global plans %d' % (d['len'], d['rot'] / (2 * math.pi), d['slow'], d['plans']), flush=True)
    print('TRACK ' + ' '.join('%.0f:(%.1f,%.1f)' % t for t in d['tr']), flush=True)
rospy.on_shutdown(summary)
rospy.spin()
