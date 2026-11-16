#!/bin/bash
# Marker test.
#   ./add_marker.sh         marker only: pickup zone, hidden after 5 seconds, drop-off zone after other 5 seconds
#   ./add_marker.sh robot   the marker follows the robot (Gazebo, navigation, RViz): send the robot to the pickup
#                           zone and then to the drop-off zone with the 2D Nav Goal tool
source "$(dirname "$0")/common.sh"

start_roscore
if [ "$1" = "robot" ]; then
  start_simulation
  start_navigation
  start_rviz navigation
  open_terminal add_markers "roslaunch add_markers add_markers.launch"
  echo "The marker is at the pickup zone (1.0, -1.5). Send the robot there with 2D Nav Goal: the marker disappears."
  echo "Then send the robot to the drop-off zone (-6.0, 0.0): the marker appears there (Ctrl+C stops everything)."
else
  open_terminal markers "roslaunch add_markers marker_demo.launch"
  sleep 5
  start_rviz markers
  echo "Watch the marker in RViz (Ctrl+C stops everything)."
fi
wait
