# Navigation and SLAM tuning reference

Values that were used and verified in the simulations, with the reason for each. They are starting points for a robot of this size (0.5 x 0.48 m, differential drive, 2D lidar), not universal constants. The exact files are in `05-home-service-robot/catkin_ws/src/my_robot/config/` and `04-map-my-world/catkin_ws/src/my_robot/launch/`.

## move_base (Home Service Robot, final configuration)

Global planner `navfn/NavfnROS` (Dijkstra), local planner `dwa_local_planner/DWAPlannerROS`, controller frequency 10 Hz.

### Costmaps (`costmap_common_params.yaml`)

| Parameter | Value | Why |
|---|---|---|
| `footprint` | `[[-0.25,-0.24],[-0.25,0.24],[0.25,0.24],[0.25,-0.24]]` | The real robot, wheels included. A circle of 0.3 m stopped the robot in doors |
| `inflation_radius` | 0.45 | The global path keeps away from walls and door frames |
| `cost_scaling_factor` | 6.0 | Gentler cost slope than the default 10 |
| `obstacle_range` / `raytrace_range` | 2.5 / 3.0 | With 1.0 / 2.0 the robot saw door frames too late |
| observation source | `/scan`, frame `hokuyo`, marking and clearing | Laser as the only obstacle source |

Global costmap: static map, global frame `map`, update 2 Hz. Local costmap: rolling window of 10 x 10 m, resolution 0.05 m, update 5 Hz, global frame `odom`.

### DWA (`dwa_local_planner_params.yaml`)

| Parameter | Value |
|---|---|
| `max_vel_x`, `max_vel_trans` | 0.5 m/s |
| `min_vel_x` | 0.0 (`min_vel_trans` 0.05) |
| `max_vel_theta`, `min_vel_theta` | 1.2, 0.3 rad/s |
| `acc_lim_x`, `acc_lim_theta` | 1.5, 3.0 |
| `xy_goal_tolerance`, `yaw_goal_tolerance` | 0.15 m, 0.4 rad, `latch_xy_goal_tolerance: true` |
| `sim_time`, `sim_granularity` | 2.0 s, 0.05 |
| `vx_samples`, `vth_samples` | 10, 30 |
| `path_distance_bias`, `goal_distance_bias`, `occdist_scale` | 32.0, 20.0, 0.02 |
| `forward_point_distance`, `stop_time_buffer` | 0.325, 0.2 |
| `oscillation_reset_dist` | 0.05 |

Result on the same task (spawn to pickup to drop-off, about 12 m): 1.3 to 2.3 full turns on itself with DWA, against 2.8 to 7.6 with `TrajectoryPlannerROS`; crossing the building to a goal 12 m away took 15 to 30 s instead of 60 to 175 s.

## AMCL

| Parameter | Value | Note |
|---|---|---|
| `min_particles` / `max_particles` | 100 / 2000 | |
| `update_min_d` / `update_min_a` | 0.1 m / 0.1 rad | |
| `laser_model_type` | `likelihood_field` | `laser_max_beams: 60`, `laser_z_hit: 0.95`, `laser_z_rand: 0.05` |
| `odom_model_type` | `diff-corrected` | |
| `odom_alpha1..4` | 0.05 | Small noise: the simulated odometry is exact |
| `initial_pose_x/y/a` | the spawn pose | Otherwise the filter starts lost |
| frames | `odom`, `robot_footprint`, `map` | |

## gmapping

| Parameter | Value |
|---|---|
| `map_update_interval` | 1.0 s |
| `maxUrange` / `maxRange` | 8.0 / 12.0 m |
| `particles` | 30 |
| `delta` | 0.05 m |
| `linearUpdate` / `angularUpdate` / `temporalUpdate` | 0.2 m / 0.2 rad / 3.0 s |
| motion noise `srr srt str stt` | 0.01 0.02 0.01 0.02 (exact odometry) |
| `xmin ymin xmax ymax` | -12 -12 12 12 |

The map is saved with `rosrun map_server map_saver -f maps/<name>` in the frame in which it was built; if the odom frame coincides with the world frame the map coordinates are world coordinates and the zones can be read directly from the world.

## RTAB-Map (Map My World)

| Parameter | Supplied world | Custom world | Note |
|---|---|---|---|
| `Reg/Strategy` | 0 (visual) | 0 | |
| `Reg/Force3DoF` | true | true | planar robot |
| `Kp/DetectorStrategy` | 1 (SIFT) | 1 | SURF is not in conda-forge OpenCV |
| `Kp/MaxFeatures` | 1000 | 1000 | course template: 400 |
| `Vis/MinInliers` | 8 | 20 | course template: 15. Repetitive textures need a stricter value |
| `Rtabmap/LoopThr` | 0.05 | 0.11 | |
| `Rtabmap/DetectionRate` | 1 | 1 | one node per second |
| `RGBD/OptimizeMaxError` | 3.0 (default) | 1.0 optional | rejects loop closures that make the graph worse |
| `Mem/NotLinkedNodesKept` | false | false | mapping only |
| localization | `Mem/IncrementalMemory false`, `RGBD/StartAtOrigin true` | | the database is not modified |

Practice: move slowly (0.3 m/s), revisit places two or three times, copy the database before remapping, check every loop closure against the odometry, and look at the 3D cloud for streaks (wrong closures) and gaps (areas never seen).
