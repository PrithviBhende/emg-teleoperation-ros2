from dataclasses import asdict, dataclass
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ['rest', 'thumb', 'index', 'middle', 'ring', 'little', 'pinch', 'fist']


@dataclass
class Config:
    sample_rate: int = 2000
    baud: int = 115200
    pre_seconds: float = 0.35
    post_seconds: float = 0.85
    camera_offset_seconds: float = 0.0
    stable_seconds: float = 0.15
    rearm_seconds: float = 0.5
    capture_timeout_seconds: float = 10.0
    window_ms: int = 250
    hop_ms: int = 50
    digital_bandpass: bool = False
    highpass_hz: float = 70.0
    lowpass_hz: float = 450.0
    notch_50hz: bool = False
    # Subtract each window's mean for amplitude/shape features, NOT saved ADC data.
    center_features: bool = True
    crossing_threshold_counts: float = 3.0
    max_clipped_fraction: float = 0.01
    agreement_threshold: float = 0.60
    min_train_trials_per_class: int = 6
    cv_folds: int = 3
    seed: int = 42
    camera_index: int = 0
    finger_bent_degrees: float = 145.0
    finger_straight_degrees: float = 165.0
    thumb_bent_degrees: float = 135.0
    thumb_straight_degrees: float = 155.0
    pinch_ratio: float = 0.30
    model_path: str = '../hand_landmarker.task'

    def validate(self):
        if self.sample_rate != 2000:
            raise ValueError('V1 firmware is fixed at 2000 Hz; change both ends for another rate.')
        if not 0 < self.hop_ms <= self.window_ms <= 1000:
            raise ValueError('Require 0 < hop_ms <= window_ms <= 1000.')
        if not 0 <= self.pre_seconds <= 2 or not 0.25 <= self.post_seconds <= 4:
            raise ValueError('Pre-capture: 0..2 s; post-capture: 0.25..4 s.')
        if not -0.5 <= self.camera_offset_seconds <= 0.5:
            raise ValueError('Camera offset must be between -0.5 and +0.5 s.')
        if (self.pre_seconds + self.post_seconds) * 1000 < self.window_ms:
            raise ValueError('Capture must contain at least one feature window.')
        if not 0 < self.highpass_hz < self.lowpass_hz < self.sample_rate / 2:
            raise ValueError('Require 0 < highpass < lowpass < Nyquist.')
        if not 0.5 <= self.agreement_threshold <= 1:
            raise ValueError('Agreement threshold must be 0.5..1 (not a probability).')
        if not 0 <= self.crossing_threshold_counts <= 4095:
            raise ValueError('Crossing threshold must be in ADC counts, 0..4095.')
        if not 0 <= self.max_clipped_fraction <= 1:
            raise ValueError('Clipped fraction must be 0..1.')
        if not 2 <= self.cv_folds <= self.min_train_trials_per_class:
            raise ValueError('Need at least cv_folds trials per class, and >=2 folds.')
        if not 0 < self.stable_seconds <= 1 or not 0 < self.rearm_seconds <= 3:
            raise ValueError('Invalid camera stability/rearm duration.')
        if self.capture_timeout_seconds < 3:
            raise ValueError('Capture timeout must be at least 3 seconds.')
        if not 0 < self.finger_bent_degrees < self.finger_straight_degrees < 180:
            raise ValueError('Invalid finger angle thresholds.')
        if not 0 < self.thumb_bent_degrees < self.thumb_straight_degrees < 180:
            raise ValueError('Invalid thumb angle thresholds.')
        if not 0 < self.pinch_ratio < 1:
            raise ValueError('Pinch ratio must be 0..1.')
        return self

    def processing(self):
        keys = ('sample_rate', 'window_ms', 'hop_ms', 'digital_bandpass',
                'highpass_hz', 'lowpass_hz', 'notch_50hz', 'center_features',
                'crossing_threshold_counts')
        return {k: asdict(self)[k] for k in keys}


def load_config():
    path = ROOT / 'settings.json'
    return Config(**json.loads(path.read_text())).validate() if path.exists() else Config()


def save_config(cfg):
    cfg.validate()
    (ROOT / 'settings.json').write_text(json.dumps(asdict(cfg), indent=2), encoding='utf-8')
