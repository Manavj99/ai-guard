#!/usr/bin/env python3
"""
AI-Guard Web Application with Database Integration
A comprehensive web interface for AI-Guard enterprise features with PostgreSQL backend.
"""

import os
import sys
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import AI-Guard modules
from ai_guard.analytics import get_analytics_system, MetricType, KPIType
from ai_guard.monitoring import get_monitoring_system, AlertLevel, AlertChannel, HealthStatus
from ai_guard.database import get_database_manager, initialize_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'ai-guard-enterprise-secret-key-2024')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-ai-guard-2024')

# Security configurations
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['PERMANENT_SESSION_LIFETIME'] = int(os.getenv('PERMANENT_SESSION_LIFETIME', '86400'))

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Global systems
analytics_system = get_analytics_system()
monitoring_system = get_monitoring_system()
db_manager = get_database_manager()

# Routes
@app.route('/')
def index():
    """Main dashboard."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session.get('user'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Verify user credentials using database
        if db_manager.verify_user_password(username, password):
            user = db_manager.get_user_by_username(username)
            if user:
                session['user_id'] = user.id
                session['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'role': user.role,
                    'email': user.email
                }
                
                # Generate JWT token
                token = jwt.encode({
                    'user_id': user.id,
                    'role': user.role,
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
                
                session['token'] = token
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout."""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Get dashboard statistics."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get analytics data
    analytics_stats = analytics_system.get_system_statistics()
    
    # Get monitoring data
    metrics = monitoring_system.metrics_collector.get_metrics()
    latest_metrics = {}
    for metric in metrics[-10:]:  # Last 10 metrics
        latest_metrics[metric.name] = {
            'value': metric.value,
            'unit': metric.unit,
            'timestamp': metric.timestamp.isoformat()
        }
    
    # Get database statistics
    db_stats = db_manager.get_system_statistics()
    
    # Get projects from database
    projects = db_manager.get_all_projects()
    total_projects = len(projects)
    healthy_projects = len([p for p in projects if p.status == 'healthy'])
    warning_projects = len([p for p in projects if p.status == 'warning'])
    critical_projects = len([p for p in projects if p.status == 'critical'])
    
    # Calculate average scores
    if projects:
        avg_quality = sum(p.quality_score for p in projects if p.quality_score) / len([p for p in projects if p.quality_score])
        avg_security = sum(p.security_score for p in projects if p.security_score) / len([p for p in projects if p.security_score])
        avg_coverage = sum(p.coverage for p in projects if p.coverage) / len([p for p in projects if p.coverage])
    else:
        avg_quality = avg_security = avg_coverage = 0.0
    
    return jsonify({
        'analytics': analytics_stats,
        'monitoring': latest_metrics,
        'database': db_stats,
        'projects': {
            'total': total_projects,
            'healthy': healthy_projects,
            'warning': warning_projects,
            'critical': critical_projects,
            'health_percentage': (healthy_projects / max(total_projects, 1)) * 100
        },
        'averages': {
            'quality_score': round(avg_quality, 1),
            'security_score': round(avg_security, 1),
            'coverage': round(avg_coverage, 1)
        },
        'alerts': db_stats.get('alerts', {})
    })

@app.route('/api/projects')
def get_projects():
    """Get all projects."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    projects = db_manager.get_all_projects()
    projects_data = []
    for project in projects:
        projects_data.append({
            'id': project.project_id,
            'name': project.name,
            'description': project.description,
            'status': project.status,
            'last_analysis': project.last_analysis.isoformat() if project.last_analysis else None,
            'quality_score': project.quality_score,
            'security_score': project.security_score,
            'coverage': project.coverage
        })
    
    return jsonify(projects_data)

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_role = session.get('user', {}).get('role')
    if user_role not in ['admin', 'manager']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    project_id = data.get('project_id')
    name = data.get('name')
    description = data.get('description', '')
    status = data.get('status', 'healthy')
    quality_score = data.get('quality_score')
    security_score = data.get('security_score')
    coverage = data.get('coverage')
    
    if not all([project_id, name]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    success = db_manager.create_project(
        project_id=project_id,
        name=name,
        description=description,
        status=status,
        quality_score=quality_score,
        security_score=security_score,
        coverage=coverage
    )
    
    if success:
        return jsonify({'message': 'Project created successfully'}), 201
    else:
        return jsonify({'error': 'Project creation failed'}), 500

@app.route('/api/alerts')
def get_alerts():
    """Get all alerts."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    alerts = db_manager.get_all_alerts()
    alerts_data = []
    for alert in alerts:
        alerts_data.append({
            'id': alert.alert_id,
            'title': alert.title,
            'message': alert.message,
            'level': alert.level,
            'timestamp': alert.timestamp.isoformat(),
            'status': alert.status,
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            'metadata': alert.metadata
        })
    
    return jsonify(alerts_data)

