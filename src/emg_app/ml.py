"""Feature-only classifiers: camera labels cannot enter predict_trial()."""
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
from .config import LABELS, Config
from .signal import SETS, features, blocking_quality
from .storage import identifier, load_trials, write_json


def candidates():
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC
    return {
        'LDA': make_pipeline(StandardScaler(), LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')),
        'SVM': make_pipeline(StandardScaler(), SVC(C=1.0, kernel='rbf', gamma='scale')),
        'KNN': make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5, weights='distance')),
    }


def vote(model, x, threshold):
    labels, counts = np.unique(model.predict(x), return_counts=True)
    top = int(np.argmax(counts))
    agreement = float(counts[top] / counts.sum())
    tie = np.sum(counts == counts[top]) > 1
    return dict(prediction=str(labels[top]), agreement=agreement,
                accepted=bool(not tie and agreement >= threshold),
                window_votes={str(k): int(v) for k, v in zip(labels, counts)})


def metrics(truth, predictions, labels=None):
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
    guesses = [p['prediction'] for p in predictions]
    labels = list(LABELS if labels is None else labels)
    labels += sorted((set(truth) | set(guesses)) - set(labels))
    accepted = np.array([p['accepted'] for p in predictions])
    correct = np.asarray(truth) == np.asarray(guesses)
    return dict(accuracy=float(accuracy_score(truth, guesses)),
                macro_f1=float(f1_score(truth, guesses, labels=labels, average='macro', zero_division=0)),
                coverage=float(accepted.mean()),
                success_all_attempts=float(np.mean(correct & accepted)),
                accepted_accuracy=float(correct[accepted].mean()) if accepted.any() else None,
                confusion=confusion_matrix(truth, guesses, labels=labels).tolist(),
                labels=labels, trials=len(truth))


def build_models(folder, cfg, progress=lambda message: None, selected_labels=None):
    import joblib
    from sklearn.base import clone
    from sklearn.model_selection import StratifiedKFold, StratifiedGroupKFold
    trials = [(p, m, raw) for p, m, raw in load_trials(folder)
              if m['mode'] == 'train' and m['reviewed'] and not blocking_quality(m['quality'])
              and m['label'] in LABELS]
    active = [label for label in LABELS if label in
              (selected_labels if selected_labels is not None else {m['label'] for _, m, _ in trials})]
    if len(active) < 2:
        raise ValueError('Select at least two recorded gestures, such as rest and fist.')
    trials = [(p, m, raw) for p, m, raw in trials if m['label'] in active]
    counts = {label: sum(m['label'] == label for _, m, _ in trials) for label in active}
    minimum = max(cfg.min_train_trials_per_class, cfg.cv_folds)
    if min(counts.values()) < minimum:
        raise ValueError(f'Need {minimum} reviewed, valid repetitions for each selected gesture. Current: {counts}')
    if len({m.get('source', 'hardware') for _, m, _ in trials}) != 1:
        raise ValueError('Synthetic and hardware trials must never be mixed.')
    # Capture rules must not silently differ between classes/trials.
    timing_keys = ('pre_seconds', 'post_seconds', 'camera_offset_seconds')
    if any(any(m['config'][k] != asdict(cfg)[k] for k in timing_keys) for _, m, _ in trials):
        raise ValueError('Capture timing differs from saved trials. Use a new placement/dataset for a new timing protocol.')
    xs = [features(raw, cfg)[0] for _, _, raw in trials]
    if any(not len(x) for x in xs):
        raise ValueError('A training trial contains no full analysis window.')
    y = np.array([m['label'] for _, m, _ in trials])
    sessions = np.array([m['session'] for _, m, _ in trials])
    enough_sessions = all(len(set(sessions[y == label])) >= cfg.cv_folds for label in active)
    if enough_sessions:
        splitter = StratifiedGroupKFold(n_splits=cfg.cv_folds, shuffle=True, random_state=cfg.seed)
        splits = list(splitter.split(np.zeros(len(y)), y, sessions))
        split_kind = 'held-out whole sessions'
    else:
        splitter = StratifiedKFold(n_splits=cfg.cv_folds, shuffle=True, random_state=cfg.seed)
        splits = list(splitter.split(np.zeros(len(y)), y))
        split_kind = 'held-out whole trials; NOT proof of cross-session generalisation'
    for tr, va in splits:
        if set(y[tr]) != set(active) or set(y[va]) != set(active):
            raise ValueError('Grouped folds lack classes. Collect each gesture in more complete sessions.')
    reports, fitted = {}, {}
    for feature_set, indices in SETS.items():
        for classifier, prototype in candidates().items():
            name = feature_set + '__' + classifier
            progress('Comparing ' + name)
            predictions = [None] * len(trials)
            for tr, va in splits:
                x_train = np.concatenate([xs[i][:, indices] for i in tr])
                y_train = np.concatenate([np.repeat(y[i], len(xs[i])) for i in tr])
                model = clone(prototype).fit(x_train, y_train)
                for i in va:
                    predictions[i] = vote(model, xs[i][:, indices], cfg.agreement_threshold)
            report = metrics(y, predictions, active)
            report['out_of_fold'] = [dict(trial=trials[i][1]['id'], label=str(y[i]), **p) for i, p in enumerate(predictions)]
            reports[name] = report
            fitted[name] = clone(prototype).fit(np.concatenate([x[:, indices] for x in xs]),
                                               np.concatenate([np.repeat(y[i], len(x)) for i, x in enumerate(xs)]))
    # Predefined rule: select by all-trial CV accuracy, then macro F1; no test labels used.
    selected = sorted(reports, key=lambda k: (-reports[k]['accuracy'], -reports[k]['macro_f1'], k))[0]
    folder = Path(folder)
    version = f'{folder.parent.name}_{folder.name}_{len(active)}_gestures_{identifier()}'
    out = Path(folder) / 'models' / version
    out.mkdir(parents=True)
    manifest = dict(version=version, selected=selected, config=asdict(cfg), counts=counts,
                    labels=active, gesture_count=len(active),
                    scope=str(Path(folder).resolve()), source=trials[0][1].get('source', 'hardware'),
                    split_kind=split_kind, training_ids=[m['id'] for _, m, _ in trials],
                    folds=[dict(train=[trials[i][1]['id'] for i in tr],
                                validation=[trials[i][1]['id'] for i in va]) for tr, va in splits],
                    reports=reports)
    write_json(out / (version + '_validation.json'), manifest)
    bundle = dict(manifest=manifest, models=fitted)
    joblib.dump(bundle, out / (version + '_models.joblib'))
    write_json(Path(folder) / 'latest_model.json', {'version': version})
    return bundle


