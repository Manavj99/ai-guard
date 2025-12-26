#!/usr/bin/env python3
"""
AI-Guard Enterprise Quick Start Script
This script provides an easy way to start the AI-Guard web application
"""

import os
import sys
import subprocess
import time
import requests
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask',
        'flask-socketio', 
        'pyjwt',
        'werkzeug',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False
    
    return True

def check_ai_guard_modules():
    """Check if AI-Guard modules are available"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from ai_guard.analytics import get_analytics_system
        from ai_guard.monitoring import get_monitoring_system
        from ai_guard.credentials import get_display_credentials  # noqa: F401
        print("✅ AI-Guard modules found")
        return True
    except ImportError as e:
        print(f"❌ AI-Guard modules not found: {e}")
        return False

def start_web_application():
    """Start the web application"""
    print("🚀 Starting AI-Guard Enterprise Web Application...")
    
    # Check if web_app.py exists
    web_app_path = Path(__file__).parent / 'web_app.py'
    if not web_app_path.exists():
        print("❌ web_app.py not found!")
        return False
    
    try:
        # Start the web application in a subprocess
        process = subprocess.Popen([
            sys.executable, str(web_app_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for the application to start
        print("⏳ Waiting for application to start...")
        time.sleep(5)
        
        # Check if the application is running
        try:
            response = requests.get('http://localhost:5000', timeout=5)
            if response.status_code == 200:
                print("✅ AI-Guard Enterprise is running!")
                print("🌐 Web Interface: http://localhost:5000")
                return True
        except requests.exceptions.RequestException:
            print("❌ Application failed to start or is not responding")
            return False
            
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False

def open_browser():
    """Open the web interface in the default browser"""
    try:
        webbrowser.open('http://localhost:5000')
        print("🌐 Opening web interface in your default browser...")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print("Please manually open: http://localhost:5000")

def print_login_info():
    """Print login information"""
    from ai_guard.credentials import get_display_credentials

    credentials = get_display_credentials()
    print("\n" + "="*60)
    print("🔐 LOGIN CREDENTIALS")
    print("="*60)
    for username, details in credentials.items():
        role = details["role"].ljust(10)
        print(f"{role}: {details['username']} / {details['password']}")
    print("="*60)
    print("📊 Dashboard: http://localhost:5000")
    print("📚 Documentation: README.md")
    print("🆘 Troubleshooting: LOGIN_TROUBLESHOOTING_GUIDE.md")
    print("="*60)

def main():
    """Main function"""
    print("🛡️  AI-Guard Enterprise Quick Start")
    print("="*50)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed. Please install missing packages manually.")
        return
    
    # Check AI-Guard modules
    if not check_ai_guard_modules():
        print("❌ AI-Guard modules not found. Please ensure the source code is properly installed.")
        return
    
    # Start web application
    if not start_web_application():
        print("❌ Failed to start web application.")
        return
    
    # Print login information
    print_login_info()
    
    # Ask if user wants to open browser
    try:
        open_browser_choice = input("\n🌐 Open web interface in browser? (y/n): ").lower().strip()
        if open_browser_choice in ['y', 'yes']:
            open_browser()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return
    
    print("\n🎉 AI-Guard Enterprise is ready!")
    print("Press Ctrl+C to stop the application when you're done.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
