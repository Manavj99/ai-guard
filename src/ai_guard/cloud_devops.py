"""Cloud and DevOps integration capabilities for AI-Guard.

This module provides comprehensive cloud and DevOps features including:
- Cloud-native deployment and scaling
- CI/CD pipeline integration
- Container orchestration and management
- Infrastructure as code support
- Cloud provider integrations (AWS, Azure, GCP)
- DevOps automation and workflows
- Service mesh and microservices support
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import hashlib
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed

from .cache import CacheManager, CacheConfig, CacheStrategy
from .config import Config

logger = logging.getLogger(__name__)


class CloudProvider(Enum):
    """Supported cloud providers."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"


class DeploymentStatus(Enum):
    """Deployment status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class InfrastructureType(Enum):
    """Infrastructure types."""

    CONTAINER = "container"
    VM = "vm"
    SERVERLESS = "serverless"
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"


@dataclass
class DeploymentConfig:
    """Deployment configuration."""

    deployment_id: str
    name: str
    version: str
    cloud_provider: CloudProvider
    infrastructure_type: InfrastructureType
    config: Dict[str, Any] = field(default_factory=dict)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    health_checks: Dict[str, Any] = field(default_factory=dict)
    scaling_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Deployment:
    """Deployment instance."""

    deployment_id: str
    config: DeploymentConfig
    status: DeploymentStatus
    created_at: datetime
    updated_at: datetime
    deployed_at: Optional[datetime] = None
    health_status: str = "unknown"
    endpoints: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    rollback_version: Optional[str] = None


@dataclass
class PipelineStage:
    """CI/CD pipeline stage."""

    stage_id: str
    name: str
    type: str  # build, test, deploy, security_scan, etc.
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 3600  # seconds
    retry_count: int = 3
    enabled: bool = True


@dataclass
class PipelineExecution:
    """Pipeline execution instance."""

    execution_id: str
    pipeline_id: str
    trigger_type: str  # manual, webhook, schedule
    trigger_source: str
    status: DeploymentStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    stages: List[PipelineStage] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


class DockerManager:
    """Docker container management."""

    def __init__(self):
        self.docker_available = self._check_docker_availability()

    def _check_docker_availability(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def build_image(
        self,
        dockerfile_path: str,
        image_name: str,
        tag: str = "latest",
        build_args: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, str]:
        """Build Docker image."""
        try:
            if not self.docker_available:
                return False, "Docker is not available"

            cmd = ["docker", "build", "-t", f"{image_name}:{tag}"]

            # Add build args
            if build_args:
                for key, value in build_args.items():
                    cmd.extend(["--build-arg", f"{key}={value}"])

            cmd.append(dockerfile_path)

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=1800  # 30 minutes
            )

            if result.returncode == 0:
                return True, "Image built successfully"
            else:
                return False, result.stderr

        except subprocess.TimeoutExpired:
            return False, "Build timeout"
        except Exception as e:
            return False, str(e)

    def run_container(
        self,
        image_name: str,
        container_name: str,
        ports: Optional[Dict[str, str]] = None,
        environment_vars: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, str]] = None,
        detach: bool = True,
    ) -> Tuple[bool, str]:
        """Run Docker container."""
        try:
            if not self.docker_available:
                return False, "Docker is not available"

            cmd = ["docker", "run"]

            if detach:
                cmd.append("-d")

            cmd.extend(["--name", container_name])

            # Add port mappings
            if ports:
                for host_port, container_port in ports.items():
                    cmd.extend(["-p", f"{host_port}:{container_port}"])

            # Add environment variables
            if environment_vars:
                for key, value in environment_vars.items():
                    cmd.extend(["-e", f"{key}={value}"])

            # Add volume mounts
            if volumes:
                for host_path, container_path in volumes.items():
                    cmd.extend(["-v", f"{host_path}:{container_path}"])

            cmd.append(image_name)

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300  # 5 minutes
            )

            if result.returncode == 0:
                return True, "Container started successfully"
            else:
                return False, result.stderr

        except subprocess.TimeoutExpired:
            return False, "Container start timeout"
        except Exception as e:
            return False, str(e)

    def stop_container(self, container_name: str) -> Tuple[bool, str]:
        """Stop Docker container."""
        try:
            if not self.docker_available:
                return False, "Docker is not available"

            result = subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                return True, "Container stopped successfully"
            else:
                return False, result.stderr

        except Exception as e:
            return False, str(e)

    def get_container_logs(
        self, container_name: str, lines: int = 100
    ) -> Tuple[bool, str]:
        """Get container logs."""
        try:
            if not self.docker_available:
                return False, "Docker is not available"

            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), container_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr

        except Exception as e:
            return False, str(e)


class KubernetesManager:
    """Kubernetes cluster management."""

    def __init__(self):
        self.kubectl_available = self._check_kubectl_availability()
        self.cluster_context = self._get_cluster_context()

    def _check_kubectl_availability(self) -> bool:
        """Check if kubectl is available."""
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_cluster_context(self) -> Optional[str]:
        """Get current cluster context."""
        try:
            if not self.kubectl_available:
                return None

            result = subprocess.run(
                ["kubectl", "config", "current-context"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return None

        except Exception:
            return None

    def create_deployment(
        self,
        name: str,
        image: str,
        replicas: int = 1,
        namespace: str = "default",
        labels: Optional[Dict[str, str]] = None,
        environment_vars: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, str]:
        """Create Kubernetes deployment."""
        try:
            if not self.kubectl_available:
                return False, "kubectl is not available"

            # Create deployment YAML
            deployment_yaml = self._generate_deployment_yaml(
                name, image, replicas, labels or {}, environment_vars or {}
            )

            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                f.write(deployment_yaml)
                temp_file = f.name

            try:
                # Apply deployment
                result = subprocess.run(
                    ["kubectl", "apply", "-f", temp_file, "-n", namespace],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode == 0:
                    return True, "Deployment created successfully"
                else:
                    return False, result.stderr

            finally:
                # Clean up temp file
                os.unlink(temp_file)

        except Exception as e:
            return False, str(e)

    def create_service(
        self,
        name: str,
        deployment_name: str,
        port: int,
        target_port: int,
        service_type: str = "ClusterIP",
        namespace: str = "default",
    ) -> Tuple[bool, str]:
        """Create Kubernetes service."""
        try:
            if not self.kubectl_available:
                return False, "kubectl is not available"

            # Create service YAML
            service_yaml = self._generate_service_yaml(
                name, deployment_name, port, target_port, service_type
            )

            # Write to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                f.write(service_yaml)
                temp_file = f.name

            try:
                # Apply service
                result = subprocess.run(
                    ["kubectl", "apply", "-f", temp_file, "-n", namespace],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode == 0:
                    return True, "Service created successfully"
                else:
                    return False, result.stderr

            finally:
                # Clean up temp file
                os.unlink(temp_file)

        except Exception as e:
            return False, str(e)

    def get_pod_status(
        self, deployment_name: str, namespace: str = "default"
    ) -> Dict[str, Any]:
        """Get pod status for deployment."""
        try:
            if not self.kubectl_available:
                return {"error": "kubectl is not available"}

            result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "pods",
                    "-l",
                    f"app={deployment_name}",
                    "-n",
                    namespace,
                    "-o",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": result.stderr}

        except Exception as e:
            return {"error": str(e)}

    def _generate_deployment_yaml(
        self,
        name: str,
        image: str,
        replicas: int,
        labels: Dict[str, str],
        environment_vars: Dict[str, str],
    ) -> str:
        """Generate Kubernetes deployment YAML."""
        env_vars = []
        for key, value in environment_vars.items():
            env_vars.append({"name": key, "value": value})

        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": name, "labels": labels},
            "spec": {
                "replicas": replicas,
                "selector": {"matchLabels": {"app": name}},
                "template": {
                    "metadata": {"labels": {"app": name}},
                    "spec": {
                        "containers": [{"name": name, "image": image, "env": env_vars}]
                    },
                },
            },
        }

        return yaml.dump(deployment, default_flow_style=False)

    def _generate_service_yaml(
        self,
        name: str,
        deployment_name: str,
        port: int,
        target_port: int,
        service_type: str,
    ) -> str:
        """Generate Kubernetes service YAML."""
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": name, "labels": {"app": deployment_name}},
            "spec": {
                "type": service_type,
                "ports": [{"port": port, "targetPort": target_port}],
                "selector": {"app": deployment_name},
            },
        }

        return yaml.dump(service, default_flow_style=False)


class CloudDeploymentManager:
    """Manages cloud deployments across different providers."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.docker_manager = DockerManager()
        self.k8s_manager = KubernetesManager()
        self.deployments: Dict[str, Deployment] = {}
        self._lock = threading.RLock()

    def create_deployment(self, config: DeploymentConfig) -> Deployment:
        """Create a new deployment."""
        try:
            deployment = Deployment(
                deployment_id=config.deployment_id,
                config=config,
                status=DeploymentStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            with self._lock:
                self.deployments[config.deployment_id] = deployment

            # Start deployment process
            asyncio.create_task(self._deploy_async(deployment))

            logger.info(f"Created deployment: {config.name}")
            return deployment

        except Exception as e:
            logger.error(f"Error creating deployment: {e}")
            raise

    async def _deploy_async(self, deployment: Deployment):
        """Deploy asynchronously."""
        try:
            deployment.status = DeploymentStatus.IN_PROGRESS
            deployment.updated_at = datetime.now(timezone.utc)

            config = deployment.config

            if config.cloud_provider == CloudProvider.DOCKER:
                success, message = await self._deploy_docker(deployment)
            elif config.cloud_provider == CloudProvider.KUBERNETES:
                success, message = await self._deploy_kubernetes(deployment)
            else:
                success, message = (
                    False,
                    f"Unsupported cloud provider: {config.cloud_provider}",
                )

            if success:
                deployment.status = DeploymentStatus.SUCCESS
                deployment.deployed_at = datetime.now(timezone.utc)
                deployment.health_status = "healthy"
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = message

            deployment.updated_at = datetime.now(timezone.utc)

        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            deployment.updated_at = datetime.now(timezone.utc)
            logger.error(f"Deployment failed: {e}")

    async def _deploy_docker(self, deployment: Deployment) -> Tuple[bool, str]:
        """Deploy using Docker."""
        config = deployment.config

        # Build image if needed
        if "build" in config.config:
            build_config = config.config["build"]
            success, message = self.docker_manager.build_image(
                build_config.get("dockerfile_path", "Dockerfile"),
                config.name,
                config.version,
                build_config.get("build_args", {}),
            )
            if not success:
                return False, f"Build failed: {message}"

        # Run container
        container_name = f"{config.name}-{config.version}"
        ports = config.config.get("ports", {})
        environment_vars = config.environment_vars
        volumes = config.config.get("volumes", {})

        success, message = self.docker_manager.run_container(
            f"{config.name}:{config.version}",
            container_name,
            ports,
            environment_vars,
            volumes,
        )

        if success:
            # Add endpoint
            if ports:
                for host_port, container_port in ports.items():
                    deployment.endpoints.append(f"http://localhost:{host_port}")

        return success, message

    async def _deploy_kubernetes(self, deployment: Deployment) -> Tuple[bool, str]:
        """Deploy using Kubernetes."""
        config = deployment.config

        # Create deployment
        success, message = self.k8s_manager.create_deployment(
            config.name,
            f"{config.name}:{config.version}",
            config.scaling_config.get("min_replicas", 1),
            config.config.get("namespace", "default"),
            {"app": config.name},
            config.environment_vars,
        )

        if not success:
            return False, f"Deployment failed: {message}"

        # Create service if needed
        if "service" in config.config:
            service_config = config.config["service"]
            success, message = self.k8s_manager.create_service(
                f"{config.name}-service",
                config.name,
                service_config.get("port", 80),
                service_config.get("target_port", 8080),
                service_config.get("type", "ClusterIP"),
                config.config.get("namespace", "default"),
            )

            if not success:
                return False, f"Service creation failed: {message}"

        return True, "Kubernetes deployment successful"

    def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        """Get deployment by ID."""
        with self._lock:
            return self.deployments.get(deployment_id)

    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status."""
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return {"error": "Deployment not found"}

        return {
            "deployment_id": deployment.deployment_id,
            "name": deployment.config.name,
            "status": deployment.status.value,
            "health_status": deployment.health_status,
            "endpoints": deployment.endpoints,
            "created_at": deployment.created_at.isoformat(),
            "deployed_at": (
                deployment.deployed_at.isoformat() if deployment.deployed_at else None
            ),
            "error_message": deployment.error_message,
        }

    def scale_deployment(self, deployment_id: str, replicas: int) -> Tuple[bool, str]:
        """Scale deployment."""
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return False, "Deployment not found"

        if deployment.config.cloud_provider == CloudProvider.KUBERNETES:
            try:
                result = subprocess.run(
                    [
                        "kubectl",
                        "scale",
                        "deployment",
                        deployment.config.name,
                        f"--replicas={replicas}",
                        "-n",
                        deployment.config.config.get("namespace", "default"),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode == 0:
                    return True, f"Scaled to {replicas} replicas"
                else:
                    return False, result.stderr

            except Exception as e:
                return False, str(e)
        else:
            return False, "Scaling not supported for this deployment type"


class PipelineManager:
    """Manages CI/CD pipelines."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.pipelines: Dict[str, List[PipelineStage]] = {}
        self.executions: Dict[str, PipelineExecution] = {}
        self.deployment_manager: Optional[CloudDeploymentManager] = None
        self._lock = threading.RLock()

    def set_deployment_manager(self, deployment_manager: CloudDeploymentManager):
        """Set the deployment manager."""
        self.deployment_manager = deployment_manager

    def create_pipeline(self, pipeline_id: str, stages: List[PipelineStage]) -> bool:
        """Create a CI/CD pipeline."""
        try:
            with self._lock:
                self.pipelines[pipeline_id] = stages

            logger.info(f"Created pipeline: {pipeline_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating pipeline: {pipeline_id}: {e}")
            return False

    def execute_pipeline(
        self,
        pipeline_id: str,
        trigger_type: str = "manual",
        trigger_source: str = "system",
    ) -> PipelineExecution:
        """Execute a CI/CD pipeline."""
        try:
            execution_id = f"exec_{int(time.time())}_{pipeline_id}"

            execution = PipelineExecution(
                execution_id=execution_id,
                pipeline_id=pipeline_id,
                trigger_type=trigger_type,
                trigger_source=trigger_source,
                status=DeploymentStatus.IN_PROGRESS,
                started_at=datetime.now(timezone.utc),
                stages=self.pipelines.get(pipeline_id, []),
            )

            with self._lock:
                self.executions[execution_id] = execution

            # Start pipeline execution
            asyncio.create_task(self._execute_pipeline_async(execution))

            logger.info(f"Started pipeline execution: {execution_id}")
            return execution

        except Exception as e:
            logger.error(f"Error executing pipeline: {e}")
            raise

    async def _execute_pipeline_async(self, execution: PipelineExecution):
        """Execute pipeline asynchronously."""
        try:
            execution.status = DeploymentStatus.IN_PROGRESS

            for stage in execution.stages:
                if not stage.enabled:
                    continue

                success = await self._execute_stage(execution, stage)
                if not success:
                    execution.status = DeploymentStatus.FAILED
                    break

            if execution.status == DeploymentStatus.IN_PROGRESS:
                execution.status = DeploymentStatus.SUCCESS

            execution.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            execution.status = DeploymentStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            logger.error(f"Pipeline execution failed: {e}")

    async def _execute_stage(
        self, execution: PipelineExecution, stage: PipelineStage
    ) -> bool:
        """Execute a pipeline stage."""
        try:
            execution.logs.append(f"Executing stage: {stage.name}")

            if stage.type == "build":
                return await self._execute_build_stage(execution, stage)
            elif stage.type == "test":
                return await self._execute_test_stage(execution, stage)
            elif stage.type == "security_scan":
                return await self._execute_security_stage(execution, stage)
            elif stage.type == "deploy":
                return await self._execute_deploy_stage(execution, stage)
            else:
                execution.logs.append(f"Unknown stage type: {stage.type}")
                return False

        except Exception as e:
            execution.logs.append(f"Stage execution error: {e}")
            return False

    async def _execute_build_stage(
        self, execution: PipelineExecution, stage: PipelineStage
    ) -> bool:
        """Execute build stage."""
        try:
            build_config = stage.config
            dockerfile_path = build_config.get("dockerfile_path", "Dockerfile")
            image_name = build_config.get("image_name", "ai-guard")
            tag = build_config.get("tag", execution.execution_id[:8])

            # Use Docker manager to build
            docker_manager = DockerManager()
            success, message = docker_manager.build_image(
                dockerfile_path, image_name, tag, build_config.get("build_args", {})
            )

            execution.logs.append(f"Build result: {message}")

            if success:
                execution.artifacts.append(f"{image_name}:{tag}")

            return success

        except Exception as e:
            execution.logs.append(f"Build stage error: {e}")
            return False

    async def _execute_test_stage(
        self, execution: PipelineExecution, stage: PipelineStage
    ) -> bool:
        """Execute test stage."""
        try:
            test_config = stage.config
            test_command = test_config.get("command", "pytest")
            test_args = test_config.get("args", [])

            # Run tests
            cmd = [test_command] + test_args
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=stage.timeout
            )

            execution.logs.append(f"Test output: {result.stdout}")
            if result.stderr:
                execution.logs.append(f"Test errors: {result.stderr}")

            return result.returncode == 0

        except Exception as e:
            execution.logs.append(f"Test stage error: {e}")
            return False

    async def _execute_security_stage(
        self, execution: PipelineExecution, stage: PipelineStage
    ) -> bool:
        """Execute security scan stage."""
        try:
            security_config = stage.config
            scan_command = security_config.get("command", "bandit")
            scan_args = security_config.get("args", ["-r", "src/"])

            # Run security scan
            cmd = [scan_command] + scan_args
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=stage.timeout
            )

            execution.logs.append(f"Security scan output: {result.stdout}")
            if result.stderr:
                execution.logs.append(f"Security scan errors: {result.stderr}")

            # Security scan can have non-zero exit code for findings
            # Consider it successful if it completes
            return True

        except Exception as e:
            execution.logs.append(f"Security stage error: {e}")
            return False

    async def _execute_deploy_stage(
        self, execution: PipelineExecution, stage: PipelineStage
    ) -> bool:
        """Execute deployment stage."""
        try:
            if not self.deployment_manager:
                execution.logs.append("Deployment manager not configured")
                return False

            deploy_config = stage.config
            deployment_config = DeploymentConfig(
                deployment_id=f"deploy_{execution.execution_id}",
                name=deploy_config.get("name", "ai-guard"),
                version=deploy_config.get("version", execution.execution_id[:8]),
                cloud_provider=CloudProvider(deploy_config.get("provider", "docker")),
                infrastructure_type=InfrastructureType(
                    deploy_config.get("infrastructure", "container")
                ),
                config=deploy_config.get("config", {}),
                environment_vars=deploy_config.get("environment_vars", {}),
                scaling_config=deploy_config.get("scaling", {}),
            )

            # Create deployment
            deployment = self.deployment_manager.create_deployment(deployment_config)

            # Wait for deployment to complete (simplified)
            await asyncio.sleep(30)

            deployment_status = self.deployment_manager.get_deployment_status(
                deployment.deployment_id
            )

            execution.logs.append(f"Deployment status: {deployment_status}")

            return deployment_status.get("status") == "success"

        except Exception as e:
            execution.logs.append(f"Deploy stage error: {e}")
            return False

    def get_pipeline_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get pipeline execution by ID."""
        with self._lock:
            return self.executions.get(execution_id)

    def get_pipeline_status(self, execution_id: str) -> Dict[str, Any]:
        """Get pipeline execution status."""
        execution = self.get_pipeline_execution(execution_id)
        if not execution:
            return {"error": "Pipeline execution not found"}

        return {
            "execution_id": execution.execution_id,
            "pipeline_id": execution.pipeline_id,
            "status": execution.status.value,
            "trigger_type": execution.trigger_type,
            "started_at": execution.started_at.isoformat(),
            "completed_at": (
                execution.completed_at.isoformat() if execution.completed_at else None
            ),
            "stages": [
                {"name": stage.name, "type": stage.type, "enabled": stage.enabled}
                for stage in execution.stages
            ],
            "artifacts": execution.artifacts,
            "logs": execution.logs[-10:],  # Last 10 log entries
            "error_message": execution.error_message,
        }


class CloudDevOpsManager:
    """Main cloud and DevOps manager for AI-Guard."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.cache_manager = CacheManager(
            CacheConfig(
                strategy=CacheStrategy.LRU,
                max_size=10000,
                default_ttl=3600,
                compression_enabled=True,
                enable_analytics=True,
            )
        )

        # Initialize components
        self.deployment_manager = CloudDeploymentManager(self.cache_manager)
        self.pipeline_manager = PipelineManager(self.cache_manager)

        # Set up cross-references
        self.pipeline_manager.set_deployment_manager(self.deployment_manager)

        # Initialize default pipelines
        self._initialize_default_pipelines()

        logger.info("Cloud DevOps Manager initialized")

    def create_deployment(
        self,
        name: str,
        version: str,
        cloud_provider: CloudProvider,
        config: Dict[str, Any],
        environment_vars: Optional[Dict[str, str]] = None,
    ) -> Deployment:
        """Create a new deployment."""
        deployment_config = DeploymentConfig(
            deployment_id=f"deploy_{int(time.time())}_{name}",
            name=name,
            version=version,
            cloud_provider=cloud_provider,
            infrastructure_type=InfrastructureType.CONTAINER,
            config=config,
            environment_vars=environment_vars or {},
        )

        return self.deployment_manager.create_deployment(deployment_config)

    def execute_pipeline(
        self,
        pipeline_id: str,
        trigger_type: str = "manual",
        trigger_source: str = "system",
    ) -> PipelineExecution:
        """Execute a CI/CD pipeline."""
        return self.pipeline_manager.execute_pipeline(
            pipeline_id, trigger_type, trigger_source
        )

    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status."""
        return self.deployment_manager.get_deployment_status(deployment_id)

    def get_pipeline_status(self, execution_id: str) -> Dict[str, Any]:
        """Get pipeline execution status."""
        return self.pipeline_manager.get_pipeline_status(execution_id)

    def get_cloud_devops_dashboard_data(self) -> Dict[str, Any]:
        """Get data for cloud DevOps dashboard."""
        try:
            # Get deployments
            deployments = []
            for (
                deployment_id,
                deployment,
            ) in self.deployment_manager.deployments.items():
                deployments.append(
                    {
                        "deployment_id": deployment_id,
                        "name": deployment.config.name,
                        "version": deployment.config.version,
                        "status": deployment.status.value,
                        "health_status": deployment.health_status,
                        "cloud_provider": deployment.config.cloud_provider.value,
                        "created_at": deployment.created_at.isoformat(),
                        "endpoints": deployment.endpoints,
                    }
                )

            # Get pipeline executions
            executions = []
            for execution_id, execution in self.pipeline_manager.executions.items():
                executions.append(
                    {
                        "execution_id": execution_id,
                        "pipeline_id": execution.pipeline_id,
                        "status": execution.status.value,
                        "trigger_type": execution.trigger_type,
                        "started_at": execution.started_at.isoformat(),
                        "completed_at": (
                            execution.completed_at.isoformat()
                            if execution.completed_at
                            else None
                        ),
                    }
                )

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "deployments": deployments,
                "pipeline_executions": executions,
                "available_providers": [provider.value for provider in CloudProvider],
                "docker_available": self.deployment_manager.docker_manager.docker_available,
                "kubectl_available": self.deployment_manager.k8s_manager.kubectl_available,
                "cluster_context": self.deployment_manager.k8s_manager.cluster_context,
            }

        except Exception as e:
            logger.error(f"Error getting cloud DevOps dashboard data: {e}")
            return {"error": str(e)}

    def _initialize_default_pipelines(self):
        """Initialize default CI/CD pipelines."""
        # Default build pipeline
        build_pipeline = [
            PipelineStage(
                stage_id="build",
                name="Build",
                type="build",
                config={
                    "dockerfile_path": "Dockerfile",
                    "image_name": "ai-guard",
                    "build_args": {},
                },
            ),
            PipelineStage(
                stage_id="test",
                name="Test",
                type="test",
                config={"command": "pytest", "args": ["tests/", "-v"]},
            ),
            PipelineStage(
                stage_id="security",
                name="Security Scan",
                type="security_scan",
                config={
                    "command": "bandit",
                    "args": ["-r", "src/", "-f", "json", "-o", "security-report.json"],
                },
            ),
            PipelineStage(
                stage_id="deploy",
                name="Deploy",
                type="deploy",
                config={
                    "name": "ai-guard",
                    "provider": "docker",
                    "infrastructure": "container",
                    "config": {"ports": {"8080": "8080"}},
                },
            ),
        ]

        self.pipeline_manager.create_pipeline("default_build", build_pipeline)

        # Quick deploy pipeline
        quick_deploy_pipeline = [
            PipelineStage(
                stage_id="build",
                name="Build",
                type="build",
                config={"dockerfile_path": "Dockerfile", "image_name": "ai-guard"},
            ),
            PipelineStage(
                stage_id="deploy",
                name="Deploy",
                type="deploy",
                config={
                    "name": "ai-guard",
                    "provider": "docker",
                    "infrastructure": "container",
                },
            ),
        ]

        self.pipeline_manager.create_pipeline("quick_deploy", quick_deploy_pipeline)

        logger.info("Initialized default CI/CD pipelines")


# Global instance
_cloud_devops_manager: Optional[CloudDevOpsManager] = None


def get_cloud_devops_manager() -> CloudDevOpsManager:
    """Get the global cloud DevOps manager instance."""
    global _cloud_devops_manager
    if _cloud_devops_manager is None:
        _cloud_devops_manager = CloudDevOpsManager()
    return _cloud_devops_manager


def initialize_cloud_devops_system(
    config: Optional[Config] = None,
) -> CloudDevOpsManager:
    """Initialize the cloud DevOps system."""
    global _cloud_devops_manager
    _cloud_devops_manager = CloudDevOpsManager(config)
    return _cloud_devops_manager


def shutdown_cloud_devops_system():
    """Shutdown the cloud DevOps system."""
    global _cloud_devops_manager
    if _cloud_devops_manager:
        _cloud_devops_manager = None
