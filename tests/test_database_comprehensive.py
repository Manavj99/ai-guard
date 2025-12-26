"""Comprehensive tests for database.py module to achieve 80%+ coverage."""

import pytest
import os
from datetime import datetime
from unittest.mock import patch, MagicMock, Mock
import psycopg2

from src.ai_guard.database import (
    User,
    Project,
    Metric,
    Alert,
    DatabaseManager,
    get_database_manager,
    initialize_database,
)


class TestModels:
    """Test database models."""

    def test_user_model(self):
        """Test User model."""
        now = datetime.now()
        user = User(
            id=1,
            username="testuser",
            name="Test User",
            email="test@example.com",
            role="admin",
            created_at=now,
            updated_at=now,
            is_active=True,
        )
        assert user.id == 1
        assert user.username == "testuser"
        assert user.is_active is True

    def test_project_model(self):
        """Test Project model."""
        now = datetime.now()
        project = Project(
            id=1,
            project_id="proj_001",
            name="Test Project",
            description="Test description",
            status="healthy",
            last_analysis=now,
            quality_score=90.0,
            security_score=85.0,
            coverage=80.0,
            created_at=now,
            updated_at=now,
        )
        assert project.project_id == "proj_001"
        assert project.quality_score == 90.0

    def test_metric_model(self):
        """Test Metric model."""
        now = datetime.now()
        metric = Metric(
            id=1,
            name="test_metric",
            value=42.0,
            metric_type="counter",
            timestamp=now,
            tags={"env": "test"},
            metadata={"key": "value"},
        )
        assert metric.name == "test_metric"
        assert metric.value == 42.0
        assert metric.tags == {"env": "test"}

    def test_alert_model(self):
        """Test Alert model."""
        now = datetime.now()
        alert = Alert(
            id=1,
            alert_id="alert_001",
            title="Test Alert",
            message="Test message",
            level="warning",
            status="active",
            timestamp=now,
            metadata={"key": "value"},
        )
        assert alert.alert_id == "alert_001"
        assert alert.status == "active"


class TestDatabaseManager:
    """Test DatabaseManager class."""

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_init(self, mock_pool):
        """Test database manager initialization."""
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        assert manager._pool is not None
        assert manager.config["host"] == os.getenv("DB_HOST", "localhost")

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_init_pool_failure(self, mock_pool):
        """Test initialization with pool failure."""
        mock_pool.side_effect = psycopg2.Error("Connection failed")
        manager = DatabaseManager()
        assert manager._pool is None

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_get_connection(self, mock_pool):
        """Test getting connection from pool."""
        mock_conn = MagicMock()
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        conn = manager.get_connection()
        assert conn == mock_conn

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_get_connection_no_pool(self, mock_pool):
        """Test getting connection when pool not initialized."""
        mock_pool.side_effect = psycopg2.Error()
        manager = DatabaseManager()
        with pytest.raises(Exception, match="Database pool not initialized"):
            manager.get_connection()

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_return_connection(self, mock_pool):
        """Test returning connection to pool."""
        mock_conn = MagicMock()
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        manager.return_connection(mock_conn)
        mock_pool_instance.putconn.assert_called_once_with(mock_conn)

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_return_connection_no_pool(self, mock_pool):
        """Test returning connection when no pool."""
        mock_pool.side_effect = psycopg2.Error()
        manager = DatabaseManager()
        manager.return_connection(MagicMock())  # Should not crash

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_execute_query_select(self, mock_pool):
        """Test executing SELECT query."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        result = manager.execute_query("SELECT * FROM users", fetch=True)
        assert len(result) == 1
        assert result[0]["name"] == "test"
        mock_cursor.execute.assert_called_once()

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_execute_query_insert(self, mock_pool):
        """Test executing INSERT query."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        result = manager.execute_query(
            "INSERT INTO users (username) VALUES (%s)", ("test",), fetch=False
        )
        assert result == 1
        mock_conn.commit.assert_called()

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_execute_query_error(self, mock_pool):
        """Test executing query with error."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("Query failed")
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        with pytest.raises(psycopg2.Error):
            manager.execute_query("SELECT * FROM users")
        mock_conn.rollback.assert_called()


class TestUserMethods:
    """Test user management methods."""

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_get_user_by_username(self, mock_pool):
        """Test getting user by username."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "username": "testuser",
                "name": "Test",
                "email": "test@example.com",
                "role": "admin",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True,
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        user = manager.get_user_by_username("testuser")
        assert user is not None
        assert user.username == "testuser"

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_get_user_by_username_not_found(self, mock_pool):
        """Test getting user by username when not found."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        user = manager.get_user_by_username("nonexistent")
        assert user is None

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_get_user_by_id(self, mock_pool):
        """Test getting user by ID."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "username": "testuser",
                "name": "Test",
                "email": "test@example.com",
                "role": "admin",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True,
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        user = manager.get_user_by_id(1)
        assert user is not None
        assert user.id == 1

    @patch("src.ai_guard.database.generate_password_hash")
    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_verify_user_password(self, mock_pool, mock_hash):
        """Test verifying user password."""
        from werkzeug.security import check_password_hash

        mock_hash.return_value = "hashed_password"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"password_hash": "hashed_password"}]
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        with patch("src.ai_guard.database.check_password_hash", return_value=True):
            result = manager.verify_user_password("testuser", "password")
            assert result is True

    @patch("src.ai_guard.database.generate_password_hash")
    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_create_user(self, mock_pool, mock_hash):
        """Test creating a user."""
        mock_hash.return_value = "hashed_password"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        result = manager.create_user(
            "testuser", "password", "Test User", "test@example.com", "user"
        )
        assert result is True

    @patch("src.ai_guard.database.generate_password_hash")
    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_create_user_integrity_error(self, mock_pool, mock_hash):
        """Test creating user with integrity error."""
        mock_hash.return_value = "hashed_password"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.IntegrityError("Duplicate key")
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        result = manager.create_user(
            "testuser", "password", "Test User", "test@example.com", "user"
        )
        assert result is False

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_get_all_users(self, mock_pool):
        """Test getting all users."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "username": "user1",
                "name": "User 1",
                "email": "user1@example.com",
                "role": "user",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "is_active": True,
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        users = manager.get_all_users()
        assert len(users) == 1
        assert users[0].username == "user1"


class TestProjectMethods:
    """Test project management methods."""

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_get_all_projects(self, mock_pool):
        """Test getting all projects."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "project_id": "proj_001",
                "name": "Project 1",
                "description": "Description",
                "status": "healthy",
                "last_analysis": datetime.now(),
                "quality_score": 90.0,
                "security_score": 85.0,
                "coverage": 80.0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        projects = manager.get_all_projects()
        assert len(projects) == 1
        assert projects[0].project_id == "proj_001"

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_create_project(self, mock_pool):
        """Test creating a project."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        result = manager.create_project(
            "proj_001", "Test Project", "Description", "healthy", 90.0, 85.0, 80.0
        )
        assert result is True


class TestMetricMethods:
    """Test metric methods."""

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_add_metric(self, mock_pool):
        """Test adding a metric."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        result = manager.add_metric("test_metric", 42.0, "counter", {"env": "test"})
        assert result is True

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_get_metrics(self, mock_pool):
        """Test getting metrics."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "test_metric",
                "value": 42.0,
                "metric_type": "counter",
                "timestamp": datetime.now(),
                "tags": {"env": "test"},
                "metadata": {},
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        metrics = manager.get_metrics()
        assert len(metrics) == 1
        assert metrics[0].name == "test_metric"

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_get_metrics_with_filters(self, mock_pool):
        """Test getting metrics with filters."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        metrics = manager.get_metrics(
            name="test", start_time=datetime.now(), end_time=datetime.now(), limit=10
        )
        assert isinstance(metrics, list)


