#!/bin/bash
# Manual SLAM test: Gazebo with the robot, gmapping, RViz and keyboard teleoperation
# usage: ./test_slam.sh [rtabmap]     (gmapping by default, RTAB-Map with the argument)
source "$(dirname "$0")/common.sh"

MAPPING=mapping.launch
if [ "$1" = "rtabmap" ]; then
  MAPPING=mapping_rtabmap.launch
  # rtabmap_ros 0.21 and newer keep the SLAM node in the rtabmap_slam package
  bash -c "$SETUP; rospack find rtabmap_slam" >/dev/null 2>&1 && MAPPING="$MAPPING slam_pkg:=rtabmap_slam"
fi

start_roscore
start_simulation
open_terminal slam "roslaunch my_robot $MAPPING"
start_rviz mapping
sleep 5

echo "Drive the robot with the keyboard and watch the map in RViz."
echo "Save the map with:  rosrun map_server map_saver -f \$(rospack find my_robot)/maps/home_service"

if have_xterm; then
  open_terminal teleop "rosrun teleop_twist_keyboard teleop_twist_keyboard.py"
  wait
elif [ "$HEADLESS" = "1" ]; then
  wait
else
  echo "xterm not found: keyboard teleoperation runs in this terminal (Ctrl+C stops everything)"
  bash -c "$SETUP; rosrun teleop_twist_keyboard teleop_twist_keyboard.py"
fi
