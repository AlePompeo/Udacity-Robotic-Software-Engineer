cmake_minimum_required(VERSION 3.5)
project(ball_chaser)

add_compile_options(-std=c++17)

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  message_generation
  roscpp
  sensor_msgs
  std_msgs
)

add_service_files(
  FILES
  DriveToTarget.srv
)

generate_messages(
  DEPENDENCIES
  std_msgs
)

catkin_package()

include_directories(${catkin_INCLUDE_DIRS})

add_executable(drive_bot src/drive_bot.cpp)
target_link_libraries(drive_bot ${catkin_LIBRARIES})
add_dependencies(drive_bot ball_chaser_generate_messages_cpp)

add_executable(process_image src/process_images.cpp)
target_link_libraries(process_image ${catkin_LIBRARIES})
add_dependencies(process_image ball_chaser_generate_messages_cpp)
