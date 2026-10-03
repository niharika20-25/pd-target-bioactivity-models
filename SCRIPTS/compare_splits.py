import pandas as pd
import numpy as np

df_75 = pd.read_csv("OUTPUT/extended_model_comparison_results.csv")
df_80 = pd.read_csv("OUTPUT/extended_model_comparison_results_80_20.csv")

# We want to compare ROC-AUC for Random Split, maybe Scaffold Split too.
# Let's merge them
merged = pd.merge(df_75, df_80, on=["Gene", "Model", "Split"], suffixes=("_7525", "_8020"))

# Calculate differences
merged["ROC-AUC_Diff"] = merged["ROC-AUC_8020"] - merged["ROC-AUC_7525"]
merged["F1_Diff"] = merged["F1_8020"] - merged["F1_7525"]

print("=== 80/20 vs 75/25 Split Comparison (ROC-AUC & F1-score) ===\n")
print(f"Overall average ROC-AUC change: {merged['ROC-AUC_Diff'].mean():.4f}")
print(f"Overall average F1-score change: {merged['F1_Diff'].mean():.4f}\n")

print("By Model (Average ROC-AUC change):")
print(merged.groupby("Model")["ROC-AUC_Diff"].mean().to_string())

print("\nBy Split Type (Average ROC-AUC change):")
print(merged.groupby("Split")["ROC-AUC_Diff"].mean().to_string())

print("\nDetailed breakdown (first 10 rows):")
cols = ["Gene", "Model", "Split", "ROC-AUC_7525", "ROC-AUC_8020", "ROC-AUC_Diff"]
print(merged[cols].head(10).to_string(index=False))

# We can also write this to a markdown table for the artifact
with open("OUTPUT/split_comparison_summary.md", "w") as f:
    f.write("# 80/20 vs 75/25 Split Comparison (XGBoost & Logistic Regression)\n\n")
    f.write(f"**Overall average ROC-AUC change:** {merged['ROC-AUC_Diff'].mean():.4f}\n\n")
    f.write(f"**Overall average F1-score change:** {merged['F1_Diff'].mean():.4f}\n\n")
    
    f.write("### Average ROC-AUC Change by Model\n")
    f.write(merged.groupby("Model")[["ROC-AUC_Diff"]].mean().reset_index().to_markdown(index=False) + "\n\n")
    
    f.write("### Average ROC-AUC Change by Split Type\n")
    f.write(merged.groupby("Split")[["ROC-AUC_Diff"]].mean().reset_index().to_markdown(index=False) + "\n\n")
    
    f.write("### Detailed Target Comparison (ROC-AUC)\n")
    f.write(merged[cols].to_markdown(index=False) + "\n")
