#!/usr/bin/env python3
"""
EMG Finger Controller Node for InMoov Hand Simulation
Maps 5 high-level finger activations [thumb, index, middle, ring, pinky] in range [0.0, 1.0]
to all 17 revolute joints in the InMoov hand for Gazebo ros2_control.

Joint mapping order in finger_position_controller (17 joints):
  [0..2]   Thumb:  r_thumb1_joint, r_thumb_joint, r_thumb3_joint
  [3..5]   Index:  r_index1_joint, r_index_joint, r_index3_joint
  [6..8]   Middle: r_middle1_joint, r_middle_joint, r_middle3_joint
  [9..12]  Ring:   r_ring1_joint, r_ring_joint, r_ring3_joint, r_ring4_joint
  [13..16] Pinky:  r_pinky1_joint, r_pinky_joint, r_pinky3_joint, r_pinky4_joint
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

class EMGFingerController(Node):
    def __init__(self):
        super().__init__('emg_finger_controller')

        # Publisher to ros2_control JointGroupPositionController
        self.cmd_pub = self.create_publisher(
            Float64MultiArray,
            '/finger_position_controller/commands',
            10
        )

        # Subscriber for 5-element EMG activations [thumb, index, middle, ring, pinky] in [0.0, 1.0]
        self.emg_sub = self.create_subscription(
            Float64MultiArray,
            '/emg/finger_activations',
            self.emg_callback,
            10
        )

        # Initialize to Rest (straight fingers)
        self.timer_init = self.create_timer(1.0, self.initial_rest_callback)
        self.initialized = False

        self.get_logger().info("==================================================")
        self.get_logger().info("  InMoov EMG Finger Controller Node Started")
        self.get_logger().info("  Listening to: /emg/finger_activations")
        self.get_logger().info("  Publishing to: /finger_position_controller/commands")
        self.get_logger().info("==================================================")

    def initial_rest_callback(self):
        if not self.initialized:
            self.publish_finger_angles([0.0, 0.0, 0.0, 0.0, 0.0])
            self.get_logger().info("Hand initialized to REST position (fingers straightened).")
            self.initialized = True
            self.timer_init.cancel()

    def emg_callback(self, msg: Float64MultiArray):
        if len(msg.data) < 5:
            self.get_logger().warn(f"Expected 5 finger activation values, received {len(msg.data)}")
            return
        self.publish_finger_angles(msg.data[:5])

    def publish_finger_angles(self, activations):
        """
        activations: [thumb, index, middle, ring, pinky] in range [0.0, 1.0]
        0.0 = completely extended / straight
        1.0 = fully flexed / curled
        """
        t = max(0.0, min(1.0, float(activations[0])))
        i = max(0.0, min(1.0, float(activations[1])))
        m = max(0.0, min(1.0, float(activations[2])))
        r = max(0.0, min(1.0, float(activations[3])))
        p = max(0.0, min(1.0, float(activations[4])))

        cmd = Float64MultiArray()
        cmd.data = [
            # Thumb (3 joints)
            t * 0.50,  # r_thumb1_joint
            t * 0.95,  # r_thumb_joint
            t * 0.90,  # r_thumb3_joint

            # Index (3 joints)
            i * 0.70,  # r_index1_joint
            i * 0.80,  # r_index_joint
            i * 0.80,  # r_index3_joint

            # Middle (3 joints)
            m * 0.70,  # r_middle1_joint
            m * 0.80,  # r_middle_joint
            m * 0.80,  # r_middle3_joint

            # Ring (4 joints)
            r * 0.10,  # r_ring1_joint
            r * 0.80,  # r_ring_joint
            r * 0.80,  # r_ring3_joint
            r * 0.75,  # r_ring4_joint

            # Pinky (4 joints)
            p * 0.10,  # r_pinky1_joint
            p * 0.80,  # r_pinky_joint
            p * 0.80,  # r_pinky3_joint
            p * 0.75   # r_pinky4_joint
        ]

        self.cmd_pub.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = EMGFingerController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
