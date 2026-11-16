# Lessons learned across the five projects

Each project README has its own "What I learned" section. This page collects what repeated from project to project: how the pieces of a mobile robot fit together, and the working method that made the simulations reliable.

## How the pieces fit

```
Build My World ──► Go Chase It ──► Where Am I ──► Map My World ──► Home Service Robot
 world (SDF)       robot + sensing   localization     SLAM (RTAB-Map)   SLAM + localization
                   + control         + navigation     + 2D/3D maps      + navigation + task
```

- **The world is the test bench.** A world with clear walls, corners and distinguishable features supports both mapping and localization; large empty or repetitive spaces do not. The same building is reused in four projects.
- **The robot description is shared.** One URDF/xacro (differential drive, lidar, camera) with Gazebo plugins carries through the projects. Small changes to it (camera optical frame, lidar height and field of view, RGB-D sensor) have large effects downstream.
- **Frames decide everything.** `map -> odom -> robot_footprint -> chassis -> sensors`. A wrong frame name or a camera without its optical frame silently breaks SLAM, AMCL or the costmaps. Draw the tf tree (`tf_tree.png` in `04-map-my-world`) before debugging anything else.
- **Topics, remaps and parameters are the real interface.** The same node (`amcl`, `move_base`, `rtabmap`, `slam_gmapping`) works or not depending on four things: remapped topics, frame ids, the parameter file, and the simulation clock (`use_sim_time`).

## Simulation realism (and where it lies)

- **Odometry in the simulation is exact** (the differential-drive plugin can use the pose of Gazebo). It is convenient, but it changes the meaning of SLAM: a loop closure can be checked against the odometry, and AMCL has nothing to correct in the drift. Say so in the write-up and keep the noise parameters of AMCL small.
- **Rendering and physics cost real time.** Camera resolution and rate, mesh complexity and software rendering decide the real-time factor. Lower the camera before changing the algorithm.
- **Sensors have a geometry.** The lidar saw the wheels of its own robot beyond 108 degrees; at the wrong height it missed 0.3 m high crates. Always read one scan with the robot standing still and look at the closest beams.

## Method that worked

1. **Measure before tuning.** "The robot turns on itself" became numbers: full turns of rotation, time below 0.05 m/s, path length, global plans per run. With numbers, three planner configurations could be compared objectively (`05-home-service-robot`).
2. **Change one thing, rerun the same scenario.** The scenarios were fixed (same spawn, same zones, same goals) and repeated several times: one good run proves little with a stochastic planner.
3. **Use a ground truth when the simulation gives one.** Loop closures were checked against the odometry; the localization error against the Gazebo pose; the map against the world geometry.
4. **Reprocess instead of resimulating.** An RTAB-Map database can be reprocessed offline with other parameters in about 30 s, against 10 minutes of simulation.
5. **Test the delivered scripts, not a copy of them.** The later projects (Go Chase It, Map My World, Home Service Robot) were built from the zip in a clean folder and run before delivering; the helper code used only for testing (an environment adapter, a metrics recorder) was kept out of the deliverables.
6. **Be honest in the write-up.** Generated worlds, automatic exploration instead of manual driving, exact odometry, changed parameters and what was not tested are all written down.

## Technical points worth remembering

- **SDF worlds:** models can be inline or referenced; a plugin needs `GAZEBO_PLUGIN_PATH`; a stale model in `~/.gazebo/models` can shadow the one of the project.
- **ROS services and topics:** `ball_chaser` is a client/server pair (`DriveToTarget`), the image processing runs in C++ on `sensor_msgs/Image`.
- **Localization:** AMCL with a likelihood-field laser model, a small number of particles when the odometry is good, an initial pose equal to the spawn pose.
- **Navigation:** `navfn` (Dijkstra) for the global path; for the local planner `DWAPlannerROS` was far smoother than `TrajectoryPlannerROS` in narrow doors. Footprint and inflation are not interchangeable with a radius.
- **SLAM:** gmapping is simple and clean with a 2D laser and good odometry; RTAB-Map adds appearance-based loop closure and a 3D map but needs features: slow motion, revisiting places, a textured world, and a check of the loop closures.
- **Task orchestration:** a goal node (`SimpleActionClient` of `move_base`) plus a marker node (`visualization_msgs/Marker`, latched) is a small state machine; keeping the zones in one YAML file shared by both nodes avoids inconsistencies.
- **Shell scripts as the user interface:** one script per test, readiness checks instead of fixed sleeps, a fallback when `xterm` is missing, and a cleanup trap that stops every process.
