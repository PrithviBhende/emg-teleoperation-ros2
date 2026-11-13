import csv
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import uuid
import numpy as np
from .config import ROOT
from .signal import NAMES, features, process, blocking_quality


def identifier():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '_' + uuid.uuid4().hex[:8]


def scope(subject, placement):
    for value in (subject, placement):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}', value):
            raise ValueError('Subject/placement: 1-40 letters, digits, underscores or hyphens.')
    path = ROOT / 'data' / subject / placement
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path, obj):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, indent=2, allow_nan=False), encoding='utf-8')
    temp.replace(path)


def save_trial(folder, rows, meta, cfg):
    folder = Path(folder) / 'trials' / meta['id']
    folder.mkdir(parents=True, exist_ok=False)
    write_segment(folder, rows, meta, cfg)
    return folder


def write_segment(folder, rows, meta, cfg):
    """Replace the analysis segment; keep any longer capture_context.npz intact."""
    folder = Path(folder)
    np.savez_compressed(folder / 'raw.npz', host_time=rows[:, 0],
                        sequence=rows[:, 1].astype(np.uint32), device_time=rows[:, 2],
                        adc=rows[:, 3].astype(np.uint16))
    meta['config'] = asdict(cfg)
    meta['samples'] = len(rows)
    write_json(folder / 'trial.json', meta)
    # CSV is a convenient inspection copy, NPZ is the authoritative full-rate recording.
    np.savetxt(folder / 'raw.csv', rows, delimiter=',',
               header='host_monotonic_s,sequence,device_s,adc_counts', comments='',
               fmt=['%.9f', '%d', '%.9f', '%d'])
    f, starts = features(rows[:, 3], cfg)
    np.savetxt(folder / 'features.csv', np.column_stack((starts, f)), delimiter=',',
               header='window_start_s,' + ','.join(NAMES), comments='')


def save_capture_context(folder, rows):
    """Archive the entire reviewable training capture separately from raw.npz."""
    np.savez_compressed(Path(folder) / 'capture_context.npz', host_time=rows[:, 0],
                        sequence=rows[:, 1].astype(np.uint32), device_time=rows[:, 2],
                        adc=rows[:, 3].astype(np.uint16))


def load_trials(folder):
    records = []
    for path in sorted((Path(folder) / 'trials').glob('*/trial.json')):
        meta = json.loads(path.read_text(encoding='utf-8'))
        with np.load(path.with_name('raw.npz'), allow_pickle=False) as arrays:
            raw = arrays['adc'].copy()
        records.append((path, meta, raw))
    return records


def export_workbook(folder, cfg):
    """Summary and feature sheets, not a lossy substitute for saved raw waveforms."""
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    folder = Path(folder)
    records = load_trials(folder)
    labels = {m['label'] for _, m, _ in records if m['mode'] == 'train' and m['reviewed']
              and not blocking_quality(m['quality'])}
    export_name = f'{folder.parent.name}_{folder.name}_{len(labels)}_gestures_{identifier()}'
    out = folder / 'exports' / export_name
    out.mkdir(parents=True)
    book = Workbook()
    summary = book.active
    summary.title = 'Trials'
    summary.append(['id', 'session', 'mode', 'reference', 'reviewed', 'quality', 'samples',
                    'selected_start_from_camera_s', 'selected_end_from_camera_s',
                    'raw_path', 'full_context_path'])
    fws = book.create_sheet('Features')
    fws.append(['id', 'label', 'window_start_s'] + NAMES)
    results = book.create_sheet('Predictions')
    results.append(['trial', 'model_version', 'method', 'reference', 'reviewed',
                    'prediction', 'window_agreement_not_probability', 'accepted', 'match'])
    notes = book.create_sheet('Notes')
    notes.append(['Camera-segmented single-channel classification. No EMG-only onset claim.'])
    notes.append(['All raw samples remain in each trial/raw.npz and raw.csv.'])
    notes.append(['Export feature settings: ' + json.dumps(asdict(cfg))])
    by_label = {}
    for path, meta, raw in records:
        capture = meta.get('capture', {})
        event = capture.get('event', 0)
        context_path = path.with_name('capture_context.npz')
        summary.append([meta['id'], meta['session'], meta['mode'], meta['label'],
                        meta['reviewed'], '; '.join(meta['quality']), len(raw),
                        capture.get('start', event) - event, capture.get('end', event) - event,
                        str(path.with_name('raw.npz')),
                        str(context_path) if context_path.exists() else ''])
        fs, starts = features(raw, cfg)
        for start, row in zip(starts, fs):
            fws.append([meta['id'], meta['label'], float(start)] + row.tolist())
        for method, pred in meta.get('predictions', {}).items():
            results.append([meta['id'], meta.get('model_version', ''), method, meta['label'],
                            meta['reviewed'], pred['prediction'], pred['agreement'],
                            pred['accepted'], pred['accepted'] and pred['prediction'] == meta['label']])
        fig = Figure(figsize=(8, 3))
        FigureCanvasAgg(fig)
        ax = fig.add_subplot()
        t = np.arange(len(raw)) / cfg.sample_rate + capture.get('start', event) - event
        ax.plot(t, raw, lw=.5, label='Raw ADC')
        if cfg.digital_bandpass or cfg.notch_50hz:
            ax.plot(t, process(raw, cfg), lw=.5, label='Analysis copy')
        ax.set(xlabel='Seconds relative to capture event', ylabel='ADC counts', title=meta['id'] + ' / ' + meta['label'])
        ax.legend()
        fig.tight_layout()
        fig.savefig(out / (meta['id'] + '.png'), dpi=120)
        if meta['mode'] == 'train' and meta['reviewed'] and not blocking_quality(meta['quality']):
            by_label.setdefault(meta['label'], []).append(fs[:, 0])
    # Average RMS envelope, not raw-waveform average (which cancels stochastic EMG).
    for label, envelopes in by_label.items():
        length = min(map(len, envelopes))
        if not length:
            continue
        a = np.stack([v[:length] for v in envelopes])
        fig = Figure(figsize=(7, 3))
        FigureCanvasAgg(fig)
        ax = fig.add_subplot()
        t = np.arange(length) * cfg.hop_ms / 1000
        ax.plot(t, a.mean(axis=0))
        ax.fill_between(t, a.mean(axis=0)-a.std(axis=0), a.mean(axis=0)+a.std(axis=0), alpha=.25)
        ax.set(title=f'{label}: mean window RMS +/- SD, {len(a)} training trials', xlabel='Window start (s)', ylabel='RMS ADC counts')
        fig.tight_layout()
        fig.savefig(out / (label + '_mean_RMS.png'), dpi=120)
    for sheet in book:
        sheet.freeze_panes = 'A2'
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = min(55, max(15, max(len(str(c.value or '')) for c in col) + 2))
    book.save(out / (export_name + '_experiment.xlsx'))
    return out
