# ==============================================================================
#  2026 Niharika Rai. 
# ==============================================================================

import pandas as pd

def main():
    # Load the results
    xgb_df = pd.read_csv("xgboost_bioactivity_results_per_gene.csv")
    lr_df = pd.read_csv("logistic_regression_bioactivity_results_per_gene.csv")
    
    # Merge them on Gene and N_total
    merged = pd.merge(xgb_df, lr_df, on=["Gene", "N_total"], suffixes=("_XGB", "_LR"))
    
    # Let's reorder columns to put the same metrics next to each other
    metrics = ["Accuracy", "Precision", "Recall/Sens", "Specificity", "F1-score", "ROC-AUC", "PR-AUC", "MCC", "TN", "FP", "FN", "TP"]
    
    ordered_cols = ["Gene", "N_total"]
    for m in metrics:
        ordered_cols.append(f"{m}_XGB")
        ordered_cols.append(f"{m}_LR")
        
    final_df = merged[ordered_cols].copy()
    
    # Determine the "winner" for ROC-AUC
    def get_winner(row):
        if row["ROC-AUC_XGB"] > row["ROC-AUC_LR"]:
            return "XGBoost"
        elif row["ROC-AUC_LR"] > row["ROC-AUC_XGB"]:
            return "Logistic Regression"
        else:
            return "Tie"
            
    final_df.insert(2, "Best_ROC_AUC", final_df.apply(get_winner, axis=1))
    
    # Save the file
    out_file = "model_comparison_results.csv"
    final_df.to_csv(out_file, index=False)
    print(f"Comparison saved to {out_file}")

if __name__ == "__main__":
    main()
