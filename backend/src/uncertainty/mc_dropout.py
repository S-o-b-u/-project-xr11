"""
Module for Monte Carlo Dropout uncertainty estimation.

Note: TorchXRayVision models (like DenseNet) contain dropout layers by default,
making them suitable for MC Dropout uncertainty estimation without architecture changes.
"""

import numpy as np
import torch
from typing import Dict, Any, List


class MCDropoutEstimator:
    """
    Estimates model uncertainty using Monte Carlo dropout sampling during inference.
    """

    def __init__(self, n_samples: int = 10, uncertainty_threshold: float = 0.15):
        """
        Initializes the MCDropoutEstimator with sample counts and variance thresholds.
        """
        self.n_samples = n_samples
        self.uncertainty_threshold = uncertainty_threshold
        self.dropout_enabled = False

    def _enable_dropout(self, model: torch.nn.Module) -> torch.nn.Module:
        """
        Enables dropout layers in the model while keeping the rest in evaluation mode.
        """

        def set_dropout_to_train(m):
            if (
                type(m) == torch.nn.Dropout
                or type(m) == torch.nn.Dropout2d
                or type(m) == torch.nn.Dropout3d
            ):
                m.train()

        # Ensure base model is in eval mode first
        model.eval()
        # Then specifically turn dropout layers to train mode
        model.apply(set_dropout_to_train)
        self.dropout_enabled = True
        return model

    def estimate(
        self,
        model: torch.nn.Module,
        image_tensor: torch.Tensor,
        n_samples: int = None,
        pathology_labels: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Runs Monte Carlo dropout passes to estimate predictive uncertainty.

        Parameters
        ----------
        model : torch.nn.Module
        image_tensor : torch.Tensor
        n_samples : int, optional
        pathology_labels : list of str, optional

        Returns
        -------
        dict
            Contains mean predictions, variance, entropy, and mutual information.
        """
        samples = n_samples if n_samples is not None else self.n_samples

        # 1. Enable dropout
        self._enable_dropout(model)

        all_preds = []
        # 2. Run model forward pass n_samples times
        with torch.no_grad():
            for _ in range(samples):
                out = model(image_tensor)
                # Enforce bounds [0, 1] for predictions (e.g., standard sigmoid)
                probs = torch.sigmoid(out)
                all_preds.append(probs.cpu().numpy().flatten())

        # 4. Disable dropout (restore eval mode)
        model.eval()
        self.dropout_enabled = False

        # 3 & 5. Compute statistics
        all_preds = np.array(all_preds)  # Shape: (samples, num_classes)

        mean_preds = np.mean(all_preds, axis=0)
        std_preds = np.std(all_preds, axis=0)
        var_preds = np.var(all_preds, axis=0)

        # 6. Compute entropies
        # Predictive entropy: -sum(mean_pred * log(mean_pred + 1e-8)) per class
        pred_entropy_per_class = -mean_preds * np.log(mean_preds + 1e-8)
        predictive_entropy = float(np.mean(pred_entropy_per_class))

        # Per-sample entropies
        sample_entropies = -all_preds * np.log(all_preds + 1e-8)
        mean_sample_entropies_per_class = np.mean(sample_entropies, axis=0)
        expected_entropy = float(np.mean(mean_sample_entropies_per_class))

        mutual_information = predictive_entropy - expected_entropy

        mean_variance = float(np.mean(var_preds))
        confidence = max(0.0, 1.0 - mean_variance)
        needs_human_review = mean_variance > self.uncertainty_threshold

        # uncertainty_level logic
        if mean_variance < 0.05:
            uncertainty_level = "low"
        elif mean_variance < 0.15:
            uncertainty_level = "medium"
        else:
            uncertainty_level = "high"

        mean_predictions_dict = {}
        if pathology_labels and len(pathology_labels) == len(mean_preds):
            for i, label in enumerate(pathology_labels):
                mean_predictions_dict[label] = float(mean_preds[i])
        else:
            for i in range(len(mean_preds)):
                mean_predictions_dict[f"class_{i}"] = float(mean_preds[i])

        return {
            "mean_predictions": mean_predictions_dict,
            "prediction_variance": mean_variance,
            "predictive_entropy": predictive_entropy,
            "mutual_information": mutual_information,
            "confidence": confidence,
            "needs_human_review": needs_human_review,
            "uncertainty_level": uncertainty_level,
            "n_samples_used": samples,
        }

    def estimate_from_array(
        self,
        model: torch.nn.Module,
        image_array: np.ndarray,
        pathology_labels: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Wrapper that converts a numpy image array to tensor and calls estimate().
        Handles normalization and batch dimension expansion.
        """
        # Add channel dim if missing
        if len(image_array.shape) == 2:
            image_array = np.expand_dims(image_array, axis=0)  # (1, H, W)

        # Add batch dim if missing
        if len(image_array.shape) == 3:
            image_array = np.expand_dims(image_array, axis=0)  # (1, C, H, W)

        tensor = torch.from_numpy(image_array).float()

        # Move to model's device
        device = next(model.parameters()).device
        tensor = tensor.to(device)

        return self.estimate(model, tensor, pathology_labels=pathology_labels)

    def get_uncertainty_report(self, estimate_result: Dict[str, Any]) -> str:
        """
        Returns a human-readable uncertainty report based on estimation results.
        """
        level = estimate_result.get("uncertainty_level", "unknown")
        conf = estimate_result.get("confidence", 0.0) * 100
        samples = estimate_result.get("n_samples_used", 0)
        needs_review = estimate_result.get("needs_human_review", False)

        report = f"Uncertainty: {level}. Prediction confidence: {conf:.2f}%. {samples} MC samples used."
        if needs_review:
            report += " HUMAN REVIEW REQUIRED: High variance detected in predictions."

        return report


if __name__ == "__main__":
    import json

    print("Testing MCDropoutEstimator...")

    # Create a dummy DenseNet-like model with dropout
    class DummyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = torch.nn.Linear(10, 10)
            self.drop = torch.nn.Dropout(0.5)
            self.fc2 = torch.nn.Linear(10, 5)

        def forward(self, x):
            x = self.fc1(x)
            x = self.drop(x)
            x = self.fc2(x)
            return x

    model = DummyModel()
    model.eval()  # Baseline is eval mode

    estimator = MCDropoutEstimator(n_samples=5)

    dummy_input = np.random.rand(1, 10).astype(np.float32)
    labels = ["Atelectasis", "Cardiomegaly", "Effusion", "Infiltration", "Mass"]

    res = estimator.estimate_from_array(model, dummy_input, pathology_labels=labels)

    print("\nEstimation Results:")
    print(json.dumps(res, indent=2))

    print("\nReport:")
    print(estimator.get_uncertainty_report(res))
