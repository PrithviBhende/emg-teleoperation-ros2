"""Camera labels are references only, never EMG model inputs."""
from collections import deque
import os
import threading
import time
import numpy as np
from .config import ROOT

FINGERS = {'thumb': (1, 2, 3, 4), 'index': (5, 6, 7, 8),
           'middle': (9, 10, 11, 12), 'ring': (13, 14, 15, 16), 'little': (17, 18, 19, 20)}


def angle(a, b, c):
    u, v = a - b, c - b
    denom = np.linalg.norm(u) * np.linalg.norm(v)
    if denom < 1e-9:
        return float('nan')
    return float(np.degrees(np.arccos(np.clip(np.dot(u, v) / denom, -1, 1))))


def classify(points, cfg):
    """Classify landmarks in image pixel coordinates; z is ignored for joint angles."""
    p = np.asarray(points)
    if p.shape != (21, 3) or not np.isfinite(p).all():
        return 'unknown', {}
    bend = {name: min(angle(p[a], p[b], p[c]), angle(p[b], p[c], p[d]))
            for name, (a, b, c, d) in FINGERS.items()}
    if not np.isfinite(list(bend.values())).all():
        return 'unknown', {}
    states = {}
    for name, value in bend.items():
        low = cfg.thumb_bent_degrees if name == 'thumb' else cfg.finger_bent_degrees
        high = cfg.thumb_straight_degrees if name == 'thumb' else cfg.finger_straight_degrees
        states[name] = 'bent' if value < low else 'straight' if value > high else 'unknown'
    scale = np.linalg.norm(p[5] - p[17])
    pinch = float(np.linalg.norm(p[4] - p[8]) / max(scale, 1e-9))
    detail = dict(angles=bend, states=states, pinch_ratio=pinch)
    if all(states[f] == 'bent' for f in ('index', 'middle', 'ring', 'little')):
        return 'fist', detail
    if pinch < cfg.pinch_ratio and all(states[f] == 'straight' for f in ('middle', 'ring', 'little')):
        return 'pinch', detail
    bent = [f for f in FINGERS if states[f] == 'bent']
    if len(bent) == 1 and all(s != 'unknown' for s in states.values()):
        return bent[0], detail
    if all(s == 'straight' for s in states.values()):
        return 'neutral', detail  # visible open hand does NOT establish physiological rest
    return 'unknown', detail


class GestureGate:
    """One event per neutral->gesture cycle. Timestamp is start of stable candidate."""
    def __init__(self, cfg):
        self.cfg = cfg
        self.candidate = None
        self.since = 0.0
        self.armed = False

    def update(self, label, stamp):
        if label != self.candidate:
            self.candidate, self.since = label, stamp
        elapsed = stamp - self.since
        if label == 'neutral' and elapsed >= self.cfg.rearm_seconds:
            self.armed = True
        if label == 'unknown':
            self.armed = False
        if self.armed and label not in ('neutral', 'unknown') and elapsed >= self.cfg.stable_seconds:
            self.armed = False
            return (label, self.since)
        return None


class Camera:
    def __init__(self, cfg):
        self.cfg = cfg
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.latest = None
        self.history = deque(maxlen=1200)
        self.error = ''
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        cap = None
        try:
            # Avoid slow MSMF hardware-transform negotiation on Windows webcams.
            # Keep the same backend/index mapping as before; respect explicit overrides.
            os.environ.setdefault('OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS', '0')
            import cv2
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            path = (ROOT / self.cfg.model_path).resolve()
            if not path.is_file():
                raise FileNotFoundError(f'Hand landmark model missing: {path}. See README.')
            options = vision.HandLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=str(path)),
                running_mode=vision.RunningMode.VIDEO, num_hands=2,
                min_hand_detection_confidence=0.6, min_tracking_confidence=0.6)
            cap = cv2.VideoCapture(self.cfg.camera_index)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            if not cap.isOpened():
                raise RuntimeError('Cannot open camera; close other apps or change camera_index.')
            previous_ms = -1
            with vision.HandLandmarker.create_from_options(options) as model:
                while not self.stop_event.is_set():
                    ok, frame = cap.read()
                    stamp = time.monotonic()  # capture arrival, NOT exposure timestamp
                    if not ok:
                        raise RuntimeError('Camera frame read failed.')
                    ms = max(previous_ms + 1, int(stamp * 1000))
                    previous_ms = ms
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    result = model.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ms)
                    label, detail = 'unknown', {}
                    if len(result.hand_landmarks) == 1:
                        h, w = frame.shape[:2]
                        image_points = [[point.x * w, point.y * h, 0.0]
                                        for point in result.hand_landmarks[0]]
                        label, detail = classify(image_points, self.cfg)
                        for point in result.hand_landmarks[0]:
                            cv2.circle(rgb, (int(point.x * w), int(point.y * h)), 3, (0, 255, 0), -1)
                    cv2.putText(rgb, f'Camera: {label}', (10, 25), cv2.FONT_HERSHEY_SIMPLEX, .65, (255, 80, 20), 2)
                    if detail:
                        states = detail['states']
                        short = ' '.join(f'{name[0].upper()}:{states[name][0].upper()}'
                                         for name in FINGERS)
                        cv2.putText(rgb, short, (10, 48), cv2.FONT_HERSHEY_SIMPLEX,
                                    .48, (255, 80, 20), 1)
                    with self.lock:
                        self.latest = (stamp, label, detail, rgb)
                        self.history.append(dict(host_time=stamp, label=label, detail=detail))
        except Exception as exc:
            self.error = str(exc)
        finally:
            if cap is not None:
                cap.release()

    def snapshot(self):
        with self.lock:
            return self.latest

    def events(self, start, end):
        with self.lock:
            return [e for e in self.history if start <= e['host_time'] <= end]

    def close(self):
        self.stop_event.set()
        self.thread.join(timeout=2)