@app.route('/api/analytics/kpis')
def get_kpis():
    """Get KPI data."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    kpis = []
    for kpi_id, kpi in analytics_system.kpi_manager.kpis.items():
        measurement = analytics_system.kpi_manager.calculate_kpi(kpi_id)
        kpi_data = {
            'id': kpi_id,
            'name': kpi.name,
            'description': kpi.description,
            'type': kpi.kpi_type.value,
            'target_value': kpi.target_value,
            'warning_threshold': kpi.warning_threshold,
            'critical_threshold': kpi.critical_threshold,
            'current_value': measurement.value if measurement else 0,
            'status': measurement.status if measurement else 'unknown',
            'last_updated': kpi.last_updated.isoformat() if kpi.last_updated else None
        }
        kpis.append(kpi_data)
    
    return jsonify(kpis)

@app.route('/api/monitoring/metrics')
def get_metrics():
    """Get monitoring metrics."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get metrics from both analytics system and database
    analytics_metrics = monitoring_system.metrics_collector.get_metrics()
    db_metrics = db_manager.get_metrics(limit=50)
    
    metrics_data = []
    
    # Add analytics metrics
    for metric in analytics_metrics[-25:]:  # Last 25 analytics metrics
        metrics_data.append({
            'name': metric.name,
            'value': metric.value,
            'unit': metric.unit,
            'timestamp': metric.timestamp.isoformat(),
            'tags': metric.tags,
            'source': 'analytics'
        })
    
    # Add database metrics
    for metric in db_metrics[-25:]:  # Last 25 database metrics
        metrics_data.append({
            'name': metric.name,
            'value': metric.value,
            'unit': metric.metric_type,
            'timestamp': metric.timestamp.isoformat(),
            'tags': metric.tags,
            'source': 'database'
        })
    
    # Sort by timestamp
    metrics_data.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify(metrics_data[:50])  # Return last 50 metrics

@app.route('/api/analytics/report')
def generate_report():
    """Generate analytics report."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    report = analytics_system.generate_executive_report()
    return jsonify({
        'report_type': report.report_type,
        'generated_at': report.generated_at.isoformat(),
        'data': report.data,
        'summary': report.summary,
        'recommendations': report.recommendations
    })

@app.route('/api/users')
def get_users():
    """Get all users (admin only)."""
    if 'user_id' not in session or session.get('user', {}).get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    users = db_manager.get_all_users()
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'role': user.role,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'is_active': user.is_active
        })
    
    return jsonify(users_data)

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user (admin only)."""
    if 'user_id' not in session or session.get('user', {}).get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role')
    email = data.get('email')
    
    if not all([username, password, name, role, email]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if role not in ['admin', 'developer', 'manager', 'viewer']:
        return jsonify({'error': 'Invalid role'}), 400
    
    success = db_manager.create_user(username, password, name, email, role)
    
    if success:
        return jsonify({'message': 'User created successfully'}), 201
    else:
        return jsonify({'error': 'User creation failed - username may already exist'}), 409

# Navigation Routes
@app.route('/projects')
def projects():
    """Projects page."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('projects.html', user=session.get('user'))

@app.route('/analytics')
def analytics():
    """Analytics page."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('analytics.html', user=session.get('user'))

@app.route('/monitoring')
def monitoring():
    """Monitoring page."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('monitoring.html', user=session.get('user'))

@app.route('/users')
def users():
    """Users page (admin only)."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_role = session.get('user', {}).get('role')
    if user_role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    return render_template('users.html', user=session.get('user'))

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    if 'user_id' not in session:
        return False
    logger.info(f"Client connected: {session['user_id']}")
    emit('status', {'msg': 'Connected to AI-Guard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {session.get('user_id', 'unknown')}")

@socketio.on('request_update')
def handle_update_request():
    """Handle real-time update request."""
    if 'user_id' not in session:
        return
    
    # Send current metrics
    metrics = monitoring_system.metrics_collector.get_metrics()
    latest_metrics = {}
    for metric in metrics[-5:]:  # Last 5 metrics
        latest_metrics[metric.name] = {
            'value': metric.value,
            'unit': metric.unit,
            'timestamp': metric.timestamp.isoformat()
        }
    
    emit('metrics_update', latest_metrics)

# Background task for real-time updates
def background_task():
    """Background task for real-time updates."""
    while True:
        try:
            # Collect new metrics
            monitoring_system._collect_system_metrics()
            
            # Store metrics in database
            metrics = monitoring_system.metrics_collector.get_metrics()
            for metric in metrics[-5:]:  # Store last 5 metrics
                db_manager.add_metric(
                    name=metric.name,
                    value=metric.value,
                    metric_type=metric.metric_type.value,
                    tags=metric.tags,
                    metadata=metric.metadata
                )
            
            # Check for alerts
            events = monitoring_system.alert_manager.check_alerts(monitoring_system.metrics_collector)
            
            if events:
                for event in events:
                    db_manager.create_alert(
                        alert_id=f"alert_{int(time.time())}",
                        title=event.title,
                        message=event.message,
                        level=event.level.value,
                        metadata=event.metadata
                    )
                socketio.emit('alerts_update', [asdict(event) for event in events])
            
            # Send metrics update
            latest_metrics = {}
            for metric in metrics[-5:]:
                latest_metrics[metric.name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp.isoformat()
                }
            
            socketio.emit('metrics_update', latest_metrics)
            
            time.sleep(10)  # Update every 10 seconds
            
        except Exception as e:
            logger.error(f"Background task error: {e}")
            time.sleep(30)

if __name__ == '__main__':
    # Initialize database
    if not initialize_database():
        logger.error("Failed to initialize database. Please check your database configuration.")
        sys.exit(1)
    
    # Start monitoring system
    monitoring_system.start_monitoring()
    
    # Add some sample metrics
    analytics_system.metrics_collector.add_metric(
        name="analysis_duration",
        value=25.5,
        metric_type=MetricType.TIMER,
        tags={"environment": "production"}
    )
    
    analytics_system.metrics_collector.add_metric(
        name="quality_score",
        value=88.5,
        metric_type=MetricType.GAUGE,
        tags={"environment": "production"}
    )
    
    # Start background task
    background_thread = threading.Thread(target=background_task, daemon=True)
    background_thread.start()
    
    # Run the application
    logger.info("🚀 Starting AI-Guard Web Application with Database")
    logger.info("📊 Analytics System: Active")
    logger.info("📈 Monitoring System: Active")
    logger.info("🗄️ Database System: Active")
    logger.info("🌐 Web Interface: http://localhost:5000")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
