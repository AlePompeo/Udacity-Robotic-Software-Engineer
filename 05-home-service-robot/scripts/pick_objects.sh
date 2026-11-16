#!/bin/bash
# Navigation stack plus the pick_objects node: the robot goes to the pickup zone, waits 5 seconds
# and goes to the drop-off zone
source "$(dirname "$0")/common.sh"

start_roscore
start_simulation
start_navigation
start_rviz navigation

open_terminal pick_objects "roslaunch pick_objects pick_objects.launch"
echo "pick_objects is running: watch its terminal for the messages (Ctrl+C stops everything)."
wait
