# ==============================================================================
# 2026 Niharika Rai. 
# ==============================================================================

"""
LOGISTIC REGRESSION — FULL PIPELINE: FETCH REAL CHEMBL DATA -> FEATURIZE -> TRAIN -> EVALUATE
=============================================================================

Identical STEP 1-3 to the XGBoost script (same data, same features, same
train/test split via random_state=42) so the two models are directly
comparable — only STEP 4's classifier differs.


    pip install chembl_webresource_client rdkit pandas numpy scikit-learn matplotlib

OUTPUT FILES:
  bioactivity_<gene>.csv                 raw labeled data per gene
  bioactivity_all_genes_combined.csv     all genes combined
  featurized_bioactivity_dataset.csv     numeric features + labels
  logistic_regression_bioactivity_results_per_gene.csv
  lr_bioactivity_confusion_matrices/<gene>_confusion_matrix.png
=============================================================================
"""

import os
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from chembl_webresource_client.new_client import new_client
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, rdFingerprintGenerator

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, matthews_corrcoef,
    confusion_matrix, ConfusionMatrixDisplay,
)

# =============================================================================
# CONFIG (identical to the XGBoost script)
# =============================================================================
ACTIVE_THRESHOLD_NM = 1000
INACTIVE_THRESHOLD_NM = 10000
BIOACTIVITY_TYPES = ["IC50", "Ki", "EC50"]

FP_SIZE = 1024
MIN_TOTAL_SAMPLES = 20
MIN_SAMPLES_PER_CLASS = 6

OUT_DIR = "lr_bioactivity_confusion_matrices"
os.makedirs(OUT_DIR, exist_ok=True)

GENE_SEARCH_TERMS = {
    "LRRK2":    ["LRRK2", "Leucine-rich repeat serine/threonine-protein kinase 2"],
    "MAO_B":    ["MAOB", "Monoamine oxidase B"],
    "ADORA2A":  ["ADORA2A", "Adenosine receptor A2a"],
    "COMT":     ["COMT", "Catechol O-methyltransferase"],
    "GBA1":     ["GBA", "GBA1", "Glucosylceramidase", "Lysosomal acid glucosylceramidase"],
    "DRD2":     ["DRD2", "Dopamine D2 receptor"],
    "DRD1":     ["DRD1", "Dopamine D1 receptor"],
    "GLP1R":    ["GLP1R", "Glucagon-like peptide 1 receptor"],
    "PINK1":    ["PINK1", "Serine/threonine-protein kinase PINK1"],
    "PARKIN":   ["PARK2", "PRKN", "Parkin", "E3 ubiquitin-protein ligase parkin"],
    "SNCA":     ["SNCA", "Alpha-synuclein"],
    "GRIN1_2":  ["GRIN1", "NMDA receptor subunit 1", "GRIN2A", "GRIN2B"],
    "CHRM":     ["CHRM1", "CHRM2", "CHRM3", "CHRM4", "Muscarinic acetylcholine receptor"],
    "SLC18A2":  ["SLC18A2", "VMAT2", "Synaptic vesicular amine transporter"],
    "SLC6A3":   ["SLC6A3", "DAT1", "Sodium-dependent dopamine transporter"],
}

DESCRIPTOR_FUNCS = {
    "MolWt":          Descriptors.MolWt,
    "LogP":           Descriptors.MolLogP,
    "TPSA":           Descriptors.TPSA,
    "NumHDonors":     Lipinski.NumHDonors,
    "NumHAcceptors":  Lipinski.NumHAcceptors,
    "NumRotBonds":    Descriptors.NumRotatableBonds,
    "NumAromRings":   Descriptors.NumAromaticRings,
}
morgan_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=FP_SIZE)


# =============================================================================
# STEP 1: FETCH REAL BIOACTIVITY DATA FROM CHEMBL (with retry logic)
# =============================================================================
MAX_RETRIES = 5
RETRY_DELAY_BASE = 15   # seconds; doubles each retry


def _retry(func, description, max_retries=MAX_RETRIES):
    """Call `func()` with exponential-backoff retries on network errors."""
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except (ConnectionError, OSError, Exception) as exc:
            # Only retry on network-related errors
            exc_str = str(exc).lower()
            is_network = any(kw in exc_str for kw in [
                "connection", "timeout", "no route", "errno 65",
                "reset by peer", "broken pipe", "eof",
            ])
            if not is_network:
                raise
            delay = RETRY_DELAY_BASE * (2 ** (attempt - 1))
            print(f"  ⚠ {description}: network error (attempt {attempt}/{max_retries}): {exc}")
            if attempt == max_retries:
                print(f"  ✘ {description}: all {max_retries} retries exhausted — skipping")
                return None
            print(f"    Retrying in {delay}s …")
            time.sleep(delay)
    return None


