# InMoov Robotic Hand - Gazebo & ROS 2 Simulation (EMG Ready)

This package integrates the **InMoov Humanoid Robotic Hand** into **ROS 2 Humble** and **Gazebo**, designed for real-time control via electromyography (sEMG) biosignals or interactive terminal commands.

---

## Workspace Structure

- **Windows Project Directory:**  
  `C:\Users\prith\Documents\MYSPACE\PROJECTS\minors\inmoov_hand_ros\src\inmoov_hand_description`
- **WSL Path (Mounted):**  
  `/mnt/c/Users/prith/Documents/MYSPACE/PROJECTS/minors/inmoov_hand_ros/src/inmoov_hand_description`
- **ROS 2 Workspace Symlink:**  
  `/home/psb/ros2_ws/src/inmoov_hand_description`

---

## 1. How to Run the Simulation

### Terminal 1: Launch Gazebo Simulation
In your WSL Ubuntu terminal:
```bash
ros2 launch inmoov_hand_description gazebo.launch.py
```
*Gazebo Classic will open with the InMoov right hand mounted upright on a sleek desktop stand, completely visible with fingers pointing straight UP.*

---

### Terminal 2: Launch the EMG Controller Node
In a second terminal:
```bash
ros2 run inmoov_hand_description emg_finger_controller.py
```
*This node bridges 5-finger EMG activation signals `[thumb, index, middle, ring, pinky]` to all 17 phalanx joints in Gazebo.*

---

### Terminal 3: Interactive EMG Tester Script (0 to 7)
In a third terminal, run the interactive tester:
```bash
ros2 run inmoov_hand_description emg_tester.py
```

You can now type any number from **0 to 7** to trigger the hand motions:

| Key | Gesture / Motion | Description |
| :---: | :--- | :--- |
| **0** | **Rest** | All 5 fingers straighten up completely (all joints at `0.0` rad). |
| **1** | **Index** | Index finger curls inward while other fingers stay straight. |
| **2** | **Middle** | Middle finger curls inward while other fingers stay straight. |
| **3** | **Ring** | Ring finger curls inward while other fingers stay straight. |
| **4** | **Pinky** | Pinky finger curls inward while other fingers stay straight. |
| **5** | **Thumb** | Thumb curls inward toward the palm. |
| **6** | **Pinch** | Thumb and Index finger curl together to meet in a precision pinch. |
| **7** | **Fist** | All 5 fingers curl together into a power grasp closed fist. |
| **q** | **Quit** | Exit the testing script. |

---

## 2. Using with Real EMG Hardware

If your Python EMG signal processing script (e.g. classifier or proportional regressor) is running:

Have your script publish an array of 5 floats `[thumb, index, middle, ring, pinky]` in range `[0.0, 1.0]` (where 0.0 = rest/straight, 1.0 = fully flexed) to topic:

```
/emg/finger_activations  (std_msgs/msg/Float64MultiArray)
```

Example command line publish:
```bash
# Pinch gesture
ros2 topic pub --once /emg/finger_activations std_msgs/msg/Float64MultiArray "{data: [0.9, 0.9, 0.0, 0.0, 0.0]}"
```

---

## 3. Rebuilding after edits

```bash
cd ~/ros2_ws
colcon build --packages-select inmoov_hand_description --symlink-install
source install/setup.bash
```
