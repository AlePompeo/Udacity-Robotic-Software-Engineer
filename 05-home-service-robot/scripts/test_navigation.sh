#!/bin/bash
# Navigation test: Gazebo with the robot, map server, AMCL, move_base and RViz.
# Send goals with the "2D Nav Goal" tool of RViz.
source "$(dirname "$0")/common.sh"

start_roscore
start_simulation
start_navigation
start_rviz navigation

echo "Use '2D Nav Goal' in RViz to send the robot to two different positions (Ctrl+C stops everything)."
wait
