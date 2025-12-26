#!/usr/bin/env python3
"""
AI-Guard Web Application Startup Script
This script starts the AI-Guard web interface with proper configuration.
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ai_guard.credentials import get_display_credentials

def main():
    """Start the AI-Guard web application."""
    print("🚀 Starting AI-Guard Enterprise Web Interface...")
    print("=" * 60)
    
    # Check if web_app.py exists
    web_app_path = Path("web_app.py")
    if not web_app_path.exists():
        print("❌ Error: web_app.py not found!")
        print("Please make sure you're in the AI-Guard project directory.")
        return False
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required!")
        return False
    
    print(f"✅ Python version: {sys.version}")
    print(f"✅ Working directory: {os.getcwd()}")
    
    # Install dependencies if needed
    print("\n📦 Checking dependencies...")
    try:
        import flask
        import flask_socketio
        import jwt
        import psutil
        print("✅ All required dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "Flask", "Flask-SocketIO", "PyJWT", "psutil"])
        print("✅ Dependencies installed")
    
    # Start the web application
    print("\n🌐 Starting web server...")
    print("📍 Server will be available at: http://localhost:5000")
    print("🔐 Updated login credentials:")
    credentials = get_display_credentials()
    for _, cred in credentials.items():
        print(f"   {cred['role']}: {cred['username']} / {cred['password']}")
    print("\n" + "=" * 60)
    print("🚀 AI-Guard Enterprise is starting...")
    print("=" * 60)
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(3)
        webbrowser.open("http://localhost:5000")
        print("🌐 Browser opened automatically")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the Flask application
    try:
        subprocess.run([sys.executable, "web_app.py"])
    except KeyboardInterrupt:
        print("\n\n🛑 AI-Guard Enterprise stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting web application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
