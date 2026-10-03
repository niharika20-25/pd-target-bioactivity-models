# Parkinson's Disease Target Models

## Overview
This project focuses on extracting, processing, featurizing, and modeling real-world bioactivity data for key Parkinson's Disease (PD) gene targets. The goal is to build machine learning models that can predict whether a given chemical compound is an active drug candidate against these specific gene targets.

## Phase 1: Baseline Pipeline

### Data Collection & Preprocessing
- Extracted bioactivity data from the ChEMBL database for important PD gene targets (e.g., **DRD2, ADORA2A, MAO_B, LRRK2, SLC6A3**).
- Filtered and aggregated the data resulting in a dataset of **35,909 unique compounds** across 12 viable PD gene targets. (Note: Targets with insufficient data like PARKIN, GRIN1_2, and PINK1 were skipped).

### Featurization
- Converted the chemical structures (SMILES strings) of the compounds into **1,031 numeric features**, consisting of 1,024-bit Morgan Fingerprints (ECFP4) and 7 physicochemical descriptors (MolWt, LogP, TPSA, NumHDonors, NumHAcceptors, NumRotBonds, NumAromRings).

### Machine Learning Modeling (Random Split)
- Implemented full machine learning pipelines to classify compounds into *Active* (potency ≤ 1000 nM) or *Inactive* (potency ≥ 10000 nM).
- Used a 75/25 random train/test split with `stratify` and `random_state=42`.
- Trained and evaluated two models per gene:
  - **XGBoost:** Very high sensitivity/recall; ROC-AUC scores often > 0.93.
  - **Logistic Regression:** Strong baseline with higher specificity.

### Analysis & Comparison
- Generated model evaluation metrics (Accuracy, Precision, Recall, Specificity, F1, ROC-AUC) for both models per gene.
- Wrote a custom comparison script (`compare_models.py`) that merges the results from both models and automatically determines the best performing model based on ROC-AUC scores for each target.
- Summarized the results in a detailed markdown report (`model_analysis_results.md`).

---

## Phase 2: Mentor-Required Extensions

### 1. Molecular Scaffold Split
- Implemented Bemis-Murcko scaffold splitting using RDKit.
- Scaffolds are assigned to either train or test without overlap to test true generalization.
- Both XGBoost and Logistic Regression were trained and evaluated under scaffold split, alongside the existing random split for direct comparison.
- **Key finding:** Scaffold split generally results in lower metrics than random split, especially for Specificity. This is expected—random splits can overestimate performance due to structurally similar compounds leaking across train/test.

### 2. Correlation Analysis
- Computed Pearson correlations among the 7 physicochemical descriptors and pIC50.
- **Key findings:**
  - MolWt, TPSA, NumHDonors, NumHAcceptors, and NumRotBonds are all highly correlated with each other (r > 0.96), reflecting that larger molecules naturally have more donors/acceptors/rotatable bonds.
  - LogP is inversely correlated with these (r ≈ -0.74 to -0.84).
  - pIC50 has weak positive correlation with all descriptors (r ≈ 0.24–0.29), indicating no single physicochemical property strongly predicts potency.
- Results saved to `OUTPUT/physicochemical_correlation.csv` and `OUTPUT/physicochemical_correlation.png`.

### 3. Duplicate & Conflicting Activity Analysis
- **1,170 compounds** appear across multiple gene targets (expected—the same molecule can be tested against different proteins).
- **220 compounds** have conflicting labels (Active for one target, Inactive for another). This is biologically valid—a molecule can strongly inhibit one protein but not another.
- Within any single gene target, there are **0 duplicate measurements**, because the original pipeline already deduplicated per target and dropped compounds with conflicting same-target labels.
- Detailed records saved to `OUTPUT/conflicting_activities_analysis.csv`.
- Note: Extended ChEMBL fields (assay_chembl_id, document_chembl_id) were not present in the original local dataset. The conflicting labels observed are cross-target, not within-target.

### 4. IC50 Analysis
- **0 missing** IC50 values in the local dataset.
- **0 duplicate** measurements for the same compound + same target (already handled by the original pipeline).
- pIC50 was calculated as `-log10(standard_value_nM × 1e-9)` for correlation and error analysis purposes.
- No averaging was needed since the data was already deduplicated per gene target.

### 5. Cross-Validation & Grid Search
- Used **5-fold StratifiedKFold** for cross-validation.
- Used **GridSearchCV** optimizing for ROC-AUC.
- **StandardScaler** embedded inside a `sklearn.Pipeline` to prevent data leakage.
- Parameter grids:
  - XGBoost: `n_estimators` ∈ {100, 200}, `max_depth` ∈ {3, 4}, `learning_rate` ∈ {0.05, 0.1}
  - Logistic Regression: `C` ∈ {0.1, 1.0, 10.0}
