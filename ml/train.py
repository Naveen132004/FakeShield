"""
train.py
========
Main training script for the Fake News Detection model.

Trains a Logistic Regression model (baseline) with TF-IDF features.
Evaluates with Accuracy, Precision, Recall, F1-score.
Saves the trained model and preprocessor.

Usage:
  python train.py                              # Use synthetic data
  python train.py --source kaggle --input data.csv  # Use Kaggle dataset
  python train.py --source liar --input train.tsv   # Use LIAR dataset

Output:
  models/fake_news_model.joblib      - Trained model
  models/preprocessor.joblib         - Fitted TF-IDF preprocessor
  models/training_report.json        - Training metrics
  models/confusion_matrix.png        - Confusion matrix visualization
"""

import os
import sys
import json
import argparse
import time
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score,
    roc_curve, precision_recall_curve
)
from sklearn.model_selection import cross_val_score

from data_loader import prepare_data
from preprocessor import TextPreprocessor, prepare_train_test_data


# ─── Configuration ───────────────────────────────────────────────────────────
MODELS_DIR = "models"
DATA_DIR = "data"
REPORTS_DIR = "reports"


def train_logistic_regression(X_train, y_train, X_test, y_test):
    """
    Train Logistic Regression model (baseline).
    
    Uses L2 regularization with tuned C parameter.
    Balanced class weights to handle any class imbalance.
    """
    print("\n" + "=" * 60)
    print("🏋️ TRAINING: Logistic Regression (Baseline)")
    print("=" * 60)
    
    model = LogisticRegression(
        C=1.0,
        penalty='l2',
        solver='lbfgs',
        max_iter=1000,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    start_time = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start_time
    
    print(f"  ⏱ Training time: {train_time:.2f}s")
    
    return model, train_time


def train_multiple_models(X_train, y_train, X_test, y_test):
    """
    Train and compare multiple models.
    
    Returns dictionary of model_name: (model, metrics)
    """
    models = {
        "Logistic Regression": LogisticRegression(
            C=1.0, max_iter=1000, class_weight='balanced',
            random_state=42, n_jobs=-1
        ),
        "Naive Bayes": MultinomialNB(alpha=1.0),
        "Random Forest": RandomForestClassifier(
            n_estimators=100, max_depth=50, class_weight='balanced',
            random_state=42, n_jobs=-1
        ),
    }
    
    results = {}
    best_f1 = 0
    best_model_name = None
    
    for name, model in models.items():
        print(f"\n{'─' * 50}")
        print(f"🏋️ Training: {name}")
        
        start_time = time.time()
        model.fit(X_train, y_train)
        train_time = time.time() - start_time
        
        y_pred = model.predict(X_test)
        
        metrics = {
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "precision": round(precision_score(y_test, y_pred, average='weighted'), 4),
            "recall": round(recall_score(y_test, y_pred, average='weighted'), 4),
            "f1_score": round(f1_score(y_test, y_pred, average='weighted'), 4),
            "train_time": round(train_time, 2),
        }
        
        results[name] = {"model": model, "metrics": metrics, "predictions": y_pred}
        
        print(f"  Accuracy:  {metrics['accuracy']}")
        print(f"  Precision: {metrics['precision']}")
        print(f"  Recall:    {metrics['recall']}")
        print(f"  F1-Score:  {metrics['f1_score']}")
        print(f"  Time:      {metrics['train_time']}s")
        
        if metrics['f1_score'] > best_f1:
            best_f1 = metrics['f1_score']
            best_model_name = name
    
    print(f"\n🏆 Best Model: {best_model_name} (F1: {best_f1})")
    
    return results, best_model_name


def evaluate_model(model, X_test, y_test, model_name: str = "Model"):
    """
    Comprehensive model evaluation.
    
    Returns metrics dictionary.
    """
    print("\n" + "=" * 60)
    print(f"📊 EVALUATION: {model_name}")
    print("=" * 60)
    
    y_pred = model.predict(X_test)
    
    # Core metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted')
    recall = recall_score(y_test, y_pred, average='weighted')
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    # Per-class metrics
    class_report = classification_report(y_test, y_pred,
                                          target_names=['REAL', 'FAKE'],
                                          output_dict=True)
    
    # Try to get ROC-AUC
    auc_score = None
    try:
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test)[:, 1]
            auc_score = roc_auc_score(y_test, y_proba)
        elif hasattr(model, 'decision_function'):
            y_scores = model.decision_function(X_test)
            auc_score = roc_auc_score(y_test, y_scores)
    except Exception as e:
        print(f"  ⚠ Could not compute AUC: {e}")
    
    # Print results
    print(f"\n  📈 Overall Metrics:")
    print(f"     Accuracy:  {accuracy:.4f}")
    print(f"     Precision: {precision:.4f}")
    print(f"     Recall:    {recall:.4f}")
    print(f"     F1-Score:  {f1:.4f}")
    if auc_score:
        print(f"     AUC-ROC:   {auc_score:.4f}")
    
    print(f"\n  📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['REAL', 'FAKE']))
    
    metrics = {
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "auc_roc": round(float(auc_score), 4) if auc_score else None,
        "classification_report": class_report,
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }
    
    return metrics, y_pred


def plot_confusion_matrix(y_test, y_pred, save_path: str):
    """Generate and save confusion matrix visualization."""
    cm = confusion_matrix(y_test, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['REAL', 'FAKE'],
                yticklabels=['REAL', 'FAKE'])
    plt.title('Confusion Matrix - Fake News Detection', fontsize=14, fontweight='bold')
    plt.ylabel('Actual', fontsize=12)
    plt.xlabel('Predicted', fontsize=12)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  📊 Confusion matrix saved to: {save_path}")


def plot_roc_curve(model, X_test, y_test, save_path: str):
    """Generate and save ROC curve."""
    try:
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test)[:, 1]
        elif hasattr(model, 'decision_function'):
            y_proba = model.decision_function(X_test)
        else:
            return
        
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        auc = roc_auc_score(y_test, y_proba)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, 'b-', linewidth=2, label=f'ROC Curve (AUC = {auc:.4f})')
        plt.plot([0, 1], [0, 1], 'r--', linewidth=1, label='Random Classifier')
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title('ROC Curve - Fake News Detection', fontsize=14, fontweight='bold')
        plt.legend(loc='lower right', fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  📈 ROC curve saved to: {save_path}")
    except Exception as e:
        print(f"  ⚠ Could not plot ROC curve: {e}")


def plot_model_comparison(results: dict, save_path: str):
    """Plot comparison of multiple models."""
    model_names = list(results.keys())
    metrics_names = ['accuracy', 'precision', 'recall', 'f1_score']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(model_names))
    width = 0.2
    
    for i, metric in enumerate(metrics_names):
        values = [results[name]['metrics'][metric] for name in model_names]
        bars = ax.bar(x + i * width, values, width, label=metric.replace('_', ' ').title())
        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.005,
                    f'{val:.3f}', ha='center', va='bottom', fontsize=8)
    
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('Model Comparison - Fake News Detection', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(model_names, fontsize=10)
    ax.legend(loc='lower right')
    ax.set_ylim(0, 1.1)
    ax.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  📊 Model comparison chart saved to: {save_path}")


def get_top_features_per_class(model, preprocessor: TextPreprocessor, n: int = 15):
    """
    Extract top features (words) that indicate fake vs real news.
    
    Only works with linear models (LogisticRegression, LinearSVC).
    """
    if not hasattr(model, 'coef_'):
        return None
    
    feature_names = preprocessor.get_feature_names()
    coefficients = model.coef_[0]
    
    # Top features for FAKE (positive coefficients)
    fake_indices = np.argsort(coefficients)[-n:][::-1]
    fake_features = [(feature_names[i], round(float(coefficients[i]), 4)) 
                     for i in fake_indices]
    
    # Top features for REAL (negative coefficients)
    real_indices = np.argsort(coefficients)[:n]
    real_features = [(feature_names[i], round(float(coefficients[i]), 4)) 
                     for i in real_indices]
    
    print(f"\n  🔴 Top {n} FAKE indicators:")
    for word, coef in fake_features:
        print(f"     {word:25s} → {coef:+.4f}")
    
    print(f"\n  🟢 Top {n} REAL indicators:")
    for word, coef in real_features:
        print(f"     {word:25s} → {coef:+.4f}")
    
    return {"fake_indicators": fake_features, "real_indicators": real_features}


def cross_validate(model, X_train, y_train, cv: int = 5):
    """Perform cross-validation on training data."""
    print(f"\n🔀 Cross-Validation ({cv}-fold):")
    
    scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='f1_weighted', n_jobs=-1)
    
    print(f"  Fold scores: {[round(s, 4) for s in scores]}")
    print(f"  Mean F1:     {scores.mean():.4f} ± {scores.std():.4f}")
    
    return {
        "fold_scores": [round(float(s), 4) for s in scores],
        "mean_f1": round(float(scores.mean()), 4),
        "std_f1": round(float(scores.std()), 4),
    }


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description="Train Fake News Detection Model")
    parser.add_argument("--source", type=str, default="all",
                        choices=["all", "synthetic", "kaggle", "liar"],
                        help="Data source ('all' downloads every available dataset)")
    parser.add_argument("--input", type=str, default=None,
                        help="Input file path for kaggle/liar datasets")
    parser.add_argument("--num-samples", type=int, default=10000,
                        help="Number of synthetic samples (also used in 'all' mode)")
    parser.add_argument("--compare", action="store_true",
                        help="Compare multiple models")
    parser.add_argument("--output", type=str, default=MODELS_DIR,
                        help="Output directory for models")
    
    args = parser.parse_args()
    
    print("╔" + "═" * 58 + "╗")
    print("║   🔍 FAKE NEWS DETECTION - MODEL TRAINING PIPELINE      ║")
    print("╚" + "═" * 58 + "╝")
    
    # ── Step 1: Load Data ─────────────────────────────────────────────────
    print("\n📂 STEP 1: Loading Data")
    data_path = prepare_data(
        source=args.source,
        input_path=args.input,
        output_dir=DATA_DIR,
        num_samples=args.num_samples
    )
    
    df = pd.read_csv(data_path)
    print(f"  Dataset shape: {df.shape}")
    
    # ── Step 2: Preprocess & Vectorize ────────────────────────────────────
    print("\n📝 STEP 2: Preprocessing & Vectorization")
    X_train, X_test, y_train, y_test, preprocessor = prepare_train_test_data(df)
    
    # ── Step 3: Train Model(s) ────────────────────────────────────────────
    print("\n🏋️ STEP 3: Training Model(s)")
    
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    if args.compare:
        # Compare multiple models
        results, best_model_name = train_multiple_models(X_train, y_train, X_test, y_test)
        model = results[best_model_name]['model']
        
        # Save comparison chart
        plot_model_comparison(results, os.path.join(REPORTS_DIR, "model_comparison.png"))
        
        # Save comparison metrics
        comparison_data = {
            name: data['metrics'] for name, data in results.items()
        }
        with open(os.path.join(REPORTS_DIR, "model_comparison.json"), 'w') as f:
            json.dump(comparison_data, f, indent=2)
    else:
        # Train baseline only
        model, train_time = train_logistic_regression(X_train, y_train, X_test, y_test)
    
    # ── Step 4: Evaluate ──────────────────────────────────────────────────
    print("\n📊 STEP 4: Evaluation")
    metrics, y_pred = evaluate_model(model, X_test, y_test, "Logistic Regression")
    
    # Cross-validation
    cv_results = cross_validate(
        LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced', random_state=42),
        X_train, y_train
    )
    metrics['cross_validation'] = cv_results
    
    # Top features analysis
    top_features = get_top_features_per_class(model, preprocessor)
    if top_features:
        metrics['top_features'] = top_features
    
    # ── Step 5: Generate Visualizations ───────────────────────────────────
    print("\n🎨 STEP 5: Generating Visualizations")
    plot_confusion_matrix(y_test, y_pred, os.path.join(REPORTS_DIR, "confusion_matrix.png"))
    plot_roc_curve(model, X_test, y_test, os.path.join(REPORTS_DIR, "roc_curve.png"))
    
    # ── Step 6: Save Model & Preprocessor ─────────────────────────────────
    print("\n💾 STEP 6: Saving Model & Preprocessor")
    
    model_path = os.path.join(args.output, "fake_news_model.joblib")
    preprocessor_path = os.path.join(args.output, "preprocessor.joblib")
    
    joblib.dump(model, model_path)
    print(f"  ✅ Model saved to: {model_path}")
    
    preprocessor.save(preprocessor_path)
    
    # Save training report
    report = {
        "model_type": type(model).__name__,
        "data_source": args.source,
        "dataset_size": len(df),
        "train_size": X_train.shape[0],
        "test_size": X_test.shape[0],
        "feature_count": X_train.shape[1],
        "metrics": metrics,
        "model_path": model_path,
        "preprocessor_path": preprocessor_path,
    }
    
    report_path = os.path.join(REPORTS_DIR, "training_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  📋 Training report saved to: {report_path}")
    
    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    print(f"  Model:       {type(model).__name__}")
    print(f"  Accuracy:    {metrics['accuracy']:.4f}")
    print(f"  Precision:   {metrics['precision']:.4f}")
    print(f"  Recall:      {metrics['recall']:.4f}")
    print(f"  F1-Score:    {metrics['f1_score']:.4f}")
    if metrics.get('auc_roc'):
        print(f"  AUC-ROC:     {metrics['auc_roc']:.4f}")
    print(f"\n  📁 Model:        {model_path}")
    print(f"  📁 Preprocessor: {preprocessor_path}")
    print(f"  📁 Report:       {report_path}")


if __name__ == "__main__":
    main()
