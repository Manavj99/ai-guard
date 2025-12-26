"""Cloud and DevOps Integration for AI-Guard.

This module provides cloud-native deployment capabilities including:
- Docker container management
- Kubernetes orchestration
- CI/CD pipeline automation
- Infrastructure as Code support
"""

import json
import logging
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Cloud providers."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    LOCAL = "local"


class ContainerStatus(Enum):
    """Container status."""

    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    PENDING = "pending"
    UNKNOWN = "unknown"


class PipelineStatus(Enum):
    """Pipeline status."""

    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PENDING = "pending"


@dataclass
class Container:
    """Docker container."""

    id: str
    name: str
    image: str
    status: ContainerStatus
    created_at: datetime = field(default_factory=datetime.now)
    ports: Dict[str, str] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KubernetesPod:
    """Kubernetes pod."""

    name: str
    namespace: str
    status: ContainerStatus
    created_at: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Pipeline:
    """CI/CD pipeline."""

    id: str
    name: str
    description: str
    status: PipelineStatus
    stages: List[Dict[str, Any]]
    triggers: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DockerManager:
    """Manages Docker containers."""

    def __init__(self):
        """Initialize the Docker manager."""
        self._lock = threading.RLock()
        self.containers: Dict[str, Container] = {}
        self.docker_available = self._check_docker_availability()

        logger.info(
            f"Docker Manager initialized (Docker available: {self.docker_available})"
        )

    def _check_docker_availability(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def create_container(
        self,
        image: str,
        name: str,
        ports: Optional[Dict[str, str]] = None,
        environment: Optional[Dict[str, str]] = None,
    ) -> Optional[Container]:
        """Create a Docker container."""
        with self._lock:
            if not self.docker_available:
                logger.warning("Docker is not available")
                return None

            try:
                # Build docker run command
                cmd = ["docker", "run", "-d"]

                if ports:
                    for host_port, container_port in ports.items():
                        cmd.extend(["-p", f"{host_port}:{container_port}"])

                if environment:
                    for key, value in environment.items():
                        cmd.extend(["-e", f"{key}={value}"])

                cmd.extend(["--name", name, image])

                # Run container
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    container_id = result.stdout.strip()
                    container = Container(
                        id=container_id,
                        name=name,
                        image=image,
                        status=ContainerStatus.RUNNING,
                        ports=ports or {},
                        environment=environment or {},
                    )

                    self.containers[container_id] = container
                    logger.info(f"Created container: {name} ({container_id})")
                    return container
                else:
                    logger.error(f"Failed to create container: {result.stderr}")
                    return None

            except Exception as e:
                logger.error(f"Error creating container: {e}")
                return None

    def stop_container(self, container_id: str) -> bool:
        """Stop a Docker container."""
        with self._lock:
            if not self.docker_available:
                return False

            try:
                result = subprocess.run(
                    ["docker", "stop", container_id],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    if container_id in self.containers:
                        self.containers[container_id].status = ContainerStatus.STOPPED
                    logger.info(f"Stopped container: {container_id}")
                    return True
                else:
                    logger.error(f"Failed to stop container: {result.stderr}")
                    return False

            except Exception as e:
                logger.error(f"Error stopping container: {e}")
                return False

    def get_container_status(self, container_id: str) -> Optional[ContainerStatus]:
        """Get container status."""
        with self._lock:
            if not self.docker_available:
                return None

            try:
                result = subprocess.run(
                    [
                        "docker",
                        "ps",
                        "-a",
                        "--filter",
                        f"id={container_id}",
                        "--format",
                        "{{.Status}}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0 and result.stdout.strip():
                    status_text = result.stdout.strip().lower()
                    if "running" in status_text:
                        return ContainerStatus.RUNNING
                    elif "exited" in status_text:
                        return ContainerStatus.STOPPED
                    else:
                        return ContainerStatus.UNKNOWN

                return None

            except Exception as e:
                logger.error(f"Error getting container status: {e}")
                return None


class KubernetesManager:
    """Manages Kubernetes resources."""

    def __init__(self):
        """Initialize the Kubernetes manager."""
        self._lock = threading.RLock()
        self.pods: Dict[str, KubernetesPod] = {}
        self.kubectl_available = self._check_kubectl_availability()

        logger.info(
            f"Kubernetes Manager initialized (kubectl available: {self.kubectl_available})"
        )

    def _check_kubectl_availability(self) -> bool:
        """Check if kubectl is available."""
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def create_pod(
        self,
        name: str,
        namespace: str = "default",
        image: str = "nginx:latest",
        labels: Optional[Dict[str, str]] = None,
    ) -> Optional[KubernetesPod]:
        """Create a Kubernetes pod."""
        with self._lock:
            if not self.kubectl_available:
                logger.warning("kubectl is not available")
                return None

            try:
                # Create pod YAML
                pod_yaml = f"""
apiVersion: v1
kind: Pod
metadata:
  name: {name}
  namespace: {namespace}
  labels:
    app: {name}
"""
                if labels:
                    for key, value in labels.items():
                        pod_yaml += f"    {key}: {value}\n"

                pod_yaml += f"""
spec:
  containers:
  - name: {name}
    image: {image}
    ports:
    - containerPort: 80
"""

                # Apply pod
                result = subprocess.run(
                    ["kubectl", "apply", "-f", "-"],
                    input=pod_yaml,
                    text=True,
                    capture_output=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    pod = KubernetesPod(
                        name=name,
                        namespace=namespace,
                        status=ContainerStatus.PENDING,
                        labels=labels or {},
                    )

                    self.pods[name] = pod
                    logger.info(f"Created pod: {name} in namespace {namespace}")
                    return pod
                else:
                    logger.error(f"Failed to create pod: {result.stderr}")
                    return None

            except Exception as e:
                logger.error(f"Error creating pod: {e}")
                return None

    def get_pod_status(
        self, name: str, namespace: str = "default"
    ) -> Optional[ContainerStatus]:
        """Get pod status."""
        with self._lock:
            if not self.kubectl_available:
                return None

            try:
                result = subprocess.run(
                    [
                        "kubectl",
                        "get",
                        "pod",
                        name,
                        "-n",
                        namespace,
                        "-o",
                        "jsonpath={.status.phase}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    phase = result.stdout.strip().lower()
                    if phase == "running":
                        return ContainerStatus.RUNNING
                    elif phase == "pending":
                        return ContainerStatus.PENDING
                    elif phase == "failed":
                        return ContainerStatus.FAILED
                    else:
                        return ContainerStatus.UNKNOWN

                return None

            except Exception as e:
                logger.error(f"Error getting pod status: {e}")
                return None


class PipelineManager:
    """Manages CI/CD pipelines."""

    def __init__(self):
        """Initialize the pipeline manager."""
        self._lock = threading.RLock()
        self.pipelines: Dict[str, Pipeline] = {}

        logger.info("Pipeline Manager initialized")

    def create_pipeline(
        self,
        name: str,
        description: str,
        stages: List[Dict[str, Any]],
        triggers: Optional[List[str]] = None,
    ) -> Pipeline:
        """Create a CI/CD pipeline."""
        with self._lock:
            pipeline_id = f"pipeline_{int(time.time())}"
            pipeline = Pipeline(
                id=pipeline_id,
                name=name,
                description=description,
                status=PipelineStatus.PENDING,
                stages=stages,
                triggers=triggers or [],
            )

            self.pipelines[pipeline_id] = pipeline
            logger.info(f"Created pipeline: {name}")
            return pipeline

    def execute_pipeline(self, pipeline_id: str) -> bool:
        """Execute a pipeline."""
        with self._lock:
            pipeline = self.pipelines.get(pipeline_id)
            if not pipeline:
                logger.error(f"Pipeline not found: {pipeline_id}")
                return False

            try:
                pipeline.status = PipelineStatus.RUNNING
                pipeline.last_run = datetime.now()

                logger.info(f"Executing pipeline: {pipeline.name}")

                # Simulate pipeline execution
                for i, stage in enumerate(pipeline.stages):
                    logger.info(
                        f"Executing stage {i+1}: {stage.get('name', 'Unknown')}"
                    )

                    # Simulate stage execution time
                    time.sleep(0.1)

                    # Check if stage has commands
                    commands = stage.get("commands", [])
                    for command in commands:
                        logger.debug(f"Executing command: {command}")
                        # In a real implementation, execute the command

                pipeline.status = PipelineStatus.SUCCESS
                logger.info(f"Pipeline completed successfully: {pipeline.name}")
                return True

            except Exception as e:
                pipeline.status = PipelineStatus.FAILED
                logger.error(f"Pipeline execution failed: {e}")
                return False

    def get_pipeline_status(self, pipeline_id: str) -> Optional[PipelineStatus]:
        """Get pipeline status."""
        with self._lock:
            pipeline = self.pipelines.get(pipeline_id)
            return pipeline.status if pipeline else None


class CloudIntegrationSystem:
    """Main cloud integration system."""

    def __init__(self):
        """Initialize the cloud integration system."""
        self._lock = threading.RLock()

        # Initialize managers
        self.docker_manager = DockerManager()
        self.kubernetes_manager = KubernetesManager()
        self.pipeline_manager = PipelineManager()

        logger.info("Cloud Integration System initialized")

    def deploy_application(
        self, app_name: str, image: str, deployment_type: str = "docker"
    ) -> bool:
        """Deploy an application."""
        with self._lock:
            try:
                if deployment_type == "docker":
                    container = self.docker_manager.create_container(
                        image=image, name=f"{app_name}_container", ports={"8080": "80"}
                    )
                    return container is not None

                elif deployment_type == "kubernetes":
                    pod = self.kubernetes_manager.create_pod(
                        name=f"{app_name}_pod", image=image
                    )
                    return pod is not None

                else:
                    logger.error(f"Unsupported deployment type: {deployment_type}")
                    return False

            except Exception as e:
                logger.error(f"Deployment failed: {e}")
                return False

    def create_ci_cd_pipeline(
        self, name: str, stages: List[Dict[str, Any]]
    ) -> Pipeline:
        """Create a CI/CD pipeline."""
        with self._lock:
            return self.pipeline_manager.create_pipeline(
                name=name,
                description=f"CI/CD pipeline for {name}",
                stages=stages,
                triggers=["push", "pull_request"],
            )

    def get_system_status(self) -> Dict[str, Any]:
        """Get cloud system status."""
        with self._lock:
            return {
                "docker": {
                    "available": self.docker_manager.docker_available,
                    "containers": len(self.docker_manager.containers),
                },
                "kubernetes": {
                    "available": self.kubernetes_manager.kubectl_available,
                    "pods": len(self.kubernetes_manager.pods),
                },
                "pipelines": {
                    "total": len(self.pipeline_manager.pipelines),
                    "running": len(
                        [
                            p
                            for p in self.pipeline_manager.pipelines.values()
                            if p.status == PipelineStatus.RUNNING
                        ]
                    ),
                },
            }


# Global instance
_cloud_system: Optional[CloudIntegrationSystem] = None
_cloud_lock = threading.RLock()


def get_cloud_system() -> CloudIntegrationSystem:
    """Get the global cloud system instance."""
    global _cloud_system
    with _cloud_lock:
        if _cloud_system is None:
            _cloud_system = CloudIntegrationSystem()
        return _cloud_system


def initialize_cloud_integration() -> bool:
    """Initialize the cloud integration system."""
    try:
        get_cloud_system()
        logger.info("Cloud integration system initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Cloud integration system initialization failed: {e}")
        return False


if __name__ == "__main__":
    # Test cloud integration
    print("☁️ Testing AI-Guard Cloud Integration")

    success = initialize_cloud_integration()
    if success:
        print("✅ Cloud integration system initialized successfully")

        cloud_system = get_cloud_system()

        # Test pipeline creation
        stages = [
            {
                "name": "Build",
                "type": "build",
                "commands": ["npm install", "npm build"],
            },
            {"name": "Test", "type": "test", "commands": ["npm test"]},
            {"name": "Deploy", "type": "deploy", "commands": ["npm deploy"]},
        ]

        pipeline = cloud_system.create_ci_cd_pipeline("Test Pipeline", stages)
        print(f"✅ Pipeline created: {pipeline.name}")

        # Test pipeline execution
        success = cloud_system.pipeline_manager.execute_pipeline(pipeline.id)
        if success:
            print("✅ Pipeline execution successful")

        # Show system status
        status = cloud_system.get_system_status()
        print(f"📊 Cloud System Status: {json.dumps(status, indent=2)}")
    else:
        print("❌ Cloud integration system initialization failed")
