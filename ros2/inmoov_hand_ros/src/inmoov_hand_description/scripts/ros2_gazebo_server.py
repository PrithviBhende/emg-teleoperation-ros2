#!/usr/bin/env python3
"""
ROS 2 Gazebo Bridge Server for InMoov Hand
Listens on TCP localhost:9996 for incoming gesture commands from Windows EMG GUI.
Publishes directly to:
  - /finger_position_controller/commands (std_msgs/msg/Float64MultiArray)
  - /emg/gesture_command (std_msgs/msg/String)
"""

import os
import sys
import time
import json
import socket
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, String

HOST = '0.0.0.0'
PORT = 9996

# Joint mapping order in finger_position_controller (17 joints):
#   [0..2]   Thumb:  r_thumb1_joint, r_thumb_joint, r_thumb3_joint
#   [3..5]   Index:  r_index1_joint, r_index_joint, r_index3_joint
#   [6..8]   Middle: r_middle1_joint, r_middle_joint, r_middle3_joint
#   [9..12]  Ring:   r_ring1_joint (splay), r_ring_joint, r_ring3_joint, r_ring4_joint
#   [13..16] Pinky:  r_pinky1_joint (splay), r_pinky_joint, r_pinky3_joint, r_pinky4_joint

GESTURE_JOINTS = {
    '0': [0.0]*17,
    'rest': [0.0]*17,
    'open_palm': [0.0]*17,
    'neutral': [0.0]*17,

    # 1: Index finger curl
    '1': [0.0,0.0,0.0,  1.15,1.25,1.25,  0.0,0.0,0.0,  0.0,0.0,0.0,0.0,  0.0,0.0,0.0,0.0],
    'index': [0.0,0.0,0.0,  1.15,1.25,1.25,  0.0,0.0,0.0,  0.0,0.0,0.0,0.0,  0.0,0.0,0.0,0.0],

    # 2: Middle finger curl
    '2': [0.0,0.0,0.0,  0.0,0.0,0.0,  1.15,1.25,1.25,  0.0,0.0,0.0,0.0,  0.0,0.0,0.0,0.0],
    'middle': [0.0,0.0,0.0,  0.0,0.0,0.0,  1.15,1.25,1.25,  0.0,0.0,0.0,0.0,  0.0,0.0,0.0,0.0],

    # 3: Ring finger curl (joint 1 is splay=0.0, joints 2..4 are flexion)
    '3': [0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,1.25,1.25,1.20,  0.0,0.0,0.0,0.0],
    'ring': [0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,1.25,1.25,1.20,  0.0,0.0,0.0,0.0],

    # 4: Pinky / Little finger curl (joint 1 is splay=0.0, joints 2..4 are flexion)
    '4': [0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,0.0,0.0,0.0,  0.0,1.25,1.25,1.20],
    'pinky': [0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,0.0,0.0,0.0,  0.0,1.25,1.25,1.20],
    'little': [0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,0.0,0.0,0.0,  0.0,1.25,1.25,1.20],

    # 5: Thumb curl
    '5': [0.60,1.20,1.20,  0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,0.0,0.0,0.0,  0.0,0.0,0.0,0.0],
    'thumb': [0.60,1.20,1.20,  0.0,0.0,0.0,  0.0,0.0,0.0,  0.0,0.0,0.0,0.0,  0.0,0.0,0.0,0.0],

    # 6: Pinch (thumb & index touch, other fingers straight)
    '6': [0.60,1.10,1.00,  0.95,1.10,1.10,  0.0,0.0,0.0,  0.0,0.0,0.0,0.0,  0.0,0.0,0.0,0.0],
    'pinch': [0.60,1.10,1.00,  0.95,1.10,1.10,  0.0,0.0,0.0,  0.0,0.0,0.0,0.0,  0.0,0.0,0.0,0.0],

    # 7: Fist (all fingers fully flexed)
    '7': [0.60,1.20,1.20,  1.15,1.25,1.25,  1.15,1.25,1.25,  0.0,1.25,1.25,1.20,  0.0,1.25,1.25,1.20],
    'fist': [0.60,1.20,1.20,  1.15,1.25,1.25,  1.15,1.25,1.25,  0.0,1.25,1.25,1.20,  0.0,1.25,1.25,1.20]
}


class Ros2GazeboServer(Node):
    def __init__(self):
        super().__init__('ros2_gazebo_server')

        self.joint_pub = self.create_publisher(
            Float64MultiArray,
            '/finger_position_controller/commands',
            10
        )
        self.gesture_pub = self.create_publisher(
            String,
            '/emg/gesture_command',
            10
        )

        self.last_gesture = 'rest'
        self.running = True

        self.get_logger().info("==================================================")
        self.get_logger().info(f" InMoov ROS 2 Gazebo TCP Server starting on port {PORT}")
        self.get_logger().info(" Publishing to: /finger_position_controller/commands")
        self.get_logger().info("==================================================")

        # Start TCP server in background thread
        self.tcp_thread = threading.Thread(target=self.run_tcp_server, daemon=True)
        self.tcp_thread.start()

        # Send initial rest
        self.publish_gesture('rest')

    def publish_gesture(self, gesture_name):
        key = str(gesture_name).lower().strip()
        if key in GESTURE_JOINTS:
            angles = GESTURE_JOINTS[key]
            msg = Float64MultiArray()
            msg.data = angles
            self.joint_pub.publish(msg)

            s_msg = String()
            s_msg.data = key
            self.gesture_pub.publish(s_msg)

            self.last_gesture = key
            self.get_logger().info(f"Published gesture: '{key}' to Gazebo joints ({len(angles)} DOF)")
            return True
        else:
            self.get_logger().warn(f"Unknown gesture key: '{gesture_name}'")
            return False

    def handle_client(self, conn, addr):
        with conn:
            conn.settimeout(5.0)
            buffer = ""
            while self.running:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    buffer += data.decode('utf-8', errors='ignore')
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        if not line:
                            continue
                        
                        gesture = line
                        if line.startswith('{') and line.endswith('}'):
                            try:
                                obj = json.loads(line)
                                gesture = obj.get('gesture', obj.get('label', line))
                            except Exception:
                                pass
                        
                        success = self.publish_gesture(gesture)
                        ack = f"OK:{gesture}\n" if success else f"ERR:unknown_{gesture}\n"
                        conn.sendall(ack.encode('utf-8'))
                except socket.timeout:
                    continue
                except Exception as e:
                    self.get_logger().warn(f"TCP client error ({addr}): {e}")
                    break

    def run_tcp_server(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_sock.bind((HOST, PORT))
            server_sock.listen(5)
            server_sock.settimeout(1.0)
            self.get_logger().info(f"TCP server listening on {HOST}:{PORT}")
        except Exception as e:
            self.get_logger().error(f"Failed to bind TCP server on port {PORT}: {e}")
            return

        while self.running and rclpy.ok():
            try:
                conn, addr = server_sock.accept()
                t = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.get_logger().error(f"Socket accept error: {e}")
                break

        server_sock.close()


def main(args=None):
    rclpy.init(args=args)
    server = Ros2GazeboServer()
    try:
        rclpy.spin(server)
    except KeyboardInterrupt:
        pass
    finally:
        server.running = False
        server.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
