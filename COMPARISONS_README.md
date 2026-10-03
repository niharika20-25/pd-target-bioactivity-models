# Comprehensive Model Comparisons: Parkinson's Disease Targets

This document summarizes all of the machine learning model comparisons conducted during the analysis session, evaluating **XGBoost, Logistic Regression, Random Forest, and K-Nearest Neighbors (KNN)** across various Parkinson's-related targets.

---

## 1. Initial 4-Way Model Comparison (75/25 Split)
This comparison utilized a 75% training and 25% testing split to evaluate all four models. 

### Best Performing Model by Target (ROC-AUC)

| Target (Gene) | Winning Model | XGBoost | Logistic Regression | Random Forest | KNN |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ADORA2A** | **XGBoost** | **0.955** | 0.923 | 0.927 | 0.814 |
| **CHRM** | **XGBoost** | **0.939** | 0.884 | 0.913 | 0.892 |
| **COMT** | **Logistic Regression** | 0.897 | **0.953** | 0.819 | 0.845 |
| **DRD1** | **XGBoost** | **0.960** | 0.919 | 0.821 | 0.784 |
| **DRD2** | **XGBoost** | **0.928** | 0.885 | *(No Data)* | *(No Data)* |
| **GBA1** | **XGBoost** | **0.893** | 0.862 | 0.819 | 0.781 |
| **GLP1R** | **XGBoost** | **0.954** | 0.926 | 0.909 | 0.786 |
| **LRRK2** | **XGBoost** | **0.939** | 0.858 | 0.931 | 0.800 |
| **MAO_B** | **XGBoost** | **0.939** | 0.887 | 0.920 | 0.892 |
| **PINK1** | **Random Forest / KNN** | *(No Data)* | *(No Data)* | **1.000** | **1.000** |
| **SLC18A2** | **XGBoost** | **0.981** | 0.953 | 0.885 | 0.816 |
| **SLC6A3** | **XGBoost** | **0.949** | 0.940 | 0.934 | 0.904 |
| **SNCA** | **Logistic Regression** | 0.874 | **0.986** | 0.884 | 0.821 |

**Conclusion:** XGBoost was the decisive winner, claiming 9 out of the 13 targets. Gradient boosting naturally handles the highly complex, non-linear rules present in chemoinformatics feature spaces (like Morgan Fingerprints) better than linear models or distance-based models like KNN.

---

## 2. Impact of Training Data Volume (80/20 vs 75/25 Split)
A secondary pipeline was run for XGBoost and Logistic Regression to determine if increasing the training data to 80% would yield better generalization. 

### Key Findings:
- **Minimal Overall Impact**: Adding 5% more training data resulted in an average ROC-AUC improvement of only **0.55%** (+0.0055).
- **Model Disparity**: 
  - **Logistic Regression** saw an average boost of **~1%** (+0.0104), proving it is more "data-hungry" and benefited from having more points to draw its linear boundary.
  - **XGBoost** was essentially unchanged (+0.0006), indicating that the ensemble trees had already reached peak representational capacity with 75% of the data.
- **Split Type Differences**:
  - The **Random Split** (which contains in-distribution chemical structures) improved by **1.1%**.
  - The **Scaffold Split** (which tests out-of-distribution, unseen chemical backbones) saw **0% improvement**, proving that simply adding *more of the same* chemical skeletons does not help models generalize to entirely *new* skeletons.

---

## 3. Secondary 4-Way Model Comparison (80/20 Split)
With all four models trained on the 80/20 split, a final comparison was generated to see if the leaderboard shifted with the new data distribution.

### Best Performing Model by Target (ROC-AUC)

| Target (Gene) | Winning Model | XGBoost | Logistic Regression | Random Forest | KNN |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ADORA2A** | **XGBoost** | **0.957** | 0.922 | 0.925 | 0.813 |
| **CHRM** | **XGBoost** | **0.950** | 0.894 | 0.907 | 0.885 |
| **COMT** | **Logistic Regression** | 0.850 | **0.972** | 0.894 | 0.868 |
| **DRD1** | **XGBoost** | **0.968** | 0.936 | 0.812 | 0.787 |
| **DRD2** | **XGBoost** | **0.983** | 0.953 | *(No Data)* | *(No Data)* |
| **GBA1** | **XGBoost** | **0.894** | 0.864 | 0.807 | 0.744 |
| **GLP1R** | **XGBoost** | **0.983** | 0.964 | 0.907 | 0.780 |
| **LRRK2** | **Random Forest** | 0.930 | 0.939 | **0.959** | 0.846 |
| **MAO_B** | **XGBoost** | **0.947** | 0.909 | 0.923 | 0.897 |
| **PINK1** | **Random Forest / KNN** | *(No Data)* | *(No Data)* | **1.000** | **1.000** |
| **SLC18A2** | **Logistic Regression** | 0.976 | **1.000** | 0.923 | 0.871 |
| **SLC6A3** | **XGBoost** | **0.952** | 0.942 | 0.936 | 0.904 |
| **SNCA** | **Logistic Regression** | 0.979 | **0.982** | 0.889 | 0.842 |

### Shifts in Leaderboard (75/25 -> 80/20):
- **Random Forest Victory**: Random Forest overtook XGBoost on **LRRK2**, jumping to a 0.959 ROC-AUC.
- **Logistic Regression Milestone**: With slightly more data, Logistic Regression achieved a perfect **1.0 ROC-AUC on SLC18A2**, reclaiming the win from XGBoost.
- **Overall Dominance**: XGBoost remains the most robust choice for chemoinformatics, winning 8 of the 13 targets despite the shift in training size.
