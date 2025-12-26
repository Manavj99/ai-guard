# PHASE 2: DATABASE INTEGRATION SETUP GUIDE

## 🎯 Overview
This guide will help you set up PostgreSQL database integration for your AI-Guard Enterprise system.

## 📋 Prerequisites
- ✅ Phase 1 completed (Web application running)
- ✅ Python 3.8+ installed
- ✅ pip package manager

## 🚀 Quick Start (Choose One Option)

### Option A: Local PostgreSQL Installation (Recommended for Development)

#### Windows:
1. **Download PostgreSQL:**
   - Visit: https://www.postgresql.org/download/windows/
   - Download the latest version installer
   - Run the installer and follow the setup wizard
   - **Important:** Remember the password you set for the 'postgres' user

2. **Verify Installation:**
   ```powershell
   psql --version
   ```

#### macOS:
```bash
# Install using Homebrew
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Verify installation
psql --version
```

#### Linux (Ubuntu):
```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
psql --version
```

### Option B: Docker Installation (Recommended for Production)

```bash
# Pull PostgreSQL image
docker pull postgres:15

# Run PostgreSQL container
docker run --name ai-guard-postgres \
  -e POSTGRES_PASSWORD=ai_guard_password \
  -e POSTGRES_DB=ai_guard_db \
  -e POSTGRES_USER=ai_guard_user \
  -p 5432:5432 \
  -d postgres:15

# Verify container is running
docker ps
```

### Option C: Cloud Database (Production)

#### AWS RDS:
1. Go to AWS RDS Console
2. Create PostgreSQL instance
3. Note the endpoint and credentials

#### Azure Database:
1. Go to Azure Portal
2. Create PostgreSQL Flexible Server
3. Note the server name and credentials

## 🛠️ Database Setup

### Step 1: Install Python Dependencies
```bash
# Install database dependencies
pip install -r requirements_db.txt

# Or install individually
pip install psycopg2-binary SQLAlchemy Flask-SQLAlchemy Flask-Migrate
```

### Step 2: Configure Environment Variables
```bash
# Copy the database configuration template
cp database_config.env .env

# Edit .env file with your database credentials
# Update these values:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_guard_db
DB_USER=ai_guard_user
DB_PASSWORD=ai_guard_password
```

### Step 3: Create Database and Schema
```bash
# Run the database setup script
python database_setup.py

# Choose option 3 for full setup with sample data
```

### Step 4: Test Database Connection
```bash
# Test the database integration
python -c "
from src.ai_guard.database import initialize_database
if initialize_database():
    print('✅ Database connection successful!')
else:
    print('❌ Database connection failed!')
"
```

## 🚀 Start the Enhanced Web Application

### Stop the Current Web App
```bash
# Stop the current web application (Ctrl+C if running in terminal)
# Or kill the process if running in background
```

### Start the Database-Integrated Web App
```bash
# Start the new web application with database support
python web_app_database.py
```

### Verify Everything is Working
1. **Open your browser:** http://localhost:5000
2. **Login with:** admin / Kc@12345
3. **Check the dashboard** for real-time data
4. **Test user management** (admin only)
5. **Verify data persistence** by refreshing the page

## 📊 What's New with Database Integration

### ✅ New Features:
- **Persistent User Management:** Users stored in PostgreSQL
- **Project Data Storage:** Projects saved to database
- **Metrics History:** All metrics stored with timestamps
- **Alert Management:** Alerts persisted and tracked
- **Real-time Data:** Background tasks store metrics to database
- **Enhanced Security:** Proper user authentication with database

### 🔧 Database Schema:
- **users:** User accounts and roles
- **projects:** Project information and metrics
- **metrics:** System metrics and analytics data
- **kpis:** Key Performance Indicators
- **kpi_measurements:** KPI measurement history
- **alerts:** System alerts and notifications
- **user_sessions:** User session management

## 🧪 Testing Your Setup

### Test 1: Database Connection
```bash
python -c "
from src.ai_guard.database import get_database_manager
db = get_database_manager()
result = db.execute_query('SELECT COUNT(*) FROM users')
print(f'Users in database: {result[0][0]}')
"
```

### Test 2: User Authentication
```bash
python -c "
from src.ai_guard.database import get_database_manager
db = get_database_manager()
user = db.get_user_by_username('admin')
print(f'Admin user found: {user.name if user else \"Not found\"}')
"
```

### Test 3: Web Application
1. Go to http://localhost:5000
2. Login with admin credentials
3. Check that dashboard loads with data
4. Navigate to different sections
5. Verify data persists after refresh

## 🚨 Troubleshooting

### Common Issues:

#### 1. Database Connection Failed
```bash
# Check if PostgreSQL is running
# Windows: Check Services
# macOS: brew services list | grep postgres
# Linux: sudo systemctl status postgresql

# Test connection manually
psql -h localhost -U postgres -d postgres
```

#### 2. Permission Denied
```bash
# Make sure the database user has proper permissions
# Run the database setup script again with option 2 or 3
python database_setup.py
```

#### 3. Port Already in Use
```bash
# Check what's using port 5000
netstat -an | findstr :5000

# Kill the process or use a different port
# Edit web_app_database.py and change port=5000 to port=5001
```

#### 4. Missing Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
pip install -r requirements_db.txt
```

## 📈 Next Steps (Phase 3)

Once Phase 2 is complete, you'll be ready for:
- **SSL/HTTPS Configuration**
- **Production Server Setup**
- **Security Hardening**
- **Advanced Monitoring**

## 🎉 Success Indicators

You'll know Phase 2 is complete when:
- ✅ PostgreSQL is installed and running
- ✅ Database schema is created
- ✅ Web application starts without errors
- ✅ Login works with database authentication
- ✅ Dashboard shows real-time data
- ✅ Data persists after page refresh
- ✅ User management works (admin only)

## 📞 Need Help?

If you encounter any issues:
1. Check the logs in the terminal
2. Verify database connection settings
3. Ensure all dependencies are installed
4. Check that PostgreSQL is running
5. Verify user permissions in database

---

**🎯 Ready to proceed to Phase 3? Let me know when Phase 2 is complete!**
