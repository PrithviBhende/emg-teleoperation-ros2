# COMPLETE EXPERIMENTAL & MODEL STUDY DATABASE — SURFACE EMG HAND GESTURE & GAZEBO SIMULATION (SUBJECT P01)

This database compiles all training, cross-validation, held-out test, manual test, confusion matrix, and Gazebo multi-model actuation data across every requested session folder under `1_final/data/P01/`, including the earlier `2026-11-09` placement `P3` (`3-gesture` & `4-gesture` runs) and the cross-session test evaluation of the newly trained 8-gesture model (`all fingers and gestures`) on `P01/P1`'s held-out test trials using the exact same selected ML model (`G_TF8__SVM`).

---

## 0. EXPERIMENTAL CONFIGURATION, FEATURE SETS, CLASSIFIERS & METRICS

### 0.1 Acquisition & Signal Processing Configuration (`config.py`, `signal.py`)
- **Acquisition Hardware**: 1-channel MyoWare 2.0 analogue EMG sensor sampled by an Arduino Due 12-bit ADC (`0–4095` counts, `3.3 V` reference) over USB serial (`115200 baud`) at fixed `sample_rate = 2000 Hz`.
- **Trial Windowing**: `pre_seconds = 0.35 s`, `post_seconds = 0.85 s` (`1.20 s` capture per reviewed trial, `camera_offset_seconds = 0.0 s`). Feature extraction slides a `250 ms` window (`500` samples) with `50 ms` hop (`100` samples), producing `20` windows per `1.20 s` trial.
- **Mean Removal**: `center_features = True` (window mean subtracted before feature calculation; raw ADC counts stored unmodified).
- **Digital Filtering**:
  - `digital_bandpass = False` across all studies (analogue front-end passband relied upon).
  - `notch_50hz = True` (2nd-order 50 Hz IIR notch filter, Q = 30) on **all `2026-11-09` (`P3`) and `2026-11-11` sessions** (`P4`, `P5`, `P6`, `P7`, `ring-little`, `P8`, `all fingers and gestures`).
  - `notch_50hz = False` on the earlier **2026-11-04 session (`P1`)**.
- **Quality & Exclusion Rules**:
  - Trials are excluded from training and scored test reports if unreviewed (`reviewed = False`), if they lack a complete duration/valid window, or if blocking acquisition errors occur (missing/duplicate sample sequence numbers, device timing discontinuity `> 0.15 ms`, or flat signal).
  - `max_clipped_fraction = 0.01` (`> 1.0%` samples at `ADC <= 1` or `>= 4094`). Clipping triggers a warning rather than automatic blocking if reviewed, unless paired with unreviewed/incomplete-duration flags.

### 0.2 Feature Sets (`SETS` in `signal.py` — 15 total features)
1. **`A_RMS`** (1 feature): Root Mean Square (`RMS`)
2. **`B_MAV`** (1 feature): Mean Absolute Value (`MAV`)
3. **`C_WL`** (1 feature): Waveform Length (`WL`, cumulative absolute sample-to-sample difference)
4. **`D_TD4`** (4 features): Hudgins time-domain features (`MAV`, `WL`, `ZC` zero crossings, `SSC` slope sign changes; `crossing_threshold_counts = 3.0` counts)
5. **`E_ALL5`** (5 features): `RMS`, `MAV`, `WL`, `ZC`, `SSC`
6. **`F_MAV_MAX_MIN`** (3 features): `MAV`, window maximum (`MAX`), window minimum (`MIN`)
7. **`G_TF8`** (8 features): Time-frequency spectral log power (`log1p` of normalised Hanning-windowed FFT power) in 4 bands (`20–80 Hz`, `80–150 Hz`, `150–250 Hz`, `250–450 Hz`) computed separately on the **early half** and **late half** of each `250 ms` window (`4 bands x 2 halves = 8 features`).
   *(Note: `G_TF8` did not exist yet in the older `2026-11-04` `P01/P1` baseline build, which evaluated 18 models `A–F`; all `2026-11-09` (`P3`) and `2026-11-11` studies evaluated all 21 models `A–G`.)*

### 0.3 Classifiers & Model Selection (`ml.py`)
All classifiers run inside `sklearn.pipeline.make_pipeline(StandardScaler(), classifier)`:
- **`LDA`**: `LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')`
- **`SVM`**: `SVC(C=1.0, kernel='rbf', gamma='scale')`
- **`KNN`**: `KNeighborsClassifier(n_neighbors=5, weights='distance')`
- **Cross-Validation (`cv_folds = 3`, `seed = 42`)**: 3-fold `StratifiedKFold` over **held-out whole trials** (`split_kind = "held-out whole trials; NOT proof of cross-session generalisation"` because fewer than 3 distinct complete sessions existed per class).
- **Automatic Selection Rule**: All 21 models are ranked by `(-CV accuracy, -CV macro_f1, model_name)`. Test labels never participate in model selection or scaling.

