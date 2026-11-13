"""Immutable raw input; optional causal filters are identical in train/test."""
import numpy as np
from functools import lru_cache

TF_BANDS = ((20, 80), (80, 150), (150, 250), (250, 450))
NAMES = (['RMS', 'MAV', 'WL', 'ZC', 'SSC', 'MAX', 'MIN'] +
         [f'TF_{low}_{high}_{part}' for part in ('EARLY', 'LATE')
          for low, high in TF_BANDS])
SETS = {'A_RMS': [0], 'B_MAV': [1], 'C_WL': [2],
        'D_TD4': [1, 2, 3, 4], 'E_ALL5': [0, 1, 2, 3, 4],
        'F_MAV_MAX_MIN': [1, 5, 6], 'G_TF8': list(range(7, 15))}


def time_frequency_features(window, sample_rate):
    """Log spectral power in four bands, separately for the early/late half."""
    result = []
    for half in np.array_split(window, 2):
        half = half - half.mean()
        spectrum = np.fft.rfft(half * np.hanning(len(half)))
        power = np.abs(spectrum) ** 2 / max(1, len(half) ** 2)
        frequencies = np.fft.rfftfreq(len(half), 1 / sample_rate)
        result.extend(float(np.log1p(power[(frequencies >= low) &
                                               (frequencies < high)].sum()))
                      for low, high in TF_BANDS)
    return result


@lru_cache(maxsize=16)
def filter_design(bandpass, notch, low, high, sample_rate):
    from scipy.signal import butter, iirnotch, sosfilt_zi, tf2sos
    sections = []
    if bandpass:
        sections.append(butter(2, [low, high], btype='bandpass', fs=sample_rate, output='sos'))
    if notch:
        sections.append(tf2sos(*iirnotch(50, 30, fs=sample_rate)))
    sos = np.vstack(sections)
    return sos, sosfilt_zi(sos)


def process(raw, cfg):
    x = np.asarray(raw, dtype=float).copy()
    if not len(x):
        return x
    if cfg.digital_bandpass or cfg.notch_50hz:
        from scipy.signal import sosfilt
        sos, zi = filter_design(cfg.digital_bandpass, cfg.notch_50hz,
                                cfg.highpass_hz, cfg.lowpass_hz, cfg.sample_rate)
        x, _ = sosfilt(sos, x, zi=zi * x[0])
    return x


def features(raw, cfg):
    x = process(raw, cfg)
    n, hop = round(cfg.window_ms * cfg.sample_rate / 1000), round(cfg.hop_ms * cfg.sample_rate / 1000)
    rows, starts = [], []
    eps = cfg.crossing_threshold_counts
    for start in range(0, len(x) - n + 1, hop):
        w = x[start:start+n].copy()
        if cfg.center_features:
            w -= w.mean()
        d = np.diff(w)
        zc = np.sum((w[:-1] * w[1:] < 0) & (np.abs(d) >= eps))
        ssc = np.sum((d[:-1] * d[1:] < 0) &
                     (np.abs(d[:-1]) >= eps) & (np.abs(d[1:]) >= eps))
        rows.append([np.sqrt(np.mean(w*w)), np.mean(np.abs(w)),
                     np.abs(d).sum(), zc, ssc, w.max(), w.min()] +
                    time_frequency_features(w, cfg.sample_rate))
        starts.append(start / cfg.sample_rate)
    return np.asarray(rows, dtype=float).reshape(-1, len(NAMES)), np.asarray(starts)


def quality(rows, cfg):
    reasons = []
    if len(rows) < round(cfg.window_ms * cfg.sample_rate / 1000):
        return ['Too few samples']
    seq = rows[:, 1].astype(np.int64)
    if np.any((np.diff(seq) & 0xffffffff) != 1):
        reasons.append('Missing or duplicate sample sequence')
    if np.any(np.abs(np.diff(rows[:, 2]) - 1 / cfg.sample_rate) > 0.00015):
        reasons.append('Device timing discontinuity')
    x = rows[:, 3]
    clipped = int(np.count_nonzero((x <= 1) | (x >= 4094)))
    if clipped / len(x) > cfg.max_clipped_fraction:
        reasons.append(f'ADC clipping: {clipped}/{len(x)} samples ({clipped/len(x):.1%}) '
                       f'at the ADC limit; allowed {cfg.max_clipped_fraction:.1%}. Check A0 voltage/gain.')
    if np.ptp(x) == 0:
        reasons.append('Flat signal / disconnected or stuck ADC')
    return reasons


def blocking_quality(problems):
    """Clipping is retained as a warning; missing/timing/flat data block use."""
    return [problem for problem in problems if not problem.startswith('ADC clipping:')]
