"""Threat detection pipeline (ANN + LSTM ensemble) for binary classification."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from tensorflow.keras.layers import LSTM, BatchNormalization, Dense, Dropout, ReLU
from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.optimizers import Adam


def _ensure_binary_targets(series: pd.Series) -> pd.Series:
    """Label-encode `class` to 0/1 and drop NaNs."""
    clean = series.dropna()
    encoder = LabelEncoder()
    encoded = encoder.fit_transform(clean)
    return pd.Series(encoded, index=clean.index, name=series.name)


def _print_metrics(name: str, y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    """Print standard metrics and return them for downstream use."""
    y_pred = (y_prob > 0.5).astype(int)
    acc = accuracy_score(y_true, y_pred)
    report = classification_report(y_true, y_pred, output_dict=True)
    cm = confusion_matrix(y_true, y_pred).tolist()
    auc_score = roc_auc_score(y_true, y_prob)
    fpr, tpr, _ = roc_curve(y_true, y_prob)

    print(f"\n{name} accuracy: {acc:.4f}")
    print(f"{name} classification report:\n{classification_report(y_true, y_pred)}")
    print(f"{name} confusion matrix:\n{confusion_matrix(y_true, y_pred)}")
    print(f"{name} ROC AUC: {auc_score:.4f}")

    return {
        "accuracy": float(acc),
        "auc": float(auc_score),
        "classification_report": report,
        "confusion_matrix": cm,
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
    }


@dataclass
class PreprocessArtifacts:
    encoders: dict[str, LabelEncoder]
    selected_features: tuple[str, ...]
    scaler: StandardScaler


class ThreatDetectionPipeline:
    """End-to-end training and inference for the ensemble threat detector."""

    def __init__(self, n_features: int = 10, random_state: int = 42):
        self.n_features = n_features
        self.random_state = random_state
        self.artifacts: PreprocessArtifacts | None = None
        self.model_ann: Sequential | None = None
        self.model_lstm: Sequential | None = None

    # --------------------
    # Preprocessing
    # --------------------
    def fit_preprocess(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        df = df.copy()
        df["class"] = _ensure_binary_targets(df["class"])
        df = df.dropna(subset=["class"])

        encoders: dict[str, LabelEncoder] = {}
        for col in df.columns:
            if col == "class":
                continue
            if df[col].dtype == "object":
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                encoders[col] = le

        if "num_outbound_cmds" in df.columns:
            df = df.drop(columns=["num_outbound_cmds"])

        X = df.drop(columns=["class"])
        y = df["class"].astype(int)

        rfe = RFE(
            estimator=RandomForestClassifier(random_state=self.random_state),
            n_features_to_select=self.n_features,
        )
        rfe.fit(X, y)
        selected_features = tuple(X.columns[rfe.get_support()])
        X_sel = X[list(selected_features)]

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_sel)

        self.artifacts = PreprocessArtifacts(
            encoders=encoders, selected_features=selected_features, scaler=scaler
        )
        return X_scaled, y.values

    def transform_raw(self, df: pd.DataFrame) -> np.ndarray:
        if self.artifacts is None:
            raise ValueError("Preprocessing artifacts are not fitted. Train first.")

        df = df.copy()
        if "class" in df.columns:
            df = df.drop(columns=["class"])

        for col, encoder in self.artifacts.encoders.items():
            # Create a mapping from known labels to their encoded integers
            label_mapping = {label: idx for idx, label in enumerate(encoder.classes_)}
            # Apply the mapping. For labels not in `label_mapping`, map to 0 as a default.
            df[col] = df[col].astype(str).map(label_mapping).fillna(0).astype(int)

        if "num_outbound_cmds" in df.columns:
            df = df.drop(columns=["num_outbound_cmds"])

        missing_cols = set(self.artifacts.selected_features) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Raw data missing expected columns: {sorted(missing_cols)}")

        # Ensure all selected features exist (fill missing with 0)
        for col in self.artifacts.selected_features:
            if col not in df.columns:
                df[col] = 0

        # Select features in the correct order (convert tuple to list for pandas)
        X_sel = df[list(self.artifacts.selected_features)]
        return self.artifacts.scaler.transform(X_sel)

    # --------------------
    # Model builders
    # --------------------
    def _build_ann(self, input_dim: int) -> Sequential:
        model = Sequential(
            [
                Dense(128, input_dim=input_dim),
                ReLU(),
                BatchNormalization(),
                Dense(128),
                ReLU(),
                BatchNormalization(),
                Dropout(0.2),
                Dense(64),
                ReLU(),
                BatchNormalization(),
                Dropout(0.2),
                Dense(32),
                ReLU(),
                BatchNormalization(),
                Dropout(0.2),
                Dense(1, activation="sigmoid"),
            ]
        )
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss=BinaryCrossentropy(),
            metrics=["accuracy"],
        )
        return model

    def _build_lstm(self, input_shape: tuple[int, int]) -> Sequential:
        model = Sequential(
            [
                LSTM(256, return_sequences=True, input_shape=input_shape),
                Dropout(0.2),
                LSTM(128, return_sequences=True),
                Dropout(0.2),
                LSTM(64),
                Dropout(0.2),
                Dense(1, activation="sigmoid"),
            ]
        )
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss=BinaryCrossentropy(),
            metrics=["accuracy"],
        )
        return model

    # --------------------
    # Training + evaluation
    # --------------------
    def train(self, df: pd.DataFrame) -> dict[str, dict[str, float]]:
        X, y = self.fit_preprocess(df)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.25, random_state=self.random_state, stratify=y_train
        )

        # ANN
        self.model_ann = self._build_ann(X_train.shape[1])
        self.model_ann.fit(
            X_train,
            y_train,
            epochs=50,
            batch_size=32,
            validation_data=(X_val, y_val),
            verbose=0,
        )
        y_prob_ann = self.model_ann.predict(X_test).ravel()
        metrics_ann = _print_metrics("ANN", y_test, y_prob_ann)

        # LSTM
        X_train_lstm = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
        X_val_lstm = X_val.reshape(X_val.shape[0], X_val.shape[1], 1)
        X_test_lstm = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)

        self.model_lstm = self._build_lstm((X_train.shape[1], 1))
        self.model_lstm.fit(
            X_train_lstm,
            y_train,
            epochs=20,
            batch_size=128,
            validation_data=(X_val_lstm, y_val),
            verbose=0,
        )
        y_prob_lstm = self.model_lstm.predict(X_test_lstm).ravel()
        metrics_lstm = _print_metrics("LSTM", y_test, y_prob_lstm)

        # Ensemble (average probs)
        y_prob_ensemble = (y_prob_ann + y_prob_lstm) / 2
        metrics_ensemble = _print_metrics("Ensemble", y_test, y_prob_ensemble)

        return {
            "ann": metrics_ann,
            "lstm": metrics_lstm,
            "ensemble": metrics_ensemble,
        }

    # --------------------
    # Inference
    # --------------------
    def predict(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self.model_ann is None or self.model_lstm is None:
            raise ValueError("Models not trained. Call train() first.")

        X = self.transform_raw(df)
        X_lstm = X.reshape(X.shape[0], X.shape[1], 1)

        prob_ann = self.model_ann.predict(X).ravel()
        prob_lstm = self.model_lstm.predict(X_lstm).ravel()
        prob_ensemble = (prob_ann + prob_lstm) / 2
        preds = (prob_ensemble > 0.5).astype(int)
        return preds, prob_ensemble, prob_ann

    # --------------------
    # Persistence
    # --------------------
    def save(self, path: str) -> None:
        if self.artifacts is None or self.model_ann is None or self.model_lstm is None:
            raise ValueError("Nothing to save. Train the pipeline first.")

        os.makedirs(path, exist_ok=True)
        # Save preprocessing artifacts
        joblib.dump(self.artifacts, os.path.join(path, "artifacts.pkl"))
        # Save models
        self.model_ann.save(os.path.join(path, "model_ann.h5"))
        self.model_lstm.save(os.path.join(path, "model_lstm.h5"))

    @classmethod
    def load(cls, path: str) -> ThreatDetectionPipeline:
        pipeline = cls()
        pipeline.artifacts = joblib.load(os.path.join(path, "artifacts.pkl"))
        pipeline.model_ann = load_model(os.path.join(path, "model_ann.h5"))
        pipeline.model_lstm = load_model(os.path.join(path, "model_lstm.h5"))
        return pipeline

    def save_as_bundle(self, filepath: str) -> None:
        """Save entire pipeline (preprocessing + models) as single .joblib file."""
        if self.artifacts is None or self.model_ann is None or self.model_lstm is None:
            raise ValueError("Nothing to save. Train the pipeline first.")

        import tempfile

        # Save Keras models to temp H5 files to serialize their weights
        with tempfile.TemporaryDirectory() as tmpdir:
            ann_path = os.path.join(tmpdir, "ann_weights.h5")
            lstm_path = os.path.join(tmpdir, "lstm_weights.h5")

            self.model_ann.save(ann_path)
            self.model_lstm.save(lstm_path)

            # Read H5 files as binary
            with open(ann_path, "rb") as f:
                ann_weights = f.read()
            with open(lstm_path, "rb") as f:
                lstm_weights = f.read()

        # Bundle everything
        bundle = {
            "artifacts": self.artifacts,
            "ann_weights": ann_weights,
            "lstm_weights": lstm_weights,
            "ann_config": self.model_ann.get_config(),
            "lstm_config": self.model_lstm.get_config(),
            "n_features": self.n_features,
            "random_state": self.random_state,
        }

        joblib.dump(bundle, filepath)
        print(f"Pipeline bundle saved to {filepath}")

    @classmethod
    def load_from_bundle(cls, filepath: str) -> ThreatDetectionPipeline:
        """Load entire pipeline from single .joblib file."""
        import sys
        import tempfile

        # Backward compatibility: Handle bundles saved with __main__ module reference
        # This happens when the bundle was created by running a script directly as __main__
        current_module = sys.modules[__name__]
        original_main = sys.modules.get("__main__")

        # Temporarily replace __main__ with current module for unpickling
        sys.modules["__main__"] = current_module

        try:
            bundle = joblib.load(filepath)
        finally:
            # Restore original __main__ module
            if original_main is not None:
                sys.modules["__main__"] = original_main
            elif "__main__" in sys.modules:
                del sys.modules["__main__"]

        pipeline = cls(n_features=bundle["n_features"], random_state=bundle["random_state"])
        pipeline.artifacts = bundle["artifacts"]

        # Reconstruct Keras models from weights
        with tempfile.TemporaryDirectory() as tmpdir:
            ann_path = os.path.join(tmpdir, "ann_weights.h5")
            lstm_path = os.path.join(tmpdir, "lstm_weights.h5")

            with open(ann_path, "wb") as f:
                f.write(bundle["ann_weights"])
            with open(lstm_path, "wb") as f:
                f.write(bundle["lstm_weights"])

            pipeline.model_ann = load_model(ann_path)
            pipeline.model_lstm = load_model(lstm_path)

        return pipeline


def generate_model_profile(pipeline: ThreatDetectionPipeline) -> dict[str, any]:
    """Generate model profile JSON for backend integration."""
    if pipeline.artifacts is None:
        raise ValueError("Pipeline not trained. Cannot generate profile.")

    # Get all categorical features that were label-encoded
    categorical_features = list(pipeline.artifacts.encoders.keys())

    # Get the selected features after RFE
    selected_features = list(pipeline.artifacts.selected_features)

    return {
        "expected_features": selected_features,
        "class_labels": ["Normal", "Attack"],
        "preprocessing_notes": (
            f"Ensemble model (ANN + LSTM) with internal preprocessing. "
            f"Performs RFE feature selection ({len(selected_features)} "
            f"features selected from original dataset). "
            f"Label encoding and standardization applied internally. "
            f"Raw input data must contain all original features including categorical: {', '.join(categorical_features)}."
        ),
        "preprocessing_pipeline": {
            "steps": ["label_encoding", "rfe_feature_selection", "standard_scaling"],
            "categorical_features": categorical_features,
            "selected_features": selected_features,
            "n_features_selected": len(selected_features),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Threat detection pipeline (single file).")
    parser.add_argument(
        "--train_csv", type=str, required=True, help="Path to training CSV with `class` column."
    )
    parser.add_argument("--predict_csv", type=str, help="Path to raw CSV for inference.")
    parser.add_argument(
        "--output_preds", type=str, help="Where to write predictions CSV (if predicting)."
    )
    parser.add_argument(
        "--n_features", type=int, default=10, help="Number of features to keep via RFE."
    )
    parser.add_argument("--random_state", type=int, default=42, help="Random seed.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Train pipeline
    print("Training pipeline...")
    train_df = pd.read_csv(args.train_csv)
    pipeline = ThreatDetectionPipeline(n_features=args.n_features, random_state=args.random_state)
    metrics = pipeline.train(train_df)

    print("\n=== Summary metrics ===")
    print(json.dumps(metrics, indent=2))

    # Save as directory (backward compatibility)
    pipeline.save("./trained_pipeline")

    # Save as single bundle
    bundle_path = "./threat_detector_ensemble.joblib"
    pipeline.save_as_bundle(bundle_path)

    # Generate and save model profile
    profile = generate_model_profile(pipeline)
    profile_path = "./threat_detector_profile.json"
    with open(profile_path, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"\nModel profile saved to {profile_path}")

    # Verify bundle can be loaded
    print("\nVerifying bundle can be reloaded...")
    loaded_pipeline = ThreatDetectionPipeline.load_from_bundle(bundle_path)
    print("\u2713 Bundle loaded successfully")

    # Prediction (if requested)
    if args.predict_csv:
        raw_df = pd.read_csv(args.predict_csv)
        preds, prob_ensemble, prob_ann = pipeline.predict(raw_df)
        result = raw_df.copy()
        result["predicted_class"] = preds
        result["prob_ensemble"] = prob_ensemble
        result["prob_ann"] = prob_ann

        if args.output_preds:
            os.makedirs(os.path.dirname(args.output_preds) or ".", exist_ok=True)
            result.to_csv(args.output_preds, index=False)
            print(f"\nPredictions saved to {args.output_preds}")
        else:
            print("\nPredictions preview:")
            print(result.head())


if __name__ == "__main__":
    main()
