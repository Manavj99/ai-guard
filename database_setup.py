#!/usr/bin/env python3
"""
AI-Guard Database Setup Script
Creates PostgreSQL database schema for AI-Guard Enterprise system.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ai_guard.credentials import get_hashed_credentials

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'ai_guard_db'),
    'user': os.getenv('DB_USER', 'ai_guard_user'),
    'password': os.getenv('DB_PASSWORD', 'ai_guard_password')
}

def create_database():
    """Create the AI-Guard database and user."""
    try:
        # Connect to PostgreSQL server (default database)
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database='postgres',  # Connect to default database
            user='postgres',  # Use postgres superuser
            password=input("Enter PostgreSQL superuser password: ")
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
        logger.info(f"✅ Database '{DB_CONFIG['database']}' created successfully")
        
        # Create user
        cursor.execute(f"""
            CREATE USER {DB_CONFIG['user']} WITH ENCRYPTED PASSWORD '{DB_CONFIG['password']}'
        """)
        logger.info(f"✅ User '{DB_CONFIG['user']}' created successfully")
        
        # Grant privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_CONFIG['database']} TO {DB_CONFIG['user']}")
        logger.info(f"✅ Privileges granted to '{DB_CONFIG['user']}'")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"❌ Database creation failed: {e}")
        return False

def create_schema():
    """Create database schema."""
    try:
        # Connect to AI-Guard database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'developer', 'manager', 'viewer')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Create projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                project_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                status VARCHAR(20) NOT NULL CHECK (status IN ('healthy', 'warning', 'critical')),
                last_analysis TIMESTAMP,
                quality_score DECIMAL(5,2),
                security_score DECIMAL(5,2),
                coverage DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                value DECIMAL(15,6) NOT NULL,
                metric_type VARCHAR(20) NOT NULL CHECK (metric_type IN ('counter', 'gauge', 'timer', 'histogram')),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags JSONB,
                metadata JSONB
            )
        """)
        
        # Create KPIs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kpis (
                id SERIAL PRIMARY KEY,
                kpi_id VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                kpi_type VARCHAR(20) NOT NULL CHECK (kpi_type IN ('performance', 'quality', 'security', 'business', 'operational')),
                metric_name VARCHAR(100) NOT NULL,
                target_value DECIMAL(10,2) NOT NULL,
                warning_threshold DECIMAL(10,2),
                critical_threshold DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP
            )
        """)
        
        # Create KPI measurements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kpi_measurements (
                id SERIAL PRIMARY KEY,
                kpi_id VARCHAR(100) NOT NULL,
                value DECIMAL(10,2) NOT NULL,
                status VARCHAR(20) NOT NULL CHECK (status IN ('normal', 'warning', 'critical', 'unknown')),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB,
                FOREIGN KEY (kpi_id) REFERENCES kpis(kpi_id)
            )
        """)
        
        # Create alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                alert_id VARCHAR(50) UNIQUE NOT NULL,
                title VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                level VARCHAR(20) NOT NULL CHECK (level IN ('info', 'warning', 'critical')),
                status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'resolved', 'acknowledged')),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                metadata JSONB
            )
        """)
        
        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON metrics(name, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kpi_measurements_kpi_id ON kpi_measurements(kpi_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status_level ON alerts(status, level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Database schema created successfully")
        return True
        
    except psycopg2.Error as e:
        logger.error(f"❌ Schema creation failed: {e}")
        return False

def insert_sample_data():
    """Insert sample data for testing."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Insert sample users
        from werkzeug.security import generate_password_hash

        hashed_credentials = get_hashed_credentials(generate_password_hash)

        for username, details in hashed_credentials.items():
            user_data = (
                username,
                details["password"],
                details["name"],
                details["email"],
                details["role"],
            )
            cursor.execute("""
                INSERT INTO users (username, password_hash, name, email, role)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """, user_data)
        
        # Insert sample projects
        sample_projects = [
            ('proj_001', 'AI-Guard Core', 'Main AI-Guard application', 'healthy', datetime.now(), 92.5, 88.0, 85.3),
            ('proj_002', 'Web Interface', 'AI-Guard web dashboard', 'healthy', datetime.now(), 89.2, 91.5, 78.9),
            ('proj_003', 'API Gateway', 'REST API services', 'warning', datetime.now(), 76.8, 82.1, 72.4)
        ]
        
        for project_data in sample_projects:
            cursor.execute("""
                INSERT INTO projects (project_id, name, description, status, last_analysis, quality_score, security_score, coverage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (project_id) DO NOTHING
            """, project_data)
        
        # Insert sample KPIs
        sample_kpis = [
            ('performance_analysis_performance', 'Analysis Performance', 'Average time to complete code analysis', 'performance', 'analysis_duration', 30.0, 45.0, 60.0),
            ('quality_code_quality_score', 'Code Quality Score', 'Average code quality score', 'quality', 'quality_score', 85.0, 70.0, 60.0)
        ]
        
        for kpi_data in sample_kpis:
            cursor.execute("""
                INSERT INTO kpis (kpi_id, name, description, kpi_type, metric_name, target_value, warning_threshold, critical_threshold)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (kpi_id) DO NOTHING
            """, kpi_data)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Sample data inserted successfully")
        return True
        
    except psycopg2.Error as e:
        logger.error(f"❌ Sample data insertion failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 AI-Guard Database Setup")
    print("=" * 50)
    
    # Check if psycopg2 is installed
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not found. Installing...")
        os.system("pip install psycopg2-binary")
        import psycopg2
    
    print("\n📋 Setup Options:")
    print("1. Create database and user only")
    print("2. Create database, user, and schema")
    print("3. Full setup with sample data")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        success = create_database()
    elif choice == "2":
        success = create_database() and create_schema()
    elif choice == "3":
        success = create_database() and create_schema() and insert_sample_data()
    else:
        print("❌ Invalid choice")
        return
    
    if success:
        print("\n🎉 Database setup completed successfully!")
        print(f"📊 Database: {DB_CONFIG['database']}")
        print(f"👤 User: {DB_CONFIG['user']}")
        print(f"🔗 Connection: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    else:
        print("\n❌ Database setup failed. Please check the logs above.")

if __name__ == "__main__":
    main()
