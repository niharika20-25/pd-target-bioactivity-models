import os
import time
import requests
import numpy as np
import pandas as pd
from chembl_webresource_client.new_client import new_client
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, rdFingerprintGenerator

# =============================================================================
# CONFIG
# =============================================================================
ACTIVE_THRESHOLD_NM = 1000        # pIC50 >= 6.0
INACTIVE_THRESHOLD_NM = 10000     # pIC50 <= 5.0
BIOACTIVITY_TYPES = ["IC50", "Ki", "EC50"]

FP_SIZE = 1024

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

def fetch_bioactivity_data_fast():
    target_client = new_client.target
    all_rows = []

    for gene, search_terms in GENE_SEARCH_TERMS.items():
        print(f"\n=== Fetching {gene} ===")
        chosen_target_id = None
        for term in search_terms:
            try:
                hits = list(target_client.search(term))
                for hit in hits:
                    if hit.get("organism") == "Homo sapiens" and hit.get("target_type") == "SINGLE PROTEIN":
                        chosen_target_id = hit["target_chembl_id"]
                        print(f"  Matched via '{term}': {hit['pref_name']} ({chosen_target_id})")
                        break
                if chosen_target_id: break
            except:
                pass
            
        if not chosen_target_id:
            print(f"  !! No single-protein human target found for {gene} — skipping")
            continue

        gene_rows = []
        types_str = ",".join(BIOACTIVITY_TYPES)
        url = f"https://www.ebi.ac.uk/chembl/api/data/activity?target_chembl_id={chosen_target_id}&standard_type__in={types_str}&standard_value__isnull=false&limit=1000&format=json"
        
        while url:
            try:
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    activities = data.get("activities", [])
                    
                    for act in activities:
                        smi, val = act.get("canonical_smiles"), act.get("standard_value")
                        if smi is None or val is None: continue
                        val = float(val)
                        
                        pchembl = act.get("pchembl_value")
                        if pchembl is not None:
                            pchembl = float(pchembl)
                        else:
                            if val > 0: pchembl = -np.log10(val * 1e-9)
                            else: pchembl = np.nan
                                
                        label = None
                        if val <= ACTIVE_THRESHOLD_NM: label = 1
                        elif val >= INACTIVE_THRESHOLD_NM: label = 0
                            
                        gene_rows.append({
                            "gene": gene,
                            "target_chembl_id": chosen_target_id,
                            "molecule_chembl_id": act.get("molecule_chembl_id"),
                            "canonical_smiles": smi,
                            "standard_type": act.get("standard_type"),
                            "standard_value_nM": val,
                            "pchembl_value": pchembl,
                            "assay_chembl_id": act.get("assay_chembl_id"),
                            "document_chembl_id": act.get("document_chembl_id"),
                            "label": label
                        })
                    
                    # Next page
                    meta = data.get("page_meta", {})
                    url = meta.get("next")
                    if url:
                        url = "https://www.ebi.ac.uk" + url
                else:
                    print(f"Error {resp.status_code} fetching URL: {url}")
                    time.sleep(5)
            except Exception as e:
                print(f"Exception {e} fetching URL: {url}")
                time.sleep(5)

        df_gene = pd.DataFrame(gene_rows)
        print(f"  Downloaded {len(df_gene)} records for {gene}")
        all_rows.append(df_gene)

    combined = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    combined.to_csv("INPUT/bioactivity_extended_raw.csv", index=False)
    print(f"\nTotal combined raw dataset: {len(combined)} rows")
    return combined

def analyze_duplicates_and_ic50(raw_df):
    print("\n=== Analyzing Duplicates & Conflicting Activities ===")
    labeled_df = raw_df.dropna(subset=["label"]).copy()
    
    agg_labels = labeled_df.groupby(["canonical_smiles", "gene"])["label"].nunique()
    conflicting_idx = agg_labels[agg_labels > 1].index
    
    conflicting_records = raw_df.set_index(["canonical_smiles", "gene"]).loc[conflicting_idx].reset_index()
    conflicting_records.to_csv("OUTPUT/conflicting_activities_analysis.csv", index=False)
    print(f"Found {len(conflicting_idx)} compound-target pairs with conflicting labels (Saved {len(conflicting_records)} records to OUTPUT/conflicting_activities_analysis.csv)")

    print("\n=== IC50 Analysis & Processing ===")
    missing_ic50 = raw_df["standard_value_nM"].isna().sum()
    print(f"Missing IC50 values in downloaded data: {missing_ic50}")
    
    clean_df = raw_df.dropna(subset=["pchembl_value"]).copy()
    grouped = clean_df.groupby(["canonical_smiles", "gene", "molecule_chembl_id"])
    avg_pchembl = grouped["pchembl_value"].mean().reset_index()
    
    def assign_label(val):
        if val >= 6.0: return 1
        elif val <= 5.0: return 0
        else: return np.nan
        
    avg_pchembl["label"] = avg_pchembl["pchembl_value"].apply(assign_label)
    final_df = avg_pchembl.dropna(subset=["label"]).copy()
    final_df["label"] = final_df["label"].astype(int)
    
    print(f"Total records after averaging and filtering: {len(final_df)}")
    final_df.to_csv("INPUT/bioactivity_processed_extended.csv", index=False)
    return final_df

def featurize_smiles(smiles: str):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None: return None
    row = {name: func(mol) for name, func in DESCRIPTOR_FUNCS.items()}
    fp_arr = np.array(morgan_gen.GetFingerprint(mol))
    for i, bit in enumerate(fp_arr):
        row[f"fp_{i}"] = int(bit)
    return row

def featurize_dataset(processed_df):
    print("\n=== Featurizing compounds ===")
    feature_rows, valid_idx, n_invalid = [], [], 0
    for idx, smi in processed_df["canonical_smiles"].items():
        feats = featurize_smiles(smi)
        if feats is None:
            n_invalid += 1
            continue
        feature_rows.append(feats)
        valid_idx.append(idx)

    print(f"Featurized {len(feature_rows)} valid molecules ({n_invalid} invalid SMILES dropped)")
    feat_df = pd.DataFrame(feature_rows, index=valid_idx)
    result = processed_df.loc[valid_idx].join(feat_df)
    result.to_csv("INPUT/featurized_extended_dataset.csv", index=False)
    return result

if __name__ == "__main__":
    if os.path.exists("INPUT/bioactivity_extended_raw.csv"):
        print("Raw extended data exists, skipping fetch.")
        raw_df = pd.read_csv("INPUT/bioactivity_extended_raw.csv")
    else:
        raw_df = fetch_bioactivity_data_fast()
        
    processed_df = analyze_duplicates_and_ic50(raw_df)
    featurized_df = featurize_dataset(processed_df)
    print("Done!")
