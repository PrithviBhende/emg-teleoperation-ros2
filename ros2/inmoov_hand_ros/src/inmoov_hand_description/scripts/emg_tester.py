#!/usr/bin/env python3
"""
Interactive EMG Finger Testing Script for ROS 2 / Gazebo
Commands the InMoov hand in Gazebo directly via /finger_position_controller/commands
AND publishes high-level activations to /emg/finger_activations.

Options:
  0 - Rest   (All fingers straightened up)
  1 - Index  (Index finger curls)
  2 - Middle (Middle finger curls)
  3 - Ring   (Ring finger curls)
  4 - Pinky  (Pinky finger curls)
  5 - Thumb  (Thumb curls)
  6 - Pinch  (Thumb + Index pinch together)
  7 - Fist   (All 5 fingers curl into a power grasp closed fist)
"""

import sys
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

# Predefined Gestures
# 'emg': [thumb, index, middle, ring, pinky] in [0.0, 1.0]
# 'joints': 17 joint angles in radians for finger_position_controller
GESTURES = {
    '0': {
        'name': 'Rest (All Fingers Straight)',
        'emg': [0.0, 0.0, 0.0, 0.0, 0.0],
        'joints': [
            # Thumb (3)
            0.0, 0.0, 0.0,
            # Index (3)
            0.0, 0.0, 0.0,
            # Middle (3)
            0.0, 0.0, 0.0,
            # Ring (4)
            0.0, 0.0, 0.0, 0.0,
            # Pinky (4)
            0.0, 0.0, 0.0, 0.0
        ],
        'desc': 'All fingers fully extended and straight up'
    },
    '1': {
        'name': 'Index Finger Flex',
        'emg': [0.0, 1.0, 0.0, 0.0, 0.0],
        'joints': [
            0.0, 0.0, 0.0,             # Thumb
            0.70, 0.80, 0.80,          # Index flexed
            0.0, 0.0, 0.0,             # Middle
            0.0, 0.0, 0.0, 0.0,        # Ring
            0.0, 0.0, 0.0, 0.0         # Pinky
        ],
        'desc': 'Index curls inward, other fingers straight'
    },
    '2': {
        'name': 'Middle Finger Flex',
        'emg': [0.0, 0.0, 1.0, 0.0, 0.0],
        'joints': [
            0.0, 0.0, 0.0,             # Thumb
            0.0, 0.0, 0.0,             # Index
            0.70, 0.80, 0.80,          # Middle flexed
            0.0, 0.0, 0.0, 0.0,        # Ring
            0.0, 0.0, 0.0, 0.0         # Pinky
        ],
        'desc': 'Middle curls inward, other fingers straight'
    },
    '3': {
        'name': 'Ring Finger Flex',
        'emg': [0.0, 0.0, 0.0, 1.0, 0.0],
        'joints': [
            0.0, 0.0, 0.0,             # Thumb
            0.0, 0.0, 0.0,             # Index
            0.0, 0.0, 0.0,             # Middle
            0.10, 0.80, 0.80, 0.75,    # Ring flexed
            0.0, 0.0, 0.0, 0.0         # Pinky
        ],
        'desc': 'Ring curls inward, other fingers straight'
    },
    '4': {
        'name': 'Pinky Finger Flex',
        'emg': [0.0, 0.0, 0.0, 0.0, 1.0],
        'joints': [
            0.0, 0.0, 0.0,             # Thumb
            0.0, 0.0, 0.0,             # Index
            0.0, 0.0, 0.0,             # Middle
            0.0, 0.0, 0.0, 0.0,        # Ring
            0.10, 0.80, 0.80, 0.75     # Pinky flexed
        ],
        'desc': 'Pinky curls inward, other fingers straight'
    },
    '5': {
        'name': 'Thumb Flex',
        'emg': [1.0, 0.0, 0.0, 0.0, 0.0],
        'joints': [
            0.50, 0.95, 0.90,          # Thumb flexed
            0.0, 0.0, 0.0,             # Index
            0.0, 0.0, 0.0,             # Middle
            0.0, 0.0, 0.0, 0.0,        # Ring
            0.0, 0.0, 0.0, 0.0         # Pinky
        ],
        'desc': 'Thumb curls inward toward palm, other fingers straight'
    },
    '6': {
        'name': 'Pinch (Thumb + Index)',
        'emg': [0.85, 0.85, 0.0, 0.0, 0.0],
        'joints': [
            0.45, 0.85, 0.80,          # Thumb
            0.65, 0.75, 0.75,          # Index
            0.0, 0.0, 0.0,             # Middle
            0.0, 0.0, 0.0, 0.0,        # Ring
            0.0, 0.0, 0.0, 0.0         # Pinky
        ],
        'desc': 'Thumb and Index tips meet in precision pinch'
    },
    '7': {
        'name': 'Fist / Power Grasp',
        'emg': [1.0, 1.0, 1.0, 1.0, 1.0],
        'joints': [
            0.50, 1.00, 1.00,          # Thumb
            0.70, 0.80, 0.80,          # Index
            0.70, 0.80, 0.80,          # Middle
            0.10, 0.80, 0.80, 0.75,    # Ring
            0.10, 0.80, 0.80, 0.75     # Pinky
        ],
        'desc': 'All 5 fingers curl completely into a closed fist'
    }
}

