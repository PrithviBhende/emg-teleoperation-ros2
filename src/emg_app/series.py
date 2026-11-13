"""Manually controlled multi-repetition test, kept separate from ordinary Test."""
from dataclasses import asdict
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .config import LABELS
from .ml import predict_series, predict_trial
from .signal import quality, blocking_quality
from .storage import identifier, write_json


class SeriesTestWindow:
    def __init__(self, app):
        self.app = app
        self.cfg = app.cfg
        self.repetitions = []
        self.review_window = None
        self.recording_since = None
        active_labels = app.bundle['manifest'].get('labels', LABELS)
        self.reference = tk.StringVar(value=app.expected.get() if app.expected.get() in active_labels else active_labels[0])
        self.status = tk.StringVar(value='Choose the movement, then press Start for one repetition.')
        self.window = tk.Toplevel(app.root)
        self.window.title('Series Test | manual Start / Stop')
        self.window.geometry('760x360')
        self.window.transient(app.root)
        self.window.protocol('WM_DELETE_WINDOW', self.cancel)
        frame = ttk.Frame(self.window, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Movement to check against the EMG prediction:').pack(anchor='w')
        self.reference_box = ttk.Combobox(frame, textvariable=self.reference,
                                          values=active_labels, state='readonly', width=14)
        self.reference_box.pack(anchor='w', pady=4)
        ttk.Label(frame, text='This reference is used only to score the result. The model receives EMG only.',
                  wraplength=650).pack(anchor='w')
        buttons = ttk.Frame(frame)
        buttons.pack(anchor='w', pady=14)
        self.start_button = ttk.Button(buttons, text='Start recording', command=self.start)
        self.start_button.pack(side='left', padx=(0, 8))
        self.stop_button = ttk.Button(buttons, text='Stop and review', command=self.stop, state='disabled')
        self.stop_button.pack(side='left', padx=8)
        ttk.Button(buttons, text='Remove last', command=self.remove_last).pack(side='left', padx=8)
        ttk.Button(buttons, text='Final Test', command=self.final_test).pack(side='left', padx=8)
        ttk.Button(buttons, text='Cancel / close', command=self.cancel).pack(side='left', padx=8)
        ttk.Label(frame, textvariable=self.status, wraplength=660).pack(anchor='w', pady=5)
        self.count = ttk.Label(frame, text='Accepted repetitions: 0')
        self.count.pack(anchor='w')
        ttk.Label(frame, text='No 10-second gesture timeout. Stop each recording within 18 seconds '
                  'so the Due reader still retains its beginning.', wraplength=660).pack(anchor='w', pady=12)

    def cancel(self):
        if (self.repetitions or self.recording_since is not None) and not messagebox.askyesno(
                'Close series without testing?',
                'Discard the recordings in this unfinished series and close? Exported PNG files will remain.',
                parent=self.review_window or self.window):
            return
        self.recording_since = None
        if self.review_window is not None:
            self.review_window.grab_release()
            self.review_window.destroy()
            self.review_window = None
        self.window.destroy()
        self.app.series_window = None
        self.app.log('Series cancelled. No test result was created.')

    def start(self):
        reader = self.app.reader
        if self.recording_since is not None:
            self.status.set('Already recording. Press Stop and review.')
            return
        if not reader or reader.error or time.monotonic() - reader.last_rx > .5:
            self.status.set('No fresh Due samples. Reconnect before recording.')
            return
        self.recording_since = time.monotonic()
        self.capture_reference = self.reference.get()
        self.reference_box.configure(state='disabled')
        self.diagnostics_at_start = reader.diagnostics()
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.status.set('Recording. Begin relaxed, move once, hold briefly, then press Stop and review.')

    def stop(self):
        if self.recording_since is None:
            return
        start, end = self.recording_since, time.monotonic()
        self.recording_since = None
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        if end - start > 18:
            self.status.set('Recording exceeded 18 seconds; the circular buffer may have lost its start. Retry.')
            if not self.repetitions:
                self.reference_box.configure(state='readonly')
            return
        rows = self.app.reader.snapshot(start, end)
        duration = self.cfg.pre_seconds + self.cfg.post_seconds
        if len(rows) < duration * self.cfg.sample_rate * .97:
            self.status.set(f'Only {len(rows)} samples captured. Record longer than {duration:.2f} seconds and retry.')
            if not self.repetitions:
                self.reference_box.configure(state='readonly')
            return
        diag = self.app.reader.diagnostics()
        problems = ['Acquisition diagnostic increased: ' + key
                    for key in ('missing', 'corrupt', 'overruns', 'late')
                    if diag[key] > self.diagnostics_at_start[key]]
        events = self.app.camera.events(start, end) if self.app.camera else []
        matching = [e for e in events if e['label'] == self.capture_reference]
        motion = matching or [e for e in events if e['label'] not in ('neutral', 'unknown')]
        event = motion[0]['host_time'] if motion else start + min(.5, (end - start) / 2)
        source = 'camera' if motion else 'approximate start marker'
        self.review_capture(rows, event, source, problems)

    def review_capture(self, rows, event, event_source, non_window_problems):
        dialog = tk.Toplevel(self.window)
        self.review_window = dialog
        dialog.title('Choose one repetition window')
        dialog.geometry(f'{min(950, dialog.winfo_screenwidth()-80)}x{min(650, dialog.winfo_screenheight()-100)}')
        dialog.transient(self.window)
        dialog.grab_set()
        duration = self.cfg.pre_seconds + self.cfg.post_seconds
        times = rows[:, 0] - event
        low = float(times[0])
        high = float(times[-1] - duration + 1 / self.cfg.sample_rate)
        if high < low:
            dialog.destroy()
            self.review_window = None
            self.status.set('Recording is too short for a complete selection. Retry.')
            if not self.repetitions:
                self.reference_box.configure(state='readonly')
            return
        position = tk.DoubleVar(value=float(np.clip(-.5, low, high)))
        detail = tk.StringVar()
        advice = tk.StringVar()
        add_button = None
        # Reserve controls before the expandable plot, including on small/high-DPI screens.
        footer = ttk.Frame(dialog, padding=8)
        footer.pack(side='bottom', fill='x')
        ttk.Label(dialog, text=f'Green = {duration:.2f} seconds saved. Vertical line = {event_source}. '
                  'Slide to include the movement; only this window enters the final test.',
                  wraplength=650).pack(pady=8)
        fig = Figure(figsize=(9, 4.3), dpi=100)
        raw_ax = fig.add_subplot(211)
        activity_ax = fig.add_subplot(212, sharex=raw_ax)
        values = rows[:, 3]
        raw_ax.plot(times, values, lw=.5, color='#1465ad')
        raw_ax.set(ylabel='ADC counts', title='Raw EMG')
        step = max(1, round(self.cfg.sample_rate * .05))
        activity = [np.std(values[i:i+2*step]) for i in range(0, len(values)-2*step+1, step)]
        activity_ax.plot(times[0:len(activity)*step:step], activity, color='#bd5b0d')
        activity_ax.set(xlabel='Seconds relative to marker', ylabel='Activity (100 ms)')
        for ax in (raw_ax, activity_ax):
            ax.axvline(0, color='#555', ls='--', lw=1)
        shades = [ax.axvspan(position.get(), position.get()+duration, color='#2ca02c', alpha=.2)
                  for ax in (raw_ax, activity_ax)]
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=dialog)
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=10)

        def chosen():
            begin = event + position.get()
            selected = rows[(rows[:, 0] >= begin) & (rows[:, 0] <= begin + duration)]
            problems = non_window_problems + quality(selected, self.cfg)
            if len(selected) < duration * self.cfg.sample_rate * .97:
                problems.append('Incomplete selected duration')
            return selected, problems

        def redraw(_=None):
            for shade in shades:
                shade.remove()
            shades[:] = [ax.axvspan(position.get(), position.get()+duration,
                                    color='#2ca02c', alpha=.2) for ax in (raw_ax, activity_ax)]
            selected, problems = chosen()
            detail.set(f'{position.get():+.2f} to {position.get()+duration:+.2f} s | '
                       f'{len(selected)} samples | '+('; '.join(problems) if problems else 'Quality checks passed'))
            blocked = blocking_quality(problems)
            clipped = any(p.startswith('ADC clipping:') for p in problems)
            if blocked:
                advice.set('Missing samples, timing errors or a flat signal cannot be tested. '
                           'Move the slider or retry. You can save this for inspection below.')
            elif clipped:
                advice.set('Clipping warning: some peaks reached the ADC limit. '
                           'You may add this exact reading to the final test; its warning will be saved and shown.')
            else:
                advice.set('Clean selection: ready to add to the series.')
            if add_button is not None:
                add_button.configure(state='disabled' if blocked else 'normal',
                                     text='Cannot add: recording problem' if blocked else
                                          'Add with clipping warning' if clipped else 'Add selection')
            canvas.draw_idle()

        ttk.Scale(footer, from_=low, to=high, variable=position,
                  orient='horizontal', command=redraw).pack(fill='x', padx=20)
        ttk.Label(footer, textvariable=detail, wraplength=650).pack(pady=5)
        ttk.Label(footer, textvariable=advice, wraplength=750, foreground='#a02020').pack(pady=3)

        def add():
            selected, problems = chosen()
            if blocking_quality(problems):
                self.status.set('Selection has a quality issue: ' + '; '.join(problems))
                return
            self.repetitions.append(dict(rows=selected.copy(), reference=self.capture_reference,
                                         selected_start_s=float(position.get()),
                                         selected_end_s=float(position.get()+duration),
                                         event_source=event_source, quality_warnings=problems))
            self.reference_box.configure(state='disabled')
            self.count.configure(text=f'Accepted repetitions: {len(self.repetitions)}')
            self.status.set(f'Repetition {len(self.repetitions)} added'
                            + (' with clipping warning.' if problems else '.')
                            + ' Press Start for another or Final Test.')
            dialog.grab_release()
            dialog.destroy()
            self.review_window = None

        controls = ttk.Frame(footer)
        controls.pack(fill='x', pady=8)
        controls.columnconfigure((0, 1), weight=1)
        add_button = ttk.Button(controls, text='Add clean selection', command=add)
        add_button.grid(row=0, column=0, sticky='ew', padx=4, pady=3)
        def retry():
            dialog.grab_release()
            dialog.destroy()
            self.review_window = None
            if not self.repetitions:
                self.reference_box.configure(state='readonly')
            self.status.set('Repetition discarded. Press Start to record again.')
        def save_graph():
            target = filedialog.asksaveasfilename(parent=dialog, title='Save captured graph',
                        defaultextension='.png', filetypes=[('PNG image', '*.png')],
                        initialfile=f'{self.app.folder.parent.name}_{self.app.folder.name}_series_{self.capture_reference}_{identifier()}.png')
            if target:
                try:
                    fig.savefig(target, dpi=150)
                    self.status.set('Graph image saved: ' + target)
                except Exception as exc:
                    messagebox.showerror('Could not save graph', str(exc), parent=dialog)
        def save_flagged():
            selected, problems = chosen()
            if not problems:
                self.status.set('This window passes quality checks. Use Add clean selection.')
                return
            try:
                name = f'{self.app.folder.parent.name}_{self.app.folder.name}_excluded_{identifier()}'
                output = self.app.folder / 'series_diagnostics' / name
                output.mkdir(parents=True, exist_ok=False)
                np.savez_compressed(output / 'capture.npz', host_time=rows[:, 0],
                                    sequence=rows[:, 1].astype(np.uint32), device_time=rows[:, 2],
                                    adc=rows[:, 3].astype(np.uint16))
                np.savez_compressed(output / 'selected.npz', host_time=selected[:, 0],
                                    sequence=selected[:, 1].astype(np.uint32), device_time=selected[:, 2],
                                    adc=selected[:, 3].astype(np.uint16))
                fig.savefig(output / 'graph.png', dpi=150)
                write_json(output / 'diagnostic.json', dict(reference=self.capture_reference,
                           quality=problems, selected_start_s=float(position.get()),
                           selected_end_s=float(position.get()+duration), event_source=event_source,
                           excluded_from_series_prediction=True))
                self.status.set('Excluded capture saved for inspection: ' + str(output))
                dialog.grab_release()
                dialog.destroy()
                self.review_window = None
                if not self.repetitions:
                    self.reference_box.configure(state='readonly')
            except Exception as exc:
                messagebox.showerror('Could not save diagnostic', str(exc), parent=dialog)
        ttk.Button(controls, text='Save graph PNG', command=save_graph).grid(row=0, column=1, sticky='ew', padx=4, pady=3)
        ttk.Button(controls, text='Save flagged (excluded)', command=save_flagged).grid(row=1, column=0, sticky='ew', padx=4, pady=3)
        ttk.Button(controls, text='Retry', command=retry).grid(row=1, column=1, sticky='ew', padx=4, pady=3)
        ttk.Button(controls, text='Cancel series', command=self.cancel).grid(row=2, column=0, columnspan=2, sticky='ew', padx=4, pady=3)
        redraw()
        dialog.protocol('WM_DELETE_WINDOW', retry)

    def remove_last(self):
        if self.recording_since is not None:
            self.status.set('Stop the current recording first.')
            return
        if self.repetitions:
            self.repetitions.pop()
            self.count.configure(text=f'Accepted repetitions: {len(self.repetitions)}')
            if not self.repetitions:
                self.reference_box.configure(state='readonly')
            self.status.set('Last repetition removed.')
        else:
            self.status.set('No repetitions to remove.')

    def final_test(self):
        if self.recording_since is not None:
            self.status.set('Stop and review the current recording first.')
            return
        if not self.repetitions:
            self.status.set('Add at least one repetition before Final Test.')
            return
        try:
            bundle = self.app.bundle
            segments = [r['rows'][:, 3] for r in self.repetitions]
            combined = predict_series(bundle, segments)
            individual = [predict_trial(bundle, segment) for segment in segments]
            reference = self.repetitions[0]['reference']
            version = bundle['manifest']['version']
            series_id = identifier()
            output = self.app.folder / 'series_tests' / series_id
            output.mkdir(parents=True, exist_ok=False)
            details = []
            for i, repetition in enumerate(self.repetitions, start=1):
                rows = repetition['rows']
                np.savez_compressed(output / f'repetition_{i:02d}.npz', host_time=rows[:, 0],
                                    sequence=rows[:, 1].astype(np.uint32), device_time=rows[:, 2],
                                    adc=rows[:, 3].astype(np.uint16))
                details.append(dict(file=f'repetition_{i:02d}.npz',
                                    selected_start_s=repetition['selected_start_s'],
                                    selected_end_s=repetition['selected_end_s'],
                                    event_source=repetition['event_source'],
                                    quality_warnings=repetition['quality_warnings'],
                                    predictions=individual[i-1]))
            clipped_count = sum(bool(r['quality_warnings']) for r in self.repetitions)
            write_json(output / 'series.json', dict(id=series_id, reference=reference,
                       model_version=version, selected_method=bundle['manifest']['selected'],
                       settings=asdict(self.cfg), repetition_count=len(details),
                       clipped_repetitions=clipped_count, repetitions=details,
                       combined_predictions=combined, wall_time=time.time(),
                       note='Manual reference. One combined series outcome; not ordinary Test accuracy.'))
            self.window.destroy()
            self.app.series_window = None
            self.app.log(f'Series Test saved: {series_id}; {len(details)} repetitions; reference={reference}.')
            self.show_results(reference, combined, individual, output, clipped_count)
        except Exception as exc:
            self.status.set('Final Test failed: ' + str(exc))

    def show_results(self, reference, combined, individual, output, clipped_count):
        selected = self.app.bundle['manifest']['selected']
        feature_set = selected.split('__', 1)[0]
        window = tk.Toplevel(self.app.root)
        window.title('Series Test results')
        frame = ttk.Frame(window, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=f'Reference: {reference} | Repetitions: {len(individual)} | '
                  f'Feature set: {feature_set}').pack(anchor='w', pady=5)
        if clipped_count:
            ttk.Label(frame, text=f'Clipping warning: {clipped_count}/{len(individual)} repetitions '
                      'contained ADC-limit peaks. Predictions include those readings as recorded.',
                      foreground='#a02020', wraplength=850).pack(anchor='w', pady=5)
        for classifier in ('LDA', 'SVM', 'KNN'):
            name = feature_set + '__' + classifier
            result = combined[name]
            correct = sum(rep[name]['prediction'] == reference for rep in individual)
            accepted_correct = sum(rep[name]['accepted'] and rep[name]['prediction'] == reference
                                   for rep in individual)
            status = ('MATCH' if result['prediction'] == reference and result['accepted'] else
                      'Correct but rejected' if result['prediction'] == reference else
                      'Wrong / rejected' if not result['accepted'] else 'NO MATCH')
            ttk.Label(frame, text=(f"{classifier}{' (selected)' if name == selected else ''}: "
                                   f"combined={result['prediction']} ({status}); "
                                   f"window agreement={result['agreement']:.0%}; "
                                   f"repetitions correct={correct}/{len(individual)} ({correct/len(individual):.0%}); "
                                   f"accepted and correct={accepted_correct}/{len(individual)}"),
                      wraplength=850).pack(anchor='w', pady=7)
        ttk.Label(frame, text='Window agreement is a vote share, not a probability. '
                  'Repeated captures in one series are one exploratory result, not independent final Test trials.',
                  wraplength=850).pack(anchor='w', pady=10)
        ttk.Label(frame, text='Saved: ' + str(output), wraplength=850).pack(anchor='w')
        ttk.Button(frame, text='Close results', command=window.destroy).pack(pady=12)
