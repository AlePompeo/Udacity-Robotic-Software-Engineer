#!/bin/bash
# Helpers shared by the home service scripts (sourced, not run directly)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="$(cd "$SCRIPT_DIR/../catkin_ws" && pwd)"
LOG_DIR="${LOG_DIR:-/tmp/home_service_logs}"
mkdir -p "$LOG_DIR"

# HEADLESS=1 runs everything without windows (no Gazebo GUI, no RViz, no terminals); logs go to $LOG_DIR
GUI=true
RVIZ=true
if [ "$HEADLESS" = "1" ]; then GUI=false; RVIZ=false; fi

SETUP="[ -f /opt/ros/noetic/setup.bash ] && source /opt/ros/noetic/setup.bash; source $WS/devel/setup.bash"
PIDS=()

have_xterm() { [ "$HEADLESS" != "1" ] && command -v xterm >/dev/null 2>&1; }

# open_terminal <title> <command>: runs the command in its own xterm, or in the background with a log file
open_terminal() {
  local title="$1" cmd="$2"
  if have_xterm; then
    setsid xterm -T "$title" -e bash -c "$SETUP; $cmd; exec bash" &
  else
    setsid bash -c "$SETUP; $cmd" > "$LOG_DIR/$title.log" 2>&1 &
  fi
  PIDS+=($!)
}

# wait_for <description> <timeout in seconds> <command>: waits until the command succeeds
wait_for() {
  local what="$1" limit="$2" cmd="$3" t=0
  echo "Waiting for $what..."
  until bash -c "$SETUP; $cmd" >/dev/null 2>&1; do
    sleep 2
    t=$((t + 2))
    if [ "$t" -ge "$limit" ]; then echo "Timeout while waiting for $what"; return 1; fi
  done
}

start_roscore() {
  local port="${ROS_MASTER_URI##*:}"
  port="${port%/}"
  [[ "$port" =~ ^[0-9]+$ ]] || port=11311
  open_terminal roscore "roscore -p $port"
  wait_for "the ROS master" 30 "rostopic list" || exit 1
}

# Gazebo with the world and the robot
start_simulation() {
  open_terminal world "roslaunch my_robot world.launch gui:=$GUI"
  wait_for "the robot in Gazebo" 180 "rosservice list | grep -q /gazebo/get_world_properties && rostopic list | grep -q '^/scan\$' && rostopic list | grep -q '^/odom\$'" || exit 1
  sleep 5
}

# map server, AMCL and move_base
start_navigation() {
  open_terminal navigation "roslaunch my_robot navigation.launch"
  wait_for "move_base" 90 "rostopic list | grep -q '^/move_base/status\$'" || exit 1
  sleep 5
}

start_rviz() {  # start_rviz <rviz configuration name>
  if [ "$RVIZ" = true ]; then
    open_terminal rviz "rosrun rviz rviz -d \$(rospack find my_robot)/rviz/$1.rviz"
  fi
}

cleanup() {
  trap - EXIT INT TERM
  echo "Stopping all the nodes..."
  for p in "${PIDS[@]}"; do kill -INT -- "-$p" 2>/dev/null; done
  sleep 3
  for p in "${PIDS[@]}"; do kill -TERM -- "-$p" 2>/dev/null; done
}
trap cleanup EXIT INT TERM