def fetch_bioactivity_data():
    target_client = new_client.target
    activity_client = new_client.activity
    all_rows = []

    for gene, search_terms in GENE_SEARCH_TERMS.items():
        print(f"\n=== Fetching {gene} ===")
        chosen_target_id = None

        for term in search_terms:
            def _search(t=term):
                return list(target_client.search(t))

            hits = _retry(_search, f"{gene} target search '{term}'")
            if hits is None:
                continue
            for hit in hits:
                if (hit.get("organism") == "Homo sapiens"
                        and hit.get("target_type") == "SINGLE PROTEIN"):
                    chosen_target_id = hit["target_chembl_id"]
                    print(f"  Matched via '{term}': {hit['pref_name']} ({chosen_target_id})")
                    break
            if chosen_target_id:
                break

        if not chosen_target_id:
            print(f"  !! No single-protein human target found for {gene} — skipping")
            continue

        def _fetch_activities(tid=chosen_target_id):
            return list(activity_client.filter(
                target_chembl_id=tid,
                standard_type__in=BIOACTIVITY_TYPES,
                standard_units="nM",
                standard_value__isnull=False,
            ).only([
                "molecule_chembl_id", "canonical_smiles", "standard_type",
                "standard_value", "standard_units",
            ]))

        activities = _retry(_fetch_activities, f"{gene} activity download")
        if activities is None:
            print(f"  !! Could not download activities for {gene} — skipping")
            continue

        gene_rows = []
        for act in activities:
            smi, val = act.get("canonical_smiles"), act.get("standard_value")
            if smi is None or val is None:
                continue
            val = float(val)
            if val <= ACTIVE_THRESHOLD_NM:
                label = 1
            elif val >= INACTIVE_THRESHOLD_NM:
                label = 0
            else:
                continue
            gene_rows.append({
                "gene": gene, "target_chembl_id": chosen_target_id,
                "molecule_chembl_id": act.get("molecule_chembl_id"),
                "canonical_smiles": smi, "standard_type": act.get("standard_type"),
                "standard_value_nM": val, "label": label,
            })

        df_gene = pd.DataFrame(gene_rows)
        # Remove compounds with conflicting labels across assays, then deduplicate
        if len(df_gene) > 0:
            ambiguous = df_gene.groupby("canonical_smiles")["label"].nunique()
            ambiguous_smiles = ambiguous[ambiguous > 1].index
            df_gene = df_gene[~df_gene["canonical_smiles"].isin(ambiguous_smiles)]
        df_gene = df_gene.drop_duplicates(subset="canonical_smiles")
        print(f"  {len(df_gene)} labeled compounds "
              f"({(df_gene['label']==1).sum() if len(df_gene) else 0} active / "
              f"{(df_gene['label']==0).sum() if len(df_gene) else 0} inactive)")
        df_gene.to_csv(f"bioactivity_{gene}.csv", index=False)
        all_rows.append(df_gene)

    combined = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    combined.to_csv("bioactivity_all_genes_combined.csv", index=False)
    print(f"\nTotal combined dataset: {len(combined)} rows across {combined['gene'].nunique() if len(combined) else 0} genes")
    return combined


# =============================================================================
# STEP 2: FEATURIZE — SMILES -> NUMERIC FEATURES (identical to XGBoost script)
# =============================================================================
def featurize_smiles(smiles: str):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    row = {name: func(mol) for name, func in DESCRIPTOR_FUNCS.items()}
    fp_arr = np.array(morgan_gen.GetFingerprint(mol))
    for i, bit in enumerate(fp_arr):
        row[f"fp_{i}"] = int(bit)
    return row


def featurize_dataset(combined_df):
    print("\n=== Featurizing compounds (SMILES -> descriptors + fingerprint) ===")
    feature_rows, valid_idx, n_invalid = [], [], 0
    for idx, smi in combined_df["canonical_smiles"].items():
        feats = featurize_smiles(smi)
        if feats is None:
            n_invalid += 1
            continue
        feature_rows.append(feats)
        valid_idx.append(idx)

    print(f"Featurized {len(feature_rows)} valid molecules ({n_invalid} invalid SMILES dropped)")
    feat_df = pd.DataFrame(feature_rows, index=valid_idx)
    result = combined_df.loc[valid_idx, ["gene", "molecule_chembl_id", "label"]].join(feat_df)
    result.to_csv("featurized_bioactivity_dataset.csv", index=False)
    return result


