# Installation guide

All five projects need **ROS 1 Noetic** and **Gazebo 11 (classic)**. Two ways to get them are described; use the first on Ubuntu 20.04 (the environment of the course), the second on any other Linux (it was tested on Fedora).

| | Option A: Ubuntu 20.04 + apt | Option B: RoboStack + micromamba |
|---|---|---|
| System | Ubuntu 20.04 | any recent Linux (tested: Fedora 44) |
| Install | `apt` | conda environments |
| Tested here | standard ROS Noetic setup, not re-run on the machine used for this repository | the environments used for all five projects |

Noetic reached end of life in May 2025. If the ROS apt repository no longer serves it for your system, use Option B.

## What every project needs

| Project | ROS packages |
|---|---|
| 01 Build My World | Gazebo 11, CMake |
| 02 Go Chase It | `gazebo_ros_pkgs`, `xacro`, `robot_state_publisher`, `joint_state_publisher`, `rviz` |
| 03 Where Am I | the above and `navigation` (`amcl`, `map_server`, `move_base`), `teleop_twist_keyboard` (a copy is in the workspace) |
| 04 Map My World | the above and `rtabmap_ros`, `teleop_twist_keyboard`, `xterm` for `teleop.launch` |
| 05 Home Service Robot | `gmapping`, `amcl`, `map_server`, `move_base`, `navfn`, `dwa_local_planner`, `teleop_twist_keyboard`, `rviz`, `xterm` (optional) |

## Option A: Ubuntu 20.04 with apt

```bash
# ROS Noetic (see http://wiki.ros.org/noetic/Installation/Ubuntu)
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
sudo apt install curl
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo apt update
sudo apt install ros-noetic-desktop-full

# Packages used by the projects
sudo apt install ros-noetic-gazebo-ros-pkgs ros-noetic-xacro ros-noetic-robot-state-publisher \
  ros-noetic-joint-state-publisher ros-noetic-rviz ros-noetic-gmapping ros-noetic-amcl \
  ros-noetic-map-server ros-noetic-move-base ros-noetic-navfn ros-noetic-dwa-local-planner \
  ros-noetic-teleop-twist-keyboard ros-noetic-rtabmap-ros xterm build-essential cmake

echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

`ros-noetic-desktop-full` already contains Gazebo 11, `rviz`, `xacro` and the state publishers; the second command makes sure that the navigation, SLAM and teleoperation packages are there.

## Option B: RoboStack with micromamba

RoboStack provides ROS Noetic as conda packages, so no system packages are changed.

```bash
# 1. micromamba (https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)
"${SHELL}" <(curl -L micro.mamba.pm/install.sh)
# open a new terminal

# 2. Environment with ROS Noetic, Gazebo 11, the navigation stack and the tools used by the projects
micromamba create -n ros_env -c conda-forge -c robostack-noetic \
  ros-noetic-desktop-full ros-noetic-navigation ros-noetic-teleop-twist-keyboard \
  ros-noetic-depthimage-to-laserscan ros-noetic-effort-controllers ros-noetic-joy \
  catkin_tools cmake compilers make ninja pkg-config rosdep "empy=3.3.4"

# 3. Environment with SLAM (RTAB-Map) and gmapping (Python 3.11)
micromamba create -n ros_slam -c conda-forge -c robostack-noetic python=3.11 \
  ros-noetic-desktop-full ros-noetic-navigation ros-noetic-gazebo-ros-pkgs ros-noetic-gazebo-ros-control \
  ros-noetic-rtabmap-ros ros-noetic-teleop-twist-keyboard ros-noetic-depthimage-to-laserscan \
  ros-noetic-effort-controllers ros-noetic-joy catkin_tools cmake compilers make ninja pkg-config \
  rosdep graphviz sqlite pip "empy=3.3.4"
```

The package lists are those of the environments used for the five projects (exported with `micromamba env export --from-history`). Versions used: Gazebo 11.15.1, `ros-noetic-desktop-full` 1.5.0, `ros-noetic-navigation` 1.17.3, `ros-noetic-rtabmap-ros` 0.21.9, `ros-noetic-gmapping` 1.4.2.

Use an environment with `micromamba activate ros_env` (or `micromamba run -n ros_env <command>`), and `source $CONDA_PREFIX/setup.bash` if ROS commands such as `xacro` are not found. For `catkin_make` with recent CMake export the policy version first:

```bash
export CMAKE_POLICY_VERSION_MINIMUM=3.5
```

### One environment or two?

Try **one** environment first (`ros_slam` has everything). On the machine used for this repository `gzserver` started through `gazebo_ros` crashed in the Python 3.11 environment (`Fatal glibc error: pthread_mutex_lock.c:88 ... mutex->__data.__owner == 0`, exit code 134) and worked in the Python 3.12 one. The workaround is to run **Gazebo in `ros_env` and everything else in `ros_slam`, with the same ROS master**:

```bash
export ROS_MASTER_URI=http://localhost:11400 GAZEBO_MASTER_URI=http://localhost:11401
# terminal 1: the world and the robot
micromamba run -n ros_env bash -c 'source $CONDA_PREFIX/setup.bash; source <workspace>/devel/setup.bash; roslaunch my_robot world.launch'
# the other terminals: the same two exports, then
micromamba run -n ros_slam bash -c 'source <workspace>/devel/setup.bash; roslaunch my_robot mapping.launch'
```

(the workspace has to be built in an environment that has the build dependencies of the packages). On Ubuntu with Option A none of this is needed.

## Check the installation

```bash
gazebo --version            # Gazebo multi-robot simulator, version 11.x
roscore &                   # starts without errors; stop it with: kill %1
rospack find gmapping       # prints a path
rospack find amcl
rospack find move_base
rospack find dwa_local_planner
rospack find rtabmap_ros    # only for the projects that use RTAB-Map
```

A quick simulation test: `gazebo` opens an empty world; `rviz` opens the visualizer.

## Build a project workspace

Each project folder with a `catkin_ws` is an independent workspace:

```bash
cd 05-home-service-robot/catkin_ws
catkin_make
source devel/setup.bash
```

Project 01 is a plain CMake project (see its README). For project 03 use `catkin_make -DCATKIN_ENABLE_TESTING=0`. Do not mix workspaces in the same terminal: source one `devel/setup.bash` at a time.

## Machines without a good GPU, virtual machines, remote sessions

- Gazebo and RViz run with software rendering: `export LIBGL_ALWAYS_SOFTWARE=1`. Expect a lower real-time factor (the worlds of this repository run at about 0.9 to 1.0 with the cameras at 3 Hz).
- Gazebo camera sensors need an X display even without a window. Export `DISPLAY` of a running session; for RViz without any window use `QT_QPA_PLATFORM=offscreen`.
- If `xterm` is missing the scripts of project 05 run the nodes in the background (`HEADLESS=1` does it on purpose) and write logs to `/tmp/home_service_logs`.
- Use a separate `ROS_MASTER_URI` and `GAZEBO_MASTER_URI` port for every simulation if you run more than one.

## When something goes wrong

See [`troubleshooting.md`](troubleshooting.md).
