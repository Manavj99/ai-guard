#!/usr/bin/env python3
"""
AI-Guard Web Application
A comprehensive web interface for AI-Guard enterprise features.
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
from ai_guard.credentials import (
    get_display_credentials,
    get_hashed_credentials,
)
from ai_guard.monitoring import get_monitoring_system, AlertLevel, AlertChannel, HealthStatus

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

def _get_login_context() -> Dict[str, Any]:
    return {"sample_credentials": get_display_credentials()}


# User management (in production, use a proper database)
USERS = get_hashed_credentials(generate_password_hash)

# Sample data for demonstration
SAMPLE_PROJECTS = [
    {
        'id': 'proj_001',
        'name': 'AI-Guard Core',
        'description': 'Main AI-Guard application',
        'status': 'healthy',
        'last_analysis': datetime.now() - timedelta(minutes=5),
        'quality_score': 92.5,
        'security_score': 88.0,
        'coverage': 85.3
    },
    {
        'id': 'proj_002',
        'name': 'Web Interface',
        'description': 'AI-Guard web dashboard',
        'status': 'healthy',
        'last_analysis': datetime.now() - timedelta(minutes=2),
        'quality_score': 89.2,
        'security_score': 91.5,
        'coverage': 78.9
    },
    {
        'id': 'proj_003',
        'name': 'API Gateway',
        'description': 'REST API services',
        'status': 'warning',
        'last_analysis': datetime.now() - timedelta(hours=1),
        'quality_score': 76.8,
        'security_score': 82.1,
        'coverage': 72.4
    }
]

SAMPLE_ALERTS = [
    {
        'id': 'alert_001',
        'title': 'High CPU Usage',
        'message': 'CPU usage has exceeded 80% threshold',
        'level': 'warning',
        'timestamp': datetime.now() - timedelta(minutes=10),
        'status': 'active'
    },
    {
        'id': 'alert_002',
        'title': 'Memory Usage Alert',
        'message': 'Memory usage is at 90%',
        'level': 'critical',
        'timestamp': datetime.now() - timedelta(minutes=5),
        'status': 'active'
    },
    {
        'id': 'alert_003',
        'title': 'Slow Analysis',
        'message': 'Code analysis taking longer than 60 seconds',
        'level': 'warning',
        'timestamp': datetime.now() - timedelta(minutes=15),
        'status': 'resolved'
    }
]

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
    context = _get_login_context()
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            if not username or not password:
                flash('Username and password are required', 'error')
                return render_template('login.html', **context)
            
            logger.info(f"Login attempt for user: {username}")
            
            if username in USERS and check_password_hash(USERS[username]['password'], password):
                session['user_id'] = username
                session.permanent = True
                session['user'] = {
                    'username': username,
                    'name': USERS[username]['name'],
                    'role': USERS[username]['role'],
                    'email': USERS[username]['email']
                }
                
                # Generate JWT token
                token = jwt.encode({
                    'user_id': username,
                    'role': USERS[username]['role'],
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }, app.config['JWT_SECRET_KEY'], algorithm='HS256')
                
                session['token'] = token
                logger.info(f"Login successful for user: {username}")
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                logger.warning(f"Invalid login attempt for user: {username}")
                flash('Invalid username or password', 'error')
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('login.html', **context)

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
    
    # Calculate project statistics
    total_projects = len(SAMPLE_PROJECTS)
    healthy_projects = len([p for p in SAMPLE_PROJECTS if p['status'] == 'healthy'])
    warning_projects = len([p for p in SAMPLE_PROJECTS if p['status'] == 'warning'])
    critical_projects = len([p for p in SAMPLE_PROJECTS if p['status'] == 'critical'])
    
    # Calculate average scores
    avg_quality = sum(p['quality_score'] for p in SAMPLE_PROJECTS) / len(SAMPLE_PROJECTS)
    avg_security = sum(p['security_score'] for p in SAMPLE_PROJECTS) / len(SAMPLE_PROJECTS)
    avg_coverage = sum(p['coverage'] for p in SAMPLE_PROJECTS) / len(SAMPLE_PROJECTS)
    
    return jsonify({
        'analytics': analytics_stats,
        'monitoring': latest_metrics,
        'projects': {
            'total': total_projects,
            'healthy': healthy_projects,
            'warning': warning_projects,
            'critical': critical_projects,
            'health_percentage': (healthy_projects / total_projects) * 100
        },
        'averages': {
            'quality_score': round(avg_quality, 1),
            'security_score': round(avg_security, 1),
            'coverage': round(avg_coverage, 1)
        },
        'alerts': {
            'total': len(SAMPLE_ALERTS),
            'active': len([a for a in SAMPLE_ALERTS if a['status'] == 'active']),
            'critical': len([a for a in SAMPLE_ALERTS if a['level'] == 'critical' and a['status'] == 'active'])
        }
    })

@app.route('/api/projects')
def get_projects():
    """Get all projects."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify(SAMPLE_PROJECTS)

@app.route('/api/alerts')
def get_alerts():
    """Get all alerts."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify(SAMPLE_ALERTS)

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
    
    metrics = monitoring_system.metrics_collector.get_metrics()
    metrics_data = []
    
    for metric in metrics[-50:]:  # Last 50 metrics
        metrics_data.append({
            'name': metric.name,
            'value': metric.value,
            'unit': metric.unit,
            'timestamp': metric.timestamp.isoformat(),
            'tags': metric.tags
        })
    
    return jsonify(metrics_data)

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
    
    users_data = []
    for username, user_data in USERS.items():
        users_data.append({
            'username': username,
            'name': user_data['name'],
            'role': user_data['role'],
            'email': user_data['email']
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
    
    if username in USERS:
        return jsonify({'error': 'User already exists'}), 409
    
    USERS[username] = {
        'password': generate_password_hash(password),
        'role': role,
        'name': name,
        'email': email
    }
    
    return jsonify({'message': 'User created successfully'}), 201

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
            
            # Check for alerts
            events = monitoring_system.alert_manager.check_alerts(monitoring_system.metrics_collector)
            
            if events:
                socketio.emit('alerts_update', [asdict(event) for event in events])
            
            # Send metrics update
            metrics = monitoring_system.metrics_collector.get_metrics()
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
    logger.info("🚀 Starting AI-Guard Web Application")
    logger.info("📊 Analytics System: Active")
    logger.info("📈 Monitoring System: Active")
    logger.info("🌐 Web Interface: http://localhost:5000")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
