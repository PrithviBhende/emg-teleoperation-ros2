# Benchmark Training Results & Decision Boundary Projections

This directory archives the complete graphical representations, 2D/3D feature projections, and classifier decision boundary gradient heatmaps across all evaluated gesture combinations and finger tests.

---

## Study Navigation Index

| Study Folder | Tested Fingers / Gestures | Classes ($N$) | Champion Model | 3-Fold CV Acc | Held-Out Test Acc |
|:---|:---|:---:|:---|:---:|:---:|
| [**`01_rest_index_fist`**](01_rest_index_fist/) | Rest, Index, Fist | 3 | `A_RMS__KNN` | **100.00%** | **100.00%** |
| [**`02_rest_middle_fist`**](02_rest_middle_fist/) | Rest, Middle, Fist | 3 | `B_MAV__KNN` | **100.00%** | **100.00%** |
| [**`03_ring_little`**](03_ring_little/) | Ring, Little (Hard Adjacent Pair) | 2 | `C_WL__KNN` / `F_MAV_MAX_MIN__SVM` | **70.00%** | **68.75%** (Best) |
| [**`04_middle_ring_little`**](04_middle_ring_little/) | Middle, Ring, Little (Adjacent Digits) | 3 | `D_TD4__LDA` / `G_TF8__KNN` | **76.67%** | **92.86%** (Best) |
| [**`05_rest_thumb_index_middle_fist`**](05_rest_thumb_index_middle_fist/) | Rest, Thumb, Index, Middle, Fist | 5 | `G_TF8__SVM` | **98.00%** | **86.67%** |
| [**`06_rest_thumb_index_pinch_fist`**](06_rest_thumb_index_pinch_fist/) | Rest, Thumb, Index, Pinch, Fist | 5 | `G_TF8__SVM` | **90.00%** | **92.31%** |
| [**`07_all_8_gestures`**](07_all_8_gestures/) | All 8 Gestures (Cross-Day P1 Test) | 8 | `G_TF8__SVM` | **76.40%** | **42.42%** |
| [**`08_rest_index_fist_p3`**](08_rest_index_fist_p3/) | Rest, Index, Fist (Placement P3) | 3 | `C_WL__KNN` | **100.00%** | **100.00%** |
| [**`09_rest_thumb_index_fist_p3`**](09_rest_thumb_index_fist_p3/) | Rest, Thumb, Index, Fist (Placement P3) | 4 | `G_TF8__SVM` / `F_MAV_MAX_MIN__KNN` | **96.25%** | **87.27%** (Best) |

---

## Directory Organization
Each subfolder contains:
* `*_training_*_2D.png`: 2D PCA projection of training trials showing class cluster distribution.
* `*_training_*_3D.png`: 3D PCA projection illustrating spatial separation across the top 3 principal components.
* `*_training_*_gradient_heatmaps.png`: Continuous decision boundaries and classification confidence gradients for LDA, SVM, and KNN.
* `*_test_*_2D.png` & `*_3D.png`: Held-out test evaluation projections overlaying accepted predictions and rejected trials.
* `README.md`: Specific summary of the protocol, data split, and model performance.
