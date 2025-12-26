// AI-Guard Enterprise JavaScript

// Global variables
let socket;
let charts = {};
let refreshInterval;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize the application
function initializeApp() {
    console.log('🚀 AI-Guard Enterprise Web Interface Initialized');
    
    // Initialize Socket.IO if available
    if (typeof io !== 'undefined') {
        initializeSocket();
    }
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize charts if on dashboard
    if (document.getElementById('metricsChart')) {
        initializeCharts();
    }
    
    // Start auto-refresh
    startAutoRefresh();
}

// Initialize Socket.IO connection
function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('✅ Connected to AI-Guard server');
        showNotification('Connected to AI-Guard server', 'success');
    });
    
    socket.on('disconnect', function() {
        console.log('❌ Disconnected from AI-Guard server');
        showNotification('Disconnected from AI-Guard server', 'warning');
    });
    
    socket.on('metrics_update', function(data) {
        console.log('📊 Metrics update received:', data);
        updateMetricsDisplay(data);
    });
    
    socket.on('alerts_update', function(alerts) {
        console.log('🚨 Alerts update received:', alerts);
        updateAlertsDisplay(alerts);
    });
    
    socket.on('status', function(data) {
        console.log('📡 Status:', data.msg);
    });
    
    // Request initial update
    socket.emit('request_update');
}

// Initialize tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize charts
function initializeCharts() {
    // Metrics Chart
    const metricsCtx = document.getElementById('metricsChart');
    if (metricsCtx) {
        charts.metrics = new Chart(metricsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU Usage (%)',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1,
                    fill: true
                }, {
                    label: 'Memory Usage (%)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    },
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }
    
    // Project Status Chart
    const projectStatusCtx = document.getElementById('projectStatusChart');
    if (projectStatusCtx) {
        charts.projectStatus = new Chart(projectStatusCtx, {
            type: 'doughnut',
            data: {
                labels: ['Healthy', 'Warning', 'Critical'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#1cc88a', '#f6c23e', '#e74a3b'],
                    hoverBackgroundColor: ['#17a673', '#dda20a', '#be2617'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
}

// Update metrics display
function updateMetricsDisplay(data) {
    if (charts.metrics) {
        const now = new Date().toLocaleTimeString();
        
        // Add new data points
        charts.metrics.data.labels.push(now);
        charts.metrics.data.datasets[0].data.push(data.cpu_usage?.value || 0);
        charts.metrics.data.datasets[1].data.push(data.memory_usage?.value || 0);
        
        // Keep only last 20 data points
        if (charts.metrics.data.labels.length > 20) {
            charts.metrics.data.labels.shift();
            charts.metrics.data.datasets[0].data.shift();
            charts.metrics.data.datasets[1].data.shift();
        }
        
        charts.metrics.update('none');
    }
    
    // Update real-time indicators
    updateRealTimeIndicators(data);
}

// Update alerts display
function updateAlertsDisplay(alerts) {
    // This will be handled by the dashboard-specific code
    if (typeof updateAlertsList === 'function') {
        updateAlertsList(alerts);
    }
}

// Update real-time indicators
function updateRealTimeIndicators(data) {
    // Add real-time indicator to relevant elements
    const indicators = document.querySelectorAll('.real-time-indicator');
    indicators.forEach(indicator => {
        indicator.classList.add('real-time-indicator');
    });
}

// Start auto-refresh
function startAutoRefresh() {
    // Refresh dashboard data every 30 seconds
    refreshInterval = setInterval(function() {
        if (typeof loadDashboardData === 'function') {
            loadDashboardData();
        }
    }, 30000);
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Utility functions
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

function getStatusColor(status) {
    switch(status) {
        case 'healthy': return 'success';
        case 'warning': return 'warning';
        case 'critical': return 'danger';
        case 'error': return 'danger';
        case 'info': return 'info';
        default: return 'secondary';
    }
}

function getAlertLevelColor(level) {
    switch(level) {
        case 'critical': return 'danger';
        case 'warning': return 'warning';
        case 'info': return 'info';
        case 'error': return 'danger';
        default: return 'secondary';
    }
}

function getKPIColor(status) {
    switch(status) {
        case 'normal': return 'success';
        case 'warning': return 'warning';
        case 'critical': return 'danger';
        case 'error': return 'danger';
        default: return 'info';
    }
}

// API helper functions
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showNotification(`API request failed: ${error.message}`, 'danger');
        throw error;
    }
}

// Export functions for global use
window.AIGuard = {
    showNotification,
    formatBytes,
    formatDateTime,
    formatDuration,
    getStatusColor,
    getAlertLevelColor,
    getKPIColor,
    apiRequest,
    initializeSocket,
    startAutoRefresh,
    stopAutoRefresh
};
