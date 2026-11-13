"""
Background ROS 2 Gazebo Bridge Client for EMG Application.
Sends verified gesture commands directly to the simulated InMoov hand in Gazebo.

Architecture:
  - Connects over local TCP (127.0.0.1:9996) to the InMoov ROS 2 Gazebo Server running in WSL.
  - If the server is not running, attempts to start it automatically in the background.
  - If TCP connection is unavailable, falls back to asynchronous CLI dispatch.
  - Completely non-blocking: never freezes or delays the Tkinter GUI.
"""

import os
import sys
import time
import json
import socket
import threading
import subprocess
from pathlib import Path

TCP_HOST = '127.0.0.1'
TCP_PORT = 9996

GESTURES = {'rest', 'fist', 'pinch', 'thumb', 'index', 'middle', 'ring', 'little', 'pinky', 'open_palm'}


class GazeboBridge:
    def __init__(self, log_fn=None):
        self.log_fn = log_fn or (lambda msg: None)
        self.lock = threading.Lock()
        self.connected = False
        self.sock = None
        self.running = True
        self.last_gesture = 'rest'
        self.wsl_available = self._check_wsl_available()

        # Start background manager thread
        self.worker_thread = threading.Thread(target=self._connection_manager, daemon=True)
        self.worker_thread.start()

    def _log(self, message):
        try:
            self.log_fn(f"[GazeboBridge] {message}")
        except Exception:
            pass

    def _check_wsl_available(self):
        try:
            res = subprocess.run(["wsl", "-l", "-q"], capture_output=True, text=True, timeout=2)
            return res.returncode == 0
        except Exception:
            return False

    def _try_connect_socket(self):
        try:
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((TCP_HOST, TCP_PORT))
            self.sock = s
            self.connected = True
            self._log("Connected to ROS 2 Gazebo TCP server (port 9996).")
            return True
        except Exception:
            self.connected = False
            self.sock = None
            return False

    def _ensure_wsl_server_running(self):
        if not self.wsl_available:
            return
        
        # Check if already listening on port 9996
        if self._try_connect_socket():
            return

        # Attempt to launch the ROS2 bridge server in WSL in background
        cmd = (
            "source /opt/ros/humble/setup.bash && "
            "python3 /home/psb/ros2_ws/src/inmoov_hand_description/scripts/ros2_gazebo_server.py"
        )
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.Popen(
                ["wsl", "-d", "Ubuntu-22.04", "--", "bash", "-c", cmd],
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self._log("Initiated background ROS 2 Gazebo server in WSL.")
            time.sleep(1.0)
            self._try_connect_socket()
        except Exception as e:
            self._log(f"Could not auto-start WSL ROS 2 server: {e}")

    def _connection_manager(self):
        """Continuously maintains connection to the WSL TCP bridge."""
        first = True
        while self.running:
            if not self.connected:
                if first:
                    self._ensure_wsl_server_running()
                    first = False
                else:
                    self._try_connect_socket()
            time.sleep(3.0)

    def send_gesture(self, gesture_name):
        """
        Sends a gesture command to Gazebo.
        Runs asynchronously so GUI never experiences lag.
        """
        key = str(gesture_name).lower().strip()
        if key not in GESTURES:
            self._log(f"Ignoring unrecognized gesture: '{key}'")
            return False

        self.last_gesture = key
        # Dispatch in worker thread to guarantee 0 ms delay for GUI
        t = threading.Thread(target=self._do_send, args=(key,), daemon=True)
        t.start()
        return True

    def _do_send(self, key):
        with self.lock:
            # 1. Try sending over persistent TCP socket
            if self.sock and self.connected:
                try:
                    payload = f"{key}\n".encode('utf-8')
                    self.sock.sendall(payload)
                    self.sock.settimeout(0.5)
                    ack = self.sock.recv(128).decode('utf-8', errors='ignore')
                    if ack.startswith("OK"):
                        self._log(f"Command '{key}' applied instantly in Gazebo.")
                        return True
                except Exception as e:
                    self._log(f"Socket send failed ({e}), reconnecting...")
                    self.connected = False
                    try:
                        self.sock.close()
                    except Exception:
                        pass
                    self.sock = None

            # 2. Try reconnecting socket once
            if self._try_connect_socket():
                try:
                    payload = f"{key}\n".encode('utf-8')
                    self.sock.sendall(payload)
                    self.sock.settimeout(0.5)
                    ack = self.sock.recv(128).decode('utf-8', errors='ignore')
                    if ack.startswith("OK"):
                        self._log(f"Command '{key}' applied in Gazebo via reconnected socket.")
                        return True
                except Exception:
                    pass

            # 3. Fallback: Direct WSL publish command
            self._fallback_wsl_publish(key)

    def _fallback_wsl_publish(self, key):
        if not self.wsl_available:
            self._log("WSL is not available on this machine.")
            return False

        try:
            client_path = Path(__file__).resolve().parents[2] / 'inmoov_hand_ros' / 'inmoov_emg_client.py'
            if client_path.exists():
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                subprocess.run(
                    [sys.executable, str(client_path), key],
                    creationflags=creationflags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5.0
                )
                self._log(f"Dispatched '{key}' to Gazebo via fallback client.")
                return True
        except Exception as exc:
            self._log(f"Fallback publish failed: {exc}")
            return False

    def close(self):
        self.running = False
        with self.lock:
            if self.sock and self.connected:
                try:
                    self.sock.sendall(b"rest\n")
                    time.sleep(0.05)
                except Exception:
                    pass
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            self.connected = False
