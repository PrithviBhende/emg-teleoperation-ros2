"""Optional SIMULATION-ONLY gesture topic bridge; no robot joint mapping assumed.

Run in a sourced ROS2 Python environment (not necessarily the GUI's venv):
  python ros2_bridge.py /path/to/data/P01/P1/simulation_commands.jsonl
Subscribers must map /emg/gesture_command String to their simulated hand's joints.
Old records are ignored. A 2-second watchdog emits rest. Do not use on physical actuators.
"""
import argparse
import json
from pathlib import Path
import time


def main():
    import rclpy
    from std_msgs.msg import String
    parser = argparse.ArgumentParser()
    parser.add_argument('commands', type=Path)
    args = parser.parse_args()
    rclpy.init()
    node = rclpy.create_node('emg_camera_verified_simulation_bridge')
    publisher = node.create_publisher(String, '/emg/gesture_command', 10)
    handle = None
    partial = ''
    last_sent = 'rest'
    last_event = time.monotonic()
    allowed = {'rest', 'thumb', 'index', 'middle', 'ring', 'little', 'pinch', 'fist'}

    def publish(label):
        publisher.publish(String(data=label))

    def poll():
        nonlocal handle, partial, last_sent, last_event
        if handle is None and args.commands.exists():
            handle = args.commands.open(encoding='utf-8')
            handle.seek(0, 2)  # never replay previous experiments
            publish('rest')
        if handle:
            partial += handle.read()
            while '\n' in partial:
                line, partial = partial.split('\n', 1)
                try:
                    event = json.loads(line)
                    label = event['gesture']
                    age = time.time() - event['time']
                    if event.get('simulation_only') and label in allowed and 0 <= age <= 2:
                        publish(label)
                        last_sent, last_event = label, time.monotonic()
                except (ValueError, KeyError):
                    node.get_logger().warning('Ignoring malformed command record')
        if time.monotonic()-last_event > 2 and last_sent != 'rest':
            publish('rest')
            last_sent = 'rest'

    node.create_timer(.05, poll)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        publish('rest')
        if handle: handle.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
