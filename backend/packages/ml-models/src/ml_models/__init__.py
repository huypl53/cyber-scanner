"""ML Models Package for Network Security Threat Detection."""

from ml_models.attack_classification import AttackClassificationPipeline

__all__ = ["AttackClassificationPipeline", "ThreatDetectionPipeline"]
__version__ = "0.1.0"


def __getattr__(name):
    """Lazy import ThreatDetectionPipeline to avoid hard tensorflow dependency."""
    if name == "ThreatDetectionPipeline":
        from ml_models.threat_classification import ThreatDetectionPipeline
        return ThreatDetectionPipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