class TestAlertMethods:
    """Test alert methods."""

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_get_all_alerts(self, mock_pool):
        """Test getting all alerts."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "alert_id": "alert_001",
                "title": "Test Alert",
                "message": "Test message",
                "level": "warning",
                "status": "active",
                "timestamp": datetime.now(),
                "resolved_at": None,
                "metadata": {},
            }
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        alerts = manager.get_all_alerts()
        assert len(alerts) == 1
        assert alerts[0].alert_id == "alert_001"

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_create_alert(self, mock_pool):
        """Test creating an alert."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        result = manager.create_alert(
            "alert_001", "Test Alert", "Test message", "warning"
        )
        assert result is True


class TestStatistics:
    """Test statistics methods."""

    @patch("src.ai_guard.database.SimpleConnectionPool")
    def test_get_system_statistics(self, mock_pool):
        """Test getting system statistics."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [{"total": 10, "active": 8}],  # users
            [{"total": 5, "healthy": 3, "warning": 1, "critical": 1}],  # projects
            [{"total": 20, "active": 5, "critical": 2}],  # alerts
            [{"total": 100, "unique_metrics": 10}],  # metrics
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn
        mock_pool.return_value = mock_pool_instance

        manager = DatabaseManager()
        stats = manager.get_system_statistics()
        assert "users" in stats
        assert "projects" in stats
        assert "alerts" in stats
        assert "metrics" in stats


class TestGlobalFunctions:
    """Test global functions."""

    @patch("src.ai_guard.database.DatabaseManager")
    def test_get_database_manager(self, mock_manager):
        """Test getting database manager."""
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance

        # Clear any existing instance
        import src.ai_guard.database as db_module
        db_module._db_manager = None

        manager1 = get_database_manager()
        manager2 = get_database_manager()
        # Should return same instance (singleton)
        assert manager1 is manager2

    @patch("src.ai_guard.database.get_database_manager")
    def test_initialize_database(self, mock_get_manager):
        """Test initializing database."""
        mock_manager = MagicMock()
        mock_manager.execute_query.return_value = [{"": 1}]
        mock_get_manager.return_value = mock_manager

        result = initialize_database()
        assert result is True

    @patch("src.ai_guard.database.get_database_manager")
    def test_initialize_database_error(self, mock_get_manager):
        """Test initializing database with error."""
        mock_manager = MagicMock()
        mock_manager.execute_query.side_effect = Exception("Connection failed")
        mock_get_manager.return_value = mock_manager

        result = initialize_database()
        assert result is False

