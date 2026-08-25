import os
import sys
import pandas as pd
import sklearn_crfsuite
from sklearn_crfsuite import metrics
from sklearn.model_selection import train_test_split
import joblib

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from features import extract_features

def main():
    master_csv = os.path.join(CURRENT_DIR, "master_address_dataset.csv")
    if not os.path.exists(master_csv):
        print(f"Error: {master_csv} not found! Please run generate_master_dataset.py first.")
        sys.exit(1)
        
    print(f"Loading Master Dataset from '{master_csv}'...")
    df = pd.read_csv(master_csv)
    print(f"Total Master Dataset Samples: {len(df):,}")
    
    # Train on 15,000 diverse samples for optimal speed, high precision, and generalization
    sample_size = min(15000, len(df))
    df_sample = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
    
    print(f"Preparing character features for {len(df_sample):,} addresses...")
    X = []
    y = []
    
    for idx, row in df_sample.iterrows():
        text = str(row['address_text'])
        labels = str(row['char_labels']).split()
        chars = list(text)
        
        # Ensure alignment
        min_len = min(len(chars), len(labels))
        chars = chars[:min_len]
        labels = labels[:min_len]
        
        feats = extract_features(chars)
        X.append(feats)
        y.append(labels)
        
        if (idx + 1) % 5000 == 0:
            print(f"  Processed {idx + 1:,} / {len(df_sample):,} feature sequences...")
            
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"\nTrain set: {len(X_train):,} | Test set: {len(X_test):,}")
    
    print("\nTraining Linear-Chain CRF Master Model (L-BFGS, L1=0.1, L2=0.1)...")
    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',
        c1=0.1,
        c2=0.1,
        max_iterations=60,
        all_possible_transitions=True,
        verbose=False
    )
    
    crf.fit(X_train, y_train)
    print("[SUCCESS] Master Model Training Complete!")
    
    print("\nEvaluating on Test Set...")
    y_pred = crf.predict(X_test)
    
    target_labels = ['N', 'S', 'C', 'A', 'P']
    report = metrics.flat_classification_report(y_test, y_pred, labels=target_labels, digits=4)
    print("\n" + "=" * 60)
    print("[EVALUATION REPORT] MASTER ADDRESS RESOLVER")
    print("=" * 60)
    print(report)
    
    weighted_f1 = metrics.flat_f1_score(y_test, y_pred, average='weighted', labels=target_labels)
    print(f"Overall Weighted Token F1-Score: {weighted_f1 * 100:.2f}%\n")
    
    # Save checkpoint
    out_model_path = os.path.join(CURRENT_DIR, "global_address_resolver_v1.pkl")
    joblib.dump(crf, out_model_path)
    print(f"[EXPORT] Master model exported successfully to '{out_model_path}' ({os.path.getsize(out_model_path) / 1024:.1f} KB)!")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    main()
