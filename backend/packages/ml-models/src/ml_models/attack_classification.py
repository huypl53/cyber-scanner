"""
End-to-end attack classification pipeline (preprocessing + feature selection +
scaling + DecisionTree) in a single, runnable file.

Usage examples:
  Train/evaluate with CSVs that include a 'Label' column:
    python -m ml_models.attack_classification --train_csvs data/*.csv

  Predict on raw CSV rows (no 'Label' required) using freshly trained model:
    python -m ml_models.attack_classification \
      --train_csvs data/*.csv \
      --predict_csv data/new_samples.csv \
      --output_preds preds.csv
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, RobustScaler
from sklearn.tree import DecisionTreeClassifier


@dataclass
class PreprocessArtifacts:
    label_encoder: LabelEncoder
    scaler: RobustScaler
    feature_columns: tuple[str, ...]  # Columns after correlation removal
    removed_columns: tuple[str, ...]  # Columns removed due to correlation
    class_mapping: dict[int, str]  # Maps encoded int -> original label


class AttackClassificationPipeline:
    """End-to-end training and inference for attack classification."""

    LABEL_COLUMN = "Label"

    def __init__(
        self, correlation_threshold: float = 0.85, max_depth: int = 10, random_state: int = 42
    ):
        self.correlation_threshold = correlation_threshold
        self.max_depth = max_depth
        self.random_state = random_state
        self.artifacts: PreprocessArtifacts | None = None
        self.model: DecisionTreeClassifier | None = None

    # --------------------
    # Preprocessing
    # --------------------
    @staticmethod
    def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Strip whitespace from column names to standardize references."""
        df = df.copy()
        df.columns = df.columns.str.strip()
        return df

    def fit_preprocess(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """
        Fit preprocessing pipeline and return scaled features and encoded labels.

        Steps:
        1. Clean/standardize column names
        2. Remove duplicates and NaN/inf values
        3. Label encode the 'Label' column and object columns
        4. Remove highly correlated features
        5. Scale features with RobustScaler
        """
        df = self._clean_column_names(df)

        # Remove duplicates and NaN
        df = df.drop_duplicates(keep="first")
        df = df.dropna()
        df = df.replace([np.inf, -np.inf], np.nan).dropna()

        print(f"After cleaning: {df.shape[0]} rows, {df.shape[1]} columns")

        # Separate features and labels
        if self.LABEL_COLUMN not in df.columns:
            raise ValueError(
                f"Training data must contain '{self.LABEL_COLUMN}' column (whitespace stripped automatically)"
            )

        y = df[self.LABEL_COLUMN]
        X = df.drop([self.LABEL_COLUMN], axis=1)

        # Convert dtypes for efficiency
        integer_cols = [col for col in X.columns if X[col].dtype == "int64"]
        float_cols = [col for col in X.columns if X[col].dtype not in ["int64", "int32", "float32"]]

        X[integer_cols] = X[integer_cols].astype("int32")
        X[float_cols] = X[float_cols].astype("float32")

        # Label encode object columns (if any remain in features)
        object_cols = X.select_dtypes(include="object").columns.tolist()
        for col in object_cols:
            le_temp = LabelEncoder()
            X[col] = le_temp.fit_transform(X[col].astype(str))

        # Label encode target
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y.astype(str))

        # Create class mapping for later reference
        class_mapping = {i: label for i, label in enumerate(label_encoder.classes_)}

        # Remove highly correlated features
        corr_matrix = X.corr()
        removed_cols = set()

        for i in range(len(corr_matrix.columns)):
            for j in range(i):
                if abs(corr_matrix.iloc[i, j]) > self.correlation_threshold:
                    colname = corr_matrix.columns[i]
                    removed_cols.add(colname)

        removed_cols = tuple(sorted(removed_cols))
        X = X.drop(columns=list(removed_cols))

        print(f"Removed {len(removed_cols)} highly correlated features")
        print(f"Remaining features: {X.shape[1]}")

        # Store feature columns
        feature_columns = tuple(X.columns)

        # Scale features
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)

        # Store artifacts
        self.artifacts = PreprocessArtifacts(
            label_encoder=label_encoder,
            scaler=scaler,
            feature_columns=feature_columns,
            removed_columns=removed_cols,
            class_mapping=class_mapping,
        )

        return X_scaled, y_encoded

    def transform_raw(self, df: pd.DataFrame) -> np.ndarray:
        """Transform raw data using fitted preprocessing pipeline."""
        if self.artifacts is None:
            raise ValueError("Preprocessing artifacts are not fitted. Train first.")

        df = self._clean_column_names(df)

        # Remove label if present
        if self.LABEL_COLUMN in df.columns:
            df = df.drop(columns=[self.LABEL_COLUMN])

        # Handle inf/nan
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna(0)  # Fill NaN with 0 for inference

        # Convert dtypes
        for col in df.columns:
            if df[col].dtype == "object":
                # Try to convert to numeric, if fails keep as object for encoding
                try:
                    df[col] = pd.to_numeric(df[col])
                except:
                    pass

        # Remove correlated columns
        for col in self.artifacts.removed_columns:
            if col in df.columns:
                df = df.drop(columns=[col])

        # Ensure all required features exist
        missing_cols = set(self.artifacts.feature_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Raw data missing required features: {sorted(missing_cols)}")

        # Select and order features correctly
        X = df[list(self.artifacts.feature_columns)]

        # Scale
        X_scaled = self.artifacts.scaler.transform(X)

        return X_scaled

    # --------------------
    # Training + evaluation
    # --------------------
    def train(self, df: pd.DataFrame) -> dict[str, any]:
        """Train the decision tree classifier and return metrics."""
        X, y = self.fit_preprocess(df)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state, shuffle=True
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.25, random_state=self.random_state, shuffle=True
        )

        print(f"\nTraining set: {X_train.shape[0]} samples")
        print(f"Validation set: {X_val.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")

        # Train model
        self.model = DecisionTreeClassifier(
            criterion="entropy", max_depth=self.max_depth, random_state=self.random_state
        )
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_val = self.model.predict(X_val)
        y_pred_test = self.model.predict(X_test)

        train_acc = accuracy_score(y_train, y_pred_train)
        val_acc = accuracy_score(y_val, y_pred_val)
        test_acc = accuracy_score(y_test, y_pred_test)

        print(f"\nTraining accuracy: {train_acc:.4f}")
        print(f"Validation accuracy: {val_acc:.4f}")
        print(f"Test accuracy: {test_acc:.4f}")

        # Get original labels for classification report
        y_test_original = [self.artifacts.class_mapping[y] for y in y_test]
        y_pred_original = [self.artifacts.class_mapping[y] for y in y_pred_test]

        print("\nClassification Report:")
        print(classification_report(y_test_original, y_pred_original))

        cm = confusion_matrix(y_test, y_pred_test)

        return {
            "train_accuracy": float(train_acc),
            "val_accuracy": float(val_acc),
            "test_accuracy": float(test_acc),
            "confusion_matrix": cm.tolist(),
            "n_classes": len(self.artifacts.class_mapping),
            "class_labels": list(self.artifacts.class_mapping.values()),
        }

    # --------------------
    # Inference
    # --------------------
    def predict(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """
        Predict attack types for raw data.

        Returns:
            predicted_encoded: Encoded class predictions
            confidence: Confidence scores (probability of predicted class)
            predicted_labels: Original string labels
        """
        if self.model is None or self.artifacts is None:
            raise ValueError("Model not trained. Call train() first.")

        X = self.transform_raw(df)

        # Get predictions
        predicted_encoded = self.model.predict(X)

        # Get probabilities if available
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X)
            confidence = np.max(proba, axis=1)
        else:
            confidence = np.ones(len(predicted_encoded))  # Default to 1.0

        # Map to original labels
        predicted_labels = [self.artifacts.class_mapping[y] for y in predicted_encoded]

        return predicted_encoded, confidence, predicted_labels

    # --------------------
    # Persistence
    # --------------------
    def save_as_bundle(self, filepath: str) -> None:
        """Save entire pipeline (preprocessing + model) as single .joblib file."""
        if self.artifacts is None or self.model is None:
            raise ValueError("Nothing to save. Train the pipeline first.")

        # Convert artifacts to dict to avoid pickling custom classes
        artifacts_dict = {
            "label_encoder": self.artifacts.label_encoder,
            "scaler": self.artifacts.scaler,
            "feature_columns": self.artifacts.feature_columns,
            "removed_columns": self.artifacts.removed_columns,
            "class_mapping": self.artifacts.class_mapping,
        }

        bundle = {
            "artifacts": artifacts_dict,
            "model": self.model,
            "correlation_threshold": self.correlation_threshold,
            "max_depth": self.max_depth,
            "random_state": self.random_state,
        }

        joblib.dump(bundle, filepath)
        print(f"Pipeline bundle saved to {filepath}")

    @classmethod
    def load_from_bundle(cls, filepath: str) -> AttackClassificationPipeline:
        """Load entire pipeline from single .joblib file."""
        bundle = joblib.load(filepath)

        pipeline = cls(
            correlation_threshold=bundle["correlation_threshold"],
            max_depth=bundle["max_depth"],
            random_state=bundle["random_state"],
        )

        # Reconstruct artifacts from dict
        artifacts_dict = bundle["artifacts"]
        pipeline.artifacts = PreprocessArtifacts(
            label_encoder=artifacts_dict["label_encoder"],
            scaler=artifacts_dict["scaler"],
            feature_columns=artifacts_dict["feature_columns"],
            removed_columns=artifacts_dict["removed_columns"],
            class_mapping=artifacts_dict["class_mapping"],
        )
        pipeline.model = bundle["model"]

        return pipeline


