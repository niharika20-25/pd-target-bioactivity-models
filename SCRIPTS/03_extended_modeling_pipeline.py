import os
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import StratifiedKFold, GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)
import warnings
warnings.filterwarnings('ignore')

def get_scaffold(smiles):
    try:
        mol = Chem.MolFromSmiles(smiles)
        return MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False)
    except:
        return None

def scaffold_split(df, test_size=0.25, random_state=42):
    # Using dataframe indices isn't safe if the index is non-unique or string. 
    # Better to use integer iloc ranges.
    df = df.reset_index(drop=True)
    if 'scaffold' not in df.columns:
        df['scaffold'] = df['canonical_smiles'].apply(get_scaffold)
    
    scaffold_groups = df.groupby('scaffold').indices
    scaffolds = list(scaffold_groups.keys())
    np.random.seed(random_state)
    np.random.shuffle(scaffolds)
    
    train_idx, test_idx = [], []
    target_test_size = int(len(df) * test_size)
    
    for scaffold in scaffolds:
        indices = scaffold_groups[scaffold]
        if len(test_idx) + len(indices) <= target_test_size:
            test_idx.extend(indices)
        else:
            train_idx.extend(indices)
            
    return train_idx, test_idx

def compute_metrics(y_true, y_pred, y_proba):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    spec = tn / (tn + fp) if (tn + fp) > 0 else np.nan
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "Specificity": spec,
        "F1": f1_score(y_true, y_pred, zero_division=0),
        "ROC-AUC": roc_auc_score(y_true, y_proba) if len(set(y_true)) > 1 else np.nan,
        "TN": tn, "FP": fp, "FN": fn, "TP": tp
    }

