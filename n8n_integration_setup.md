# n8n Integration Setup for AI-Guard Enterprise

## 🚀 Quick Start Guide

### Step 1: Start n8n
```bash
# Option A: Using Docker (Recommended)
docker run -d --name n8n-ai-guard -p 5678:5678 n8nio/n8n

# Option B: Using docker-compose
docker-compose -f docker-compose-n8n.yml up -d
```

### Step 2: Access n8n Interface
- Open your browser and go to: http://localhost:5678
- Create your first account (no authentication required for local setup)

### Step 3: Configure PostgreSQL Connection
1. In n8n, go to **Credentials** → **Add Credential**
2. Select **PostgreSQL**
3. Configure with your AI-Guard database settings:
   - **Host**: localhost (or your database host)
   - **Database**: ai_guard
   - **User**: ai_guard_user
   - **Password**: ai_guard_pass
   - **Port**: 5432

## 🔧 Integration Workflows

### Workflow 1: Daily Security Report
```json
{
  "name": "Daily Security Report",
  "nodes": [
    {
      "name": "Cron Trigger",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "rule": {
          "interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]
        }
      }
    },
    {
      "name": "Query Security Data",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT * FROM security_scans WHERE created_at >= NOW() - INTERVAL '24 hours'"
      }
    },
    {
      "name": "Generate Report",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://localhost:5000/api/reports/generate",
        "method": "POST",
        "headers": {
          "Content-Type": "application/json"
        }
      }
    }
  ]
}
```

### Workflow 2: Real-time Security Alerts
```json
{
  "name": "Security Alert System",
  "nodes": [
    {
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "security-alert",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Process Alert",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Process security alert data\nconst alert = $input.first().json;\nreturn {\n  severity: alert.severity,\n  message: alert.message,\n  timestamp: new Date().toISOString()\n};"
      }
    },
    {
      "name": "Send Slack Notification",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "resource": "message",
        "operation": "post",
        "channel": "#security-alerts",
        "text": "🚨 Security Alert: {{ $json.message }}"
      }
    }
  ]
}
```

## 📊 Database Integration Points

### Available Tables for n8n Integration:
- `users` - User management data
- `security_scans` - Security scan results
- `projects` - Project information
- `analytics` - System analytics data

### Sample Queries:
```sql
-- Get recent security scans
SELECT * FROM security_scans 
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Get user activity
SELECT u.username, COUNT(s.id) as scan_count
FROM users u
LEFT JOIN security_scans s ON u.id = s.user_id
GROUP BY u.id, u.username;

-- Get system metrics
SELECT 
  DATE(created_at) as date,
  COUNT(*) as total_scans,
  AVG(execution_time) as avg_execution_time
FROM security_scans
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

## 🔗 API Endpoints for n8n

### AI-Guard API Endpoints:
- `GET /api/health` - System health check
- `GET /api/users` - User management
- `POST /api/reports/generate` - Generate reports
- `GET /api/analytics/metrics` - System metrics
- `POST /api/security/scan` - Trigger security scan

### Webhook Endpoints:
- `POST /webhook/security-alert` - Security alert webhook
- `POST /webhook/scan-complete` - Scan completion webhook
- `POST /webhook/user-activity` - User activity webhook

## 🎯 Next Steps

1. **Start n8n**: Follow Step 1 above
2. **Access Interface**: Go to http://localhost:5678
3. **Create First Workflow**: Import the sample workflows
4. **Test Integration**: Run test workflows
5. **Customize**: Adapt workflows to your needs

## 🔧 Troubleshooting

### Common Issues:
- **Port 5678 in use**: Change port with `-p 5679:5678`
- **Database connection failed**: Check PostgreSQL is running
- **Webhook not working**: Verify AI-Guard web app is running

### Logs:
```bash
# Check n8n logs
docker logs n8n-ai-guard

# Check AI-Guard logs
docker logs ai-guard-postgres
```

## 📈 Advanced Features

### Custom Nodes for AI-Guard:
- **AI-Guard Scanner Node**: Direct integration with security scanner
- **Report Generator Node**: Automated report creation
- **Analytics Processor Node**: Data analysis and insights

### Integration Examples:
- **Slack Integration**: Real-time notifications
- **Email Alerts**: Automated email reports
- **Jira Integration**: Create tickets for security issues
- **GitHub Integration**: Update repositories with scan results