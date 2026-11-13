#!/usr/bin/env python3
"""
InMoov Hand EMG Python Client
Can be imported into any Python script (Windows or WSL) to send finger commands directly to Gazebo.

Usage:
  from inmoov_emg_client import InMoovEMGClient

  hand = InMoovEMGClient()
  hand.send_gesture('fist')    # or 'rest', 'index', 'pinch', etc.
  hand.send_code(7)            # 0 to 7
  hand.send_levels([1, 0, 0, 0, 0])  # [thumb, index, middle, ring, pinky]
"""

import subprocess
import json

# Predefined 17 joint angle targets for InMoov Hand
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

class InMoovEMGClient:
    """Publishes directly to Gazebo's /finger_position_controller/commands."""
    def __init__(self, is_wsl=None):
        if is_wsl is None:
            import os
            self.is_wsl = os.path.exists('/etc/wsl.conf') or os.path.exists('/proc/sys/fs/binfmt_misc/WSL')
        else:
            self.is_wsl = is_wsl

    def send_raw_joints(self, angles_17):
        data_str = ", ".join(f"{float(x):.3f}" for x in angles_17)
        cmd = f"source /opt/ros/humble/setup.bash && ros2 topic pub --once /finger_position_controller/commands std_msgs/msg/Float64MultiArray '{{data: [{data_str}]}}'"
        if self.is_wsl:
            subprocess.run(["bash", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["wsl", "-d", "Ubuntu-22.04", "--", "bash", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def send_gesture(self, gesture_name_or_id):
        key = str(gesture_name_or_id).lower().strip()
        if key in GESTURE_JOINTS:
            self.send_raw_joints(GESTURE_JOINTS[key])
            return True
        return False

    def send_code(self, number: int):
        return self.send_gesture(str(number))

    def send_levels(self, thumb=0.0, index=0.0, middle=0.0, ring=0.0, pinky=0.0):
        t, i, m, r, p = [max(0.0, min(1.0, float(x))) for x in [thumb, index, middle, ring, pinky]]
        joints = [
            t*0.60, t*1.20, t*1.20,
            i*1.15, i*1.25, i*1.25,
            m*1.15, m*1.25, m*1.25,
            0.0, r*1.25, r*1.25, r*1.20,
            0.0, p*1.25, p*1.25, p*1.20
        ]
        self.send_raw_joints(joints)

if __name__ == '__main__':
    import sys
    client = InMoovEMGClient()
    arg = sys.argv[1] if len(sys.argv) > 1 else 'fist'
    print(f"Sending gesture: {arg}")
    client.send_gesture(arg)
