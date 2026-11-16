# Troubleshooting

Problems met while building and testing the five projects, with the cause and the fix that was verified. Each entry says where it appeared.

## Gazebo and the simulation

### `gzserver` aborts with `Fatal glibc error: pthread_mutex_lock.c:88 ... mutex->__data.__owner == 0` (exit code 134)
*Seen in: Map My World, Home Service Robot (RoboStack environment with Python 3.11).*

`gzserver` started through `gazebo_ros` crashed in one conda environment, while it ran fine alone and in a second environment (Python 3.12). Fix: run Gazebo in the environment where it works and run the other nodes (RTAB-Map, gmapping, navigation) in the other one, with the same ROS master:

```bash
export ROS_MASTER_URI=http://localhost:11400 GAZEBO_MASTER_URI=http://localhost:11401
micromamba run -n ros_env roslaunch my_robot world.launch      # Gazebo
micromamba run -n ros_slam roslaunch my_robot mapping.launch   # everything else
```

On a standard Ubuntu 20.04 + ROS Noetic installation this problem does not exist: use one terminal environment.

### The world loads but is empty, or the robot sees nothing
*Seen in: Map My World.*

A model with the same name in `~/.gazebo/models` (downloaded earlier from the online database) shadowed the model of the package, and its version had no collision shapes, so neither the lidar nor the camera saw it. Check which copy is used with `GAZEBO_MODEL_PATH`, put the package `models` folder first, and remove stale copies from `~/.gazebo/models`.

### Heavy meshes make the simulation crawl (real-time factor 0.1)
*Seen in: Map My World.*

Gazebo with software rendering and a textured mesh slowed to a tenth of real time. Fixes that worked: lower the camera to 320 x 240 at 3 Hz and the lidar to 10 Hz (real-time factor back to about 0.9 to 1.0). For the collision geometry use simple shapes, not the visual mesh: the lidar of the kitchen world only saw the room after the collision shapes were replaced by about 1100 boxes generated from the mesh (a script is in `04-map-my-world/tools`).

### Camera sensors fail when there is no display
Gazebo camera and depth sensors need an X display even with `gui:=false`. Export `DISPLAY` (and `XAUTHORITY`) of a running session. For RViz without windows use `QT_QPA_PLATFORM=offscreen`.

### Gazebo takes a long time to be ready and scripts start nodes too early
Do not use fixed `sleep`s only. The scripts of Home Service Robot wait for `/gazebo/get_world_properties`, the `/scan` topic and `/odom` before starting the next node.

## RTAB-Map (Map My World)

### Zero loop closures
With the default parameters of the course (400 features, 15 inliers) the rendered kitchen has too few features and no loop closure was found. What worked: `Kp/MaxFeatures 1000`, `Vis/MinInliers 8`, `Rtabmap/LoopThr 0.05`. Reprocessing a database offline (`rtabmap-reprocess`) takes about 30 s and is the fast way to try parameters without repeating a 10 minute simulation.

### SURF is not available
OpenCV from conda-forge has no `nonfree` module, so `Kp/DetectorStrategy 0` (SURF) falls back to SIFT. Set `Kp/DetectorStrategy 1` explicitly.

### Wrong loop closures distort the map
Repetitive textures (bricks, wood) and a symmetrical building produced a few wrong loop closures that bent the pose graph. Compare every loop closure with the odometry (exact in the simulation) and count the ones that disagree by more than 0.3 m or 10 degrees. `RGBD/OptimizeMaxError 1.0` rejects them. Stricter `Rtabmap/LoopThr` and `Vis/MinInliers` help too.

### `rtabmap` node not found
`rtabmap_ros` 0.21 and newer moved the nodes to the `rtabmap_slam` and `rtabmap_viz` packages. The launch files of Map My World have the arguments `slam_pkg`, `viz_pkg` and `viz_type`; pass `slam_pkg:=rtabmap_slam` with new versions.

### The 3D cloud is sparse or has long streaks
`rtabmap-export` decimates the depth images by 4 by default (a 320 x 240 image becomes 80 x 60). Export with `--decimation 1 --voxel 0.02`. The built-in noise filter (`--noise_radius`) failed on one database with an empty-cloud error; filtering by point density at render time worked.

## Localization and navigation (Where Am I, Home Service Robot)

### The robot turns on itself, circles an obstacle, hesitates at doors
*Seen in: Home Service Robot.* Measured over a complete run (about 12 m, correct global path): 2.8 to 7.6 full turns on itself and 39 to 70 s below 0.05 m/s with `TrajectoryPlannerROS`. The fixes, in the order of impact:

1. Replace the local planner with `DWAPlannerROS` (1.3 to 2.3 turns, no crawling).
2. Obstacle range of the costmaps from 1.0 m to 2.5 m (raytrace 2.0 to 3.0 m): the robot saw door frames too late.
3. Use the real footprint (a rectangle, wheels included) instead of `robot_radius`: with a circle of 0.3 m the robot stopped in a 1.5 m door opening in 2 of 6 runs.
4. Small odometry noise in AMCL when the odometry is exact.

How to measure it: record `/odom` and accumulate the path length, the absolute rotation, and the time below a speed threshold (the script used for this is described in `05-home-service-robot/README.md`).

### `move_base` fails every goal after the lidar was changed to 360 degrees
A lidar with a field of view wider than about 216 degrees saw the wheels of the robot as obstacles (172 beams closer than 0.45 m at 108 to 150 degrees on each side), so the planner considered the robot in collision. Raising the lidar above the wheels solved it but then the 0.3 m high crates were invisible. Final choice: lidar at the original height with a 200 degree field of view.

### Goals inside a wall are aborted
A goal in a cell occupied or inflated in the map is aborted by `move_base`. Pick goals in free space (check the map image before choosing them).

### The robot stops in a door opening
Check three things: footprint (not a circle larger than the robot), inflation radius against the door width (the free band is the width minus twice the inscribed radius), and the planner minimum speed (`min_vel_x`). Door width 1.5 m with a robot 0.48 m wide works with inflation 0.45 m.

### AMCL starts at the wrong pose
Set `initial_pose_x`, `initial_pose_y`, `initial_pose_a` in `amcl_params.yaml` to the spawn pose of the robot. In Map My World the database must be loaded with `RGBD/StartAtOrigin true`, otherwise RTAB-Map starts at the last pose stored in the file (the error was about 10 m).

## Environment and tooling

### `xacro` or other ROS commands are not found inside a conda environment
Source the environment ROS setup first (`source $CONDA_PREFIX/setup.bash`) and add the workspace to `ROS_PACKAGE_PATH`. For catkin builds with recent CMake set `CMAKE_POLICY_VERSION_MINIMUM=3.5`.

### `xterm` is not installed
The scripts of Home Service Robot open one `xterm` per node. Without it they run the nodes in the background and write logs to `/tmp/home_service_logs`; the keyboard teleoperation then runs in the current terminal. Install it with `sudo apt install xterm` (Ubuntu) or `sudo dnf install xterm` (Fedora).

### `pkill -f pattern` kills my own shell
If the pattern appears in the command line of the shell running `pkill`, it kills that shell too. Write the first letter in brackets: `pkill -f "[g]zserver"`.

### Several simulations on one machine
Gazebo with a camera is heavy in a virtual machine with 8 GB of RAM (a load average above 10 was common). Run one simulation at a time and give each one its own `ROS_MASTER_URI` and `GAZEBO_MASTER_URI` ports so that they cannot talk to each other's master.