class EMGTester(Node):
    def __init__(self):
        super().__init__('emg_tester')

        # Direct publisher to Gazebo ros2_control (17 joints)
        self.gazebo_cmd_pub = self.create_publisher(
            Float64MultiArray,
            '/finger_position_controller/commands',
            10
        )

        # Publisher to high-level EMG topic (5 finger channels)
        self.emg_pub = self.create_publisher(
            Float64MultiArray,
            '/emg/finger_activations',
            10
        )

    def send_gesture(self, key):
        if key not in GESTURES:
            return False

        item = GESTURES[key]

        # 1. Publish directly to Gazebo controller
        joint_msg = Float64MultiArray()
        joint_msg.data = [float(x) for x in item['joints']]
        self.gazebo_cmd_pub.publish(joint_msg)

        # 2. Publish to /emg/finger_activations
        emg_msg = Float64MultiArray()
        emg_msg.data = [float(x) for x in item['emg']]
        self.emg_pub.publish(emg_msg)

        # Pretty terminal display
        t, i, m, r, p = [int(x * 100) for x in item['emg']]
        print("\n" + "="*60)
        print(f"  >>> EXECUTED: [{key}] {item['name'].upper()}")
        print(f"  Description:  {item['desc']}")
        print(f"  EMG Levels:   Thumb:{t:>3}% | Index:{i:>3}% | Mid:{m:>3}% | Ring:{r:>3}% | Pinky:{p:>3}%")
        print("="*60)
        return True

def print_menu():
    print("\n" + "="*60)
    print("      INMOOV ROBOTIC HAND - EMG INTERACTIVE TESTER     ")
    print("="*60)
    print("  Type a number from 0 to 7 to command the hand:")
    print("    0 - Rest   (All fingers straighten up)")
    print("    1 - Index  (Index finger curls)")
    print("    2 - Middle (Middle finger curls)")
    print("    3 - Ring   (Ring finger curls)")
    print("    4 - Pinky  (Pinky finger curls)")
    print("    5 - Thumb  (Thumb curls)")
    print("    6 - Pinch  (Thumb + Index pinch together)")
    print("    7 - Fist   (All 5 fingers curl into a closed fist)")
    print("    q - Quit")
    print("-" * 60)

def main(args=None):
    rclpy.init(args=args)
    tester = EMGTester()

    # Small delay to ensure ROS 2 publishers are registered with discovery
    time.sleep(0.3)
    # Send initial Rest (straight hand)
    tester.send_gesture('0')

    print_menu()

    try:
        while rclpy.ok():
            try:
                choice = input("\nEnter choice (0-7, q to quit): ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not choice:
                continue

            if choice.lower() in ['q', 'quit', 'exit']:
                print("\nExiting EMG Tester...")
                break

            if choice in GESTURES:
                tester.send_gesture(choice)
            else:
                print(f"Invalid option '{choice}'. Please type a number from 0 to 7.")

    finally:
        tester.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