def generate_model_profile(pipeline: AttackClassificationPipeline) -> dict[str, any]:
    """Generate model profile JSON for backend integration."""
    if pipeline.artifacts is None:
        raise ValueError("Pipeline not trained. Cannot generate profile.")

    feature_columns = list(pipeline.artifacts.feature_columns)
    class_labels = list(pipeline.artifacts.class_mapping.values())

    return {
        "expected_features": feature_columns,
        "class_labels": class_labels,
        "preprocessing_notes": (
            f"DecisionTree attack classifier with internal preprocessing. "
            f"Uses correlation-based feature selection (threshold={pipeline.correlation_threshold}). "
            f"{len(feature_columns)} features after removing {len(pipeline.artifacts.removed_columns)} "
            f"highly correlated features. RobustScaler applied. "
            f"Predicts {len(class_labels)} attack types."
        ),
        "preprocessing_pipeline": {
            "steps": ["deduplication", "label_encoding", "correlation_removal", "robust_scaling"],
            "n_features_original": len(feature_columns) + len(pipeline.artifacts.removed_columns),
            "n_features_selected": len(feature_columns),
            "removed_features": list(pipeline.artifacts.removed_columns),
            "scaler_type": "RobustScaler",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Attack classification pipeline (single file).")
    parser.add_argument(
        "--train_csvs",
        type=str,
        nargs="+",
        required=True,
        help="Paths to training CSV files with 'Label' column (whitespace in headers is stripped automatically)",
    )
    parser.add_argument("--predict_csv", type=str, help="Path to raw CSV for inference.")
    parser.add_argument(
        "--output_preds", type=str, help="Where to write predictions CSV (if predicting)."
    )
    parser.add_argument(
        "--correlation_threshold",
        type=float,
        default=0.85,
        help="Correlation threshold for feature removal.",
    )
    parser.add_argument("--max_depth", type=int, default=10, help="Max depth of decision tree.")
    parser.add_argument("--random_state", type=int, default=42, help="Random seed.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Load and combine training data
    print(f"Loading {len(args.train_csvs)} CSV file(s)...")
    dfs = []
    for csv_path in args.train_csvs:
        df = pd.read_csv(csv_path, low_memory=False)
        dfs.append(df)
        print(f"  Loaded {csv_path}: {df.shape[0]} rows, {df.shape[1]} columns")

    train_df = pd.concat(dfs, ignore_index=True)
    print(f"\nCombined dataset: {train_df.shape[0]} rows, {train_df.shape[1]} columns")

    # Train pipeline
    print("\nTraining pipeline...")
    pipeline = AttackClassificationPipeline(
        correlation_threshold=args.correlation_threshold,
        max_depth=args.max_depth,
        random_state=args.random_state,
    )
    metrics = pipeline.train(train_df)

    print("\n=== Summary metrics ===")
    print(json.dumps({k: v for k, v in metrics.items() if k != "confusion_matrix"}, indent=2))

    # Save as single bundle
    bundle_path = "./attack_classifier.joblib"
    pipeline.save_as_bundle(bundle_path)

    # Generate and save model profile
    profile = generate_model_profile(pipeline)
    profile_path = "./attack_classifier_profile.json"
    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"\nModel profile saved to {profile_path}")

    # Verify bundle can be loaded
    print("\nVerifying bundle can be reloaded...")
    loaded_pipeline = AttackClassificationPipeline.load_from_bundle(bundle_path)
    print("✓ Bundle loaded successfully")

    # Prediction (if requested)
    if args.predict_csv:
        raw_df = pd.read_csv(args.predict_csv, low_memory=False)
        predicted_encoded, confidence, predicted_labels = pipeline.predict(raw_df)

        result = raw_df.copy()
        result["predicted_class_encoded"] = predicted_encoded
        result["predicted_class_label"] = predicted_labels
        result["confidence"] = confidence

        if args.output_preds:
            os.makedirs(os.path.dirname(args.output_preds) or ".", exist_ok=True)
            result.to_csv(args.output_preds, index=False)
            print(f"\nPredictions saved to {args.output_preds}")
        else:
            print("\nPredictions preview:")
            print(result[["predicted_class_label", "confidence"]].head(10))


if __name__ == "__main__":
    main()
