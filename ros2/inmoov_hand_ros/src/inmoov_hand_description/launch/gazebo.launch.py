import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_share = get_package_share_directory('inmoov_hand_description')
    gazebo_ros_share = get_package_share_directory('gazebo_ros')

    # Path to Xacro file
    xacro_file = os.path.join(pkg_share, 'urdf', 'inmoov_hand.urdf.xacro')
    
    # Process Xacro
    doc = xacro.process_file(xacro_file)
    robot_description_config = doc.toxml()

    # Robot State Publisher Node
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_config,
            'use_sim_time': True
        }]
    )

    # Gazebo Launch (Starts gzserver and gzclient)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'verbose': 'true'}.items()
    )

    # Spawn Entity Node in Gazebo
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'inmoov_hand',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.0'
        ],
        output='screen'
    )

    # Controller Spawners
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen'
    )

    finger_position_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['finger_position_controller', '--controller-manager', '/controller_manager'],
        output='screen'
    )

    # EMG Bridge Controller Node (bridges /emg/finger_activations to Gazebo)
    emg_bridge_node = Node(
        package='inmoov_hand_description',
        executable='emg_finger_controller.py',
        output='screen'
    )

    # ROS 2 Gazebo TCP Server Node (bridges Windows EMG GUI directly to Gazebo)
    tcp_server_node = Node(
        package='inmoov_hand_description',
        executable='ros2_gazebo_server.py',
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[
                    joint_state_broadcaster_spawner,
                    finger_position_controller_spawner,
                    emg_bridge_node,
                    tcp_server_node
                ]
            )
        )
    ])
