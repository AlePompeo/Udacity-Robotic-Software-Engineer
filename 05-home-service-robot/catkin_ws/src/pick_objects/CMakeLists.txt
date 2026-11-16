cmake_minimum_required(VERSION 3.5)
project(pick_objects)

find_package(catkin REQUIRED COMPONENTS roscpp actionlib move_base_msgs)

catkin_package()

include_directories(${catkin_INCLUDE_DIRS})

add_executable(pick_objects src/pick_objects.cpp)
target_link_libraries(pick_objects ${catkin_LIBRARIES})

install(TARGETS pick_objects RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
