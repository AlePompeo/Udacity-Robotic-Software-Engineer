#!/usr/bin/env python3
"""Drives the robot along the walls so that a map can be recorded without the keyboard.

usage: explore_walls.py [seconds] [xmin xmax ymin ymax]

The box keeps the robot inside the building; in this simulation the odom frame is the world frame.
"""
import math
import sys
import time

import rospy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan

DURATION = float(sys.argv[1]) if len(sys.argv) > 1 else 600.0
XMIN, XMAX, YMIN, YMAX = [float(v) for v in sys.argv[2:6]] if len(sys.argv) > 5 else (-7.4, 7.4, -5.4, 5.4)
MAX_DIAGONAL = 10.8   # limit on |x| + |y| that follows the diagonal walls of the building
WALL_DISTANCE = 0.8   # distance kept from the wall on the right

state = {'scan': None, 'pose': None}


def on_odom(msg):
    p, q = msg.pose.pose.position, msg.pose.pose.orientation
    yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
    state['pose'] = (p.x, p.y, yaw)


def sector(scan, low_deg, high_deg):
    values = []
    for i, r in enumerate(scan.ranges):
        angle = math.degrees(scan.angle_min + i * scan.angle_increment)
        if low_deg <= angle <= high_deg and not math.isnan(r):
            values.append(min(r, scan.range_max))
    return min(values) if values else scan.range_max


def main():
    rospy.init_node('explore_walls')
    pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
    rospy.Subscriber('/scan', LaserScan, lambda m: state.__setitem__('scan', m))
    rospy.Subscriber('/odom', Odometry, on_odom)
    start = time.time()
    rate = rospy.Rate(10)
    while time.time() - start < DURATION and not rospy.is_shutdown():
        scan, pose = state['scan'], state['pose']
        if scan is None or pose is None:
            rate.sleep()
            continue
        x, y, yaw = pose
        front = sector(scan, -25, 25)
        front_right = sector(scan, -55, -25)
        right = sector(scan, -90, -60)
        cmd = Twist()
        inside = XMIN < x < XMAX and YMIN < y < YMAX and abs(x) + abs(y) < MAX_DIAGONAL
        if not inside:
            # Back to the center of the building
            error = math.atan2(-y, -x) - yaw
            error = math.atan2(math.sin(error), math.cos(error))
            if abs(error) > 0.35:
                cmd.angular.z = 0.6 if error > 0 else -0.6
            elif front > 0.6:
                cmd.linear.x = 0.25
                cmd.angular.z = 0.8 * error
            else:
                cmd.angular.z = 0.6
        elif front < 0.7 or front_right < 0.45:
            cmd.angular.z = 0.6
        elif right > 1.6 and front_right > 1.6:
            cmd.linear.x = 0.2
            cmd.angular.z = -0.4
        else:
            cmd.linear.x = 0.3
            cmd.angular.z = max(-0.5, min(0.5, -1.2 * (right - WALL_DISTANCE)))
        pub.publish(cmd)
        rate.sleep()
    pub.publish(Twist())


if __name__ == '__main__':
    main()
