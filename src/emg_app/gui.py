from dataclasses import asdict
import json
import queue
import shutil
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
from serial.tools import list_ports
from .acquisition import Reader
from .camera import Camera, GestureGate
from .config import Config, LABELS, ROOT, load_config, save_config
from .ml import build_models, load_latest, predict_trial, test_report, manifest_path
from .gazebo_bridge import GazeboBridge
from .series import SeriesTestWindow
from .manual_test import ManualTestReview
from .signal import process, quality, blocking_quality
from .storage import (identifier, scope, save_trial, save_capture_context,
                      write_segment, write_json, export_workbook, load_trials)


class App:
    def __init__(self, root):
        self.root = root
        self.cfg = load_config()
        self.reader = self.camera = self.bundle = self.pending = None
        self.events = queue.Queue()
        self.busy = False
        self.mode = None
        self.session = identifier()
        self.gate = GestureGate(self.cfg)
        self.last_camera_time = 0
        self.last_preview_time = 0
        self.last_plot = 0
        self.last_command_time = 0
        self.last_command = 'rest'
        self.folder = None
        self.last_trial_path = None
        self.repeat_after_id = None
        self.series_window = None
        self.manual_recording_since = None
        self.gazebo_bridge = GazeboBridge(log_fn=lambda msg: self.events.put(('progress', msg)))
        self.build()
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.root.bind('<Return>', lambda _: self.start('test'))
        self.root.after(50, self.tick)

    def build(self):
        self.root.title('EMG + Camera | Single-channel experiment V1')
        self.root.geometry('1220x870')
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill='x')
        self.subject = tk.StringVar(value='P01')
        self.placement = tk.StringVar(value='P1')
        self.port = tk.StringVar()
        self.expected = tk.StringVar(value='index')
        self.repeat_train = tk.BooleanVar(value=True)
        for text, var, width in [('Subject', self.subject, 12), ('Placement', self.placement, 12)]:
            ttk.Label(top, text=text).pack(side='left', padx=3)
            ttk.Entry(top, textvariable=var, width=width).pack(side='left')
        ttk.Label(top, text='COM port').pack(side='left', padx=3)
        self.port_box = ttk.Combobox(top, textvariable=self.port, width=10)
        self.port_box.pack(side='left')
        ttk.Button(top, text='List ports', command=self.ports).pack(side='left', padx=4)
        ttk.Button(top, text='Connect Due', command=self.connect).pack(side='left', padx=4)
        ttk.Label(top, text='Camera #').pack(side='left', padx=(8, 2))
        self.camera_index = tk.StringVar(value=str(self.cfg.camera_index))
        self.camera_box = ttk.Combobox(top, textvariable=self.camera_index,
                                       values=[str(i) for i in range(6)], width=3, state='readonly')
        self.camera_box.pack(side='left')
        ttk.Button(top, text='Camera', command=self.open_camera).pack(side='left', padx=4)
        ttk.Button(top, text='Settings / timings', command=self.settings).pack(side='left', padx=4)
        ttk.Button(top, text='New session', command=self.new_session).pack(side='left', padx=4)
        controls = ttk.Frame(self.root, padding=8)
        controls.pack(fill='x')
        ttk.Label(controls, text='Training block / Verify reference:').pack(side='left')
        self.expected_box = ttk.Combobox(controls, values=LABELS, textvariable=self.expected, state='readonly', width=10)
        self.expected_box.pack(side='left', padx=4)
        ttk.Checkbutton(controls, text='Repeat Train', variable=self.repeat_train).pack(side='left')
        for label, fn in [('Start Train', lambda: self.start('train')),
                          ('Verify', lambda: self.start('verify')),
                          ('Test (Enter)', lambda: self.start('test')),
                          ('Series Test', self.open_series),
                          ('Capture relaxed rest', self.rest), ('Stop', self.stop)]:
            ttk.Button(controls, text=label, command=fn).pack(side='left', padx=3)
        modelbar = ttk.Frame(self.root, padding=8)
        modelbar.pack(fill='x')
        for label, fn in [('Train / compare models', self.fit), ('Load latest models', self.load),
                          ('Export Excel + plots', self.export), ('Show results', self.results)]:
            ttk.Button(modelbar, text=label, command=fn).pack(side='left', padx=3)
        self.manual_test_button = ttk.Button(modelbar, text='Manual Test: Start', command=self.manual_test_toggle)
        self.manual_test_button.pack(side='left', padx=5)
        ttk.Button(modelbar, text='Delete last recording', command=self.delete_last).pack(side='left', padx=5)
        self.filter_var = tk.BooleanVar(value=self.cfg.digital_bandpass)
        self.notch_var = tk.BooleanVar(value=self.cfg.notch_50hz)
        ttk.Checkbutton(modelbar, text='Analysis band-pass', variable=self.filter_var, command=self.filter_changed).pack(side='left')
        ttk.Checkbutton(modelbar, text='50 Hz notch', variable=self.notch_var, command=self.filter_changed).pack(side='left')
        self.status = tk.StringVar(value='No devices connected. Raw acquisition; filters OFF by default. Review README before wiring.')
        ttk.Label(self.root, textvariable=self.status, wraplength=1180).pack(fill='x', padx=12, pady=4)
        self.telemetry = tk.StringVar(value='Session: ' + self.session)
        ttk.Label(self.root, textvariable=self.telemetry).pack(fill='x', padx=12)
        body = ttk.Frame(self.root)
        body.pack(fill='both', expand=True, padx=8)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky='nsew')
        right = ttk.Frame(body, width=410)
        right.grid(row=0, column=1, sticky='ns')
        right.pack_propagate(False)
        fig = Figure(figsize=(7, 3.3), dpi=100)
        self.ax = fig.add_subplot()
        self.raw_line, = self.ax.plot([], [], lw=.8, label='Raw ADC, unchanged')
        self.filtered_line, = self.ax.plot([], [], lw=.8, label='Optional analysis copy')
        self.ax.set(xlabel='Recent time (s)', ylabel='ADC counts', ylim=(0, 4095), xlim=(-3, 0))
        self.ax.legend(loc='upper left')
        fig.tight_layout()
        self.plot = FigureCanvasTkAgg(fig, master=left)
        self.plot.get_tk_widget().pack(fill='both', expand=True)
        self.logbox = tk.Text(left, height=11, wrap='word', state='disabled')
        self.logbox.pack(fill='x')
        self.camera_label = ttk.Label(right, text='Camera preview appears here', wraplength=400)
        self.camera_label.pack(padx=5, pady=5)
        ttk.Label(right, text='Simulation: gesture commands, not measured joint angles', wraplength=400).pack()
        self.hand = tk.Canvas(right, width=400, height=230, bg='#eaf0f7')
        self.hand.pack()
        self.draw_hand('rest')
        ttk.Label(self.root, text='DUE A0: 0–3.3 V ONLY. No automatic 5 V conversion. Camera labels never select an EMG model/table.',
                  foreground='#a02020', wraplength=1180).pack(side='bottom', pady=6, before=body)

    def log(self, message):
        self.status.set(message)
        self.logbox.configure(state='normal')
        self.logbox.insert('end', time.strftime('%H:%M:%S ') + message + '\n')
        self.logbox.see('end')
        self.logbox.configure(state='disabled')

    def idle(self):
        if self.busy or self.mode or self.pending or self.series_window is not None or self.manual_recording_since is not None:
            self.log('Stop acquisition / wait for the current operation first.')
            return False
        return True

    def ports(self):
        ports = list(list_ports.comports())
        self.port_box['values'] = [p.device for p in ports]
        self.log('; '.join(f'{p.device}: {p.description}' for p in ports) or 'No serial ports found.')
        if ports and not self.port.get():
            self.port.set(ports[0].device)

    def connect(self):
        if not self.idle(): return
        if self.reader:
            self.reader.close()
            self.reader = None
            self.log('Serial disconnected.')
            return
        port = self.port.get().strip().upper()
        if port.isdecimal():
            port = 'COM' + port
        self.port.set(port)
        if not port:
            self.ports()
            return
        matches = [p for p in list_ports.comports() if p.device.upper() == port]
        if not matches:
            self.log(f'{port} is not available. Click List ports and choose a listed COM port.')
            return
        if 'Programming Port' in matches[0].description:
            if not messagebox.askyesno('Programming Port selected',
                    f'{port} is the Due Programming Port. The supplied sketch defaults to Native USB.\n\n'
                    'To use this port, change USE_NATIVE_USB to 0 in the sketch and re-upload it.\n\n'
                    'Have you already made that change and uploaded the sketch?'):
                self.log('Connect the Native USB port, or set USE_NATIVE_USB to 0 and re-upload for this port.')
                return
        if not messagebox.askyesno('Electrical interface must be reviewed',
                'The previous direct shield-output → A0 wire is NOT approved.\n\n'
                'Continue only if A0 is protected/scaled to 0–3.3 V and either:\n'
                '• this is a bench test with NO person connected, or\n'
                '• the complete human-connected power/data safety arrangement was reviewed.\n\n'
                'Have these conditions been met? This software cannot verify them.'):
            return
        self.reader = Reader(port, self.cfg.baud)
        self.log('Connecting. Firmware: due_raw_emg, native USB by default. Waiting for EMG1 packets.')

    def open_camera(self):
        if not self.idle(): return
        if self.camera:
            self.camera.close()
            self.camera = None
            self.log('Camera stopped.')
        else:
            self.cfg.camera_index = int(self.camera_index.get())
            save_config(self.cfg)
            self.camera = Camera(self.cfg)
            self.log(f'Starting camera #{self.cfg.camera_index}. Keep only one hand in view.')

    def resolve_folder(self):
        return scope(self.subject.get().strip(), self.placement.get().strip())

    def new_session(self):
        if not self.idle(): return
        self.session = identifier()
        self.log('New session ' + self.session + '. Keep placement IDs distinct if electrodes move.')

    def filter_changed(self):
        if not self.idle():
            self.filter_var.set(self.cfg.digital_bandpass)
            self.notch_var.set(self.cfg.notch_50hz)
            return
        self.cfg.digital_bandpass = self.filter_var.get()
        self.cfg.notch_50hz = self.notch_var.get()
        save_config(self.cfg)
        self.bundle = None
        self.log('Analysis settings changed; raw recordings unchanged. Rebuild models before testing.')

    def settings(self):
        if not self.idle(): return
        dialog = tk.Toplevel(self.root)
        dialog.title('Settings — stop camera before changing camera thresholds')
        text = tk.Text(dialog, width=72, height=32)
        text.pack()
        text.insert('1.0', json.dumps(asdict(self.cfg), indent=2))
        def apply():
            try:
                cfg = Config(**json.loads(text.get('1.0', 'end'))).validate()
                if self.camera:
                    self.camera.close()
                    self.camera = None
                self.cfg = cfg
                save_config(cfg)
                self.camera_index.set(str(cfg.camera_index))
                self.gate = GestureGate(cfg)
                self.bundle = None
                self.filter_var.set(cfg.digital_bandpass)
                self.notch_var.set(cfg.notch_50hz)
                dialog.destroy()
                self.log('Settings saved. Reopen camera; rebuild models if processing/timing changed.')
            except Exception as exc:
                messagebox.showerror('Settings', str(exc), parent=dialog)
        ttk.Button(dialog, text='Validate and save', command=apply).pack()

    def ready(self):
        if not self.reader or self.reader.error or time.monotonic() - self.reader.last_rx > .5:
            raise ValueError('No fresh EMG data. Check serial port, firmware and diagnostics.')
        if not self.camera or self.camera.error:
            raise ValueError('Open a working camera first.')
        current = self.camera.snapshot()
        if current is None or time.monotonic() - current[0] > .5:
            raise ValueError('No fresh camera frames.')

    def start(self, mode):
        if not self.idle(): return
        try:
            self.ready()
            self.folder = self.resolve_folder()
            if mode != 'train':
                if not self.bundle:
                    self.bundle = load_latest(self.folder)
                manifest = self.bundle['manifest']
                if manifest['scope'] != str(self.folder.resolve()):
                    raise ValueError('Loaded model belongs to another subject/placement. Load the correct model.')
                if manifest['source'] != 'hardware':
                    raise ValueError('Synthetic test model cannot control hardware experiments.')
                keys = list(self.cfg.processing()) + ['pre_seconds', 'post_seconds', 'camera_offset_seconds', 'agreement_threshold']
                if any(manifest['config'][k] != asdict(self.cfg)[k] for k in keys):
                    raise ValueError('Current analysis/capture settings differ from frozen model. Restore settings or rebuild.')
            self.mode = mode
            self.block_label = self.expected.get() if mode != 'test' else None
            self.expected_box.configure(state='disabled')
            self.gate = GestureGate(self.cfg)
            # Repeated training waits for the next neutral -> gesture cycle until Stop.
            self.deadline = (float('inf') if mode == 'train' and self.repeat_train.get()
                             else time.monotonic() + self.cfg.capture_timeout_seconds)
            self.last_camera_time = 0
            self.start_diagnostics = self.reader.diagnostics()
            if self.last_command != 'rest':
                self.draw_hand('rest')
                self.last_command = 'rest'
                if self.gazebo_bridge:
                    self.gazebo_bridge.send_gesture('rest')
            self.log(f'{mode.upper()}: show a neutral/open hand to arm, then bend and briefly hold. Rest uses its separate button.')
        except Exception as exc:
            self.log(str(exc))

    def open_series(self):
        if not self.idle():
            return
        try:
            if not self.reader or self.reader.error or time.monotonic() - self.reader.last_rx > .5:
                raise ValueError('Connect the Due and wait for fresh EMG samples first.')
            self.folder = self.resolve_folder()
            if not self.bundle:
                self.bundle = load_latest(self.folder)
            manifest = self.bundle['manifest']
            if manifest['scope'] != str(self.folder.resolve()) or manifest['source'] != 'hardware':
                raise ValueError('The loaded model does not belong to this hardware subject/placement.')
            keys = list(self.cfg.processing()) + ['pre_seconds', 'post_seconds',
                                                  'camera_offset_seconds', 'agreement_threshold']
            if any(manifest['config'][k] != asdict(self.cfg)[k] for k in keys):
                raise ValueError('Current settings differ from the frozen model. Restore settings or rebuild.')
            self.series_window = SeriesTestWindow(self)
            self.log('Series Test opened. Record each repetition with Start/Stop, then press Final Test.')
        except Exception as exc:
            self.log(str(exc))

    def manual_test_toggle(self):
        """Start/stop an EMG-only capture; prediction never receives a camera label."""
        if self.manual_recording_since is not None:
            self.finish_manual_test()
            return
        if not self.idle():
            return
        try:
            if not self.reader or self.reader.error or time.monotonic() - self.reader.last_rx > .5:
                raise ValueError('Connect the Due and wait for fresh EMG samples first.')
            self.folder = self.resolve_folder()
            if not self.bundle:
                self.bundle = load_latest(self.folder)
            manifest = self.bundle['manifest']
            if manifest['scope'] != str(self.folder.resolve()) or manifest['source'] != 'hardware':
                raise ValueError('The loaded model does not belong to this hardware subject/placement.')
            keys = list(self.cfg.processing()) + ['pre_seconds', 'post_seconds',
                                                  'camera_offset_seconds', 'agreement_threshold']
            if any(manifest['config'][k] != asdict(self.cfg)[k] for k in keys):
                raise ValueError('Current settings differ from the frozen model. Restore settings or rebuild.')
            self.manual_recording_since = time.monotonic()
            self.manual_diagnostics = self.reader.diagnostics()
            self.manual_test_button.configure(text='Manual Test: Stop')
            self.log('Manual Test recording. Move once, then press Manual Test: Stop. Camera is not used.')
        except Exception as exc:
            self.log(str(exc))

    def finish_manual_test(self):
        start, end = self.manual_recording_since, time.monotonic()
        self.manual_recording_since = None
        self.manual_test_button.configure(text='Manual Test: Start')
        if not self.reader or self.reader.error or end - self.reader.last_rx > .5:
            self.log('Manual Test cancelled: Due samples are not fresh.')
            return
        if end - start > 18:
            self.log('Manual Test exceeded 18 seconds; the reader may have lost its beginning. Retry.')
            return
        rows = self.reader.snapshot(start, end)
        duration = self.cfg.pre_seconds + self.cfg.post_seconds
        if len(rows) < duration * self.cfg.sample_rate * .97:
            self.log(f'Record at least {duration:.2f} seconds before stopping. Captured {len(rows)} samples.')
            return
        diag = self.reader.diagnostics()
        problems = ['Acquisition diagnostic increased: ' + key
                    for key in ('missing', 'corrupt', 'overruns', 'late')
                    if diag[key] > self.manual_diagnostics[key]]
        self.busy = True
        try:
            ManualTestReview(self, rows, problems)
        except Exception as exc:
            self.busy = False
            self.log('Could not review Manual Test: ' + str(exc))

    def rest(self):
        if not self.mode or self.pending or self.busy:
            self.log('Start Train, Verify or Test first, then relax and press Capture relaxed rest.')
            return
        snap = self.camera.snapshot()
        if snap is None or snap[1] != 'neutral' or time.monotonic()-snap[0] > .5:
            self.log('Rest requires a visible neutral/open hand; consciously relax, do not actively spread.')
            return
        self.begin_capture('rest', time.monotonic())

    def begin_capture(self, label, stamp):
        event = stamp + self.cfg.camera_offset_seconds
        self.pending = dict(label=label, event=event, start=event-self.cfg.pre_seconds,
                            end=event+self.cfg.post_seconds, detected_at=time.monotonic())
        if self.mode in ('train', 'test'):
            self.pending['context_start'] = event - max(1.0, self.cfg.pre_seconds)
            self.pending['context_end'] = event + max(1.5, self.cfg.post_seconds)
        self.log(f'Capturing {label}; preserve posture until the capture finishes.')

    def stop(self):
        if self.manual_recording_since is not None:
            self.manual_recording_since = None
            self.manual_test_button.configure(text='Manual Test: Start')
            self.log('Manual Test recording cancelled.')
            return
        if self.repeat_after_id is not None:
            self.root.after_cancel(self.repeat_after_id)
            self.repeat_after_id = None
        if self.mode and self.folder:
            with (self.folder / 'attempt_events.jsonl').open('a', encoding='utf-8') as f:
                f.write(json.dumps(dict(time=time.time(), session=self.session, mode=self.mode, event='stopped_or_timeout'))+'\n')
        self.mode = None
        self.pending = None
        self.expected_box.configure(state='readonly')
        self.draw_hand('rest')
        if self.gazebo_bridge:
            self.gazebo_bridge.send_gesture('rest')
        self.log('Stopped. Existing recordings retained.')

    def worker(self, fn, kind):
        self.busy = True
        def run():
            try:
                self.events.put((kind, fn()))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        threading.Thread(target=run, daemon=True).start()

    def finish_capture(self):
        pending, mode, folder = self.pending, self.mode, self.folder
        self.pending = None
        self.mode = None
        context_rows = (self.reader.snapshot(pending['context_start'], pending['context_end'])
                        if mode in ('train', 'test') else None)
        rows = (context_rows[(context_rows[:, 0] >= pending['start']) &
                             (context_rows[:, 0] <= pending['end'])]
                if context_rows is not None else self.reader.snapshot(pending['start'], pending['end']))
        problems = quality(rows, self.cfg)
        target = (pending['end'] - pending['start']) * self.cfg.sample_rate
        if len(rows) < target * .97 or len(rows) > target * 1.03:
            problems.append('Incomplete capture duration / host alignment error')
        diag = self.reader.diagnostics()
        for key in ('missing', 'corrupt', 'overruns', 'late'):
            if diag[key] > self.start_diagnostics[key]:
                problems.append('Acquisition diagnostic increased: ' + key)
        camera_events = self.camera.events(pending.get('context_start', pending['start']),
                                           pending.get('context_end', pending['end']))
        snap = self.camera.snapshot()
        if snap is None or time.monotonic() - snap[0] > .5:
            problems.append('Camera frames stale at capture end')
        meta = dict(id=identifier(), session=self.session, mode=mode, label=pending['label'],
                    camera_label=pending['label'], block_label=self.block_label, reviewed=False,
                    quality=problems, source='hardware', capture=pending, diagnostics=diag,
                    camera_events=camera_events, wall_time=time.time(), predictions={})
        bundle, cfg = self.bundle, self.cfg
        def save():
            # Critical ordering: EMG prediction has no access to meta/camera label.
            if mode == 'verify' and not blocking_quality(problems):
                meta['predictions'] = predict_trial(bundle, rows[:, 3])
                meta['model_version'] = bundle['manifest']['version']
                meta['selected_method'] = bundle['manifest']['selected']
            path = save_trial(folder, rows, meta, cfg)
            if context_rows is not None:
                save_capture_context(path, context_rows)
            if snap is not None:
                Image.fromarray(snap[3]).save(path / 'camera_at_capture_end.png')
            return path, meta
        self.worker(save, 'captured')

    def review(self, path, meta):
        self.last_trial_path = path
        dialog = tk.Toplevel(self.root)
        dialog.title('Review captured signal window' if meta['mode'] in ('train', 'test')
                     else 'Review the observed movement — predictions already saved')
        dialog.transient(self.root)
        dialog.grab_set()
        quality_name = 'Initial selection quality' if meta['mode'] in ('train', 'test') else 'Quality'
        text = (f"Saved {meta['id']}\nCamera: {meta['camera_label']} | Block: {meta['block_label']}\n"
                f"{quality_name}: {meta['quality'] or 'No automatic flags'}")
        ttk.Label(dialog, text=text, wraplength=650).pack(padx=15, pady=12)
        if meta['mode'] != 'train':
            ttk.Label(dialog, text='Confirm the camera label BEFORE viewing the EMG prediction. Wrong test labels are excluded, not corrected to match.').pack(padx=10)
        label = tk.StringVar(value=meta['camera_label'])
        if meta['mode'] == 'test':
            ttk.Label(dialog, text='Observed by camera: ' + meta['camera_label']).pack(pady=8)
        else:
            ttk.Combobox(dialog, values=LABELS, textvariable=label, state='readonly').pack(pady=8)
        selected_capture_rows = None
        if meta['mode'] in ('train', 'test'):
            try:
                selected_capture_rows = self.training_window_review(dialog, path, meta)
            except Exception as exc:
                meta['quality'].append('Window review unavailable: ' + str(exc))
                ttk.Label(dialog, text='The waveform could not be shown. Exclude this trial and try again.',
                          foreground='#a02020').pack(pady=8)
        def done(reviewed):
            meta['reviewed'] = reviewed
            if reviewed:
                meta['label'] = label.get()
            try:
                if reviewed and selected_capture_rows is not None:
                    selected = selected_capture_rows()
                    if meta['mode'] == 'test' and not blocking_quality(meta['quality']):
                        # Prediction takes only the chosen EMG segment, never the camera label.
                        meta['predictions'] = predict_trial(self.bundle, selected[:, 3])
                        meta['model_version'] = self.bundle['manifest']['version']
                        meta['selected_method'] = self.bundle['manifest']['selected']
                        write_json(path / 'trial.json', meta)
                else:
                    write_json(path / 'trial.json', meta)
            except Exception as exc:
                messagebox.showerror('Could not save selection', str(exc), parent=dialog)
                return
            dialog.destroy()
            self.expected_box.configure(state='readonly')
            if meta['predictions']:
                selected = meta['selected_method']
                result = meta['predictions'][selected]
                feature_set = selected.split('__', 1)[0]
                ref_label = meta['label']

                # Multi-model verification:
                # If any of the 3 models (LDA, SVM, KNN), 2/3, or all 3 correctly predict
                # the camera ground-truth reference, trigger the gesture in Gazebo.
                matching_models = []
                for classifier in ('LDA', 'SVM', 'KNN'):
                    candidate_name = feature_set + '__' + classifier
                    cand_pred = meta['predictions'].get(candidate_name)
                    if cand_pred and cand_pred.get('prediction') == ref_label:
                        matching_models.append(classifier)

                multi_model_match = reviewed and (len(matching_models) >= 1)
                selected_match = reviewed and result.get('accepted') and (result.get('prediction') == ref_label)

                if multi_model_match:
                    status = f"MULTI-MODEL MATCH ({len(matching_models)}/3: {', '.join(matching_models)})"
                elif not result.get('accepted'):
                    status = 'UNCERTAIN'
                else:
                    status = 'NOT MATCH / UNREVIEWED'

                self.log(f"{selected}: EMG={result['prediction']}; reference={ref_label}; {status}; "
                         f"window agreement={result['agreement']:.0%}")

                if (multi_model_match or selected_match) and meta['mode'] in ('test', 'verify'):
                    self.log(f"-> Multi-model verification PASSED ({len(matching_models)}/3 models match). "
                             f"Sending gesture '{ref_label}' to Gazebo InMoov hand!")
                    self.command(ref_label, meta)
                elif meta['mode'] in ('test', 'verify'):
                    self.log(f"-> Verification FAILED: 0/3 models matched camera reference '{ref_label}'. Hand kept at rest.")

                if meta['mode'] == 'test':
                    self.show_test_comparison(meta)
            else:
                self.log('Trial saved without a prediction; check its quality flags.' if meta['mode'] != 'train'
                         else 'Trial saved. Reviewed valid TRAIN trials will be used at the next model build.')
            self.busy = False
            if meta['mode'] == 'train' and self.repeat_train.get():
                self.log('Repeat Train will rearm. Show a neutral hand for at least 0.5 s before moving again.')
                self.repeat_after_id = self.root.after(250, self.repeat_training)
        buttons = ttk.Frame(dialog)
        buttons.pack(pady=12)
        ttk.Button(buttons, text='Confirm label', command=lambda: done(True)).pack(side='left', padx=8)
        ttk.Button(buttons, text='Leave unreviewed / exclude', command=lambda: done(False)).pack(side='left')
        dialog.protocol('WM_DELETE_WINDOW', lambda: done(False))

    def show_test_comparison(self, meta):
        """Reveal all three classifiers only after the camera label has been reviewed."""
        selected = meta['selected_method']
        feature_set = selected.split('__', 1)[0]
        window = tk.Toplevel(self.root)
        window.title('Test comparison: ' + feature_set)
        window.transient(self.root)
        frame = ttk.Frame(window, padding=14)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=f"Test {meta['id']}  |  Camera reference: {meta['label']}").grid(
            row=0, column=0, columnspan=4, sticky='w', pady=(0, 8))
        headers = ('Model', 'EMG prediction', 'Window agreement', 'Result')
        for col, header in enumerate(headers):
            ttk.Label(frame, text=header, font=('TkDefaultFont', 9, 'bold')).grid(
                row=1, column=col, sticky='w', padx=(0, 16), pady=3)
        valid_reference = meta['reviewed'] and not blocking_quality(meta['quality'])
        for row, classifier in enumerate(('LDA', 'SVM', 'KNN'), start=2):
            name = feature_set + '__' + classifier
            pred = meta['predictions'].get(name)
            if pred is None:
                values = (classifier, 'Unavailable', '—', '—')
            else:
                correct = pred['prediction'] == meta['label']
                result = ('Excluded' if not valid_reference else
                          'MATCH' if correct and pred['accepted'] else
                          'Correct, rejected' if correct else
                          'Wrong, rejected' if not pred['accepted'] else 'NO MATCH')
                values = (classifier + ('  (selected)' if name == selected else ''),
                          pred['prediction'], f"{pred['agreement']:.0%}", result)
            for col, value in enumerate(values):
                ttk.Label(frame, text=value).grid(row=row, column=col, sticky='w', padx=(0, 16), pady=3)
        ttk.Label(frame, text='Window agreement = share of signal windows voting for that gesture; '
                  'it is not the chance the prediction is correct.', wraplength=650).grid(
            row=5, column=0, columnspan=4, sticky='w', pady=(10, 5))
        matching_classifiers = [c for c in ('LDA', 'SVM', 'KNN')
                                if meta['predictions'].get(feature_set + '__' + c, {}).get('prediction') == meta['label']]
        gazebo_status = (f"Gazebo Hand Status: Actuated '{meta['label']}' ({len(matching_classifiers)}/3 models agreed)"
                         if (len(matching_classifiers) >= 1 and valid_reference) else
                         "Gazebo Hand Status: Held at rest (no model matched camera reference)")
        ttk.Label(frame, text=gazebo_status, font=('TkDefaultFont', 9, 'bold'),
                  foreground='#1a73e8' if (len(matching_classifiers) >= 1 and valid_reference) else '#888888').grid(
            row=6, column=0, columnspan=4, sticky='w', pady=(4, 6))
        try:
            report = test_report(self.folder)
            protocol = meta['capture'].get('selection_method', 'automatic')
            totals = {r['method']: r for r in report['results']
                      if r['version'] == meta['model_version'] and r['protocol'] == protocol}
            ttk.Separator(frame).grid(row=7, column=0, columnspan=4, sticky='ew', pady=8)
            ttk.Label(frame, text='Running Test totals for these three models (reviewed, valid trials):').grid(
                row=8, column=0, columnspan=4, sticky='w')
            for row, classifier in enumerate(('LDA', 'SVM', 'KNN'), start=9):
                name = feature_set + '__' + classifier
                total = totals.get(name)
                detail = (f"{classifier}: {total['accuracy']:.1%} correct predictions; "
                          f"{total['success_all_attempts']:.1%} accepted and correct; "
                          f"{total['coverage']:.1%} accepted; N={total['trials']}"
                          if total else classifier + ': no reviewed, valid Test trials yet')
                ttk.Label(frame, text=detail).grid(row=row, column=0, columnspan=4, sticky='w', pady=2)
        except Exception as exc:
            ttk.Label(frame, text='Could not calculate running totals: ' + str(exc)).grid(
                row=7, column=0, columnspan=4, sticky='w')
        ttk.Button(frame, text='Close', command=window.destroy).grid(
            row=11, column=0, columnspan=4, pady=(12, 0))

    def repeat_training(self):
        self.repeat_after_id = None
        self.start('train')

    def training_window_review(self, dialog, path, meta):
        """Return a commit callback for a fixed-duration segment of saved context."""
        with np.load(path / 'capture_context.npz', allow_pickle=False) as saved:
            context = np.column_stack((saved['host_time'], saved['sequence'],
                                       saved['device_time'], saved['adc']))
        event = meta['capture']['event']
        duration = self.cfg.pre_seconds + self.cfg.post_seconds
        first = float(context[0, 0] - event)
        last = float(context[-1, 0] - event)
        low, high = first, last - duration + 1 / self.cfg.sample_rate
        if high < low:
            raise ValueError('Captured context is shorter than one training window.')
        default_start = float(np.clip(-0.5, low, high))
        ttk.Label(dialog, text=f'Slide the shaded {duration:.2f}-second window over the recorded signal. '
                  'The vertical line marks the camera event. Full context is kept.').pack(padx=12)
        fig = Figure(figsize=(8.5, 3.5), dpi=100)
        raw_ax = fig.add_subplot(211)
        activity_ax = fig.add_subplot(212, sharex=raw_ax)
        times = context[:, 0] - event
        values = context[:, 3]
        raw_ax.plot(times, values, lw=.5, color='#1465ad')
        raw_ax.set(ylabel='ADC counts', title='Captured raw EMG')
        step = max(1, round(self.cfg.sample_rate * .05))
        activity = [np.std(values[i:i+2*step]) for i in range(0, len(values)-2*step+1, step)]
        activity_ax.plot(times[0:len(activity)*step:step], activity, color='#bd5b0d')
        activity_ax.set(xlabel='Seconds relative to camera event', ylabel='Activity (100 ms)')
        for ax in (raw_ax, activity_ax):
            ax.axvline(0, color='#555', ls='--', lw=1)
        shades = [ax.axvspan(default_start, default_start + duration, color='#2ca02c', alpha=.2)
                  for ax in (raw_ax, activity_ax)]
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=dialog)
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=12)
        position = tk.DoubleVar(value=default_start)
        detail = tk.StringVar()
        def chosen():
            start = event + position.get()
            end = start + duration
            selected = context[(context[:, 0] >= start) & (context[:, 0] <= end)]
            problems = quality(selected, self.cfg)
            if len(selected) < duration * self.cfg.sample_rate * .97:
                problems.append('Incomplete selected duration')
            return selected, start, end, problems
        def redraw(_=None):
            start = position.get()
            for shade in shades:
                shade.remove()
            shades[:] = [ax.axvspan(start, start + duration, color='#2ca02c', alpha=.2)
                         for ax in (raw_ax, activity_ax)]
            selected, _, _, problems = chosen()
            detail.set(f'Selected: {start:+.2f} to {start+duration:+.2f} s | '
                       f'{len(selected)} samples | ' + ('; '.join(problems) if problems else 'Quality checks passed'))
            canvas.draw_idle()
        ttk.Scale(dialog, from_=low, to=high, variable=position,
                  orient='horizontal', command=redraw).pack(fill='x', padx=18)
        ttk.Label(dialog, textvariable=detail).pack(pady=3)
        redraw()
        def commit():
            selected, start, end, problems = chosen()
            non_window = [p for p in meta['quality'] if p.startswith('Acquisition diagnostic')
                          or p == 'Camera frames stale at capture end']
            meta['quality'] = non_window + problems
            capture = meta['capture']
            capture['default_start'] = capture['start']
            capture['default_end'] = capture['end']
            capture['start'], capture['end'] = start, end
            capture['selection_method'] = 'manual_' + meta['mode'] + '_slider'
            write_segment(path, selected, meta, self.cfg)
            return selected
        return commit

    def delete_last(self):
        if self.busy or self.pending:
            self.log('Wait for the current recording to finish before deleting it.')
            return
        if self.repeat_after_id is not None:
            self.root.after_cancel(self.repeat_after_id)
            self.repeat_after_id = None
        if self.mode:
            self.stop()
        path = self.last_trial_path
        if path is None or not path.is_dir():
            self.log('No recording from this app run is available to delete.')
            return
        try:
            folder = self.resolve_folder()
            if path.resolve().parent != (folder / 'trials').resolve():
                raise ValueError('The last recording belongs to another subject or placement.')
            meta = json.loads((path / 'trial.json').read_text(encoding='utf-8'))
            if meta['id'] != path.name:
                raise ValueError('Trial folder and metadata do not match.')
            if not messagebox.askyesno('Delete last recording',
                    f"Delete the last {meta['mode']} recording ({meta['label']}, {meta['id']})?\n"
                    'Its raw data and selected window will be removed.'):
                return
            latest = folder / 'latest_model.json'
            invalidate_model = False
            if latest.exists():
                version = json.loads(latest.read_text(encoding='utf-8'))['version']
                manifest = manifest_path(folder, version)
                if manifest.exists() and meta['id'] in json.loads(manifest.read_text(encoding='utf-8'))['training_ids']:
                    invalidate_model = True
            shutil.rmtree(path)
            self.last_trial_path = None
            if invalidate_model:
                self.bundle = None
                latest.unlink()
                self.log('Latest model used this trial; rebuild models before further testing.')
            if meta['mode'] == 'test':
                test_report(folder)
            self.log('Deleted last recording: ' + meta['id'])
        except Exception as exc:
            self.log('Could not delete last recording: ' + str(exc))

    def fit(self):
        if not self.idle(): return
        try:
            folder = self.resolve_folder()
            cfg = self.cfg
            counts = dict.fromkeys(LABELS, 0)
            for path in (folder / 'trials').glob('*/trial.json'):
                meta = json.loads(path.read_text(encoding='utf-8'))
                if (meta['mode'] == 'train' and meta['reviewed']
                        and not blocking_quality(meta['quality']) and meta['label'] in counts):
                    counts[meta['label']] += 1
            dialog = tk.Toplevel(self.root)
            dialog.title('Choose gestures to train')
            dialog.transient(self.root)
            dialog.grab_set()
            minimum = max(cfg.min_train_trials_per_class, cfg.cv_folds)
            ttk.Label(dialog, text=f'Select at least 2 gestures, with {minimum} valid recordings each.\n'
                      'Rest counts as one gesture. Unselected recordings stay saved.').pack(padx=16, pady=12)
            choices = {}
            for label, count in counts.items():
                choices[label] = tk.BooleanVar(value=count >= minimum)
                ttk.Checkbutton(dialog, text=f'{label}: {count} valid recordings', variable=choices[label],
                                state='normal' if count >= minimum else 'disabled').pack(anchor='w', padx=16)
            def train_selected():
                labels = [label for label, var in choices.items() if var.get()]
                if len(labels) < 2:
                    messagebox.showerror('Select gestures', 'Select at least two gestures with enough recordings.', parent=dialog)
                    return
                dialog.destroy()
                self.log(f'Training {len(labels)} gestures: ' + ', '.join(labels))
                self.worker(lambda: build_models(folder, cfg,
                            lambda msg: self.events.put(('progress', msg)), selected_labels=labels), 'trained')
            ttk.Button(dialog, text='Train selected gestures', command=train_selected).pack(pady=12)
        except Exception as exc:
            self.log(str(exc))

    def load(self):
        if not self.idle(): return
        try:
            folder = self.resolve_folder()
            self.log('Loading models in the background...')
            self.worker(lambda: load_latest(folder), 'loaded')
        except Exception as exc:
            self.log(str(exc))

    def export(self):
        if not self.idle(): return
        try:
            folder, cfg = self.resolve_folder(), self.cfg
            self.worker(lambda: export_workbook(folder, cfg), 'exported')
        except Exception as exc:
            self.log(str(exc))

    def results(self):
        if not self.idle(): return
        try:
            folder = self.resolve_folder()
            report = test_report(folder)
            lines = ['TEST results: reviewed, valid trials. Invalid/unreviewed trials reported separately.',
                     f"Excluded: {len(report['excluded'])}"]
            if self.bundle:
                selected = self.bundle['manifest']['selected']
                version = self.bundle['manifest']['version']
                feature_set = selected.split('__', 1)[0]
                lines += ['', f'CURRENT FEATURE SET: {feature_set} | model version {version}',
                          'Slider-reviewed Test trials:']
                for classifier in ('LDA', 'SVM', 'KNN'):
                    name = feature_set + '__' + classifier
                    row = next((r for r in report['results'] if r['version'] == version
                                and r['method'] == name
                                and r['protocol'] == 'manual_test_slider'), None)
                    if row:
                        lines.append(f"{name}{' (selected)' if name == selected else ''}: "
                                     f"correct={row['accuracy']:.1%}, accepted-and-correct/all="
                                     f"{row['success_all_attempts']:.1%}, coverage={row['coverage']:.1%}, N={row['trials']}")
                    else:
                        lines.append(f'{name}: no reviewed, valid Test trials yet')
                lines += ['', 'ALL FEATURE SETS AND MODELS:']
            for row in report['results']:
                lines.append(f"{row['version']} {row['method']} [{row['protocol']}]: accuracy={row['accuracy']:.1%}, coverage={row['coverage']:.1%}, accepted-and-correct/all={row['success_all_attempts']:.1%}, N={row['trials']}")
            if self.bundle:
                m = self.bundle['manifest']
                lines += ['', 'MODEL-SELECTION VALIDATION (not final test): ' + m['split_kind']]
                for name, row in sorted(m['reports'].items(), key=lambda v: -v[1]['accuracy']):
                    lines.append(f"{name}: {row['accuracy']:.1%}, macro F1={row['macro_f1']:.3f}")
            window = tk.Toplevel(self.root)
            window.title('Measured results')
            text = tk.Text(window, width=120, height=32)
            text.pack(fill='both', expand=True)
            text.insert('1.0', '\n'.join(lines))
        except Exception as exc:
            self.log(str(exc))

    def command(self, label, meta):
        self.draw_hand(label)
        self.last_command_time = time.monotonic()
        self.last_command = label
        if self.folder:
            with (self.folder / 'simulation_commands.jsonl').open('a', encoding='utf-8') as f:
                f.write(json.dumps(dict(time=time.time(), gesture=label, trial=meta.get('id', ''),
                                        model_version=meta.get('model_version', ''), simulation_only=True))+'\n')
        if self.gazebo_bridge:
            self.gazebo_bridge.send_gesture(label)

    def draw_hand(self, label):
        self.hand.delete('all')
        self.hand.create_rectangle(110, 120, 305, 205, fill='#c3cedb', outline='#526678')
        bent = set(LABELS[1:6]) if label == 'fist' else {'thumb', 'index'} if label == 'pinch' else {label}
        for i, finger in enumerate(LABELS[1:6]):
            x = 65 + i*60
            y = 95 if finger in bent else 35
            self.hand.create_rectangle(x, y, x+35, 145, fill='#e89f50' if finger in bent else '#74b7bd')
            self.hand.create_text(x+17, 18, text=finger)
        self.hand.create_text(200, 220, text='Simulation: ' + label)

    def tick(self):
        now = time.monotonic()
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'progress': self.log(value)
                elif kind == 'captured': self.review(*value)
                else:
                    self.busy = False
                    self.expected_box.configure(state='readonly')
                    if kind == 'trained':
                        self.bundle = value
                        self.log('Models saved: ' + value['manifest']['version'] + '\nGestures: ' +
                                 ', '.join(value['manifest']['labels']) + '\nSelected by validation: ' + value['manifest']['selected'])
                    elif kind == 'loaded':
                        self.bundle = value
                        self.log('Loaded trusted local model: ' + value['manifest']['selected'] +
                                 ' | Gestures: ' + ', '.join(value['manifest'].get('labels', LABELS)))
                    elif kind == 'exported': self.log('Export saved: ' + str(value))
                    else: self.log('Error: ' + str(value))
        except queue.Empty:
            pass
        if self.reader:
            d = self.reader.diagnostics()
            age = f'{now-self.reader.last_rx:.1f}s' if self.reader.last_rx else 'awaiting first packet'
            self.telemetry.set(f"{self.session} | {d} | age={age} | {self.reader.error}")
            if not self.busy and self.series_window is None and now-self.last_plot > .25:
                rows = self.reader.snapshot(start=now-3)
                if len(rows):
                    self.raw_line.set_data(rows[:, 0]-now, rows[:, 3])
                    filtered = self.cfg.digital_bandpass or self.cfg.notch_50hz
                    self.filtered_line.set_data(rows[:, 0]-now if filtered else [], process(rows[:, 3], self.cfg) if filtered else [])
                    self.ax.set_ylim(-2100 if filtered else 0, 4095)
                    self.plot.draw_idle()
                self.last_plot = now
        if self.camera:
            snap = self.camera.snapshot()
            if self.camera.error:
                self.status.set('Camera error: ' + self.camera.error)
            if snap and snap[0] != self.last_camera_time:
                self.last_camera_time = snap[0]
                # Throttle only the visible preview, not camera recognition/gating.
                if now-self.last_preview_time >= .1:
                    picture = Image.fromarray(snap[3])
                    picture.thumbnail((400, 300))
                    self.camera_image = ImageTk.PhotoImage(picture)
                    self.camera_label.configure(image=self.camera_image, text='')
                    self.last_preview_time = now
                if self.mode and not self.pending and now-snap[0] < .5:
                    event = self.gate.update(snap[1], snap[0])
                    if event:
                        self.begin_capture(*event)
        if self.mode:
            camera_snap = self.camera.snapshot()
            if (self.reader.error or now-self.reader.last_rx > 1 or self.camera.error
                    or camera_snap is None or now-camera_snap[0] > 1):
                self.stop()
                self.log('Capture stopped: device/camera data unavailable; attempt retained in log.')
            elif self.pending and now >= self.pending.get('context_end', self.pending['end']) + .10:
                self.finish_capture()
            elif not self.pending and now > self.deadline:
                self.stop()
                self.log('No complete gesture detected before timeout. Attempt logged; not an EMG prediction.')
        self.root.after(50, self.tick)

    def close(self):
        if self.busy and not messagebox.askyesno('Operation running', 'A save/training/export is running. Closing now may interrupt it. Close anyway?'):
            return
        if self.gazebo_bridge:
            try:
                self.gazebo_bridge.close()
            except Exception:
                pass
        if self.reader: self.reader.close()
        if self.camera: self.camera.close()
        self.root.destroy()


def configure_dpi():
    import sys
    if sys.platform == 'win32':
        import ctypes
        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError, OSError):
            pass


def main(smoke=False):
    configure_dpi()
    root = tk.Tk()
    app = App(root)
    if smoke:
        root.after(1200, app.close)
    root.mainloop()
