import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_share = get_package_share_directory('inmoov_hand_description')
    xacro_file = os.path.join(pkg_share, 'urdf', 'inmoov_hand.urdf.xacro')
    rviz_config_file = os.path.join(pkg_share, 'config', 'hand.rviz')

    doc = xacro.process_file(xacro_file)
    robot_description_config = doc.toxml()

    gui_arg = DeclareLaunchArgument(
        name='gui',
        default_value='true',
        description='Launch joint_state_publisher_gui if true'
    )

    jsp_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        condition=UnlessCondition(LaunchConfiguration('gui'))
    )

    jsp_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        condition=IfCondition(LaunchConfiguration('gui'))
    )

    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_config}]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen'
    )

    return LaunchDescription([
        gui_arg,
        jsp_node,
        jsp_gui_node,
        rsp_node,
        rviz_node
    ])
