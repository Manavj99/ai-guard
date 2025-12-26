"""Machine Learning Integration for AI-Guard.

This module provides ML capabilities for performance prediction and quality scoring.
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """ML model types."""

    PERFORMANCE_PREDICTION = "performance_prediction"
    QUALITY_SCORING = "quality_scoring"
    SECURITY_RISK_ASSESSMENT = "security_risk_assessment"
    CODE_COMPLEXITY_ANALYSIS = "code_complexity_analysis"


class ModelStatus(Enum):
    """ML model status."""

    TRAINING = "training"
    TRAINED = "trained"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class PredictionResult:
    """ML prediction result."""

    model_type: ModelType
    prediction: Union[float, int, str]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimpleMLModel:
    """Simple ML model implementation."""

    id: str
    model_type: ModelType
    name: str = ""
    status: ModelStatus = ModelStatus.UNKNOWN
    training_data: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_trained: Optional[datetime] = None
    accuracy: Optional[float] = None

    def train(self, data: List[Dict[str, Any]]) -> bool:
        """Train the model with provided data."""
        try:
            self.training_data.extend(data)
            self.status = ModelStatus.TRAINING

            # Simple training simulation
            time.sleep(0.1)  # Simulate training time

            self.status = ModelStatus.TRAINED
            self.last_trained = datetime.now()
            self.accuracy = 0.85 + (len(data) / 1000) * 0.1  # Simulate accuracy

            logger.info(
                f"Model {self.id} trained successfully with {len(data)} samples"
            )
            return True
        except Exception as e:
            self.status = ModelStatus.FAILED
            logger.error(f"Model {self.id} training failed: {e}")
            return False

    def predict(self, features: Dict[str, Any]) -> PredictionResult:
        """Make a prediction using the model."""
        if self.status != ModelStatus.TRAINED:
            raise ValueError(f"Model {self.id} is not trained")

        # Simple prediction logic based on model type
        if self.model_type == ModelType.PERFORMANCE_PREDICTION:
            # Predict execution time based on file count and complexity
            file_count = features.get("file_count", 1)
            complexity = features.get("complexity", 1.0)
            prediction = file_count * complexity * 0.5
            confidence = min(0.95, 0.7 + (len(self.training_data) / 100) * 0.25)
        elif self.model_type == ModelType.QUALITY_SCORING:
            # Predict quality score based on various metrics
            lines_of_code = features.get("lines_of_code", 100)
            test_coverage = features.get("test_coverage", 0.5)
            prediction = min(
                100, (test_coverage * 100) + (1000 / max(lines_of_code, 1)) * 10
            )
            confidence = min(0.95, 0.6 + test_coverage * 0.3)
        else:
            prediction = 0.5
            confidence = 0.5

        return PredictionResult(
            model_type=self.model_type,
            prediction=prediction,
            confidence=confidence,
            metadata={"features": features},
        )


class MLModelManager:
    """Manages ML models and training data."""

    def __init__(self):
        """Initialize the ML model manager."""
        self._lock = threading.RLock()
        self.models: Dict[str, SimpleMLModel] = {}
        self.training_data: Dict[ModelType, List[Dict[str, Any]]] = {}
        self.data_collector = MLDataCollector()

        # Initialize default models
        self._create_default_models()

        logger.info("ML Model Manager initialized")

    def _create_default_models(self):
        """Create default ML models."""
        default_models = [
            ModelType.PERFORMANCE_PREDICTION,
            ModelType.QUALITY_SCORING,
            ModelType.SECURITY_RISK_ASSESSMENT,
            ModelType.CODE_COMPLEXITY_ANALYSIS,
        ]

        for model_type in default_models:
            model_id = f"{model_type.value}_model"
            model = SimpleMLModel(id=model_id, model_type=model_type)
            self.models[model_id] = model
            self.training_data[model_type] = []

    def create_model(self, model_type: ModelType, name: str = "") -> SimpleMLModel:
        """Create a new ML model."""
        with self._lock:
            model_id = f"{model_type.value}_model_{int(time.time())}"
            model = SimpleMLModel(id=model_id, model_type=model_type, name=name)
            self.models[model_id] = model

            if model_type not in self.training_data:
                self.training_data[model_type] = []

            logger.info(f"Created ML model: {model_id}")
            return model

    def add_training_data(self, model_type: ModelType, data: Dict[str, Any]):
        """Add training data for a model type."""
        with self._lock:
            if model_type not in self.training_data:
                self.training_data[model_type] = []

            self.training_data[model_type].append(data)
            logger.debug(f"Added training data for {model_type.value}")

    def train_model(self, model_type: ModelType) -> bool:
        """Train a model with available training data."""
        with self._lock:
            # Find the model for this type
            model = None
            for m in self.models.values():
                if m.model_type == model_type:
                    model = m
                    break

            if not model:
                logger.error(f"No model found for type: {model_type}")
                return False

            training_data = self.training_data.get(model_type, [])
            if not training_data:
                logger.warning(f"No training data available for {model_type}")
                return False

            logger.info(
                f"Training {model_type.value} model with {len(training_data)} samples"
            )
            return model.train(training_data)

    def predict(
        self, model_type: ModelType, features: Dict[str, Any]
    ) -> Optional[PredictionResult]:
        """Make a prediction using the specified model."""
        with self._lock:
            # Find the model for this type
            model = None
            for m in self.models.values():
                if m.model_type == model_type:
                    model = m
                    break

            if not model:
                logger.error(f"No model found for type: {model_type}")
                return None

            try:
                return model.predict(features)
            except Exception as e:
                logger.error(f"Prediction failed for {model_type}: {e}")
                return None

    def get_model_status(self, model_type: ModelType) -> Optional[ModelStatus]:
        """Get the status of a model."""
        with self._lock:
            for model in self.models.values():
                if model.model_type == model_type:
                    return model.status
            return None

    def get_training_data_count(self, model_type: ModelType) -> int:
        """Get the number of training samples for a model type."""
        with self._lock:
            return len(self.training_data.get(model_type, []))

    def get_model_statistics(self) -> Dict[str, Any]:
        """Get statistics about all models."""
        with self._lock:
            stats = {
                "total_models": len(self.models),
                "models_by_type": {},
                "training_data_by_type": {},
                "model_statuses": {},
            }

            for model in self.models.values():
                model_type = model.model_type.value

                if model_type not in stats["models_by_type"]:
                    stats["models_by_type"][model_type] = 0
                stats["models_by_type"][model_type] += 1

                if model_type not in stats["model_statuses"]:
                    stats["model_statuses"][model_type] = model.status.value

                stats["training_data_by_type"][model_type] = len(
                    self.training_data.get(model.model_type, [])
                )

            return stats


class MLDataCollector:
    """Collects and organizes training data for ML models."""

    def __init__(self):
        """Initialize the ML data collector."""
        self._lock = threading.RLock()
        self.collected_data: Dict[str, List[Dict[str, Any]]] = {}

        logger.info("ML Data Collector initialized")

    def collect_performance_data(
        self,
        file_count: int,
        lines_of_code: int,
        complexity: float,
        execution_time: float,
    ) -> None:
        """Collect performance-related training data."""
        with self._lock:
            data = {
                "file_count": file_count,
                "lines_of_code": lines_of_code,
                "complexity": complexity,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
            }

            if "performance" not in self.collected_data:
                self.collected_data["performance"] = []

            self.collected_data["performance"].append(data)
            logger.debug(f"Collected performance data: {data}")

    def collect_quality_data(
        self,
        lines_of_code: int,
        test_coverage: float,
        cyclomatic_complexity: float,
        quality_score: float,
    ) -> None:
        """Collect quality-related training data."""
        with self._lock:
            data = {
                "lines_of_code": lines_of_code,
                "test_coverage": test_coverage,
                "cyclomatic_complexity": cyclomatic_complexity,
                "quality_score": quality_score,
                "timestamp": datetime.now().isoformat(),
            }

            if "quality" not in self.collected_data:
                self.collected_data["quality"] = []

            self.collected_data["quality"].append(data)
            logger.debug(f"Collected quality data: {data}")

    def get_collected_data(self, data_type: str) -> List[Dict[str, Any]]:
        """Get collected data of a specific type."""
        with self._lock:
            return self.collected_data.get(data_type, []).copy()

    def clear_data(self, data_type: Optional[str] = None) -> None:
        """Clear collected data."""
        with self._lock:
            if data_type:
                self.collected_data.pop(data_type, None)
                logger.info(f"Cleared {data_type} data")
            else:
                self.collected_data.clear()
                logger.info("Cleared all collected data")

    def add_data(self, data: Dict[str, Any]) -> None:
        """Add generic training data."""
        with self._lock:
            if "generic" not in self.collected_data:
                self.collected_data["generic"] = []

            self.collected_data["generic"].append(data)
            logger.debug(f"Added generic data: {data}")


# Global instances
_ml_manager: Optional[MLModelManager] = None
_ml_data_collector: Optional[MLDataCollector] = None
_ml_lock = threading.RLock()


def get_ml_manager() -> MLModelManager:
    """Get the global ML model manager instance."""
    global _ml_manager
    with _ml_lock:
        if _ml_manager is None:
            _ml_manager = MLModelManager()
        return _ml_manager


def get_ml_data_collector() -> MLDataCollector:
    """Get the global ML data collector instance."""
    global _ml_data_collector
    with _ml_lock:
        if _ml_data_collector is None:
            _ml_data_collector = MLDataCollector()
        return _ml_data_collector


def initialize_ml_integration() -> bool:
    """Initialize the ML integration system."""
    try:
        # Initialize components
        get_ml_manager()
        get_ml_data_collector()

        logger.info("ML Integration initialized successfully")
        return True
    except Exception as e:
        logger.error(f"ML Integration initialization failed: {e}")
        return False


if __name__ == "__main__":
    # Test ML integration
    print("🤖 Testing AI-Guard ML Integration")

    success = initialize_ml_integration()
    if success:
        print("✅ ML Integration initialized successfully")

        ml_manager = get_ml_manager()
        data_collector = get_ml_data_collector()

        # Test data collection
        data_collector.collect_performance_data(10, 1000, 5.2, 15.5)
        data_collector.collect_quality_data(1000, 0.85, 3.2, 92.5)

        # Test model training
        ml_manager.add_training_data(
            ModelType.PERFORMANCE_PREDICTION,
            {
                "file_count": 5,
                "lines_of_code": 500,
                "complexity": 3.0,
                "execution_time": 10.0,
            },
        )

        ml_manager.train_model(ModelType.PERFORMANCE_PREDICTION)

        # Test prediction
        prediction = ml_manager.predict(
            ModelType.PERFORMANCE_PREDICTION,
            {"file_count": 8, "lines_of_code": 800, "complexity": 4.0},
        )

        if prediction:
            print(
                f"✅ Prediction successful: {prediction.prediction} (confidence: {prediction.confidence:.2f})"
            )

        # Show statistics
        stats = ml_manager.get_model_statistics()
        print(f"📊 Model Statistics: {json.dumps(stats, indent=2)}")
    else:
        print("❌ ML Integration initialization failed")
