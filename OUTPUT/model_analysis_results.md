# Parkinson's Disease Target Models: Results Analysis

We've successfully extracted, featurized, and modeled real-world bioactivity data from ChEMBL for key Parkinson's Disease (PD) gene targets. Here is a comprehensive breakdown of what we can retrieve from the results.

## 1. The Dataset Retrieved

The pipeline aggregated **35,909 unique compounds** across **12 viable PD gene targets**. Each compound was featurized into 1031 numeric features (1024-bit Morgan Fingerprints + 7 physicochemical descriptors).

| Top Targets | Total Compounds | Notes |
| :--- | :--- | :--- |
| **DRD2** | 8,946 | The largest dataset, critical for dopaminergic targeting. |
| **ADORA2A** | 7,002 | Highly relevant for non-dopaminergic symptom management. |
| **MAO_B** | 5,201 | A classic PD target (inhibitors like Selegiline/Rasagiline). |
| **LRRK2** | 4,285 | Major genetic target for familial/sporadic PD. |
| **SLC6A3** (DAT) | 3,205 | Dopamine transporter, vital for neurotransmitter regulation. |

> [!NOTE]
> Three targets (**PARKIN**, **GRIN1_2**, and **PINK1**) yielded insufficient data (fewer than 6 labeled compounds each) and were safely skipped by the pipeline.

## 2. Model Performance: XGBoost vs. Logistic Regression

By running both algorithms on the exact same train/test splits, we can directly compare their predictive power for classifying a compound as *Active* (potency $\leq$ 1000 nM) or *Inactive* (potency $\geq$ 10000 nM).

### Overall Accuracy & ROC-AUC
Both models performed exceptionally well, with **ROC-AUC scores consistently above 0.88** and often pushing past 0.95. This indicates both models are highly capable of ranking active compounds above inactive ones.

### The Trade-off: Sensitivity vs. Specificity
Because the ChEMBL database is naturally imbalanced (researchers test and publish far more "Active" compounds than "Inactive" ones), the models exhibit a classic trade-off:

*   **XGBoost** leans towards higher **Sensitivity (Recall)**. It is better at catching almost every active compound. For example, on **DRD2**, XGBoost achieved a **98.4% Recall** (missing almost nothing), but a lower Specificity (49.8%).
*   **Logistic Regression** leans towards higher **Specificity**. It is slightly more conservative and better at identifying true negatives. On **DRD2**, LR achieved a **65.3% Specificity** (fewer false positives) but dropped Recall to 93.6%.

### Highlighted Target: MAO_B
MAO_B had the most balanced dataset (2,480 Active / 2,721 Inactive). Here, the comparison is very pure:
*   **XGBoost**: 86.6% Accuracy \| 87.3% Recall \| 86.0% Specificity \| **0.939 ROC-AUC**
*   **Logistic Regression**: 82.8% Accuracy \| 81.8% Recall \| 83.7% Specificity \| **0.887 ROC-AUC**
*   *Conclusion:* XGBoost handles the non-linear fingerprint relationships slightly better than the linear model when classes are balanced.

## 3. What Can We Retrieve & Do Next?

With these generated files, you now have a powerful toolkit for chemoinformatics:

1.  **Virtual Screening (Drug Discovery):** You can take any novel chemical structure, convert it to a SMILES string, generate its 1031 features, and feed it into these trained models to predict if it will be an active drug candidate for LRRK2, MAO_B, or DRD2.
2.  **Multi-Target Profiling:** You can evaluate a single compound across *all 12 models* to predict its target profile (e.g., finding a drug that activates DRD2 but cleanly avoids CHRM to minimize side effects).
3.  **Physical Data Extraction:** The raw `bioactivity_<gene>.csv` files contain the exact SMILES structures and nanomolar potencies of every compound. You can retrieve the exact chemical structures of the top 10 most potent LRRK2 inhibitors known to science.

> [!TIP]
> **Next Steps:** If you'd like, I can write a short prediction script that takes a brand new SMILES string (like Aspirin or a novel synthesized compound) and uses your trained XGBoost models to predict its activity across all 12 Parkinson's targets!
