#!/bin/bash
# Full home service robot: simulation, navigation, RViz, the marker node and the goal node
source "$(dirname "$0")/common.sh"

start_roscore
start_simulation
start_navigation
start_rviz navigation

open_terminal add_markers "roslaunch add_markers add_markers.launch"
sleep 3
open_terminal pick_objects "roslaunch pick_objects pick_objects.launch"

echo "Home service started: pickup, 5 second wait, drop-off (Ctrl+C stops everything)."
wait