# =============================================================================
# STEP 3: METRICS HELPER
# =============================================================================
def compute_all_metrics(y_true, y_pred, y_proba):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    specificity = tn / (tn + fp) if (tn + fp) > 0 else np.nan
    return {
        "Accuracy":    accuracy_score(y_true, y_pred),
        "Precision":   precision_score(y_true, y_pred, zero_division=0),
        "Recall/Sens": recall_score(y_true, y_pred, zero_division=0),
        "Specificity": specificity,
        "F1-score":    f1_score(y_true, y_pred, zero_division=0),
        "ROC-AUC":     roc_auc_score(y_true, y_proba) if len(set(y_true)) > 1 else np.nan,
        "PR-AUC":      average_precision_score(y_true, y_proba) if len(set(y_true)) > 1 else np.nan,
        "MCC":         matthews_corrcoef(y_true, y_pred),
        "TN": tn, "FP": fp, "FN": fn, "TP": tp,
    }


# =============================================================================
# STEP 4: TRAIN + EVALUATE LOGISTIC REGRESSION, ONE MODEL PER GENE
# =============================================================================
def train_and_evaluate(featurized_df):
    print("\n=== Training Logistic Regression per gene ===")
    feature_cols = [c for c in featurized_df.columns
                    if c not in ("gene", "molecule_chembl_id", "label")]
    results, skipped = [], []

    for gene, gdf in featurized_df.groupby("gene"):
        n = len(gdf)
        class_counts = gdf["label"].value_counts()
        min_class_count = class_counts.min() if len(class_counts) > 0 else 0

        if n < MIN_TOTAL_SAMPLES or min_class_count < MIN_SAMPLES_PER_CLASS:
            skipped.append((gene, n, dict(class_counts)))
            continue

        X, y = gdf[feature_cols].values, gdf["label"].values
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        # Logistic Regression is scale-sensitive -> scaling is REQUIRED
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        # C=1.0 (moderate L2 regularization) guards against overfitting
        # given ~1000+ fingerprint-bit features vs. often-small compound counts
        model = LogisticRegression(C=1.0, solver="lbfgs", max_iter=2000, random_state=42)
        model.fit(X_train_s, y_train)
        y_pred = model.predict(X_test_s)
        y_proba = model.predict_proba(X_test_s)[:, 1]

        m = compute_all_metrics(y_test, y_pred, y_proba)
        m["Gene"], m["N_total"] = gene, n
        results.append(m)

        cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
        disp = ConfusionMatrixDisplay(cm, display_labels=["Inactive", "Active"])
        fig, ax = plt.subplots(figsize=(4, 4))
        disp.plot(ax=ax, cmap="Oranges", colorbar=False)
        ax.set_title(f"Logistic Regression — {gene}")
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/{gene}_confusion_matrix.png", dpi=120)
        plt.close(fig)

    if skipped:
        print("\nSkipped genes (not enough compounds for a reliable split):")
        for gene, n, counts in skipped:
            print(f"  {gene}: N={n}, class counts={counts}")

    if not results:
        print("\nNo gene had enough data to model.")
        return None

    results_df = pd.DataFrame(results).set_index("Gene")
    col_order = ["N_total", "Accuracy", "Precision", "Recall/Sens", "Specificity",
                 "F1-score", "ROC-AUC", "PR-AUC", "MCC", "TN", "FP", "FN", "TP"]
    results_df = results_df[col_order].round(3)

    print("\n" + "=" * 100)
    print("LOGISTIC REGRESSION — REAL BIOACTIVITY RESULTS, PER GENE")
    print("=" * 100)
    print(results_df.to_string())
    results_df.to_csv("logistic_regression_bioactivity_results_per_gene.csv")
    print("\nSaved: logistic_regression_bioactivity_results_per_gene.csv")
    print(f"Confusion matrices: {OUT_DIR}/")
    return results_df


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    if os.path.exists("featurized_bioactivity_dataset.csv"):
        print("Loading previously featurized dataset to save time...")
        featurized = pd.read_csv("featurized_bioactivity_dataset.csv")
    else:
        combined = fetch_bioactivity_data()
        if len(combined) == 0:
            raise SystemExit("No data fetched from ChEMBL — check your internet connection / target search terms.")
        featurized = featurize_dataset(combined)
    train_and_evaluate(featurized)
