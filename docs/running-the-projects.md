# Try the projects on your own computer

A guided tour in the order of the course. Install ROS Noetic and Gazebo 11 first ([installation guide](installation.md)). Every project has its own README with the full details; this page tells you what to run, how long it takes and what you should see.

```bash
git clone https://github.com/AlePompeo/Udacity-Robotic-Software-Engineer.git
cd Udacity-Robotic-Software-Engineer
```

Run one simulation at a time. Close it (Ctrl+C in its terminals) before starting the next one.

| # | Project | Time | Windows you will see |
|---|---|---|---|
| 01 | Build My World | 2 min | Gazebo |
| 02 | Go Chase It | 5 min | Gazebo, RViz |
| 03 | Where Am I | 10 min | Gazebo, RViz |
| 04 | Map My World | 20 min (the mapping run is 10 to 15 min) | Gazebo, RViz |
| 05 | Home Service Robot | 5 min with the saved map | Gazebo, RViz, one terminal per node |

## 01 - Build My World

```bash
cd 01-build-my-world/project
mkdir build && cd build && cmake .. && make
export GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:$PWD
cd ../world && gazebo MyWorld.world --verbose
```

**Expect:** the octagonal building with rooms, furniture, plants and two rovers, and `Welcome to Alessio's World!` in the terminal.

## 02 - Go Chase It

```bash
cd 02-go-chase-it/catkin_ws && catkin_make && source devel/setup.bash
roslaunch my_robot world.launch            # terminal 1
roslaunch ball_chaser ball_chaser.launch   # terminal 2 (source devel/setup.bash first)
```

**Expect:** the robot turns towards the white ball in front of it and drives to it by itself. RViz shows the camera image and the laser. Terminal 2 prints `ball in the middle: drive forward`, `ball on the left: turn left`, and so on.

## 03 - Where Am I

```bash
cd 03-where-am-i/catkin_ws && catkin_make -DCATKIN_ENABLE_TESTING=0 && source devel/setup.bash
roslaunch my_robot world.launch rviz:=false             # terminal 1
roslaunch my_robot localization.launch                  # terminal 2
rosrun teleop_twist_keyboard teleop_twist_keyboard.py   # terminal 3
```

**Expect:** in RViz a green cloud of particles around the robot. Drive a few meters with the keyboard (`i` forward, `j`/`l` turn): the cloud shrinks and follows the robot. Use *2D Nav Goal* to send the robot to a point.

## 04 - Map My World

```bash
cd 04-map-my-world/catkin_ws && catkin_make && source devel/setup.bash
roslaunch my_robot world.launch      # terminal 1 (world:=custom_world.world for the building)
roslaunch my_robot mapping.launch    # terminal 2 (slam_pkg:=rtabmap_slam with rtabmap_ros 0.21 or newer)
roslaunch my_robot teleop.launch     # terminal 3
```

**Expect:** drive slowly around the room for 10 to 15 minutes, passing through the same places more than once. `/map` fills in RViz. Stop `mapping.launch` with Ctrl+C to write `~/.ros/rtabmap.db`, then `rtabmap-databaseViewer ~/.ros/rtabmap.db` to see the graph and the loop closures. The database of the project is not in the repository; the images and the report show the result of the long run.

## 05 - Home Service Robot

```bash
cd 05-home-service-robot/catkin_ws && catkin_make && source devel/setup.bash
cd ../scripts
./home_service.sh
```

**Expect:** after a minute of start-up: a blue cube at the pickup zone in RViz; the robot drives through the door to the pickup zone and the cube disappears; after 5 seconds the robot drives to the drop-off zone and the cube appears there. The terminals print `Reached the pickup zone`, `Picking up the object: waiting 5 seconds` and `Reached the drop-off zone: object delivered`.

The other scripts test one part at a time: `./test_slam.sh` (map the building), `./test_navigation.sh` (2D Nav Goal), `./pick_objects.sh`, `./add_marker.sh`. Without `xterm` the nodes run in the background and write logs to `/tmp/home_service_logs`; `HEADLESS=1 ./home_service.sh` runs without any window.

## If it does not work

- Gazebo takes a long time to open the first time (it builds a model cache): wait for it.
- `Waiting for master` or nodes that do not see each other: a leftover `roscore` or another simulation is running. Stop everything and start again.
- Gazebo crashes at start with a glibc error, or the simulation is very slow: see [troubleshooting](troubleshooting.md).
