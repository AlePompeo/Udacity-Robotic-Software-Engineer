cmake_minimum_required(VERSION 3.5)
project(my_robot)

find_package(catkin REQUIRED)

catkin_package()

install(DIRECTORY launch urdf worlds maps config rviz meshes
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
