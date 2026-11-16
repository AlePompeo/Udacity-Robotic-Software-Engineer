cmake_minimum_required(VERSION 3.5)
project(add_markers)

find_package(catkin REQUIRED COMPONENTS roscpp visualization_msgs geometry_msgs)

catkin_package()

include_directories(${catkin_INCLUDE_DIRS})

add_executable(add_markers src/add_markers.cpp)
target_link_libraries(add_markers ${catkin_LIBRARIES})

install(TARGETS add_markers RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
