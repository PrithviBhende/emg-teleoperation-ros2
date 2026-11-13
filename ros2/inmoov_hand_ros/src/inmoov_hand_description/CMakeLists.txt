cmake_minimum_required(VERSION 3.8)
project(inmoov_hand_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(trajectory_msgs REQUIRED)

install(DIRECTORY
  launch
  urdf
  meshes
  config
  scripts
  worlds
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/emg_finger_controller.py
  scripts/emg_tester.py
  scripts/ros2_gazebo_server.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
