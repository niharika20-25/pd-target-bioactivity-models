# Four-Model Comparison: XGBoost vs Logistic Regression vs Random Forest vs KNN

You can download the full, combined CSV dataset here: [model_comparison_results_all.csv](file:///Users/niharikarai/Documents/MODELPARKINSON/OUTPUT/model_comparison_results_all.csv).

## Overall Performance Matrix (Top Targets)

Below is a detailed breakdown of the models based on Precision, Recall, F1-Score, and ROC-AUC. *(Note: Higher is better for all metrics).*

| Target | Model | Precision | Recall (Sens) | F1-Score | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ADORA2A** | **XGBoost** | 0.943 | **0.989** | **0.965** | **0.955** |
| | Logistic Reg. | **0.960** | 0.955 | 0.957 | 0.923 |
| | Random Forest | 0.945 | 0.933 | 0.939 | 0.927 |
| | KNN | 0.918 | 0.965 | 0.941 | 0.814 |
| | | | | | |
| **CHRM** | **XGBoost** | 0.881 | **0.954** | **0.917** | **0.939** |
| | Logistic Reg. | **0.884** | 0.901 | 0.892 | 0.884 |
| | Random Forest | 0.855 | 0.855 | 0.855 | 0.913 |
| | KNN | 0.835 | 0.860 | 0.847 | 0.892 |
| | | | | | |
| **LRRK2** | **XGBoost** | **0.979** | **0.995** | **0.987** | **0.939** |
| | Logistic Reg. | 0.975 | 0.994 | 0.985 | 0.858 |
| | Random Forest | 0.972 | 0.966 | 0.969 | 0.931 |
| | KNN | 0.958 | 0.989 | 0.973 | 0.800 |
| | | | | | |
| **SLC6A3** | **XGBoost** | 0.910 | **0.971** | **0.940** | **0.949** |
| | Logistic Reg. | **0.939** | 0.936 | 0.938 | 0.940 |
| | Random Forest | 0.927 | 0.881 | 0.903 | 0.934 |
| | KNN | 0.862 | 0.897 | 0.879 | 0.904 |

---

## Why is XGBoost Usually the Best?

Across nearly all targets, **XGBoost** achieved the highest ROC-AUC and F1-Scores. Here is the technical explanation for why it outperformed Logistic Regression, Random Forest, and KNN on this chemoinformatics dataset:

1. **Handling Non-Linearity in Chemical Space**: 
   Chemical properties (like LogP, Molecular Weight, and Fingerprints) rarely have a strict linear relationship with biological activity. Logistic Regression struggles here because it attempts to fit a linear decision boundary. XGBoost (being a tree-based ensemble) naturally captures highly complex, non-linear relationships.
   
2. **Sequential Learning vs. Independent Voting**: 
   Both Random Forest and XGBoost are ensemble methods (they use many decision trees). However, Random Forest trains trees *independently* in parallel. XGBoost uses **Gradient Boosting**, meaning each new tree is specifically trained to correct the *errors (residuals)* made by the previous trees. This makes XGBoost highly optimized for tough edge cases where chemical structures are similar but have different bioactivities (activity cliffs).

3. **Feature Interactions (Fingerprints)**:
   Morgan fingerprints represent the presence or absence of molecular substructures. The bioactivity of a molecule often depends on the *combination* of substructures rather than them acting alone. XGBoost handles multi-feature interactions deeply and efficiently, whereas KNN treats all features with equal distance metrics (which dilutes important features with noise).

4. **Robustness to Class Imbalance**:
   Our datasets frequently have unequal distributions of active vs. inactive compounds. XGBoost optimizes specific loss functions (like logloss) and manages imbalanced classifications much more elegantly than KNN (which often defaults to the majority class in the neighborhood).

### When did Logistic Regression Win?
Logistic Regression won on a few smaller targets like **COMT** and **SNCA**. When the dataset is very small (e.g., COMT has an N_total of 139), complex models like XGBoost can overfit the training data, while simpler linear models like Logistic Regression generalize better.
