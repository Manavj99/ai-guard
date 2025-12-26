"""Database models and utilities for AI-Guard Enterprise."""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)


@dataclass
class User:
    """User model."""

    id: int
    username: str
    name: str
    email: str
    role: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


@dataclass
class Project:
    """Project model."""

    id: int
    project_id: str
    name: str
    description: str
    status: str
    last_analysis: Optional[datetime]
    quality_score: Optional[float]
    security_score: Optional[float]
    coverage: Optional[float]
    created_at: datetime
    updated_at: datetime


@dataclass
class Metric:
    """Metric model."""

    id: int
    name: str
    value: float
    metric_type: str
    timestamp: datetime
    tags: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert model."""

    id: int
    alert_id: str
    title: str
    message: str
    level: str
    status: str
    timestamp: datetime
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DatabaseManager:
    """Database connection and query manager."""

    def __init__(self):
        """Initialize database manager."""
        self.config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "ai_guard_db"),
            "user": os.getenv("DB_USER", "ai_guard_user"),
            "password": os.getenv("DB_PASSWORD", "ai_guard_password"),
        }

        # Connection pool settings
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))

        self._pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool."""
        try:
            self._pool = SimpleConnectionPool(
                minconn=1, maxconn=self.pool_size, **self.config
            )
            logger.info("Database connection pool initialized")
        except psycopg2.Error as e:
            logger.error(f"Failed to initialize database pool: {e}")
            self._pool = None

    def get_connection(self):
        """Get database connection from pool."""
        if not self._pool:
            raise Exception("Database pool not initialized")
        return self._pool.getconn()

    def return_connection(self, conn):
        """Return connection to pool."""
        if self._pool:
            self._pool.putconn(conn)

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        """Execute database query."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)

            if fetch:
                if query.strip().upper().startswith("SELECT"):
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.rowcount
            else:
                conn.commit()
                return cursor.rowcount

        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database query failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.return_connection(conn)

    # User management methods
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = """
            SELECT id, username, name, email, role, created_at, updated_at, is_active
            FROM users WHERE username = %s AND is_active = TRUE
        """
        result = self.execute_query(query, (username,))
        if result:
            user_data = result[0]
            return User(
                id=user_data["id"],
                username=user_data["username"],
                name=user_data["name"],
                email=user_data["email"],
                role=user_data["role"],
                created_at=user_data["created_at"],
                updated_at=user_data["updated_at"],
                is_active=user_data["is_active"],
            )
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        query = """
            SELECT id, username, name, email, role, created_at, updated_at, is_active
            FROM users WHERE id = %s AND is_active = TRUE
        """
        result = self.execute_query(query, (user_id,))
        if result:
            user_data = result[0]
            return User(
                id=user_data["id"],
                username=user_data["username"],
                name=user_data["name"],
                email=user_data["email"],
                role=user_data["role"],
                created_at=user_data["created_at"],
                updated_at=user_data["updated_at"],
                is_active=user_data["is_active"],
            )
        return None

    def verify_user_password(self, username: str, password: str) -> bool:
        """Verify user password."""
        query = (
            "SELECT password_hash FROM users WHERE username = %s AND is_active = TRUE"
        )
        result = self.execute_query(query, (username,))
        if result:
            return check_password_hash(result[0]["password_hash"], password)
        return False

    def create_user(
        self, username: str, password: str, name: str, email: str, role: str
    ) -> bool:
        """Create new user."""
        query = """
            INSERT INTO users (username, password_hash, name, email, role)
            VALUES (%s, %s, %s, %s, %s)
        """
        password_hash = generate_password_hash(password)
        try:
            self.execute_query(
                query, (username, password_hash, name, email, role), fetch=False
            )
            return True
        except psycopg2.IntegrityError:
            return False

    def get_all_users(self) -> List[User]:
        """Get all users."""
        query = """
            SELECT id, username, name, email, role, created_at, updated_at, is_active
            FROM users WHERE is_active = TRUE ORDER BY created_at DESC
        """
        result = self.execute_query(query)
        users = []
        for user_data in result:
            users.append(
                User(
                    id=user_data["id"],
                    username=user_data["username"],
                    name=user_data["name"],
                    email=user_data["email"],
                    role=user_data["role"],
                    created_at=user_data["created_at"],
                    updated_at=user_data["updated_at"],
                    is_active=user_data["is_active"],
                )
            )
        return users

    # Project management methods
    def get_all_projects(self) -> List[Project]:
        """Get all projects."""
        query = """
            SELECT id, project_id, name, description, status, last_analysis,
                   quality_score, security_score, coverage, created_at, updated_at
            FROM projects ORDER BY updated_at DESC
        """
        result = self.execute_query(query)
        projects = []
        for project_data in result:
            projects.append(
                Project(
                    id=project_data["id"],
                    project_id=project_data["project_id"],
                    name=project_data["name"],
                    description=project_data["description"],
                    status=project_data["status"],
                    last_analysis=project_data["last_analysis"],
                    quality_score=(
                        float(project_data["quality_score"])
                        if project_data["quality_score"]
                        else None
                    ),
                    security_score=(
                        float(project_data["security_score"])
                        if project_data["security_score"]
                        else None
                    ),
                    coverage=(
                        float(project_data["coverage"])
                        if project_data["coverage"]
                        else None
                    ),
                    created_at=project_data["created_at"],
                    updated_at=project_data["updated_at"],
                )
            )
        return projects

    def create_project(
        self,
        project_id: str,
        name: str,
        description: str,
        status: str = "healthy",
        quality_score: float = None,
        security_score: float = None,
        coverage: float = None,
    ) -> bool:
        """Create new project."""
        query = """
            INSERT INTO projects (project_id, name, description, status, last_analysis,
                                 quality_score, security_score, coverage)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            self.execute_query(
                query,
                (
                    project_id,
                    name,
                    description,
                    status,
                    datetime.now(),
                    quality_score,
                    security_score,
                    coverage,
                ),
                fetch=False,
            )
            return True
        except psycopg2.IntegrityError:
            return False

    # Metrics methods
    def add_metric(
        self,
        name: str,
        value: float,
        metric_type: str,
        tags: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Add metric to database."""
        query = """
            INSERT INTO metrics (name, value, metric_type, tags, metadata)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            self.execute_query(
                query,
                (name, value, metric_type, tags or {}, metadata or {}),
                fetch=False,
            )
            return True
        except psycopg2.Error:
            return False

    def get_metrics(
        self,
        name: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100,
    ) -> List[Metric]:
        """Get metrics with optional filters."""
        query = "SELECT * FROM metrics WHERE 1=1"
        params = []

        if name:
            query += " AND name = %s"
            params.append(name)
        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)

        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)

        result = self.execute_query(query, tuple(params))
        metrics = []
        for metric_data in result:
            metrics.append(
                Metric(
                    id=metric_data["id"],
                    name=metric_data["name"],
                    value=float(metric_data["value"]),
                    metric_type=metric_data["metric_type"],
                    timestamp=metric_data["timestamp"],
                    tags=metric_data["tags"] or {},
                    metadata=metric_data["metadata"] or {},
                )
            )
        return metrics

    # Alerts methods
    def get_all_alerts(self) -> List[Alert]:
        """Get all alerts."""
        query = """
            SELECT id, alert_id, title, message, level, status, timestamp, resolved_at, metadata
            FROM alerts ORDER BY timestamp DESC
        """
        result = self.execute_query(query)
        alerts = []
        for alert_data in result:
            alerts.append(
                Alert(
                    id=alert_data["id"],
                    alert_id=alert_data["alert_id"],
                    title=alert_data["title"],
                    message=alert_data["message"],
                    level=alert_data["level"],
                    status=alert_data["status"],
                    timestamp=alert_data["timestamp"],
                    resolved_at=alert_data["resolved_at"],
                    metadata=alert_data["metadata"] or {},
                )
            )
        return alerts

    def create_alert(
        self,
        alert_id: str,
        title: str,
        message: str,
        level: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Create new alert."""
        query = """
            INSERT INTO alerts (alert_id, title, message, level, status, metadata)
            VALUES (%s, %s, %s, %s, 'active', %s)
        """
        try:
            self.execute_query(
                query, (alert_id, title, message, level, metadata or {}), fetch=False
            )
            return True
        except psycopg2.IntegrityError:
            return False

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        stats = {}

        # User statistics
        user_query = "SELECT COUNT(*) as total, COUNT(CASE WHEN is_active THEN 1 END) as active FROM users"
        user_result = self.execute_query(user_query)
        if user_result:
            stats["users"] = dict(user_result[0])

        # Project statistics
        project_query = """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN status = 'healthy' THEN 1 END) as healthy,
                   COUNT(CASE WHEN status = 'warning' THEN 1 END) as warning,
                   COUNT(CASE WHEN status = 'critical' THEN 1 END) as critical
            FROM projects
        """
        project_result = self.execute_query(project_query)
        if project_result:
            stats["projects"] = dict(project_result[0])

        # Alert statistics
        alert_query = """
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
                   COUNT(CASE WHEN level = 'critical' AND status = 'active' THEN 1 END) as critical
            FROM alerts
        """
        alert_result = self.execute_query(alert_query)
        if alert_result:
            stats["alerts"] = dict(alert_result[0])

        # Metric statistics
        metric_query = """
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT name) as unique_metrics
            FROM metrics
        """
        metric_result = self.execute_query(metric_query)
        if metric_result:
            stats["metrics"] = dict(metric_result[0])

        return stats


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def initialize_database() -> bool:
    """Initialize database connection."""
    try:
        db = get_database_manager()
        # Test connection
        db.execute_query("SELECT 1")
        logger.info("Database connection initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
