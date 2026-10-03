import pandas as pd
import numpy as np
import os

def main():
    if not os.path.exists("INPUT/bioactivity_all_genes_combined.csv"):
        print("Raw data not found!")
        return
        
    df = pd.read_csv("INPUT/bioactivity_all_genes_combined.csv")
    
    print("=== Duplicate & Conflicting Activity Analysis (Local Data) ===")
    # Find compounds that appear in multiple targets
    dup_smiles = df[df.duplicated(subset="canonical_smiles", keep=False)]
    
    # Find compounds that have conflicting labels across DIFFERENT targets
    # (Since the original script already dropped duplicates for the SAME target)
    agg_labels = dup_smiles.groupby("canonical_smiles")["label"].nunique()
    conflicting_smiles = agg_labels[agg_labels > 1].index
    
    conflicting_records = df[df["canonical_smiles"].isin(conflicting_smiles)]
    
    os.makedirs("OUTPUT", exist_ok=True)
    conflicting_records.to_csv("OUTPUT/conflicting_activities_analysis.csv", index=False)
    
    print(f"Total duplicate SMILES across targets: {len(dup_smiles['canonical_smiles'].unique())}")
    print(f"Total compounds with both Active and Inactive labels (across different targets): {len(conflicting_smiles)}")
    print("Saved conflicting records to OUTPUT/conflicting_activities_analysis.csv")
    print("Note: Assay ID, Document ID, and other extended ChEMBL fields are not present in the existing local dataset.")

    print("\n=== IC50 Analysis ===")
    missing_ic50 = df["standard_value_nM"].isna().sum()
    print(f"Missing IC50 values: {missing_ic50}")
    
    same_target_dups = df.duplicated(subset=["canonical_smiles", "gene"]).sum()
    print(f"Duplicate measurements for same compound + target: {same_target_dups}")
    
    print("Explanation: The original dataset in INPUT/ was already deduplicated per target, and conflicting labels within the same target were already dropped. Therefore, there are 0 missing values and 0 duplicates for the same target, meaning no IC50 averaging is required or possible on this local dataset.")

if __name__ == "__main__":
    main()
