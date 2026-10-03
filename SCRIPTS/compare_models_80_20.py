import pandas as pd
import os

def main():
    output_dir = "OUTPUT"
    
    # Read the combined 80/20 extended results
    ext_df = pd.read_csv(os.path.join(output_dir, "extended_model_comparison_results_80_20.csv"))
    
    # Filter for Random split (to match RF/KNN)
    ext_df = ext_df[ext_df["Split"] == "Random"].copy()
    
    # We need to reshape ext_df so that XGBoost and LogisticRegression have separate columns
    xgb_df = ext_df[ext_df["Model"] == "XGBoost"].copy()
    xgb_cols = {c: f"{c}_XGB" for c in xgb_df.columns if c not in ["Gene", "Model", "Split", "Best_Params", "CV_ROC-AUC_mean", "CV_ROC-AUC_std", "Test_Size", "Train_Size"]}
    # specifically rename Recall to Recall/Sens to match RF/KNN
    if "Recall" in xgb_df.columns:
        xgb_df.rename(columns={"Recall": "Recall/Sens"}, inplace=True)
        xgb_cols = {c: f"{c}_XGB" for c in xgb_df.columns if c not in ["Gene", "Model", "Split", "Best_Params", "CV_ROC-AUC_mean", "CV_ROC-AUC_std", "Test_Size", "Train_Size"]}
    xgb_df.rename(columns=xgb_cols, inplace=True)
    
    lr_df = ext_df[ext_df["Model"] == "LogisticRegression"].copy()
    if "Recall" in lr_df.columns:
        lr_df.rename(columns={"Recall": "Recall/Sens"}, inplace=True)
    lr_cols = {c: f"{c}_LR" for c in lr_df.columns if c not in ["Gene", "Model", "Split", "Best_Params", "CV_ROC-AUC_mean", "CV_ROC-AUC_std", "Test_Size", "Train_Size"]}
    lr_df.rename(columns=lr_cols, inplace=True)
    
    # Load RF and KNN
    rf_df = pd.read_csv(os.path.join(output_dir, "rf_bioactivity_results_per_gene_80_20.csv"))
    knn_df = pd.read_csv(os.path.join(output_dir, "knn_bioactivity_results_per_gene_80_20.csv"))
    
    rf_cols = {c: f"{c}_RF" for c in rf_df.columns if c != "Gene"}
    rf_df.rename(columns=rf_cols, inplace=True)
    
    knn_cols = {c: f"{c}_KNN" for c in knn_df.columns if c != "Gene"}
    knn_df.rename(columns=knn_cols, inplace=True)
    
    # Merge them all on Gene
    merged = pd.merge(xgb_df[["Gene"] + list(xgb_cols.values())], lr_df[["Gene"] + list(lr_cols.values())], on="Gene", how="outer")
    merged = pd.merge(merged, rf_df, on="Gene", how="outer")
    merged = pd.merge(merged, knn_df, on="Gene", how="outer")
    
    # Reorder columns
    metrics = ["Accuracy", "Precision", "Recall/Sens", "Specificity", "F1", "F1-score", "ROC-AUC", "PR-AUC", "MCC", "TN", "FP", "FN", "TP"]
    ordered_cols = ["Gene"]
    for m in metrics:
        if f"{m}_XGB" in merged.columns or f"{m}_LR" in merged.columns or f"{m}_RF" in merged.columns:
            # Note: in ext_df the metric is 'F1', in RF/KNN it's 'F1-score'
            # Let's handle variations gracefully by just taking whatever exists
            for suff in ["_XGB", "_LR", "_RF", "_KNN"]:
                col_name = f"{m}{suff}"
                if col_name in merged.columns:
                    ordered_cols.append(col_name)
                    
    # Ensure no duplicates in ordered_cols
    ordered_cols = list(dict.fromkeys(ordered_cols))
    
    final_df = merged[[c for c in ordered_cols if c in merged.columns]].copy()
    
    def get_winner(row):
        scores = {
            "XGBoost": row.get("ROC-AUC_XGB", 0) if pd.notna(row.get("ROC-AUC_XGB")) else 0,
            "Logistic Regression": row.get("ROC-AUC_LR", 0) if pd.notna(row.get("ROC-AUC_LR")) else 0,
            "Random Forest": row.get("ROC-AUC_RF", 0) if pd.notna(row.get("ROC-AUC_RF")) else 0,
            "KNN": row.get("ROC-AUC_KNN", 0) if pd.notna(row.get("ROC-AUC_KNN")) else 0,
        }
        if all(v == 0 for v in scores.values()):
            return "None"
        best = max(scores, key=scores.get)
        return best
            
    final_df.insert(1, "Best_ROC_AUC", final_df.apply(get_winner, axis=1))
    
    out_file = os.path.join(output_dir, "model_comparison_results_all_80_20.csv")
    final_df.to_csv(out_file, index=False)
    print(f"Comparison saved to {out_file}")

if __name__ == "__main__":
    main()
