from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

def create_presentation():
    prs = Presentation()

    # Define some standard colors
    theme_color = RGBColor(0, 51, 102)

    # 1. Title Slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "Parkinson's Disease Target Models"
    subtitle.text = "Predicting Drug Targets using Machine Learning\nProject Overview, Workflow, and Results"
    
    # 2. What is the Project?
    bullet_slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(bullet_slide_layout)
    shapes = slide.shapes
    title_shape = shapes.title
    body_shape = shapes.placeholders[1]
    title_shape.text = "Project Overview"
    tf = body_shape.text_frame
    tf.text = "Goal: Build ML models to predict if a compound is an active drug candidate against Parkinson's Disease (PD) gene targets."
    p = tf.add_paragraph()
    p.text = "Extracted bioactivity data from the ChEMBL database."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Focuses on key PD gene targets (e.g., DRD2, ADORA2A, MAO_B, LRRK2, SLC6A3)."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Resulted in a dataset of 35,909 unique compounds across 12 viable targets."
    p.level = 1

    # 3. Workflow: Data Preprocessing & Featurization
    slide = prs.slides.add_slide(bullet_slide_layout)
    shapes = slide.shapes
    title_shape.text = "Workflow: Featurization & Preparation"
    title_shape = shapes.title
    body_shape = shapes.placeholders[1]
    title_shape.text = "Workflow: Preprocessing & Featurization"
    tf = body_shape.text_frame
    tf.text = "Converted chemical structures (SMILES) into numeric features."
    p = tf.add_paragraph()
    p.text = "Generated 1,031 features per compound:"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "1,024-bit Morgan Fingerprints (ECFP4)"
    p.level = 2
    p = tf.add_paragraph()
    p.text = "7 Physicochemical descriptors (MolWt, LogP, TPSA, NumHDonors, NumHAcceptors, NumRotBonds, NumAromRings)"
    p.level = 2
    p = tf.add_paragraph()
    p.text = "Classification targets defined as:"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Active (potency ≤ 1000 nM)"
    p.level = 2
    p = tf.add_paragraph()
    p.text = "Inactive (potency ≥ 10000 nM)"
    p.level = 2

    # 4. Machine Learning Modeling (Splits & Models)
    slide = prs.slides.add_slide(bullet_slide_layout)
    shapes = slide.shapes
    title_shape = shapes.title
    body_shape = shapes.placeholders[1]
    title_shape.text = "Machine Learning Modeling Strategy"
    tf = body_shape.text_frame
    tf.text = "Evaluated multiple algorithms:"
    p = tf.add_paragraph()
    p.text = "XGBoost, Logistic Regression, Random Forest, K-Nearest Neighbors (KNN)"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Data Splitting Strategies:"
    p.level = 0
    p = tf.add_paragraph()
    p.text = "Random Split (75/25 and 80/20)"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Scaffold Split (Bemis-Murcko) to test out-of-distribution generalization"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Robust evaluation using 5-fold StratifiedKFold cross-validation and GridSearchCV."
    p.level = 0

    # 5. Advanced Analysis (Phase 2)
    slide = prs.slides.add_slide(bullet_slide_layout)
    shapes = slide.shapes
    title_shape = shapes.title
    body_shape = shapes.placeholders[1]
    title_shape.text = "Advanced Analysis Workflow"
    tf = body_shape.text_frame
    tf.text = "Scaffold splitting revealed expected drops in Specificity compared to random splits."
    p = tf.add_paragraph()
    p.text = "Physicochemical Correlation Analysis:"
    p.level = 0
    p = tf.add_paragraph()
    p.text = "Highly correlated descriptors (MolWt, TPSA, NumHDonors etc.)"
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Weak correlation between single properties and potency (pIC50), requiring complex ML models."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Duplicate & Error Analysis:"
    p.level = 0
    p = tf.add_paragraph()
    p.text = "Handled conflicting labels across different targets cleanly."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Categorized True Positives, True Negatives, False Positives, False Negatives."
    p.level = 1

    # 6. Outputs Till Now: Results & Comparisons
    slide = prs.slides.add_slide(bullet_slide_layout)
    shapes = slide.shapes
    title_shape = shapes.title
    body_shape = shapes.placeholders[1]
    title_shape.text = "Output Till Now: Model Comparisons"
    tf = body_shape.text_frame
    tf.text = "Initial 75/25 Split Comparison:"
    p = tf.add_paragraph()
    p.text = "XGBoost won decisively, claiming 9 out of 13 targets."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Logistic Regression won on COMT and SNCA."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "80/20 Split Comparison:"
    p.level = 0
    p = tf.add_paragraph()
    p.text = "XGBoost claimed 8 of 13 targets."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Random Forest overtook XGBoost on LRRK2 (ROC-AUC 0.959)."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Logistic Regression achieved a perfect 1.0 ROC-AUC on SLC18A2."
    p.level = 1

    # 7. Outputs Till Now: Key Deliverables
    slide = prs.slides.add_slide(bullet_slide_layout)
    shapes = slide.shapes
    title_shape = shapes.title
    body_shape = shapes.placeholders[1]
    title_shape.text = "Output Till Now: Deliverables"
    tf = body_shape.text_frame
    tf.text = "Data Artifacts:"
    p = tf.add_paragraph()
    p.text = "Cleaned bioactivity datasets and featurized datasets."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Model Evaluation:"
    p.level = 0
    p = tf.add_paragraph()
    p.text = "ROC-AUC, F1, Precision, Recall scores for all combinations."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Confusion matrix images for XGBoost & Logistic Regression."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Detailed CSV outputs for correlation, conflicting activities, and error analysis."
    p.level = 1
    p = tf.add_paragraph()
    p.text = "Scripts:"
    p.level = 0
    p = tf.add_paragraph()
    p.text = "End-to-end reproducible pipelines for data extraction, featurization, training, and evaluation."
    p.level = 1

    # 8. Conclusion Slide
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "Conclusion"
    subtitle.text = "XGBoost is the most robust choice for chemoinformatics on this dataset.\nThe project successfully demonstrates a rigorous, multi-faceted ML approach to Parkinson's Disease drug discovery."

    prs.save('OUTPUT/Project_Summary_Presentation.pptx')
    print("Presentation created successfully at OUTPUT/Project_Summary_Presentation.pptx")

if __name__ == "__main__":
    create_presentation()