def main():
    if not os.path.exists("INPUT/featurized_bioactivity_dataset.csv"):
        print("Data not found!")
        return
        
    df = pd.read_csv("INPUT/featurized_bioactivity_dataset.csv")
    raw_df = pd.read_csv("INPUT/bioactivity_all_genes_combined.csv")
    
    # Merge canonical_smiles and pchembl_value (if we want to use pIC50)
    raw_df["pIC50"] = raw_df["standard_value_nM"].apply(lambda x: -np.log10(x * 1e-9) if x > 0 else np.nan)
    df = df.merge(raw_df[["molecule_chembl_id", "gene", "canonical_smiles", "pIC50"]], on=["molecule_chembl_id", "gene"], how="left")
    
    feature_cols = [c for c in df.columns if c.startswith("fp_") or c in [
        "MolWt", "LogP", "TPSA", "NumHDonors", "NumHAcceptors", "NumRotBonds", "NumAromRings"
    ]]
    
    df['scaffold'] = df['canonical_smiles'].apply(get_scaffold)
    
    results = []
    error_cases = []
    
    models = {
        "XGBoost": {
            "model": XGBClassifier(eval_metric="logloss", random_state=42),
            "params": {
                "classifier__n_estimators": [100, 200],
                "classifier__max_depth": [3, 4],
                "classifier__learning_rate": [0.05, 0.1]
            }
        },
        "LogisticRegression": {
            "model": LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42),
            "params": {
                "classifier__C": [0.1, 1.0, 10.0]
            }
        }
    }
    
    MIN_SAMPLES = 20
    MIN_CLASS = 6
    
    # Stratified K-Fold
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    for gene, gdf in df.groupby("gene"):
        class_counts = gdf["label"].value_counts()
        if len(gdf) < MIN_SAMPLES or (len(class_counts) > 0 and class_counts.min() < MIN_CLASS):
            continue
            
        print(f"\n--- Processing {gene} (N={len(gdf)}) ---")
        
        gdf = gdf.reset_index(drop=True)
        
        # 1. Splits
        # Random Split
        rand_train_idx, rand_test_idx = train_test_split(
            gdf.index, test_size=0.25, random_state=42, stratify=gdf["label"]
        )
        
        # Scaffold Split
        scaff_train_idx, scaff_test_idx = scaffold_split(gdf, test_size=0.25, random_state=42)
        
        splits = {
            "Random": (rand_train_idx, rand_test_idx),
            "Scaffold": (scaff_train_idx, scaff_test_idx)
        }
        
        for split_name, (train_idx, test_idx) in splits.items():
            if len(train_idx) == 0 or len(test_idx) == 0:
                print(f"Skipping {split_name} split for {gene} due to zero size.")
                continue
                
            train_df = gdf.iloc[train_idx]
            test_df = gdf.iloc[test_idx]
            
            X_train, y_train = train_df[feature_cols].values, train_df["label"].values
            X_test, y_test = test_df[feature_cols].values, test_df["label"].values
            
            if len(np.unique(y_train)) < 2:
                print(f"Skipping {split_name} split for {gene} due to single class in train.")
                continue
            
            for model_name, m_config in models.items():
                print(f"Training {model_name} on {split_name} split...")
                
                pipeline = Pipeline([
                    ('scaler', StandardScaler()),
                    ('classifier', m_config["model"])
                ])
                
                grid = GridSearchCV(
                    pipeline, param_grid=m_config["params"], 
                    cv=cv, scoring='roc_auc', n_jobs=-1
                )
                
                grid.fit(X_train, y_train)
                best_model = grid.best_estimator_
                
                # CV results
                cv_auc = grid.cv_results_['mean_test_score'][grid.best_index_]
                cv_std = grid.cv_results_['std_test_score'][grid.best_index_]
                
                # Test set evaluation
                y_pred = best_model.predict(X_test)
                y_proba = best_model.predict_proba(X_test)[:, 1]
                
                metrics = compute_metrics(y_test, y_pred, y_proba)
                
                res = {
                    "Gene": gene,
                    "Model": model_name,
                    "Split": split_name,
                    "Best_Params": str(grid.best_params_),
                    "CV_ROC-AUC_mean": cv_auc,
                    "CV_ROC-AUC_std": cv_std,
                    "Test_Size": len(test_df),
                    "Train_Size": len(train_df),
                    **metrics
                }
                results.append(res)
                
                # Collect error analysis cases
                for i, idx in enumerate(test_idx):
                    actual = y_test[i]
                    pred = y_pred[i]
                    if actual == 1 and pred == 1: cat = "TP"
                    elif actual == 0 and pred == 0: cat = "TN"
                    elif actual == 0 and pred == 1: cat = "FP"
                    else: cat = "FN"
                    
                    row = gdf.iloc[idx]
                    error_cases.append({
                        "Compound_ID": row.get("molecule_chembl_id", ""),
                        "Target": gene,
                        "SMILES": row["canonical_smiles"],
                        "pIC50": row.get("pIC50", ""),
                        "Assay_ID": row.get("assay_chembl_id", ""),
                        "Actual": actual,
                        "Predicted": pred,
                        "Probability": y_proba[i],
                        "Category": cat,
                        "Model": model_name,
                        "Split": split_name
                    })

    res_df = pd.DataFrame(results)
    res_df.to_csv("OUTPUT/extended_model_comparison_results.csv", index=False)
    print("\nSaved overall results to OUTPUT/extended_model_comparison_results.csv")
    
    # Process error cases
    err_df = pd.DataFrame(error_cases)
    
    # Save first 20 of each category
    sampled_errs = err_df.groupby("Category").head(20)
    sampled_errs.to_csv("OUTPUT/error_analysis_examples.csv", index=False)
    print("Saved sampled error cases to OUTPUT/error_analysis_examples.csv")
    
    # Print TP/TN/FP/FN counts (total across everything)
    print("\nTotal Prediction Categories:")
    print(err_df["Category"].value_counts())
    
    # Find compound in all four categories
    # We want a compound (canonical_smiles) that has TP, TN, FP, FN
    print("\nSearching for a compound in all four categories...")
    
    agg = err_df.groupby("SMILES")["Category"].unique()
    four_cat_smiles = agg[agg.apply(lambda x: len(set(x)) == 4)].index.tolist()
    
    if len(four_cat_smiles) > 0:
        print(f"Found {len(four_cat_smiles)} compounds that appeared in all four categories!")
        all_four_df = err_df[err_df["SMILES"].isin(four_cat_smiles)]
        all_four_df.to_csv("OUTPUT/compound_all_four_categories.csv", index=False)
        print("Saved to OUTPUT/compound_all_four_categories.csv")
    else:
        print("No single compound appeared in all four categories across all contexts.")
        # Create an empty CSV to satisfy requirement
        pd.DataFrame(columns=err_df.columns).to_csv("OUTPUT/compound_all_four_categories.csv", index=False)
        
        # Let's try matching by molecule_chembl_id in case smiles differed
        agg2 = err_df.groupby("Compound_ID")["Category"].unique()
        four_cat_id = agg2[agg2.apply(lambda x: len(set(x)) == 4)].index.tolist()
        if len(four_cat_id) > 0:
            print(f"Wait, found matching via Compound_ID: {four_cat_id}")
            all_four_df = err_df[err_df["Compound_ID"].isin(four_cat_id)]
            all_four_df.to_csv("OUTPUT/compound_all_four_categories.csv", index=False)

if __name__ == "__main__":
    main()