### 0.4 Exact Evaluation Metrics (`ml.py`)
- **Trial Prediction**: Majority vote of window predictions across the 20 windows in a trial.
- **Rejection Gate (`agreement_threshold = 0.60`)**: A prediction is **accepted** only if there is no top-vote tie and the winning class has at least `60%` (`>= 12/20`) of window votes.
- **Accuracy (Percentage of Correct Prediction)**: `(Total correct majority-vote trials) / (Total evaluated trials) * 100%` (computed across ALL valid reviewed trials regardless of rejection).
- **Macro-F1**: Unweighted mean F1 across the study's gesture label list. *(Important note: in test batches where one trained class has `0` test trials, e.g. `rest` missing in `P3 (3-gest)`, `P8`, and `P1`, sklearn includes that zero-count label with `F1 = 0`, depressing macro-F1 relative to overall accuracy.)*
- **Coverage**: `(Accepted trials) / (Total evaluated trials) * 100%`.
- **Accepted Accuracy**: `(Correct accepted trials) / (Accepted trials) * 100%`.
- **Overall Success (`success_all_attempts`)**: `(Trials both accepted AND correct) / (Total evaluated trials) * 100%`.
- **Gazebo Multi-Model Demonstration Trigger (`gui.py`)**: On all `2026-11-11` sessions (`P4`–`P8`, `all fingers`), after each camera-reviewed `test` trial, Gazebo InMoov hand actuation triggers if **at least 1 of the 3 models** (`LDA`, `SVM`, `KNN`) in the selected feature set matches the camera label (or if the selected model matches). Percentages for both `>= 1/3` match and `3/3` unanimous match are reported separately from autonomous EMG-only classifier accuracy. *(For the earlier `2026-11-09` `P01/P3` session, which pre-dated the `2026-11-11` Gazebo bridge and logged `simulation_only: True` 2D canvas commands, the table reports offline `>= 1/3` and `3/3` multi-model agreement computed across the 3 classifiers in `P3`'s selected feature family.)*

### 0.5 Important Note on Root `test_results.json` vs Model-Version `<version>_test_results.json`
In folders `P3`, `P5`, `P6`, `P7`, and `P8`, multiple model versions or trials copied forward from earlier runs still carry their original `model_version` tag (`P3 3-gest`, `P4`, or `P5`), so the folder-level `test_results.json` lists multiple separate per-version evaluation blocks. Each `<version>_test_results.json` file (used in all comparative tables below) isolates **only the held-out test trials actually evaluated by that study's frozen model version**.

---

## 1. MASTER COMPARATIVE TABLE ACROSS ALL STUDIES

| # | Gesture Combination (`N` classes) | Session Folder(s) | Model Version ID | Train Trials (`N`) | Selected ML Model | 3-Fold CV Acc (%) | CV Macro-F1 | CV Cov (%) | CV Accepted Acc (%) | Held-Out Test Trials (`N`) | Selected Model Test Acc (%) | Test Macro-F1 | Test Cov (%) | Test Accepted Acc (%) | Best Test Model (if different) & Acc (%) | Gazebo `>=1/3` Match (`3/3` Match) |
|---|---|---|---|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---:|
| **1** | **`rest, index, fist`** (3) | `P01/P4` | `P01_P4_3_gestures_20261111T135651_48a46e02` | 60 (`20/class`) | **`A_RMS__KNN`** | **100.00%** (`60/60`) | 1.0000 | 100.00% | 100.00% | 10 (`4 rest, 3 index, 3 fist`) | **100.00%** (`10/10`) | 1.0000 | 100.00% | 100.00% | Tied with 17 other models at **100.00%** | 10/10 (`100.0%`) / `100.0%` |
| **2** | **`rest, middle, fist`** (3) | `P01/P5` | `P01_P5_3_gestures_20261111T142409_35232df9` | 60 (`20/class`; `rest` & `fist` reused from `P4`) | **`B_MAV__KNN`** | **100.00%** (`60/60`) | 1.0000 | 98.33% | 100.00% | 10 (`3 rest, 4 middle, 3 fist`) | **100.00%** (`10/10`) | 1.0000 | 100.00% | 100.00% | Tied with 18 other models at **100.00%** | 10/10 (`100.0%`) / `100.0%` |
| **3** | **`ring, little`** (2 — hard adjacent pair) | `P01/P7` (2-gest) & `P01/ring-little` | `P01_P7_2_gestures_20261111T155532_1bf387dd` | 40 (`20/class`) | **`C_WL__KNN`** | **70.00%** (`28/40`) | 0.6875 | 62.50% | 76.00% | 16 (`8 ring, 8 little`) | **50.00%** (`8/16`) | 0.5000 | 43.75% | 28.57% | `F_MAV_MAX_MIN__SVM`: **68.75%** (`11/16`, `77.78%` acc-acc) | 13/16 (`81.2%`) / `6.2%` (`1/16`) |
| **4** | **`middle, ring, little`** (3 — adjacent ulnar/central digits) | `P01/P7` (3-gest) | `P01_P7_3_gestures_20261111T160322_48965968` | 60 (`20/class`) | **`D_TD4__LDA`** | **76.67%** (`46/60`) | 0.7613 | 85.00% | 80.39% | 14 (`4 middle, 2 ring, 8 little`) | **35.71%** (`5/14`) | 0.3883 | 100.00% | 35.71% | **`G_TF8__KNN`: 92.86%** (`13/14`, `100.00%` acc-acc); `A_RMS__SVM`/`B_MAV__LDA`/`C_WL__SVM`: **85.71%** (`12/14`) | 7/14 (`50.0%`) / `35.7%` (`5/14`) |
| **5** | **`rest, thumb, index, middle, fist`** (5) | `P01/P6` | `P01_P6_5_gestures_20261111T144541_0cfdf8bc` | 100 (`20/class`) | **`G_TF8__SVM`** | **98.00%** (`98/100`) | 0.9799 | 90.00% | 100.00% | 45 (`6 rest, 12 thumb, 12 index, 10 middle, 5 fist`) | **86.67%** (`39/45`) | 0.8852 | 66.67% | 93.33% | Tied at **86.67%**: `G_TF8__KNN` (`100%` acc-acc) & `D_TD4__SVM` | 41/45 (`91.1%`) / `73.3%` (`33/45`) |
| **6** | **`rest, thumb, index, pinch, fist`** (5) | `P01/P8` | `P01_P8_5_gestures_20261111T161220_c752da28` | 100 (`20/class`) | **`G_TF8__SVM`** | **90.00%** (`90/100`) | 0.8975 | 69.00% | 100.00% | 26 (`0 rest, 7 thumb, 7 index, 5 pinch, 7 fist`) | **92.31%** (`24/26`) | 0.7379 *(missing `rest`)* | 50.00% | **100.00%** (`13/13`) | **`G_TF8__SVM` is highest among all 21 models** (`F_MAV_MAX_MIN__SVM/KNN`: `80.77%`) | 25/26 (`96.2%`) / `61.5%` (`16/26`) |
| **7** | **All 8 gestures: `rest, thumb, index, middle, ring, little, pinch, fist`** (Train = `2026-11-11`, Test = `P01/P1` `2026-11-04` cross-day) | Train: `P01/all fingers and gestures` (from `P02/P3`); Test: `P01/P1` | `P02_P3_8_gestures_20261111T165458_12def92b` | 161 (`21 index`, `20` each other class) | **`G_TF8__SVM`** | **76.40%** (`123/161`) | 0.7556 | 43.48% | **100.00%** (`70/70`) | 33 (`P01/P1` valid test trials: `0 rest, 3 thumb, 8 index, 6 middle, 5 ring, 4 little, 1 pinch, 6 fist`) | **42.42%** (`14/33`) *(cross-day eval using `G_TF8__SVM`)* | 0.2602 | 39.39% | 46.15% (`6/13`) | Tied at **42.42%** (`F_MAV_MAX_MIN__KNN`) | 15/33 (`45.5%`) (`G_TF8` family on `P1`) |
| **Ref** | *Original `P01/P1` baseline (`2026-11-04`, same-day, `notch=False`, 18 models `A–F` only)* | `P01/P1` | `20261104T145018_5dd187af` | 136 (`18 thumb, 16 pinch, 17` others) | `E_ALL5__SVM` | **72.79%** (`99/136`) | 0.7122 | 63.97% | 82.76% | 33 (same 33 `P01/P1` test trials) | **36.36%** (`12/33`) | 0.2425 | 54.55% | 27.78% (`5/18`) | Tied at **36.36%**: `E_ALL5__LDA` & `D_TD4__SVM` | 12/33 (`36.4%`) / `24.2%` (`8/33`) |
| **8** | **`rest, index, fist`** (3 — `2026-11-09` earlier placement) | `P01/P3` (3-gest) | `P01_P3_3_gestures_20261109T184600_eb8894dc` | 60 (`20/class`) | **`C_WL__KNN`** | **100.00%** (`60/60`) | 1.0000 | 98.33% | 100.00% | 5 (`0 rest, 3 index, 2 fist`) | **100.00%** (`5/5`) | 0.6667 *(missing `rest`)* | 100.00% | 100.00% | Tied across all 21 models at **100.00%** | 5/5 (`100.0%`) / `100.0%` *(2026-11-09 2D sim; offline `C_WL`)* |
| **9a** | **`rest, thumb, index, fist`** (4 — `2026-11-09` 30-trial same-session benchmark) | `P01/P3` (4-gest archived) | `P01_P3_4_gestures_20261109T190452_852a6598` | 80 (`20/class`) | **`G_TF8__SVM`** | **96.25%** (`77/80`) | 0.9623 | 86.25% | 98.55% (`68/69`) | 30 (`6 rest, 15 thumb, 6 index, 3 fist` — Nov 9) | **83.33%** (`25/30`) | 0.8765 | 63.33% | **100.00%** (`19/19`) | **`F_MAV_MAX_MIN__KNN`: 90.00%** (`27/30`, `95.00%` acc-acc); `F_MAV_MAX_MIN__SVM`: **86.67%** (`26/30`) | 27/30 (`90.0%`) / `66.7%` (`20/30`) *(2026-11-09 2D sim; offline `G_TF8`)* |
| **9b** | **`rest, thumb, index, fist`** (4 — all in-scope `N=55` & live report `N=61` w/ 6 probes) | `P01/P3` (4-gest live) | `P01_P3_4_gestures_20261109T190452_852a6598` | 80 (`20/class`) | **`G_TF8__SVM`** | **96.25%** (`77/80`) | 0.9623 | 86.25% | 98.55% (`68/69`) | 55 in-scope (`45` Nov 9 + `10` Nov 11: `7 rest, 30 thumb, 11 index, 7 fist`) / 61 live (`+6` out-of-scope probes) | **67.27%** (`37/55` in-scope) / **60.66%** (`37/61` live) | 0.7543 (`N=55`) / 0.3508 (`N=61`, 8-lbl) | 60.00% (`N=55`) / 57.38% (`N=61`) | 87.88% (`29/33`) / 82.86% (`29/35`) | **`F_MAV_MAX_MIN__SVM` & `KNN`: 87.27%** (`48/55` in-scope) / **78.69%** (`48/61` live) | 43/55 (`78.2%`) / `56.4%` (`31/55`) in-scope; 43/61 (`70.5%`) / `50.8%` live *(offline `G_TF8`)* |

---

## 2. INDIVIDUAL STUDY DATABASES (ALL 21 MODELS, CONFUSION MATRICES & SESSION LOGS)

---

### STUDY 1: `rest, index, fist` (3 Gestures) — `P01/P4`

- **Model Version**: `P01_P4_3_gestures_20261111T135651_48a46e02`
- **Selected Model**: **`A_RMS__KNN`** (`notch_50hz = True`, `digital_bandpass = False`, `agreement_threshold = 0.60`, `3-fold CV`)
- **Dataset Inventory**: `101` total trial directories (`2026-11-11 12:23:34` to `14:12:57`):
  - Reviewed valid training trials (`N = 60`): `rest: 20, index: 20, fist: 20`.
  - Unreviewed training trials (`30`): `rest: 14, index: 5, fist: 5, thumb: 2, ring: 2, middle: 1, little: 1`.
  - Reviewed valid test trials (`N = 10`): `rest: 4, index: 3, fist: 3`.
  - Unreviewed/excluded test trials: `1` unreviewed `fist` trial (`20261111T141216_e99d3cf1`, flagged with `ADC clipping: 83/2401 samples (3.5%) at the ADC limit; allowed 1.0%`, listed under `excluded` in root `test_results.json`, `0` excluded inside model-dir `test_results.json`).
  - Attempt events (`attempt_events.jsonl`): `16` stopped/timeout in `train`, `1` in `test`.
- **Gazebo Actuation (`P4`)**:
  - `simulation_commands.jsonl`: `10` commands (`fist, index, rest, index, fist, rest, index, fist, rest, rest`).
  - Multi-model agreement in `A_RMS` (`LDA`, `SVM`, `KNN`): `10/10` (`100.0%`) had `>= 1/3` model match, and `10/10` (`100.0%`) had `3/3` unanimous match.

#### Selected Model (`A_RMS__KNN`) Confusion Matrices — `P01/P4`
- **3-Fold CV (`N = 60`, `100.00%`, `cov = 100.00%`, `acc_acc = 100.00%`)**:
  - `rest` (`20`): `[20, 0, 0]` -> recall `100.0%`
  - `index` (`20`): `[0, 20, 0]` -> recall `100.0%`
  - `fist` (`20`): `[0, 0, 20]` -> recall `100.0%`
- **Held-Out Test (`N = 10`, `100.00%`, `cov = 100.00%`, `acc_acc = 100.00%`)**:
  - `rest` (`4`): `[4, 0, 0]` -> recall `100.0%`
  - `index` (`3`): `[0, 3, 0]` -> recall `100.0%`
  - `fist` (`3`): `[0, 0, 3]` -> recall `100.0%`

#### All 21 Models — `P01/P4` (`CV N = 60`, `Test N = 10`)
| Model | Val Acc (%) | Val F1 | Val Cov (%) | Val Suc (%) | Val Acc-Acc (%) | Test Acc (%) | Test F1 | Test Cov (%) | Test Suc (%) | Test Acc-Acc (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `A_RMS__LDA` | 98.33% | 0.9833 | 100.00% | 98.33% | 98.33% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `A_RMS__SVM` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| **`A_RMS__KNN` *(SELECTED)*** | **100.00%** | **1.0000** | **100.00%** | **100.00%** | **100.00%** | **100.00%** | **1.0000** | **100.00%** | **100.00%** | **100.00%** |
| `B_MAV__LDA` | 98.33% | 0.9833 | 100.00% | 98.33% | 98.33% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `B_MAV__SVM` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `B_MAV__KNN` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `C_WL__LDA` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `C_WL__SVM` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `C_WL__KNN` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 70.00% | 0.6690 | 70.00% | 70.00% | 100.00% |
| `D_TD4__LDA` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 80.00% | 0.8056 | 90.00% | 80.00% | 88.89% |
| `D_TD4__SVM` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `D_TD4__KNN` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `E_ALL5__LDA` | 100.00% | 1.0000 | 98.33% | 98.33% | 100.00% | 80.00% | 0.8056 | 90.00% | 80.00% | 88.89% |
| `E_ALL5__SVM` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `E_ALL5__KNN` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `F_MAV_MAX_MIN__LDA` | 95.00% | 0.9497 | 98.33% | 93.33% | 94.92% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `F_MAV_MAX_MIN__SVM` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `F_MAV_MAX_MIN__KNN` | 98.33% | 0.9833 | 98.33% | 98.33% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `G_TF8__LDA` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `G_TF8__SVM` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `G_TF8__KNN` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |

---

### STUDY 2: `rest, middle, fist` (3 Gestures) — `P01/P5`

- **Model Version**: `P01_P5_3_gestures_20261111T142409_35232df9`
- **Selected Model**: **`B_MAV__KNN`** *(note: tied at `100.00%` CV accuracy and `1.0000` F1 with `C_WL__LDA`, `D_TD4__SVM`, `E_ALL5__SVM`, `G_TF8__LDA/SVM/KNN`; `B_MAV__KNN` won alphabetical tie-break even though `G_TF8__LDA` had `100.00%` CV coverage vs `B_MAV__KNN`'s `98.33%`)*.
- **Dataset Inventory**: `99` trial directories (`2026-11-11 12:23:34` to `14:27:34`):
  - Reviewed valid training trials (`N = 60`): `rest: 20, middle: 20, fist: 20` (`rest` & `fist` copied from `P4`; `middle` recorded for `P5`).
  - Unreviewed training trials (`21`): `rest: 14, fist: 5, middle: 2`.
  - Reviewed valid test trials (`17` total in folder): `10` evaluated by `P5`'s model (`middle: 4, fist: 3, rest: 3`) plus `7` earlier `P4`-version test trials (`fist: 3, rest: 4` appearing as a separate `n=7` block in root `test_results.json`).
  - Unreviewed test: `1` `fist` trial (`20261111T141216_e99d3cf1`, `3.5%` ADC clipping excluded in root `test_results.json`).
  - Attempt events: `5` stopped/timeout in `train`, `4` in `test`.
- **Gazebo Actuation (`P5`)**:
  - `simulation_commands.jsonl`: `10` commands (`middle, fist, fist, fist, middle, middle, middle, rest, rest, rest`).
  - Multi-model `B_MAV` (`LDA`, `SVM`, `KNN`) agreement on `n=10` `P5` test trials: `10/10` (`100.0%`) `>= 1/3` and `10/10` (`100.0%`) `3/3`.

#### Selected Model (`B_MAV__KNN`) Confusion Matrices — `P01/P5`
- **3-Fold CV (`N = 60`, `100.00%`, `cov = 98.33%`, `acc_acc = 100.00%`)**:
  - `rest` (`20`): `[20, 0, 0]` -> recall `100.0%`
  - `middle` (`20`): `[0, 20, 0]` -> recall `100.0%`
  - `fist` (`20`): `[0, 0, 20]` -> recall `100.0%`
- **Held-Out Test (`N = 10`, `100.00%`, `cov = 100.00%`, `acc_acc = 100.00%`)**:
  - `rest` (`3`): `[3, 0, 0]` -> recall `100.0%`
  - `middle` (`4`): `[0, 4, 0]` -> recall `100.0%`
  - `fist` (`3`): `[0, 0, 3]` -> recall `100.0%`

#### All 21 Models — `P01/P5` (`CV N = 60`, `Test N = 10`)
| Model | Val Acc (%) | Val F1 | Val Cov (%) | Val Suc (%) | Val Acc-Acc (%) | Test Acc (%) | Test F1 | Test Cov (%) | Test Suc (%) | Test Acc-Acc (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `A_RMS__LDA` | 98.33% | 0.9833 | 95.00% | 95.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `A_RMS__SVM` | 96.67% | 0.9666 | 98.33% | 96.67% | 98.31% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `A_RMS__KNN` | 96.67% | 0.9666 | 93.33% | 91.67% | 98.21% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `B_MAV__LDA` | 98.33% | 0.9833 | 95.00% | 95.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `B_MAV__SVM` | 98.33% | 0.9833 | 95.00% | 95.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| **`B_MAV__KNN` *(SELECTED)*** | **100.00%** | **1.0000** | **98.33%** | **98.33%** | **100.00%** | **100.00%** | **1.0000** | **100.00%** | **100.00%** | **100.00%** |
| `C_WL__LDA` | 100.00% | 1.0000 | 98.33% | 98.33% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `C_WL__SVM` | 98.33% | 0.9833 | 100.00% | 98.33% | 98.33% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `C_WL__KNN` | 98.33% | 0.9833 | 100.00% | 98.33% | 98.33% | 80.00% | 0.7500 | 100.00% | 80.00% | 80.00% |
| `D_TD4__LDA` | 98.33% | 0.9833 | 93.33% | 93.33% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `D_TD4__SVM` | 100.00% | 1.0000 | 98.33% | 98.33% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `D_TD4__KNN` | 98.33% | 0.9833 | 98.33% | 98.33% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `E_ALL5__LDA` | 98.33% | 0.9833 | 93.33% | 93.33% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `E_ALL5__SVM` | 100.00% | 1.0000 | 98.33% | 98.33% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `E_ALL5__KNN` | 98.33% | 0.9833 | 98.33% | 98.33% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `F_MAV_MAX_MIN__LDA` | 98.33% | 0.9833 | 93.33% | 91.67% | 98.21% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `F_MAV_MAX_MIN__SVM` | 98.33% | 0.9833 | 96.67% | 96.67% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `F_MAV_MAX_MIN__KNN` | 98.33% | 0.9833 | 95.00% | 93.33% | 98.25% | 90.00% | 0.9048 | 90.00% | 90.00% | 100.00% |
| `G_TF8__LDA` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `G_TF8__SVM` | 100.00% | 1.0000 | 98.33% | 98.33% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |
| `G_TF8__KNN` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% |

---

### STUDY 3: `ring, little` (2 Gestures — Adjacent Finger Overlap) — `P01/P7` (2-gesture run) & `P01/ring-little`

- **Relationship Between Folders**: `1_final/data/P01/ring-little` contains an exact copy of model `P01_P7_2_gestures_20261111T155532_1bf387dd` from `P01/P7`, with identical validation (`N=40`) and test (`N=16`) reports (`ring-little/simulation_commands.jsonl` stores `13` dispatches for this run: `little` & `ring`; raw trials remain in `P01/P7/trials`).
- **Selected Model**: **`C_WL__KNN`** (`notch_50hz = True`).
- **Training Class Counts (`N = 40`)**: `ring: 20, little: 20`.
- **Held-Out Test (`N = 16`)**: `ring: 8, little: 8`; `0` excluded.
- **Gazebo Multi-Model (`C_WL` LDA/SVM/KNN on `n=16` in `P7`)**: `13/16` (`81.2%`) had `>= 1/3` match, but only `1/16` (`6.2%`) had `3/3` agreement — extreme disagreement across classifiers.
- **Confusion Matrices**:
  - **Selected `C_WL__KNN` CV (`N = 40`, `70.00%`, `cov = 62.50%`, `acc_acc = 76.00%`)**:
    - `ring` (`20`): `[10, 10]` -> recall `50.0%` (`10` confused as `little`)
    - `little` (`20`): `[2, 18]` -> recall `90.0%` (`2` confused as `ring`)
  - **Selected `C_WL__KNN` Test (`N = 16`, `50.00%` — chance level, `cov = 43.75%`, `acc_acc = 28.57%`)**:
    - `ring` (`8`): `[4, 4]` -> recall `50.0%`
    - `little` (`8`): `[4, 4]` -> recall `50.0%`
  - **Best Test Model `F_MAV_MAX_MIN__SVM` (`N = 16`, `68.75%`, `cov = 56.25%`, `acc_acc = 77.78%`)**:
    - `ring` (`8`): `[6, 2]` -> recall `75.0%`
    - `little` (`8`): `[3, 5]` -> recall `62.5%`

#### All 21 Models — `P01/P7 (2-gesture)` & `P01/ring-little` (`CV N = 40`, `Test N = 16`)
| Model | Val Acc (%) | Val F1 | Val Cov (%) | Val Suc (%) | Val Acc-Acc (%) | Test Acc (%) | Test F1 | Test Cov (%) | Test Suc (%) | Test Acc-Acc (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `A_RMS__LDA` | 45.00% | 0.4444 | 85.00% | 40.00% | 47.06% | 37.50% | 0.2727 | 81.25% | 25.00% | 30.77% |
| `A_RMS__SVM` | 55.00% | 0.5055 | 92.50% | 50.00% | 54.05% | 50.00% | 0.4667 | 75.00% | 43.75% | 58.33% |
| `A_RMS__KNN` | 50.00% | 0.4949 | 47.50% | 15.00% | 31.58% | 56.25% | 0.5466 | 68.75% | 37.50% | 54.55% |
| `B_MAV__LDA` | 47.50% | 0.4720 | 92.50% | 45.00% | 48.65% | 37.50% | 0.2727 | 75.00% | 25.00% | 33.33% |
| `B_MAV__SVM` | 45.00% | 0.3956 | 85.00% | 35.00% | 41.18% | 43.75% | 0.3043 | 81.25% | 43.75% | 53.85% |
| `B_MAV__KNN` | 47.50% | 0.4667 | 62.50% | 30.00% | 48.00% | 43.75% | 0.4170 | 56.25% | 31.25% | 55.56% |
| `C_WL__LDA` | 50.00% | 0.4987 | 85.00% | 45.00% | 52.94% | 31.25% | 0.3098 | 68.75% | 18.75% | 27.27% |
| `C_WL__SVM` | 42.50% | 0.4068 | 67.50% | 30.00% | 44.44% | 50.00% | 0.3333 | 100.00% | 50.00% | 50.00% |
| **`C_WL__KNN` *(SELECTED)*** | **70.00%** | **0.6875** | **62.50%** | **47.50%** | **76.00%** | **50.00%** | **0.5000** | **43.75%** | **12.50%** | **28.57%** |
| `D_TD4__LDA` | 67.50% | 0.6698 | 87.50% | 62.50% | 71.43% | 56.25% | 0.5152 | 93.75% | 50.00% | 53.33% |
| `D_TD4__SVM` | 67.50% | 0.6647 | 92.50% | 65.00% | 70.27% | 56.25% | 0.5466 | 87.50% | 43.75% | 50.00% |
| `D_TD4__KNN` | 65.00% | 0.6419 | 80.00% | 50.00% | 62.50% | 43.75% | 0.4170 | 62.50% | 31.25% | 50.00% |
| `E_ALL5__LDA` | 67.50% | 0.6698 | 87.50% | 62.50% | 71.43% | 56.25% | 0.5152 | 87.50% | 43.75% | 50.00% |
| `E_ALL5__SVM` | 67.50% | 0.6647 | 95.00% | 65.00% | 68.42% | 50.00% | 0.4667 | 87.50% | 50.00% | 57.14% |
| `E_ALL5__KNN` | 62.50% | 0.6132 | 80.00% | 52.50% | 65.62% | 50.00% | 0.4921 | 68.75% | 37.50% | 54.55% |
| `F_MAV_MAX_MIN__LDA` | 65.00% | 0.6465 | 77.50% | 47.50% | 61.29% | 56.25% | 0.5608 | 75.00% | 37.50% | 50.00% |
| **`F_MAV_MAX_MIN__SVM` *(BEST TEST)*** | 55.00% | 0.5312 | 82.50% | 42.50% | 51.52% | **68.75%** | **0.6863** | **56.25%** | **43.75%** | **77.78%** |
| `F_MAV_MAX_MIN__KNN` | 42.50% | 0.3571 | 55.00% | 25.00% | 45.45% | 62.50% | 0.6250 | 62.50% | 43.75% | 70.00% |
| `G_TF8__LDA` | 47.50% | 0.4747 | 72.50% | 35.00% | 48.28% | 50.00% | 0.4667 | 75.00% | 43.75% | 58.33% |
| `G_TF8__SVM` | 57.50% | 0.5683 | 67.50% | 40.00% | 59.26% | 50.00% | 0.4921 | 81.25% | 37.50% | 46.15% |
| `G_TF8__KNN` | 47.50% | 0.4747 | 50.00% | 25.00% | 50.00% | 43.75% | 0.4353 | 56.25% | 37.50% | 66.67% |

---

### STUDY 4: `middle, ring, little` (3 Gestures) — `P01/P7` (3-gesture run)

- **Model Version**: `P01_P7_3_gestures_20261111T160322_48965968`
- **Dataset Inventory (`P01/P7`)**: `104` total trial directories (`2026-11-11 14:15:09` to `16:06:49`): `60` reviewed valid train (`middle: 20, ring: 20, little: 20`), `10` unreviewed train (`middle: 2, ring: 4, little: 3, rest: 1`), `34` reviewed test total (`4` inherited `middle` from `P5`, `16` from `P7 2-gesture`, `14` from `P7 3-gesture`), `0` excluded; `5` train & `2` test stopped/timeout events. `20` Gazebo commands in `P7/simulation_commands.jsonl`.
- **Selected Model**: **`D_TD4__LDA`** *(selected over `D_TD4__SVM`, `E_ALL5__LDA`, `E_ALL5__KNN`, all tied at `76.67%` CV accuracy, via highest `macro_f1 = 0.7613`)*.
- **Gazebo Multi-Model (`D_TD4` LDA/SVM/KNN on `n=14`)**: `7/14` (`50.0%`) `>= 1/3` matched; `5/14` (`35.7%`) `3/3` matched.
- **Confusion Matrices & Critical Generalisation Contrast**:
  - **Selected `D_TD4__LDA` CV (`N = 60`, `76.67%`, `cov = 85.00%`, `acc_acc = 80.39%`)**:
    - `middle` (`20`): `[20, 0, 0]` -> `100.0%` recall (cleanly separated from `ring/little`)
    - `ring` (`20`): `[0, 10, 10]` -> `50.0%` recall (`10` confused as `little`)
    - `little` (`20`): `[0, 4, 16]` -> `80.0%` recall (`4` confused as `ring`)
  - **Selected `D_TD4__LDA` Test (`N = 14`, `4 middle, 2 ring, 8 little` -> `35.71%`, `cov = 100.00%`, `acc_acc = 35.71%`)**:
    - `middle` (`4`): `[3, 1, 0]` -> `75.0%`
    - `ring` (`2`): `[0, 2, 0]` -> `100.0%`
    - `little` (`8`): `[0, 8, 0]` -> **`0.0%` recall (all 8 `little` trials misclassified as `ring`!)**
  - **Best Test Model `G_TF8__KNN` (`N = 14` -> `92.86%` (`13/14`), `F1 = 0.9111`, `cov = 64.29%`, `acc_acc = 100.00%` (`9/9`))**:
    - `middle` (`4`): `[4, 0, 0]` -> `100.0%`
    - `ring` (`2`): `[0, 2, 0]` -> `100.0%`
    - `little` (`8`): `[0, 1, 7]` -> `87.5%`
    - *(Also `A_RMS__SVM`, `B_MAV__LDA`, and `C_WL__SVM` reached `85.71%` (`12/14`). `D_TD4__LDA` overfit in-session CV relative to test shift, whereas `G_TF8__KNN` preserved `ring` vs `little` separation online despite lower CV (`63.33%`).)*

#### All 21 Models — `P01/P7 (3-gesture)` (`CV N = 60`, `Test N = 14`)
| Model | Val Acc (%) | Val F1 | Val Cov (%) | Val Suc (%) | Val Acc-Acc (%) | Test Acc (%) | Test F1 | Test Cov (%) | Test Suc (%) | Test Acc-Acc (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `A_RMS__LDA` | 58.33% | 0.5876 | 90.00% | 53.33% | 59.26% | 78.57% | 0.5820 | 57.14% | 50.00% | 87.50% |
| `A_RMS__SVM` | 63.33% | 0.6181 | 93.33% | 60.00% | 64.29% | 85.71% | 0.8042 | 78.57% | 71.43% | 90.91% |
| `A_RMS__KNN` | 63.33% | 0.6249 | 41.67% | 33.33% | 80.00% | 42.86% | 0.4286 | 35.71% | 28.57% | 80.00% |
| `B_MAV__LDA` | 56.67% | 0.5738 | 91.67% | 55.00% | 60.00% | 85.71% | 0.7661 | 64.29% | 57.14% | 88.89% |
| `B_MAV__SVM` | 63.33% | 0.6181 | 88.33% | 55.00% | 62.26% | 78.57% | 0.5664 | 92.86% | 78.57% | 84.62% |
| `B_MAV__KNN` | 71.67% | 0.7151 | 43.33% | 38.33% | 88.46% | 71.43% | 0.6690 | 57.14% | 42.86% | 75.00% |
| `C_WL__LDA` | 58.33% | 0.5633 | 91.67% | 56.67% | 61.82% | 50.00% | 0.5265 | 64.29% | 42.86% | 66.67% |
| `C_WL__SVM` | 66.67% | 0.5512 | 96.67% | 65.00% | 67.24% | 85.71% | 0.6296 | 85.71% | 78.57% | 91.67% |
| `C_WL__KNN` | 71.67% | 0.6935 | 55.00% | 46.67% | 84.85% | 64.29% | 0.6337 | 28.57% | 28.57% | 100.00% |
| **`D_TD4__LDA` *(SELECTED)*** | **76.67%** | **0.7613** | **85.00%** | **68.33%** | **80.39%** | **35.71%** | **0.3883** | **100.00%** | **35.71%** | **35.71%** |
| `D_TD4__SVM` | 76.67% | 0.7511 | 85.00% | 68.33% | 80.39% | 50.00% | 0.5286 | 85.71% | 35.71% | 41.67% |
| `D_TD4__KNN` | 73.33% | 0.7156 | 65.00% | 56.67% | 87.18% | 50.00% | 0.5286 | 78.57% | 42.86% | 54.55% |
| `E_ALL5__LDA` | 76.67% | 0.7613 | 85.00% | 68.33% | 80.39% | 35.71% | 0.3883 | 100.00% | 35.71% | 35.71% |
| `E_ALL5__SVM` | 75.00% | 0.7261 | 85.00% | 66.67% | 78.43% | 50.00% | 0.5286 | 85.71% | 35.71% | 41.67% |
| `E_ALL5__KNN` | 76.67% | 0.7479 | 71.67% | 63.33% | 88.37% | 64.29% | 0.6633 | 57.14% | 28.57% | 50.00% |
| `F_MAV_MAX_MIN__LDA` | 65.00% | 0.6507 | 76.67% | 51.67% | 67.39% | 50.00% | 0.5229 | 57.14% | 35.71% | 62.50% |
| `F_MAV_MAX_MIN__SVM` | 73.33% | 0.7306 | 83.33% | 63.33% | 76.00% | 71.43% | 0.7143 | 71.43% | 50.00% | 70.00% |
| `F_MAV_MAX_MIN__KNN` | 70.00% | 0.6931 | 70.00% | 58.33% | 83.33% | 64.29% | 0.6190 | 50.00% | 42.86% | 85.71% |
| `G_TF8__LDA` | 68.33% | 0.6664 | 78.33% | 55.00% | 70.21% | 64.29% | 0.6337 | 57.14% | 42.86% | 75.00% |
| `G_TF8__SVM` | 65.00% | 0.6313 | 78.33% | 58.33% | 74.47% | 78.57% | 0.7333 | 50.00% | 50.00% | 100.00% |
| **`G_TF8__KNN` *(BEST TEST)*** | 63.33% | 0.6249 | 58.33% | 48.33% | 82.86% | **92.86%** | **0.9111** | **64.29%** | **64.29%** | **100.00%** |

---

### STUDY 5: `rest, thumb, index, middle, fist` (5 Gestures) — `P01/P6`

- **Model Version**: `P01_P6_5_gestures_20261111T144541_0cfdf8bc`
- **Selected Model**: **`G_TF8__SVM`** (`notch_50hz = True`).
- **Dataset Inventory**: `195` total trial directories (`2026-11-11 12:23:34` to `14:56:06`):
  - Reviewed valid training trials (`N = 100`): `rest: 20, thumb: 20, index: 20, middle: 20, fist: 20`.
  - Unreviewed training trials (`32`): `rest: 14, index: 5, fist: 5, middle: 3, thumb: 2, ring: 2, little: 1`.
  - Reviewed valid test trials (`59` total in folder): `45` evaluated by `P6`'s model (`index: 12, thumb: 12, middle: 10, rest: 6, fist: 5`), plus `10` earlier `P4` trials and `4` earlier `P5` `middle` trials appearing in root `test_results.json`.
  - Excluded in root `test_results.json`: `4` unreviewed test trials (including `20261111T141216_e99d3cf1` with `3.5%` ADC clipping, plus `144638`, `144842`, `144851`); `0` excluded inside `P6` model-dir `test_results.json`.
  - Attempt events: `1` stopped/timeout in `train`, `1` in `test`.
- **Gazebo Actuation (`P6`)**:
  - `simulation_commands.jsonl`: `41` dispatches (`index, thumb, middle, fist, rest`).
  - Multi-model `G_TF8` (`LDA`, `SVM`, `KNN`) agreement on `n=45` test trials: `41/45` (`91.1%`) `>= 1/3` matched; `33/45` (`73.3%`) `3/3` matched.

#### Selected Model (`G_TF8__SVM`) Confusion Matrices — `P01/P6`
- **3-Fold CV (`N = 100`, `98.00%`, `cov = 90.00%`, `acc_acc = 100.00%`)**:
  - `rest` (`20`): `[20, 0, 0, 0, 0]` -> `100.0%`
  - `thumb` (`20`): `[0, 18, 2, 0, 0]` -> `90.0%` (`2` -> `index`)
  - `index` (`20`): `[0, 0, 20, 0, 0]` -> `100.0%`
  - `middle` (`20`): `[0, 0, 0, 20, 0]` -> `100.0%`
  - `fist` (`20`): `[0, 0, 0, 0, 20]` -> `100.0%`
- **Held-Out Test (`N = 45`, `86.67%` (`39/45`), `cov = 66.67%`, `acc_acc = 93.33%`)**:
  - `rest` (`6`): `[5, 0, 1, 0, 0]` -> `83.3%` (`1` -> `index`)
  - `thumb` (`12`): `[0, 11, 1, 0, 0]` -> `91.7%` (`1` -> `index`)
  - `index` (`12`): `[0, 0, 8, 4, 0]` -> `66.7%` (`4` -> `middle`)
  - `middle` (`10`): `[0, 0, 0, 10, 0]` -> `100.0%`
  - `fist` (`5`): `[0, 0, 0, 0, 5]` -> `100.0%`
  - *(Note: `G_TF8__KNN` also achieved `86.67%` (`39/45`) with `100.00%` accepted accuracy (`26/26` accepted right), misclassifying `1 rest->thumb`, `1 thumb->index`, `2 index->thumb`, `2 index->middle`.)*

#### All 21 Models — `P01/P6` (`CV N = 100`, `Test N = 45`)
| Model | Val Acc (%) | Val F1 | Val Cov (%) | Val Suc (%) | Val Acc-Acc (%) | Test Acc (%) | Test F1 | Test Cov (%) | Test Suc (%) | Test Acc-Acc (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `A_RMS__LDA` | 72.00% | 0.6739 | 69.00% | 57.00% | 82.61% | 55.56% | 0.6547 | 48.89% | 33.33% | 68.18% |
| `A_RMS__SVM` | 78.00% | 0.7185 | 96.00% | 75.00% | 78.12% | 73.33% | 0.7276 | 80.00% | 53.33% | 66.67% |
| `A_RMS__KNN` | 83.00% | 0.8271 | 42.00% | 40.00% | 95.24% | 71.11% | 0.7708 | 26.67% | 26.67% | 100.00% |
| `B_MAV__LDA` | 74.00% | 0.6929 | 71.00% | 61.00% | 85.92% | 51.11% | 0.6243 | 55.56% | 33.33% | 60.00% |
| `B_MAV__SVM` | 80.00% | 0.7333 | 97.00% | 77.00% | 79.38% | 68.89% | 0.7041 | 84.44% | 60.00% | 71.05% |
| `B_MAV__KNN` | 84.00% | 0.8411 | 52.00% | 52.00% | 100.00% | 57.78% | 0.6667 | 31.11% | 28.89% | 92.86% |
| `C_WL__LDA` | 75.00% | 0.7155 | 81.00% | 71.00% | 87.65% | 51.11% | 0.6294 | 64.44% | 40.00% | 62.07% |
| `C_WL__SVM` | 79.00% | 0.7233 | 98.00% | 78.00% | 79.59% | 64.44% | 0.6644 | 84.44% | 60.00% | 71.05% |
| `C_WL__KNN` | 78.00% | 0.7815 | 63.00% | 61.00% | 96.83% | 64.44% | 0.6628 | 28.89% | 28.89% | 100.00% |
| `D_TD4__LDA` | 89.00% | 0.8867 | 71.00% | 67.00% | 94.37% | 84.44% | 0.8800 | 53.33% | 48.89% | 91.67% |
| `D_TD4__SVM` | 96.00% | 0.9598 | 87.00% | 86.00% | 98.85% | 86.67% | 0.8841 | 62.22% | 57.78% | 92.86% |
| `D_TD4__KNN` | 96.00% | 0.9600 | 83.00% | 82.00% | 98.80% | 84.44% | 0.8757 | 64.44% | 57.78% | 89.66% |
| `E_ALL5__LDA` | 87.00% | 0.8634 | 69.00% | 66.00% | 95.65% | 82.22% | 0.8506 | 48.89% | 44.44% | 90.91% |
| `E_ALL5__SVM` | 96.00% | 0.9589 | 88.00% | 87.00% | 98.86% | 84.44% | 0.8650 | 64.44% | 60.00% | 93.10% |
| `E_ALL5__KNN` | 96.00% | 0.9598 | 86.00% | 85.00% | 98.84% | 82.22% | 0.8491 | 57.78% | 53.33% | 92.31% |
| `F_MAV_MAX_MIN__LDA` | 73.00% | 0.7075 | 58.00% | 54.00% | 93.10% | 66.67% | 0.7126 | 28.89% | 26.67% | 92.31% |
| `F_MAV_MAX_MIN__SVM` | 86.00% | 0.8536 | 76.00% | 72.00% | 94.74% | 80.00% | 0.8426 | 66.67% | 62.22% | 93.33% |
| `F_MAV_MAX_MIN__KNN` | 87.00% | 0.8710 | 71.00% | 66.00% | 92.96% | 77.78% | 0.8110 | 57.78% | 53.33% | 92.31% |
| `G_TF8__LDA` | 93.00% | 0.9278 | 77.00% | 76.00% | 98.70% | 80.00% | 0.8365 | 42.22% | 40.00% | 94.74% |
| **`G_TF8__SVM` *(SELECTED)*** | **98.00%** | **0.9799** | **90.00%** | **90.00%** | **100.00%** | **86.67%** | **0.8852** | **66.67%** | **62.22%** | **93.33%** |
| `G_TF8__KNN` | 95.00% | 0.9497 | 90.00% | 89.00% | 98.89% | 86.67% | 0.8852 | 57.78% | 57.78% | 100.00% |

---

### STUDY 6: `rest, thumb, index, pinch, fist` (5 Gestures) — `P01/P8`

- **Model Version**: `P01_P8_5_gestures_20261111T161220_c752da28`
- **Selected Model**: **`G_TF8__SVM`** (`notch_50hz = True`).
- **Dataset Inventory**: `167` total trial directories (`2026-11-11 12:23:34` to `16:31:25`):
  - Reviewed valid training trials (`N = 100`): `rest: 20, thumb: 20, index: 20, pinch: 20, fist: 20`.
  - Unreviewed training trials (`29`): `rest: 16, index: 5, fist: 5, thumb: 2, pinch: 1`.
  - Reviewed valid test trials (`36` total in folder): `26` evaluated by `P8`'s model (`thumb: 7, index: 7, pinch: 5, fist: 7, rest: 0`) plus `10` earlier `P4` trials in root `test_results.json`.
  - Excluded in root `test_results.json`: `2` unreviewed test trials (`20261111T141216_e99d3cf1` clipped `fist`, `20261111T161327_aca9a3ee` unreviewed `pinch`); `0` excluded inside `P8` model-dir `test_results.json`.
  - Attempt events: `4` stopped/timeout in `train`.
- **Camera-Free Manual Slider Tests (`P8/manual_tests`, `5` captures under `G_TF8__SVM`, no ground truth)**:
  - `20261111T162455_6a411c6f`: `thumb` (**accepted**, agreement `0.65`, votes `{thumb: 13, fist: 5, index: 2}`)
  - `20261111T162526_e7b426c9`: `index` (rejected, agreement `0.45`, votes `{index: 9, pinch: 5, thumb: 4, fist: 2}`)
  - `20261111T162904_f0660f5b`: `pinch` (rejected, agreement `0.30`, votes `{pinch: 6, index: 5, thumb: 5, fist: 2, rest: 2}`)
  - `20261111T162926_0359d91a`: `index` (rejected, agreement `0.35`, votes `{index: 7, pinch: 6, thumb: 5, fist: 2}`)
  - `20261111T163158_454e6e0d`: `thumb` (rejected, agreement `0.45`, votes `{thumb: 9, fist: 5, pinch: 4, index: 2}`)
- **Gazebo Actuation (`P8`)**:
  - `simulation_commands.jsonl`: `26` commands (`pinch, index, fist, thumb`).
  - Multi-model `G_TF8` (`LDA`, `SVM`, `KNN`) agreement on `n=26` test trials: `25/26` (`96.2%`) `>= 1/3` matched; `16/26` (`61.5%`) `3/3` matched.

#### Selected Model (`G_TF8__SVM`) Confusion Matrices — `P01/P8`
- **3-Fold CV (`N = 100`, `90.00%`, `cov = 69.00%`, `acc_acc = 100.00%` (`69/69`))**:
  - `rest` (`20`): `[20, 0, 0, 0, 0]` -> `100.0%`
  - `thumb` (`20`): `[0, 20, 0, 0, 0]` -> `100.0%`
  - `index` (`20`): `[0, 3, 14, 3, 0]` -> `70.0%` (`3` -> `thumb`, `3` -> `pinch`)
  - `pinch` (`20`): `[0, 0, 4, 16, 0]` -> `80.0%` (`4` -> `index`)
  - `fist` (`20`): `[0, 0, 0, 0, 20]` -> `100.0%`
- **Held-Out Test (`N = 26`, `92.31%` (`24/26`), `cov = 50.00%`, `acc_acc = 100.00%` (`13/13`))**:
  - `rest` (`0`): `[0, 0, 0, 0, 0]` *(not present in this 26-trial batch; contributes `0` F1 to 5-class `macro_f1 = 0.7379`)*
  - `thumb` (`7`): `[0, 6, 0, 1, 0]` -> `85.7%` (`1` -> `pinch`)
  - `index` (`7`): `[0, 1, 6, 0, 0]` -> `85.7%` (`1` -> `thumb`)
  - `pinch` (`5`): `[0, 0, 0, 5, 0]` -> `100.0%`
  - `fist` (`7`): `[0, 0, 0, 0, 7]` -> `100.0%`

#### All 21 Models — `P01/P8` (`CV N = 100`, `Test N = 26`)
| Model | Val Acc (%) | Val F1 | Val Cov (%) | Val Suc (%) | Val Acc-Acc (%) | Test Acc (%) | Test F1 | Test Cov (%) | Test Suc (%) | Test Acc-Acc (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `A_RMS__LDA` | 62.00% | 0.5695 | 66.00% | 51.00% | 77.27% | 46.15% | 0.3475 | 38.46% | 23.08% | 60.00% |
| `A_RMS__SVM` | 64.00% | 0.5955 | 74.00% | 57.00% | 77.03% | 69.23% | 0.5064 | 46.15% | 42.31% | 91.67% |
| `A_RMS__KNN` | 69.00% | 0.6842 | 45.00% | 44.00% | 97.78% | 53.85% | 0.4266 | 19.23% | 19.23% | 100.00% |
| `B_MAV__LDA` | 65.00% | 0.6075 | 70.00% | 54.00% | 77.14% | 50.00% | 0.3658 | 30.77% | 15.38% | 50.00% |
| `B_MAV__SVM` | 64.00% | 0.6064 | 69.00% | 54.00% | 78.26% | 57.69% | 0.4326 | 23.08% | 23.08% | 100.00% |
| `B_MAV__KNN` | 67.00% | 0.6575 | 47.00% | 47.00% | 100.00% | 53.85% | 0.4122 | 26.92% | 23.08% | 85.71% |
| `C_WL__LDA` | 61.00% | 0.6073 | 66.00% | 52.00% | 78.79% | 50.00% | 0.3643 | 73.08% | 50.00% | 68.42% |
| `C_WL__SVM` | 61.00% | 0.5435 | 83.00% | 58.00% | 69.88% | 61.54% | 0.4476 | 61.54% | 46.15% | 75.00% |
| `C_WL__KNN` | 67.00% | 0.6707 | 43.00% | 41.00% | 95.35% | 53.85% | 0.3691 | 26.92% | 26.92% | 100.00% |
| `D_TD4__LDA` | 73.00% | 0.7278 | 57.00% | 50.00% | 87.72% | 69.23% | 0.5307 | 61.54% | 53.85% | 87.50% |
| `D_TD4__SVM` | 79.00% | 0.7876 | 73.00% | 66.00% | 90.41% | 76.92% | 0.6036 | 73.08% | 69.23% | 94.74% |
| `D_TD4__KNN` | 73.00% | 0.7337 | 56.00% | 54.00% | 96.43% | 57.69% | 0.4393 | 46.15% | 42.31% | 91.67% |
| `E_ALL5__LDA` | 75.00% | 0.7480 | 60.00% | 52.00% | 86.67% | 65.38% | 0.4807 | 65.38% | 53.85% | 82.35% |
| `E_ALL5__SVM` | 81.00% | 0.8108 | 73.00% | 66.00% | 90.41% | 73.08% | 0.5657 | 73.08% | 69.23% | 94.74% |
| `E_ALL5__KNN` | 80.00% | 0.8027 | 58.00% | 55.00% | 94.83% | 65.38% | 0.5079 | 50.00% | 42.31% | 84.62% |
| `F_MAV_MAX_MIN__LDA` | 73.00% | 0.7074 | 58.00% | 52.00% | 89.66% | 57.69% | 0.4903 | 38.46% | 26.92% | 70.00% |
| `F_MAV_MAX_MIN__SVM` | 76.00% | 0.7612 | 68.00% | 59.00% | 86.76% | 80.77% | 0.6509 | 46.15% | 42.31% | 91.67% |
| `F_MAV_MAX_MIN__KNN` | 63.00% | 0.6286 | 55.00% | 48.00% | 87.27% | 80.77% | 0.6358 | 50.00% | 50.00% | 100.00% |
| `G_TF8__LDA` | 80.00% | 0.7977 | 58.00% | 56.00% | 96.55% | 76.92% | 0.6109 | 42.31% | 42.31% | 100.00% |
| **`G_TF8__SVM` *(SELECTED)*** | **90.00%** | **0.8975** | **69.00%** | **69.00%** | **100.00%** | **92.31%** | **0.7379** | **50.00%** | **50.00%** | **100.00%** |
| `G_TF8__KNN` | 88.00% | 0.8787 | 66.00% | 61.00% | 92.42% | 73.08% | 0.5762 | 53.85% | 53.85% | 100.00% |

---

### STUDY 7: All 8 Gestures (`rest, thumb, index, middle, ring, little, pinch, fist`) — Trained in `P01/all fingers and gestures` (from `P02/P3`) & Evaluated on `P01/P1` Test Data

#### Training / Cross-Validation Metadata (`P01/all fingers and gestures`)
- **Model Version**: `P02_P3_8_gestures_20261111T165458_12def92b`
- **Selected Model**: **`G_TF8__SVM`** (`notch_50hz = True`, `digital_bandpass = False`, `agreement_threshold = 0.60`, `cv_folds = 3`).
- **Training Trial Composition (`N = 161` valid reviewed trials)**:
  - Counts per gesture: `rest: 20, thumb: 20, index: 21, middle: 20, ring: 20, little: 20, pinch: 20, fist: 20`.
  - Session provenance inside `P02/P3/trials` (from `2026-11-11` P01 recordings): `60` trials from session `20261111T133423_057a0eb9` (`rest: 20, index: 20, fist: 20`), `100` trials from session `20261111T141015_2d36403e` (`middle: 20, thumb: 20, ring: 20, little: 20, pinch: 20`), plus `1` extra `index` trial (`20261111T164312_4ddaa41b`) from `20261111T164224_5d6c1743`.

#### Cross-Validation Performance (`N = 161`) — Selected `G_TF8__SVM`
- **3-Fold CV Metrics**: `Accuracy = 76.40% (123/161)`, `Macro-F1 = 0.7556`, `Coverage = 43.48% (70/161)`, `Overall Success = 43.48% (70/161)`, **`Accepted Accuracy = 100.00% (70/70)`**. *(Every accepted prediction was right, while 56.5% of trials fell below the 60% window-agreement threshold.)*
- **8x8 CV Confusion Matrix (`G_TF8__SVM`, labels: `rest, thumb, index, middle, ring, little, pinch, fist`)**:
  - `rest` (`20`): `[20, 0, 0, 0, 0, 0, 0, 0]` -> recall `100.0%`
  - `thumb` (`20`): `[0, 18, 0, 0, 0, 2, 0, 0]` -> recall `90.0%` (`2 -> little`)
  - `index` (`21`): `[0, 0, 10, 0, 0, 4, 7, 0]` -> recall `47.6%` (`7 -> pinch`, `4 -> little`)
  - `middle` (`20`): `[0, 0, 0, 20, 0, 0, 0, 0]` -> recall `100.0%`
  - `ring` (`20`): `[0, 2, 0, 2, 8, 6, 2, 0]` -> recall `40.0%` (`6 -> little`, `2 -> thumb`, `2 -> middle`, `2 -> pinch`)
  - `little` (`20`): `[0, 2, 3, 1, 3, 9, 2, 0]` -> recall `45.0%` (`3 -> ring`, `3 -> index`, `2 -> thumb`, `2 -> pinch`, `1 -> middle`)
  - `pinch` (`20`): `[0, 0, 0, 0, 0, 2, 18, 0]` -> recall `90.0%` (`2 -> little`)
  - `fist` (`20`): `[0, 0, 0, 0, 0, 0, 0, 20]` -> recall `100.0%`

#### Paired Held-Out Test Evaluation Using `P01/P1` Test Data (`N = 33`) & Same Selected Model (`G_TF8__SVM`)
- **Test Dataset (`P01/P1`, recorded `2026-11-04`, 7 days before `2026-11-11` training)**:
  - `34` reviewed `test` trials exist in `P01/P1`: `1` excluded (`20261104T150805_4b16aa6d`, `middle`, rejected for ADC clipping + incomplete capture duration/host alignment error), leaving **`N = 33` valid reviewed test trials**:
    - Ground-truth distribution (`N = 33`): `rest: 0, thumb: 3, index: 8, middle: 6, ring: 5, little: 4, pinch: 1, fist: 6`.
  - **Result Using the Exact `all fingers and gestures` Model Bundle (`G_TF8__SVM`, with model's `notch_50hz = True`) on `P01/P1` (`N = 33`)**:
    - **Accuracy (`% correct`)**: **`42.42%` (`14/33`)**
    - **Macro-F1**: `0.2602` *(note: `rest` had 0 samples in `P1` test data)*
    - **Coverage**: `39.39%` (`13/33` accepted)
    - **Overall Success (`accepted & correct`)**: `18.18%` (`6/33`)
    - **Accepted Accuracy**: `46.15%` (`6/13`)
    - **Gazebo `G_TF8` Multi-Model Agreement on `P1` (`LDA/SVM/KNN`)**: `15/33` (`45.5%`) had `>= 1/3` model match.
  - **8x8 Test Confusion Matrix (`G_TF8__SVM` trained `2026-11-11` tested on `P01/P1` `2026-11-04`, `N = 33`)**:
    - `rest` (`0`): `[0, 0, 0, 0, 0, 0, 0, 0]` *(no test trials in `P1`)*
    - `thumb` (`3`): `[0, 0, 3, 0, 0, 0, 0, 0]` -> `0.0%` (`3 -> index`)
    - `index` (`8`): `[0, 0, 6, 0, 0, 1, 1, 0]` -> `75.0%` (`1 -> little`, `1 -> pinch`)
    - `middle` (`6`): `[0, 0, 0, 5, 0, 0, 1, 0]` -> `83.3%` (`1 -> pinch`)
    - `ring` (`5`): `[0, 0, 3, 0, 2, 0, 0, 0]` -> `40.0%` (`3 -> index`)
    - `little` (`4`): `[0, 0, 3, 1, 0, 0, 0, 0]` -> `0.0%` (`3 -> index`, `1 -> middle`)
    - `pinch` (`1`): `[0, 0, 0, 0, 0, 0, 1, 0]` -> `100.0%`
    - `fist` (`6`): `[0, 0, 0, 5, 0, 0, 1, 0]` -> `0.0%` (`5 -> middle`, `1 -> pinch`)
  - **Cross-Session / Experimental Context**: Despite a 7-day gap between electrode placement sessions (`Nov 4` vs `Nov 11`, plus `notch_50hz = True` in Nov 11 vs `False` in Nov 4), `all fingers and gestures` (`G_TF8__SVM`, **`42.42%`**) actually outperformed `P01/P1`'s own original same-day selected model (`E_ALL5__SVM`, **`36.36%`**) on the identical 33 `P1` test trials — though both suffer sharply compared with within-day 8-gesture CV (`76.40%`), particularly with `fist` shifting into `middle` (`5/6`) and `thumb`/`ring`/`little` shifting toward `index`.

#### All 21 Models — `all fingers and gestures` (`CV N = 161`) Cross-Evaluated on `P01/P1` (`Test N = 33`)
| Model | All-8 Val Acc (%) | All-8 Val F1 | All-8 Val Cov (%) | All-8 Val Suc (%) | All-8 Val Acc-Acc (%) | Cross-Eval on `P1` Acc (%) | `P1` Correct/Total | `P1` Macro-F1 | `P1` Cov (%) | `P1` Suc (%) | `P1` Acc-Acc (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `A_RMS__LDA` | 44.10% | 0.3949 | 57.14% | 35.40% | 61.96% | 27.27% | 9/33 | 0.1200 | 63.64% | 24.24% | 38.10% |
| `A_RMS__SVM` | 52.80% | 0.4900 | 55.28% | 37.89% | 68.54% | 21.21% | 7/33 | 0.1012 | 69.70% | 12.12% | 17.39% |
| `A_RMS__KNN` | 47.20% | 0.4636 | 22.36% | 22.36% | 100.00% | 30.30% | 10/33 | 0.1563 | 6.06% | 0.00% | 0.00% |
| `B_MAV__LDA` | 45.96% | 0.4119 | 55.90% | 37.27% | 66.67% | 27.27% | 9/33 | 0.1200 | 57.58% | 24.24% | 42.11% |
| `B_MAV__SVM` | 53.42% | 0.4952 | 55.90% | 39.75% | 71.11% | 21.21% | 7/33 | 0.1071 | 66.67% | 15.15% | 22.73% |
| `B_MAV__KNN` | 51.55% | 0.5025 | 24.84% | 24.84% | 100.00% | 21.21% | 7/33 | 0.1219 | 12.12% | 3.03% | 25.00% |
| `C_WL__LDA` | 48.45% | 0.4534 | 54.04% | 39.75% | 73.56% | 27.27% | 9/33 | 0.1396 | 54.55% | 12.12% | 22.22% |
| `C_WL__SVM` | 45.34% | 0.4318 | 69.57% | 41.61% | 59.82% | 30.30% | 10/33 | 0.1973 | 60.61% | 18.18% | 30.00% |
| `C_WL__KNN` | 51.55% | 0.5100 | 31.06% | 31.06% | 100.00% | 30.30% | 10/33 | 0.2335 | 12.12% | 6.06% | 50.00% |
| `D_TD4__LDA` | 57.14% | 0.5426 | 45.96% | 37.89% | 82.43% | 30.30% | 10/33 | 0.1141 | 69.70% | 21.21% | 30.43% |
| `D_TD4__SVM` | 60.25% | 0.5746 | 49.07% | 44.72% | 91.14% | 33.33% | 11/33 | 0.1292 | 78.79% | 30.30% | 38.46% |
| `D_TD4__KNN` | 65.84% | 0.6417 | 37.27% | 37.27% | 100.00% | 36.36% | 12/33 | 0.1429 | 48.48% | 21.21% | 43.75% |
| `E_ALL5__LDA` | 54.66% | 0.5133 | 44.10% | 36.02% | 81.69% | 30.30% | 10/33 | 0.1141 | 69.70% | 21.21% | 30.43% |
| `E_ALL5__SVM` | 62.11% | 0.5947 | 50.93% | 44.72% | 87.80% | 33.33% | 11/33 | 0.1292 | 78.79% | 30.30% | 38.46% |
| `E_ALL5__KNN` | 69.57% | 0.6862 | 37.27% | 37.27% | 100.00% | 36.36% | 12/33 | 0.1406 | 51.52% | 21.21% | 41.18% |
| `F_MAV_MAX_MIN__LDA` | 50.31% | 0.4686 | 33.54% | 29.19% | 87.04% | 27.27% | 9/33 | 0.1784 | 33.33% | 12.12% | 36.36% |
| `F_MAV_MAX_MIN__SVM` | 62.11% | 0.5969 | 46.58% | 39.75% | 85.33% | 24.24% | 8/33 | 0.1666 | 45.45% | 9.09% | 20.00% |
| `F_MAV_MAX_MIN__KNN` | 53.42% | 0.5315 | 34.78% | 34.16% | 98.21% | 42.42% | 14/33 | 0.3063 | 18.18% | 6.06% | 33.33% |
| `G_TF8__LDA` | 62.73% | 0.5937 | 39.75% | 38.51% | 96.88% | 33.33% | 11/33 | 0.1924 | 30.30% | 12.12% | 40.00% |
| **`G_TF8__SVM` *(SELECTED)*** | **76.40%** | **0.7556** | **43.48%** | **43.48%** | **100.00%** | **42.42%** | **14/33** | **0.2602** | **39.39%** | **18.18%** | **46.15%** |
| `G_TF8__KNN` | 68.32% | 0.6781 | 37.89% | 37.89% | 100.00% | 27.27% | 9/33 | 0.1281 | 27.27% | 18.18% | 66.67% |

---

### REFERENCE BASELINE: Original `P01/P1` Same-Day Session (`2026-11-04`, 18 Models `A–F`, `notch_50hz = False`)

*(Included for baseline comparison against Study 7 above, showing same-day `P01/P1` performance before `G_TF8` and `notch_50hz = True` were introduced.)*
- **Model Version**: `20261104T145018_5dd187af` (`187` trial dirs; `136` reviewed valid train: `rest: 17, thumb: 18, index: 17, middle: 17, ring: 17, little: 17, pinch: 16, fist: 17`; `34` reviewed test -> `33` valid + `1` excluded clipped/incomplete `middle` trial `20261104T150805_4b16aa6d`; `5` Gazebo commands; `E_ALL5` family `>=1/3` match `12/33` (`36.4%`)).
- **Selected Model**: **`E_ALL5__SVM`** (`G_TF8` not present).
  - **CV (`N = 136`)**: `72.79%` (`99/136`), F1 `0.7122`, cov `63.97%`, suc `52.94%`, acc-acc `82.76%` (`rest 15/17 [88.2%]`, `thumb 9/18 [50.0%]`, `index 12/17 [70.6%]`, `middle 15/17 [88.2%]`, `ring 13/17 [76.5%]`, `little 13/17 [76.5%]`, `pinch 5/16 [31.2%]`, `fist 17/17 [100.0%]`).
  - **Same-Day Test (`N = 33`)**: **`36.36%` (`12/33`)**, F1 `0.2425`, cov `54.55%`, suc `15.15%`, acc-acc `27.78%` (`thumb 3/3 [100%]`, `index 4/8 [50%]`, `middle 1/6 [16.7%]`, `ring 1/5 [20%]`, `little 0/4 [0%]`, `pinch 0/1 [0%]`, `fist 3/6 [50%]`).
- **All 18 Original `P01/P1` Models (`CV N=136` / `Test N=33`)**:
  - `A_RMS`: LDA `35.29%` CV / `21.21%` Test; SVM `39.71%` CV / `21.21%` Test; KNN `40.44%` CV / `27.27%` Test
  - `B_MAV`: LDA `27.21%` CV / `24.24%` Test; SVM `38.24%` CV / `24.24%` Test; KNN `31.62%` CV / `24.24%` Test
  - `C_WL`: LDA `44.12%` CV / `18.18%` Test; SVM `42.65%` CV / `24.24%` Test; KNN `42.65%` CV / `24.24%` Test
  - `D_TD4`: LDA `62.50%` CV / `30.30%` Test; SVM `70.59%` CV / `36.36%` Test; KNN `72.06%` CV / `21.21%` Test
  - `E_ALL5`: LDA `65.44%` CV / `36.36%` Test; **`SVM` (Selected)** `72.79%` CV / **`36.36%`** Test; KNN `72.79%` CV / `24.24%` Test
  - `F_MAV_MAX_MIN`: LDA `45.59%` CV / `27.27%` Test; SVM `60.29%` CV / `27.27%` Test; KNN `49.26%` CV / `33.33%` Test

---

### STUDY 8: `rest, index, fist` (3 Gestures — Earlier Placement `2026-11-09`) — `P01/P3` (3-gesture run)

- **Model Version**: `P01_P3_3_gestures_20261109T184600_eb8894dc`
- **Selected Model**: **`C_WL__KNN`** (`notch_50hz = True`, `digital_bandpass = False`, `agreement_threshold = 0.60`, `3-fold CV`) *(tied at `100.00%` CV accuracy and `1.0000` F1 with `C_WL__LDA` and `G_TF8__LDA`; `C_WL__KNN` won alphabetical tie-break)*.
- **Training Class Counts (`N = 60`)**: `rest: 20, index: 20, fist: 20` (recorded `2026-11-09 18:20–18:35`).
- **Held-Out Test Trials (`N = 5`, `2026-11-09 18:46–18:51`)**: `index: 3, fist: 2, rest: 0`; `0` excluded (full folder unreviewed breakdown listed under Study 9 below).
- **Camera-Free Manual Slider Tests (`P3/manual_tests`, `3` captures under `C_WL__KNN`, no ground truth)**:
  - `20261109T185012_f4fac29c`: `fist` (**accepted**, agreement `0.90`, votes `{fist: 18, index: 2}`)
  - `20261109T185045_53847022`: `fist` (rejected, agreement `0.50`, votes `{fist: 10, index: 10}`)
  - `20261109T185103_c2b5de08`: `fist` (**accepted**, agreement `0.70`, votes `{fist: 14, index: 6}`)
- **Series Test (`P3/series_tests/20261109T184922_3f300454`)**: `5` repetitions with camera reference `index` -> combined `C_WL__KNN` outcome was `fist` (`0.50` tie `{fist: 50, index: 50}`, rejected).
- **2D Simulation & Offline Multi-Model Agreement (`P3`, `2026-11-09` pre-Gazebo)**:
  - `simulation_commands.jsonl`: `7` commands (`fist: 4, index: 3`, `simulation_only: True` 2D canvas sim).
  - Offline `C_WL` (`LDA`, `SVM`, `KNN`) agreement on `n=5` test trials: `5/5` (`100.0%`) `>= 1/3` matched and `5/5` (`100.0%`) `3/3` unanimous match.

#### Selected Model (`C_WL__KNN`) Confusion Matrices — `P01/P3 (3-gesture)`
- **3-Fold CV (`N = 60`, `100.00%`, `cov = 98.33%`, `acc_acc = 100.00%`)**:
  - `rest` (`20`): `[20, 0, 0]` -> recall `100.0%`
  - `index` (`20`): `[0, 20, 0]` -> recall `100.0%`
  - `fist` (`20`): `[0, 0, 20]` -> recall `100.0%`
- **Held-Out Test (`N = 5`, `100.00%` (`5/5`), `F1 = 0.6667` *(missing `rest`)*, `cov = 100.00%`, `acc_acc = 100.00%`)**:
  - `rest` (`0`): `[0, 0, 0]` *(no rest test trials in this batch)*
  - `index` (`3`): `[0, 3, 0]` -> recall `100.0%`
  - `fist` (`2`): `[0, 0, 2]` -> recall `100.0%`

#### All 21 Models — `P01/P3 (3-gesture)` (`CV N = 60`, `Test N = 5`)
| Model | Val Acc (%) | Val F1 | Val Cov (%) | Val Suc (%) | Val Acc-Acc (%) | Test Acc (%) | Test F1 | Test Cov (%) | Test Suc (%) | Test Acc-Acc (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `A_RMS__LDA` | 93.33% | 0.9332 | 90.00% | 88.33% | 98.15% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `A_RMS__SVM` | 98.33% | 0.9833 | 98.33% | 96.67% | 98.31% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `A_RMS__KNN` | 98.33% | 0.9833 | 96.67% | 95.00% | 98.28% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `B_MAV__LDA` | 98.33% | 0.9833 | 98.33% | 96.67% | 98.31% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `B_MAV__SVM` | 98.33% | 0.9833 | 100.00% | 98.33% | 98.33% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `B_MAV__KNN` | 98.33% | 0.9833 | 100.00% | 98.33% | 98.33% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `C_WL__LDA` | 100.00% | 1.0000 | 98.33% | 98.33% | 100.00% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `C_WL__SVM` | 98.33% | 0.9833 | 98.33% | 98.33% | 100.00% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| **`C_WL__KNN` *(SELECTED)*** | **100.00%** | **1.0000** | **98.33%** | **98.33%** | **100.00%** | **100.00%** | **0.6667** | **100.00%** | **100.00%** | **100.00%** |
| `D_TD4__LDA` | 96.67% | 0.9666 | 95.00% | 93.33% | 98.25% | 100.00% | 0.6667 | 80.00% | 80.00% | 100.00% |
| `D_TD4__SVM` | 98.33% | 0.9833 | 98.33% | 96.67% | 98.31% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `D_TD4__KNN` | 98.33% | 0.9833 | 98.33% | 96.67% | 98.31% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `E_ALL5__LDA` | 96.67% | 0.9666 | 95.00% | 93.33% | 98.25% | 100.00% | 0.6667 | 80.00% | 80.00% | 100.00% |
| `E_ALL5__SVM` | 98.33% | 0.9833 | 98.33% | 96.67% | 98.31% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `E_ALL5__KNN` | 98.33% | 0.9833 | 98.33% | 96.67% | 98.31% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `F_MAV_MAX_MIN__LDA` | 90.00% | 0.9001 | 81.67% | 76.67% | 93.88% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `F_MAV_MAX_MIN__SVM` | 98.33% | 0.9833 | 98.33% | 96.67% | 98.31% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `F_MAV_MAX_MIN__KNN` | 98.33% | 0.9833 | 100.00% | 98.33% | 98.33% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `G_TF8__LDA` | 100.00% | 1.0000 | 100.00% | 100.00% | 100.00% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `G_TF8__SVM` | 98.33% | 0.9833 | 98.33% | 98.33% | 100.00% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |
| `G_TF8__KNN` | 98.33% | 0.9833 | 100.00% | 98.33% | 98.33% | 100.00% | 0.6667 | 100.00% | 100.00% | 100.00% |

---

### STUDY 9: `rest, thumb, index, fist` (4 Gestures — `2026-11-09` & `2026-11-11` Cross-Day) — `P01/P3` (4-gesture run)

- **Model Version**: `P01_P3_4_gestures_20261109T190452_852a6598` (still active in `P01/P3/latest_model.json`, and archived in `1_final/report_evidence/P01_P3_4_gestures_20261109T190452_852a6598/`).
- **Selected Model**: **`G_TF8__SVM`** (`notch_50hz = True`, `digital_bandpass = False`, `agreement_threshold = 0.60`, `3-fold CV`).
- **Complete Folder Inventory (`P01/P3/trials`, `174` trial directories: `164` on `2026-11-09 18:20:26` to `21:05:31`, `10` on `2026-11-11 12:19:13` to `12:22:20`; `173` `trial.json` files + `1` empty aborted dir `20261109T193516_6b748a64`)**:
  - Reviewed valid training trials (`N = 80`): `rest: 20, thumb: 20, index: 20, fist: 20` (`9` reviewed `fist` training trials carried `1.0%–3.6%` ADC clipping warnings; `12` reviewed `pinch` training trials from `2026-11-09` were deleted on `2026-11-10` per `P01_P3_four_gesture_evidence.md` so live reviewed `pinch` train count is `0`).
  - Unreviewed training trials (`23`): `index: 11, thumb: 6, pinch: 4, rest: 2` (`2` `rest` carried `1.3%` & `2.3%` clipping warnings).
  - Reviewed test trials (`66` total in `P01/P3`): `5` evaluated by Study 8 (`P01_P3_3_gestures`, `2026-11-09`), plus **`61` evaluated by Study 9 (`P01_P3_4_gestures`)**:
    - **Batch A (`2026-11-09 19:05–19:26`, archived 30-trial same-session snapshot, `N = 30`)**: `rest: 6, thumb: 15, index: 6, fist: 3` (`model_test_results_after_30_tests.json`).
    - **Exploratory Out-of-Scope Probes (`2026-11-09 19:35–19:37`, `N = 6`)**: `pinch: 3, middle: 1, ring: 1, little: 1` (0% accuracy possible on untrained labels; included in live 61-trial `test_results.json`).
    - **Batch B (`2026-11-09 20:55–20:59`, later same-day follow-up, `N = 15`)**: `rest: 1, thumb: 9, index: 3, fist: 2`.
    - **Batch C (`2026-11-11 12:19–12:22`, separate-day follow-up 2 days later, `N = 10`)**: `rest: 0, thumb: 6, index: 2, fist: 2`.
    - *(Note: `6` `fist` test trials carried `1.5%–3.0%` ADC clipping warnings and were retained as reviewed valid.)*
  - Excluded in root `test_results.json`: `4` unreviewed `2026-11-09` test trials (`20261109T193733_ca863cc2` [`pinch`], `20261109T193742_04400707` [`pinch`], `20261109T193811_1caee408` [`index`], `20261109T193856_7e32f2d4` [`index`]); `0` excluded inside `<version>_test_results.json`.
  - Attempt events (`attempt_events.jsonl`): `19` (`test: 11, train: 7, verify: 1`).
- **Camera-Free Manual Slider Tests (`P3/manual_tests`, `5` captures under `G_TF8__SVM`, no ground truth)**:
  - `20261109T190835_72071a94`: `index` (rejected, agreement `0.50`, votes `{index: 10, fist: 9, thumb: 1}`)
  - `20261109T190854_ed0f6c41`: `index` (rejected, agreement `0.45`, votes `{index: 9, thumb: 8, fist: 2, rest: 1}`)
  - `20261109T190917_81144fd5`: `fist` (**accepted**, agreement `0.90`, votes `{fist: 18, index: 1, thumb: 1}`)
  - `20261109T190937_485a14fa`: `thumb` (rejected, agreement `0.45`, votes `{thumb: 9, fist: 7, index: 4}`)
  - `20261109T192538_b9c70ff0`: `thumb` (rejected, agreement `0.55`, votes `{thumb: 11, index: 8, fist: 1}`)
- **2D Simulation & Offline Multi-Model Agreement (`G_TF8` `LDA/SVM/KNN`)**:
  - `simulation_commands.jsonl`: `30` dispatches under `P01_P3_4_gestures` (`index: 9, fist: 8, rest: 7, thumb: 6`, `simulation_only: True` 2D canvas sim).
  - Archived `N = 30` snapshot: `27/30` (`90.0%`) `>= 1/3` matched; `20/30` (`66.7%`) `3/3` matched.
  - All `2026-11-09` in-scope (`N = 45`): `36/45` (`80.0%`) `>= 1/3` matched; `26/45` (`57.8%`) `3/3` matched (`15` late-night `20:55` trials alone: `9/15` [`60.0%`] `>=1/3`, `6/15` [`40.0%`] `3/3`).
  - `2026-11-11` cross-day (`N = 10`): `7/10` (`70.0%`) `>= 1/3` matched; `5/10` (`50.0%`) `3/3` matched.
  - Combined all in-scope (`N = 55`): `43/55` (`78.2%`) `>= 1/3` matched; `31/55` (`56.4%`) `3/3` matched (`N = 61` live total: `43/61` [`70.5%`] / `31/61` [`50.8%`]).

#### Selected (`G_TF8__SVM`) & Best Test (`F_MAV_MAX_MIN`) Confusion Matrices — `P01/P3 (4-gesture)`
- **3-Fold CV (`G_TF8__SVM`, `N = 80`, `96.25%`, `F1 = 0.9623`, `cov = 86.25%`, `acc_acc = 98.55%` [`68/69`])**:
  - `rest` (`20`): `[20, 0, 0, 0]` -> recall `100.0%`
  - `thumb` (`20`): `[0, 17, 3, 0]` -> recall `85.0%` (`3 -> index`)
  - `index` (`20`): `[0, 0, 20, 0]` -> recall `100.0%`
  - `fist` (`20`): `[0, 0, 0, 20]` -> recall `100.0%`
- **Archived 30-Trial Same-Session Snapshot (`2026-11-09 19:05–19:26`, `N = 30`)**:
  - `G_TF8__SVM` (**`83.33%`** [`25/30`], `F1 = 0.8765`, `cov = 63.33%` [`19/30`], **`acc_acc = 100.00%` [`19/19`]**):
    - `rest` (`6`): `[6, 0, 0, 0]` -> `100.0%`
    - `thumb` (`15`): `[0, 10, 5, 0]` -> `66.7%` (`5 -> index`, all 5 rejected)
    - `index` (`6`): `[0, 0, 6, 0]` -> `100.0%`
    - `fist` (`3`): `[0, 0, 0, 3]` -> `100.0%`
  - `F_MAV_MAX_MIN__KNN` (Best at `N=30`: **`90.00%`** [`27/30`], `F1 = 0.9164`, `cov = 66.67%`, `acc_acc = 95.00%`):
    - `rest` (`6`): `[6, 0, 0, 0]`, `thumb` (`15`): `[0, 13, 2, 0]`, `index` (`6`): `[0, 1, 5, 0]`, `fist` (`3`): `[0, 0, 0, 3]`.
- **Sub-Batch Drift Inside Later Test Sessions (`G_TF8__SVM`)**:
  - `2026-11-09 20:55` later batch (`N = 15`): **`40.00%` (`6/15`)**, `F1 = 0.4821`, `cov = 60.00%`, `acc_acc = 66.67%` (`rest 1/1`, `index 3/3`, `fist 2/2`, **`thumb 0/9` [7 -> `index`, 1 -> `rest`, 1 -> `fist`]**).
  - Combined `2026-11-09` in-scope (`N = 45`): **`68.89%` (`31/45`)**, `F1 = 0.7577`, `cov = 62.22%`, `acc_acc = 89.29%` (`rest 7/7`, `thumb 10/24`, `index 9/9`, `fist 5/5`).
  - `2026-11-11` cross-day (`N = 10`): **`60.00%` (`6/10`)**, `F1 = 0.5000`, `cov = 50.00%`, `acc_acc = 80.00%` (`thumb 2/6` [4 -> `index`], `index 2/2`, `fist 2/2`). *(On this same Nov 11 `N=10` batch, `F_MAV_MAX_MIN__SVM` achieved **`90.0%` [`9/10`]**!)*
- **All In-Scope Test Trials Combined (`N = 55`, `rest: 7, thumb: 30, index: 11, fist: 7`)**:
  - `G_TF8__SVM` (**`67.27%`** [`37/55`], `F1 = 0.7543`, `cov = 60.00%` [`33/55`], `suc = 52.73%` [`29/55`], `acc_acc = 87.88%` [`29/33`]):
    - `rest` (`7`): `[7, 0, 0, 0]` -> `100.0%`
    - `thumb` (`30`): `[1, 12, 16, 1]` -> `40.0%` (`16 -> index`, `1 -> rest`, `1 -> fist`)
    - `index` (`11`): `[0, 0, 11, 0]` -> `100.0%`
    - `fist` (`7`): `[0, 0, 0, 7]` -> `100.0%`
  - `F_MAV_MAX_MIN__SVM` (Best in-scope w/ highest coverage & accepted accuracy: **`87.27%`** [`48/55`], `F1 = 0.8901`, `cov = 69.09%`, `suc = 67.27%`, `acc_acc = 97.37%`):
    - `rest` (`7`): `[7, 0, 0, 0]`, `thumb` (`30`): `[1, 25, 4, 0]`, `index` (`11`): `[0, 2, 9, 0]`, `fist` (`7`): `[0, 0, 0, 7]`.
  - `F_MAV_MAX_MIN__KNN` (Tied highest in-scope accuracy: **`87.27%`** [`48/55`], `F1 = 0.8993`, `cov = 56.36%`, `suc = 49.09%`, `acc_acc = 87.10%`):
    - `rest` (`7`): `[7, 0, 0, 0]`, `thumb` (`30`): `[0, 25, 5, 0]`, `index` (`11`): `[0, 2, 9, 0]`, `fist` (`7`): `[0, 0, 0, 7]`.
- **Full Live `<version>_test_results.json` (`N = 61`, adding `6` out-of-scope probes `3 pinch, 1 middle, 1 ring, 1 little`)**:
  - `G_TF8__SVM`: **`60.66%`** (`37/61`), 8-label `F1 = 0.3508`, `cov = 57.38%` (`35/61`), `suc = 47.54%` (`29/61`), `acc_acc = 82.86%` (`29/35`).
  - Out-of-scope probe responses by `G_TF8__SVM`: `pinch (3) -> 2 rest, 1 index` (`2` accepted wrong); `middle (1) -> fist`; `ring (1) -> thumb`; `little (1) -> index`.

#### All 21 Models — `P01/P3 (4-gesture)` (`CV N = 80`, `Nov 9 N = 30`, `All In-Scope N = 55`, `Live Report N = 61`)
| Model | Val Acc (%) | Val F1 | Val Cov (%) | Val Acc-Acc (%) | Test30 Acc (%) | Test30 Cov (%) | Test30 Acc-Acc (%) | In55 Acc (%) | In55 F1 | In55 Cov (%) | In55 Acc-Acc (%) | Live61 Acc (%) | Live61 Cov (%) | Live61 Acc-Acc (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `A_RMS__LDA` | 67.50% | 0.6594 | 76.25% | 81.97% | 63.33% | 43.33% | 92.31% | 52.73% | 0.6067 | 36.36% | 85.00% | 47.54% | 39.34% | 70.83% |
| `A_RMS__SVM` | 72.50% | 0.6481 | 87.50% | 77.14% | 50.00% | 56.67% | 64.71% | 47.27% | 0.5792 | 65.45% | 55.56% | 42.62% | 67.21% | 48.78% |
| `A_RMS__KNN` | 68.75% | 0.6905 | 47.50% | 92.11% | 60.00% | 43.33% | 92.31% | 58.18% | 0.6772 | 36.36% | 95.00% | 52.46% | 37.70% | 82.61% |
| `B_MAV__LDA` | 71.25% | 0.7015 | 78.75% | 79.37% | 56.67% | 46.67% | 85.71% | 52.73% | 0.6285 | 47.27% | 69.23% | 47.54% | 50.82% | 58.06% |
| `B_MAV__SVM` | 73.75% | 0.6575 | 93.75% | 76.00% | 50.00% | 80.00% | 58.33% | 45.45% | 0.6058 | 81.82% | 53.33% | 40.98% | 80.33% | 48.98% |
| `B_MAV__KNN` | 72.50% | 0.7240 | 58.75% | 87.23% | 66.67% | 36.67% | 90.91% | 61.82% | 0.7000 | 34.55% | 78.95% | 55.74% | 31.15% | 78.95% |
| `C_WL__LDA` | 68.75% | 0.6774 | 83.75% | 77.61% | 50.00% | 53.33% | 75.00% | 43.64% | 0.5237 | 41.82% | 73.91% | 39.34% | 42.62% | 65.38% |
| `C_WL__SVM` | 75.00% | 0.6841 | 83.75% | 82.09% | 60.00% | 80.00% | 62.50% | 52.73% | 0.6592 | 76.36% | 59.52% | 47.54% | 72.13% | 56.82% |
| `C_WL__KNN` | 73.75% | 0.7333 | 53.75% | 90.70% | 60.00% | 53.33% | 81.25% | 52.73% | 0.6224 | 43.64% | 83.33% | 47.54% | 40.98% | 80.00% |
| `D_TD4__LDA` | 82.50% | 0.8222 | 67.50% | 96.30% | 56.67% | 53.33% | 81.25% | 47.27% | 0.5920 | 50.91% | 64.29% | 42.62% | 47.54% | 62.07% |
| `D_TD4__SVM` | 83.75% | 0.8393 | 75.00% | 96.67% | 66.67% | 63.33% | 73.68% | 54.55% | 0.6636 | 69.09% | 63.16% | 49.18% | 65.57% | 60.00% |
| `D_TD4__KNN` | 83.75% | 0.8376 | 72.50% | 94.83% | 56.67% | 66.67% | 70.00% | 50.91% | 0.6288 | 69.09% | 60.53% | 45.90% | 67.21% | 56.10% |
| `E_ALL5__LDA` | 81.25% | 0.8095 | 71.25% | 96.49% | 60.00% | 56.67% | 82.35% | 49.09% | 0.5965 | 54.55% | 66.67% | 44.26% | 50.82% | 64.52% |
| `E_ALL5__SVM` | 85.00% | 0.8515 | 77.50% | 96.77% | 66.67% | 63.33% | 68.42% | 54.55% | 0.6636 | 69.09% | 60.53% | 49.18% | 65.57% | 57.50% |
| `E_ALL5__KNN` | 87.50% | 0.8755 | 75.00% | 95.00% | 60.00% | 50.00% | 86.67% | 52.73% | 0.6428 | 61.82% | 64.71% | 47.54% | 62.30% | 57.89% |
| `F_MAV_MAX_MIN__LDA` | 76.25% | 0.7560 | 58.75% | 95.74% | 80.00% | 50.00% | 100.00% | 80.00% | 0.8167 | 54.55% | 96.67% | 72.13% | 54.10% | 87.88% |
| **`F_MAV_MAX_MIN__SVM` *(BEST TEST w/ HIGHEST ACC-ACC & COV)*** | 87.50% | 0.8722 | 72.50% | 98.28% | 86.67% | 66.67% | 95.00% | **87.27%** | 0.8901 | **69.09%** | **97.37%** | **78.69%** | **67.21%** | **90.24%** |
| **`F_MAV_MAX_MIN__KNN` *(BEST TEST)*** | 88.75% | 0.8873 | 67.50% | 96.30% | **90.00%** | 66.67% | 95.00% | **87.27%** | **0.8993** | 56.36% | 87.10% | **78.69%** | 54.10% | 81.82% |
| `G_TF8__LDA` | 92.50% | 0.9233 | 67.50% | 100.00% | 76.67% | 40.00% | 100.00% | 65.45% | 0.7310 | 40.00% | 90.91% | 59.02% | 37.70% | 86.96% |
| **`G_TF8__SVM` *(SELECTED)*** | **96.25%** | **0.9623** | **86.25%** | **98.55%** | **83.33%** | **63.33%** | **100.00%** | **67.27%** | **0.7543** | **60.00%** | **87.88%** | **60.66%** | **57.38%** | **82.86%** |
| `G_TF8__KNN` | 93.75% | 0.9380 | 76.25% | 100.00% | 76.67% | 50.00% | 100.00% | 65.45% | 0.7418 | 49.09% | 88.89% | 59.02% | 45.90% | 85.71% |

---

## 3. CROSS-STUDY SYNTHESIS & KEY ANALYTICAL CONCLUSIONS (FOR CHAPTER 6 & DISCUSSION)

1. **Class-Count Scaling & Gesture Separability**:
   - Distinct 3-class sets (`rest, index, fist` in `P3 3-gest` and `P4`; `rest, middle, fist` in `P5`) are trivial to separate even from single-amplitude or waveform-length features (`C_WL__KNN`, `A_RMS__KNN`, and `B_MAV__KNN` all hit `100.00%` CV and `100.00%` held-out test, with nearly all 21 models reaching `100%` test accuracy).
   - Adding `thumb` to form a **4-class set** (`P3 4-gest`: `rest, thumb, index, fist`) drops single-feature (`A_RMS`, `B_MAV`, `C_WL`) CV to `67.50%–75.00%` while `G_TF8__SVM` lifts CV to **`96.25%`** and achieves **`83.33%` (`25/30`, `100.00%` accepted precision)** on the initial same-session test block.
   - Moving to **5 distinct/semi-distinct gestures** (`P6`: `rest, thumb, index, middle, fist` and `P8`: `rest, thumb, index, pinch, fist`), single-feature sets (`A_RMS`, `B_MAV`, `C_WL`) drop sharply (`~46%–73%` test accuracy), whereas time-frequency features (`G_TF8__SVM`) sustain **`98.00%` CV / `86.67%` test** (`P6`) and **`90.00%` CV / `92.31%` test** (`P8`) with `93.33%–100.00%` accepted precision.
   - Moving to **8 classes** (`all fingers and gestures`), adding `ring` and `little` alongside `middle`, `index`, `thumb`, and `pinch` causes overall 3-fold CV accuracy to settle at **`76.40%`** (`G_TF8__SVM`), while cross-session evaluation against a 7-day-old `P1` session drops to **`42.42%`** (`14/33`).

2. **Why `G_TF8__SVM` Replaces `A_RMS` / `B_MAV` / `D_TD4` as Complexity Increases**:
   - On `>= 4` non-trivial classes (`P3 4-gest`, `P6`, `P8`, `all fingers and gestures`), `G_TF8__SVM` won CV model selection in **every single study** (`96.25%`, `98.00%`, `90.00%`, `76.40%` CV), outperforming `A_RMS`/`B_MAV`/`C_WL` by `+15` to `+31` percentage points in validation accuracy and achieving **`98.55%–100.00%` accepted accuracy during CV** (`68/69` in `P3 4-gest`, `90/90` in `P6`, `69/69` in `P8`, `70/70` in `all fingers and gestures`).
   - Early/late spectral sub-band power (`G_TF8`) captures both spectral distribution changes and transient onset-to-hold shifts within the `250 ms` window, separating gestures that share similar total EMG RMS amplitude.

3. **Biomechanically Linked Failure Clusters (Exact Confusion Evidence)**:
   - **`ring` <-> `little` (`P7` 2-gest, `P7` 3-gest, `all-8`)**: Across every single study containing both digits, `ring` and `little` formed the single largest confusion bottleneck (due to anatomical flexor/extensor tendon sharing and single-channel forearm cross-talk). In `P7 (2-gesture)`, `C_WL__KNN` dropped to `50.00%` test accuracy (`28.57%` accepted accuracy), and in `P7 (3-gesture)`, `middle` separated `100%` in CV while `100%` of CV errors (`14/14`) and `100%` of `little` test errors (`8/8` `little -> ring` under `D_TD4__LDA`) were `ring <-> little`. In the 8-gesture CV (`G_TF8__SVM`), `rest` (`100%`), `middle` (`100%`), `fist` (`100%`), `thumb` (`90%`), and `pinch` (`90%`) stayed high while `ring` (`40.0%`) and `little` (`45.0%`) dragged overall accuracy down.
   - **`index` <-> `pinch` <-> `thumb` (`P3 4-gest`, `P8`, `P6`, `all-8`)**: In `P3 (4-gest)`, `rest` (`7/7`), `index` (`11/11`), and `fist` (`7/7`) hit `100%` test recall under `G_TF8__SVM`, whereas **every error except two single-trial outliers (`16/18` errors across `N=55`) was `thumb -> index`** (`16/30` `thumb` trials misclassified as `index`). In `P8` CV (`G_TF8__SVM`), `rest`, `thumb`, and `fist` were `100%`, whereas all errors lay between `index` (`70%`, confusing `3` as `thumb` and `3` as `pinch`) and `pinch` (`80%`, confusing `4` as `index`). In `all-8` CV (`G_TF8__SVM`), `7/21` `index` trials confused with `pinch`. Anatomically, precision `pinch` directly recruits index and thumb flexors simultaneously.

4. **Cross-Validation Over-Selection vs Test Generalisation (`P7 3-gesture` Case Study)**:
   - In `P7 (3-gesture)`, the automated CV selector chose `D_TD4__LDA` (`76.67%` CV), which collapsed to **`35.71%` (`5/14`)** on held-out test trials (`0/8` `little` recall). Yet on those identical 14 test trials, **`G_TF8__KNN` achieved `92.86%` (`13/14`, `100%` accepted accuracy)** despite ranking lower in within-session CV (`63.33%`). This highlights that in small single-session CV (`N=60`), marginal CV winners on time-domain features can overfit trial-specific amplitude baselines, whereas spectro-temporal (`G_TF8`) features remain more robust online.

5. **Confidence-Gated Rejection Trade-Off (`agreement_threshold = 0.60`)**:
   - The 60% window-vote gate reliably rejects ambiguous trials at the expense of coverage: in `all-8` CV (`G_TF8__SVM`), coverage fell to **`43.48%` (`70/161`)**, but accepted accuracy reached **`100.00%` (`70/70`)**. In `P8` online tests (`G_TF8__SVM`), coverage was `50.00%` (`13/26`) with **`100.00%` (`13/13`) accepted accuracy** (`P6`: `66.67%` cov, `93.33%` accepted acc). Conversely, across a 7-day session gap (`all-8` evaluated on Nov 4 `P1`), confidence gating alone could not recover distribution shift (`39.39%` cov, `46.15%` accepted acc).

6. **Cross-Session / Hardware Shift Evidence (`all-8` on `P01/P1` vs Same-Session Studies)**:
   - Single-channel sEMG models trained in one session (`2026-11-11`) degraded from `76.40%` within-day CV to `42.42%` when tested against `P01/P1` (`2026-11-04`), where `fist` test trials shifted predominantly toward `middle` (`5/6`) and `thumb`/`ring`/`little` shifted toward `index`. Contributing factors are electrode re-placement shift, gain/impedance differences over 7 days, `notch_50hz=False` in `P1`'s original run vs `True` in Nov 11, and `0` `rest` trials in `P1`'s test set. Multi-channel acquisition (`CapFix` ADS1296 6-channel PCB) is directly motivated by resolving `ring/little` and `index/pinch` spatial overlap and reducing single-site sensitivity.

7. **Time/Session Drift & Out-of-Scope Vulnerability (`P01/P3` 4-Gesture Benchmark)**:
   - Across `P01/P3`'s `55` in-scope test trials, `G_TF8__SVM` held `83.33%` (`25/30`, `100.00%` accepted accuracy) immediately after training (`19:05–19:26`), then fell to `40.00%` (`6/15`; `0/9` `thumb`) two hours later (`20:55–20:59`) and `60.00%` (`6/10`) two days later (`2026-11-11`), yielding `67.27%` (`37/55`) across all in-scope tests (or `60.66%` [`37/61`] when mixing in `6` untrained `pinch/middle/ring/little` probes). Meanwhile, simple peak-envelope features (`F_MAV_MAX_MIN__SVM/KNN`) sustained **`87.27%` (`48/55`)** across all in-scope tests (`90.00%` at `N=30`, **`90.0%` [`9/10`] on the Nov 11 cross-day batch**, with `97.37%` accepted accuracy for `F_MAV_MAX_MIN__SVM`), showing that extreme signal bounds can resist late-session `thumb -> index` spectral drift better than `G_TF8` on placement `P3`, while closed-set models still misclassify untrained gestures (`2/3` `pinch` probes accepted erroneously as `rest`/`index`).