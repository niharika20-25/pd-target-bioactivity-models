import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

def main():
    if not os.path.exists("INPUT/featurized_bioactivity_dataset.csv"):
        print("Data not found!")
        return

    print("Loading featurized data...")
    df = pd.read_csv("INPUT/featurized_bioactivity_dataset.csv")
    raw_df = pd.read_csv("INPUT/bioactivity_all_genes_combined.csv")

    features = [
        "MolWt", "LogP", "TPSA", "NumHDonors", 
        "NumHAcceptors", "NumRotBonds", "NumAromRings"
    ]
    
    # Calculate pIC50 in raw data
    # standard_value_nM is in raw_df
    # pIC50 = -log10(standard_value_nM * 1e-9)
    raw_df["pIC50"] = raw_df["standard_value_nM"].apply(lambda x: -np.log10(x * 1e-9) if x > 0 else np.nan)
    
    # Merge pIC50 into featurized df based on canonical_smiles and gene
    merged_df = df.merge(raw_df[["molecule_chembl_id", "gene", "pIC50"]], on=["molecule_chembl_id", "gene"], how="left")

    cols_to_correlate = features + ["pIC50"]

    print("\n=== Calculating Correlations ===")
    corr_matrix = merged_df[cols_to_correlate].corr(method='pearson')
    
    os.makedirs("OUTPUT", exist_ok=True)
    corr_matrix.to_csv("OUTPUT/physicochemical_correlation.csv")
    print("Saved correlation matrix to OUTPUT/physicochemical_correlation.csv")

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", vmin=-1, vmax=1)
    plt.title("Correlation Matrix of Physicochemical Descriptors & pIC50")
    plt.tight_layout()
    plt.savefig("OUTPUT/physicochemical_correlation.png", dpi=150)
    plt.close()
    print("Saved correlation plot to OUTPUT/physicochemical_correlation.png")

if __name__ == "__main__":
    main()
