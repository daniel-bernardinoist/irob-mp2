"""Launch the map-aligned Gazebo simulation, Nav2, and Foxglove Bridge."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('turtlebot_datasets')
    nav2_share = get_package_share_directory('nav2_bringup')
    world_path = os.path.join(package_share, 'worlds', 'task2a_lab.sdf')
    map_path = os.path.join(package_share, 'data', 'gmapping-xy10-res002-2.yaml')
    simulation_launch = os.path.join(
        nav2_share, 'launch', 'tb3_simulation_launch.py'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'x_pose', default_value='-0.59',
            description='Gazebo spawn x in the map frame',
        ),
        DeclareLaunchArgument(
            'y_pose', default_value='3.83',
            description='Gazebo spawn y in the map frame',
        ),
        DeclareLaunchArgument(
            'yaw', default_value='0.0',
            description='Gazebo spawn yaw in radians',
        ),
        AppendEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            os.path.join(package_share, 'worlds'),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(simulation_launch),
            launch_arguments={
                'world': world_path,
                'map': map_path,
                'use_sim_time': 'True',
                'slam': 'False',
                'use_simulator': 'True',
                'use_robot_state_pub': 'True',
                'use_rviz': 'False',
                'headless': 'False',
                'x_pose': LaunchConfiguration('x_pose'),
                'y_pose': LaunchConfiguration('y_pose'),
                'yaw': LaunchConfiguration('yaw'),
            }.items(),
        ),
        TimerAction(
            period=15.0,
            actions=[
                Node(
                    package='turtlebot_datasets',
                    executable='publish_task2a_initial_pose',
                    name='task2a_initial_pose_publisher',
                    parameters=[{
                        'use_sim_time': True,
                        'x': LaunchConfiguration('x_pose'),
                        'y': LaunchConfiguration('y_pose'),
                        'yaw': LaunchConfiguration('yaw'),
                    }],
                    output='screen',
                )
            ],
        ),
        Node(
            package='foxglove_bridge',
            executable='foxglove_bridge',
            name='foxglove_bridge',
            output='screen',
        ),
    ])
