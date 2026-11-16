cmake_minimum_required(VERSION 3.5)
project(my_robot)

find_package(catkin REQUIRED)
find_package(gazebo REQUIRED)

catkin_package()

include_directories(${catkin_INCLUDE_DIRS} ${GAZEBO_INCLUDE_DIRS})
link_directories(${GAZEBO_LIBRARY_DIRS})
list(APPEND CMAKE_CXX_FLAGS "${GAZEBO_CXX_FLAGS}")

# World plugin: prints a welcome message when the world loads
add_library(welcome_message SHARED src/welcome_message.cpp)
target_link_libraries(welcome_message ${GAZEBO_LIBRARIES})
