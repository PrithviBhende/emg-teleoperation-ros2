"""One camera-free, manually timed EMG test. Results have no ground-truth score."""
import time
import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .ml import predict_trial
from .series import blocking_quality
from .signal import quality
from .storage import identifier, write_json


class ManualTestReview:
    def __init__(self, app, rows, acquisition_problems):
        self.app = app
        self.rows = rows
        self.acquisition_problems = acquisition_problems
        self.duration = app.cfg.pre_seconds + app.cfg.post_seconds
        # This marker is only a slider reference; no camera event or gesture label is used.
        self.marker = rows[0, 0] + min(.5, (rows[-1, 0] - rows[0, 0]) / 2)
        times = rows[:, 0] - self.marker
        low = float(times[0])
        high = float(times[-1] - self.duration + 1 / app.cfg.sample_rate)
        if high < low:
            raise ValueError('Recording is too short for a complete selection.')
        self.position = tk.DoubleVar(value=float(np.clip(-.5, low, high)))
        self.detail = tk.StringVar()
        self.window = tk.Toplevel(app.root)
        self.window.title('Manual Test | choose EMG window')
        self.window.geometry(f'{min(950, self.window.winfo_screenwidth()-80)}x'
                             f'{min(650, self.window.winfo_screenheight()-100)}')
        self.window.transient(app.root)
        self.window.grab_set()
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        footer = ttk.Frame(self.window, padding=8)
        footer.pack(side='bottom', fill='x')
        ttk.Label(self.window, text='Camera-free test: slide the green window over the movement, then predict. '
                  'There is no reference label or accuracy score for this capture.', wraplength=760).pack(pady=8)
        fig = Figure(figsize=(9, 4.3), dpi=100)
        self.raw_ax = fig.add_subplot(211)
        self.activity_ax = fig.add_subplot(212, sharex=self.raw_ax)
        values = rows[:, 3]
        self.raw_ax.plot(times, values, lw=.5, color='#1465ad')
        self.raw_ax.set(ylabel='ADC counts', title='Recorded raw EMG')
        step = max(1, round(app.cfg.sample_rate * .05))
        activity = [np.std(values[i:i+2*step]) for i in range(0, len(values)-2*step+1, step)]
        self.activity_ax.plot(times[0:len(activity)*step:step], activity, color='#bd5b0d')
        self.activity_ax.set(xlabel='Seconds relative to start marker', ylabel='Activity (100 ms)')
        for ax in (self.raw_ax, self.activity_ax):
            ax.axvline(0, color='#555', ls='--', lw=1)
        self.shades = []
        fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(fig, master=self.window)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10)
        ttk.Scale(footer, from_=low, to=high, variable=self.position,
                  orient='horizontal', command=self.redraw).pack(fill='x', padx=20)
        ttk.Label(footer, textvariable=self.detail, wraplength=800).pack(pady=5)
        controls = ttk.Frame(footer)
        controls.pack(pady=6)
        self.predict_button = ttk.Button(controls, text='Predict selected window', command=self.predict)
        self.predict_button.pack(side='left', padx=6)
        ttk.Button(controls, text='Discard / close', command=self.close).pack(side='left', padx=6)
        self.result = ttk.Label(footer, text='', wraplength=850)
        self.result.pack(pady=4)
        self.redraw()

    def selected(self):
        start = self.marker + self.position.get()
        selected = self.rows[(self.rows[:, 0] >= start) &
                             (self.rows[:, 0] <= start + self.duration)]
        problems = self.acquisition_problems + quality(selected, self.app.cfg)
        if len(selected) < self.duration * self.app.cfg.sample_rate * .97:
            problems.append('Incomplete selected duration')
        return selected, problems

    def redraw(self, _=None):
        for shade in self.shades:
            shade.remove()
        start = self.position.get()
        self.shades = [ax.axvspan(start, start + self.duration, color='#2ca02c', alpha=.2)
                       for ax in (self.raw_ax, self.activity_ax)]
        selected, problems = self.selected()
        self.detail.set(f'{start:+.2f} to {start+self.duration:+.2f} s | '
                        f'{len(selected)} samples | '
                        + ('; '.join(problems) if problems else 'Quality checks passed'))
        self.predict_button.configure(state='disabled' if blocking_quality(problems) else 'normal')
        self.canvas.draw_idle()

    def predict(self):
        selected, problems = self.selected()
        if blocking_quality(problems):
            self.result.configure(text='This window has missing/timing/flat-signal data. Move the slider or retry.')
            return
        try:
            predictions = predict_trial(self.app.bundle, selected[:, 3])
            manifest = self.app.bundle['manifest']
            chosen = manifest['selected']
            selected_result = predictions[chosen]
            feature_set = chosen.split('__', 1)[0]
            name = identifier()
            output = self.app.folder / 'manual_tests' / name
            output.mkdir(parents=True, exist_ok=False)
            np.savez_compressed(output / 'capture.npz', host_time=self.rows[:, 0],
                                sequence=self.rows[:, 1].astype(np.uint32),
                                device_time=self.rows[:, 2], adc=self.rows[:, 3].astype(np.uint16))
            np.savez_compressed(output / 'selected.npz', host_time=selected[:, 0],
                                sequence=selected[:, 1].astype(np.uint32),
                                device_time=selected[:, 2], adc=selected[:, 3].astype(np.uint16))
            write_json(output / 'result.json', dict(id=name, mode='manual_test',
                       source='hardware', reference_label=None, scored=False,
                       model_version=manifest['version'], selected_method=chosen,
                       selected_start_s=float(self.position.get()),
                       selected_end_s=float(self.position.get()+self.duration),
                       quality_warnings=problems, predictions=predictions, wall_time=time.time()))
            lines = [f"Selected {chosen}: {selected_result['prediction']}"
                     + (' (accepted)' if selected_result['accepted'] else ' (uncertain / rejected)'),
                     'Window agreement is a vote share, not the probability of being correct.']
            for classifier in ('LDA', 'SVM', 'KNN'):
                result = predictions.get(feature_set + '__' + classifier)
                if result:
                    lines.append(f"{classifier}: {result['prediction']} | "
                                 f"agreement {result['agreement']:.0%} | "
                                 + ('accepted' if result['accepted'] else 'rejected'))
            if problems:
                lines.append('Warning: ' + '; '.join(problems))
            self.result.configure(text='\n'.join(lines))
            self.predict_button.configure(state='disabled')
            self.app.log(f"Manual Test: {selected_result['prediction']} "
                         f"({'accepted' if selected_result['accepted'] else 'uncertain'}); "
                         'unscored because no camera/reference label was used.')
            if selected_result['accepted']:
                self.app.command(selected_result['prediction'], dict(id=name,
                                  model_version=manifest['version']))
        except Exception as exc:
            self.result.configure(text='Prediction failed: ' + str(exc))

    def close(self):
        self.window.grab_release()
        self.window.destroy()
        self.app.busy = False