- Best parameters and CV results (mean ± SD) saved to `OUTPUT/extended_model_comparison_results.csv`.

### 6. TP/TN/FP/FN Error Analysis
- Categorized all test-set predictions across all genes, models, and splits.
- **Total counts:**
  - TP: 26,994 | TN: 5,240 | FP: 2,268 | FN: 1,402
- First 20 examples of each category saved to `OUTPUT/error_analysis_examples.csv`, including Compound ID, Target, SMILES, pIC50, Actual label, Predicted label, and Probability.

#### Compound in All Four Categories
- **8 compounds** were found that appear across all four categories (TP, TN, FP, FN) when considering different targets, models, and splits.
- This is biologically meaningful: the same compound can be Active against one target (correctly predicted → TP) and Inactive against another (correctly predicted → TN), while being misclassified in other contexts (FP, FN).
- A single prediction record logically cannot be all four categories simultaneously—but the same compound absolutely can appear in all four across different experimental contexts.
- Full details saved to `OUTPUT/compound_all_four_categories.csv`.

### 7. Final Comparison Summary

Performance is reported as held-out test set metrics. CV ROC-AUC (mean ± SD) is available in the extended results CSV.

| Target | Model | Split | Accuracy | Precision | Recall | Specificity | F1 | ROC-AUC |
|--------|-------|-------|----------|-----------|--------|-------------|-----|---------|
| MAO_B | XGBoost | Random | 0.885 | 0.877 | 0.882 | 0.887 | 0.879 | 0.949 |
| MAO_B | XGBoost | Scaffold | 0.795 | 0.762 | 0.783 | 0.805 | 0.772 | 0.891 |
| DRD2 | XGBoost | Random | 0.912 | 0.957 | 0.966 | 0.498 | 0.961 | 0.932 |
| DRD2 | XGBoost | Scaffold | 0.906 | 0.918 | 0.980 | 0.420 | 0.948 | 0.922 |

(Full results for all 12 genes × 2 models × 2 splits in `OUTPUT/extended_model_comparison_results.csv`.)

**Key observations:**
- Random split consistently outperforms scaffold split, as expected.
- XGBoost generally outperforms Logistic Regression on both splits.
- The performance drop under scaffold split is more pronounced for targets with less chemical diversity (e.g., LRRK2 Specificity drops dramatically).

---

## Directory Structure

### `INPUT/`
- `bioactivity_<gene>.csv` — Raw labeled data per gene from ChEMBL.
- `bioactivity_all_genes_combined.csv` — All genes combined (35,909 rows).
- `featurized_bioactivity_dataset.csv` — Numeric features + labels (1,031 features).

### `SCRIPTS/`
- `xgboost_full_pipeline_antigravity.py` — Original end-to-end XGBoost pipeline (fetch → featurize → train → evaluate).
- `logistic_regression_full_pipeline_antigravity.py` — Original end-to-end Logistic Regression pipeline.
- `compare_models.py` — Merges and compares the results of both original models.
- `01_local_data_analysis.py` — Duplicate & conflicting activity analysis; IC50 analysis using local data.
- `02_correlation_analysis.py` — Physicochemical descriptor correlation analysis with pIC50.
- `03_extended_modeling_pipeline.py` — Scaffold split, GridSearchCV, error analysis, compound-in-all-four-categories search.

### `OUTPUT/`
- `xgb_bioactivity_confusion_matrices/` — Original XGBoost confusion matrix images.
- `lr_bioactivity_confusion_matrices/` — Original Logistic Regression confusion matrix images.
- `xgboost_bioactivity_results_per_gene.csv` — Original XGBoost metrics per gene.
- `logistic_regression_bioactivity_results_per_gene.csv` — Original LR metrics per gene.
- `model_comparison_results.csv` — Original model comparison output.
- `model_analysis_results.md` — Original detailed analysis writeup.
- `physicochemical_correlation.csv` — Correlation matrix of descriptors + pIC50.
- `physicochemical_correlation.png` — Correlation heatmap.
- `conflicting_activities_analysis.csv` — Compounds with conflicting labels across targets.
- `extended_model_comparison_results.csv` — Full results: random vs scaffold, CV scores, best params, test metrics.
- `error_analysis_examples.csv` — First 20 TP, TN, FP, FN examples with compound details.
- `compound_all_four_categories.csv` — Compounds found in all four prediction categories across contexts.
- Presentation files (`.pptx`) summarizing the project and findings.
