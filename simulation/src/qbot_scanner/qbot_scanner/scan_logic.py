import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
import math
import numpy as np

class QbotOrbitNode(Node):
    def __init__(self):
        super().__init__('scan_logic')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscription = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        
        self.obj_height = 1.0  
        self.v_fov = 1.047     
        self.target_radius = self.obj_height / (2 * math.tan(self.v_fov / 2))
        
        # --- NEW: Tracking Variables for 3-Round Stop Logic ---
        self.last_time = self.get_clock().now()
        self.total_angle_turned = 0.0
        self.is_finished = False
        self.target_laps = 3
        self.target_radians = self.target_laps * 2 * math.pi
        
        self.get_logger().info(f'Calculated Target Orbit Radius: {self.target_radius:.2f}m')
        self.get_logger().info(f'Will stop after {self.target_laps} rounds ({self.target_radians:.2f} radians).')

    def scan_callback(self, msg):
        # 1. Check if we already finished 3 rounds
        if self.is_finished:
            return

        cmd = Twist()
        
        # Calculate time elapsed (dt) since last scan
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9  # Convert nanoseconds to seconds
        self.last_time = current_time

        ranges = np.array(msg.ranges)
        valid_indices = np.where(np.isfinite(ranges) & (ranges > 0.1) & (ranges < 2.0))[0]
        
        if len(valid_indices) == 0:
            self.get_logger().info('No object within 2m. Searching...')
            cmd.angular.z = 0.5
            self.publisher_.publish(cmd)
            return

        min_idx_in_valid = np.argmin(ranges[valid_indices])
        min_dist = ranges[valid_indices][min_idx_in_valid]
        original_idx = valid_indices[min_idx_in_valid]
        angle_to_obj = msg.angle_min + (original_idx * msg.angle_increment)
        dist_error = min_dist - self.target_radius

        # 2. State Machine: Seeking vs Orbiting
        if min_dist > self.target_radius + 0.15:
            self.get_logger().info(f'Seeking object. Current Dist: {min_dist:.2f}m')
            cmd.linear.x = 0.15
            angle_error = (angle_to_obj + math.pi) % (2 * math.pi) - math.pi
            cmd.angular.z = angle_error * 1.0
            
        else:
            # We are locked on and Orbiting!
            v = 0.15  
            w_orbit = v / self.target_radius
            
            side_angle_error = angle_to_obj - (math.pi / 2)
            side_angle_error = (side_angle_error + math.pi) % (2 * math.pi) - math.pi
            
            cmd.linear.x = v
            cmd.angular.z = w_orbit + (dist_error * 1.5) + (side_angle_error * 0.8)
            
            # --- NEW: Integrate the angle and check for stop condition ---
            self.total_angle_turned += abs(cmd.angular.z) * dt
            
            if self.total_angle_turned >= self.target_radians:
                self.get_logger().info('=============================================')
                self.get_logger().info('SUCCESS: 3 Rounds Completed! Stopping Robot.')
                self.get_logger().info('=============================================')
                
                cmd.linear.x = 0.0
                cmd.angular.z = 0.0
                self.publisher_.publish(cmd)
                self.is_finished = True  # Lock the state so it never moves again
                return
            else:
                laps_done = self.total_angle_turned / (2 * math.pi)
                self.get_logger().info(f'Orbiting... Laps completed: {laps_done:.2f} / {self.target_laps}')

        self.publisher_.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = QbotOrbitNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()