def load_latest(folder):
    import joblib
    version = json.loads((Path(folder) / 'latest_model.json').read_text())['version']
    if Path(version).name != version or '/' in version or '\\' in version:
        raise ValueError('Invalid model version path')
    # Only load files created by this app in your own dataset. joblib is not safe for untrusted files.
    directory = Path(folder) / 'models' / version
    named = directory / (version + '_models.joblib')
    return joblib.load(named if named.exists() else directory / 'models.joblib')


def manifest_path(folder, version):
    if Path(version).name != version or '/' in version or '\\' in version:
        raise ValueError('Invalid model version path')
    directory = Path(folder) / 'models' / version
    named = directory / (version + '_validation.json')
    return named if named.exists() else directory / 'validation.json'


def predict_trial(bundle, raw):
    """Deliberately has NO camera label, expected label, or table-selection argument."""
    cfg = Config(**bundle['manifest']['config'])
    x, _ = features(raw, cfg)
    if not len(x):
        raise ValueError('Not enough samples for prediction.')
    return {name: vote(model, x[:, SETS[name.split('__')[0]]], cfg.agreement_threshold)
            for name, model in bundle['models'].items()}


def predict_series(bundle, segments):
    """One result from all selected repetitions; no camera/reference label enters."""
    if not segments:
        raise ValueError('Record at least one repetition before the final test.')
    cfg = Config(**bundle['manifest']['config'])
    feature_rows = [features(raw, cfg)[0] for raw in segments]
    if any(not len(rows) for rows in feature_rows):
        raise ValueError('A repetition is too short for an analysis window.')
    combined = np.concatenate(feature_rows)
    return {name: vote(model, combined[:, SETS[name.split('__')[0]]],
                       cfg.agreement_threshold)
            for name, model in bundle['models'].items()}


def test_report(folder):
    """Separate reports per frozen model version; all reviewed valid tests retained."""
    groups = {}
    excluded = []
    for _, m, _ in load_trials(folder):
        if m['mode'] != 'test':
            continue
        if not m['reviewed'] or blocking_quality(m['quality']) or not m.get('predictions'):
            excluded.append(dict(trial=m['id'], quality=m['quality'], reviewed=m['reviewed']))
            continue
        protocol = m.get('capture', {}).get('selection_method', 'automatic')
        for name, pred in m['predictions'].items():
            pair = groups.setdefault((m['model_version'], name, protocol), ([], []))
            pair[0].append(m['label'])
            pair[1].append(pred)
    versions = {}
    for version, _, _ in groups:
        if version not in versions:
            path = manifest_path(folder, version)
            versions[version] = json.loads(path.read_text()).get('labels', LABELS) if path.exists() else LABELS
    report = dict(excluded=excluded, results=[dict(version=v, method=n, protocol=protocol,
                                                  **metrics(y, p, versions[v]))
                                            for (v, n, protocol), (y, p) in groups.items()])
    write_json(Path(folder) / 'test_results.json', report)
    for version in versions:
        directory = Path(folder) / 'models' / version
        if directory.exists():
            write_json(directory / (version + '_test_results.json'),
                       dict(version=version, labels=versions[version],
                            results=[r for r in report['results'] if r['version'] == version]))
    return report
