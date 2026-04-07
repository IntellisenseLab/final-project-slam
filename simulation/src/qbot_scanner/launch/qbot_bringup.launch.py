import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_qbot_scanner = get_package_share_directory('qbot_scanner')
    world_file = os.path.join(pkg_qbot_scanner, 'worlds', 'scan_world.world')
    urdf_file = os.path.join(pkg_qbot_scanner, 'urdf', 'qbot.urdf')
    rviz_file = os.path.join(pkg_qbot_scanner, 'rviz', 'config.rviz')
    
    # Path to your new SLAM params
    slam_params_file = os.path.join(pkg_qbot_scanner, 'config', 'slam_toolbox_params.yaml')

    with open(urdf_file, 'r') as infp: robot_desc = infp.read()

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': f'-r {world_file}'}.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        output='both', parameters=[{'robot_description': robot_desc}]
    )

    bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/model/qbot/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
            '/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            '/camera/image@sensor_msgs/msg/Image[ignition.msgs.Image',
            '/camera/depth_image@sensor_msgs/msg/Image[ignition.msgs.Image',
            '/joint_states@sensor_msgs/msg/JointState[ignition.msgs.Model'
        ],
        remappings=[('/model/qbot/tf', '/tf')],
        output='screen'
    )

    # Launch SLAM Toolbox directly using your parameter file
    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py')),
        launch_arguments={'slam_params_file': slam_params_file}.items()
    )

    rviz = Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_file], output='screen')
    scan_logic = Node(package='qbot_scanner', executable='scan_logic', output='screen')

    return LaunchDescription([
        gazebo, 
        robot_state_publisher, 
        bridge, 
        slam_toolbox,   # Starts mapping immediately
        rviz, 
        scan_logic
    ])