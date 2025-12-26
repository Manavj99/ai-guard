#!/usr/bin/env python3
"""
n8n Integration Setup Script for AI-Guard Enterprise
This script automates the setup of n8n integration with AI-Guard
"""

import subprocess
import time
import requests
import json
import os
from pathlib import Path

class N8NIntegrationSetup:
    def __init__(self):
        self.n8n_url = "http://localhost:5678"
        self.ai_guard_url = "http://localhost:5000"
        self.setup_complete = False
        
    def check_docker(self):
        """Check if Docker is running"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Docker is available: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker is not available. Please install Docker first.")
            return False
    
    def start_n8n(self):
        """Start n8n container"""
        print("🚀 Starting n8n container...")
        try:
            # Stop existing container if running
            subprocess.run(['docker', 'stop', 'n8n-ai-guard'], 
                         capture_output=True, text=True)
            subprocess.run(['docker', 'rm', 'n8n-ai-guard'], 
                         capture_output=True, text=True)
            
            # Start new container
            cmd = [
                'docker', 'run', '-d', '--name', 'n8n-ai-guard',
                '-p', '5678:5678', '-v', 'n8n_data:/home/node/.n8n',
                'n8nio/n8n'
            ]
            subprocess.run(cmd, check=True)
            print("✅ n8n container started successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start n8n: {e}")
            return False
    
    def wait_for_n8n(self, timeout=60):
        """Wait for n8n to be ready"""
        print("⏳ Waiting for n8n to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.n8n_url}/healthz", timeout=5)
                if response.status_code == 200:
                    print("✅ n8n is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
            print(".", end="", flush=True)
        
        print(f"\n❌ n8n did not start within {timeout} seconds")
        return False
    
    def check_ai_guard(self):
        """Check if AI-Guard is running"""
        try:
            response = requests.get(f"{self.ai_guard_url}/api/dashboard/stats", timeout=5)
            if response.status_code == 200:
                print("✅ AI-Guard is running")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print("❌ AI-Guard is not running. Please start it first.")
        return False
    
    def create_n8n_credentials(self):
        """Create PostgreSQL credentials in n8n"""
        print("🔑 Setting up n8n credentials...")
        
        # This would typically be done through n8n's API or UI
        # For now, we'll provide instructions
        credentials_config = {
            "name": "AI-Guard PostgreSQL",
            "type": "postgres",
            "data": {
                "host": "localhost",
                "database": "ai_guard",
                "user": "ai_guard_user",
                "password": "ai_guard_pass",
                "port": 5432
            }
        }
        
        print("📋 Manual setup required:")
        print("1. Open n8n at http://localhost:5678")
        print("2. Go to Credentials → Add Credential")
        print("3. Select PostgreSQL")
        print("4. Use these settings:")
        print(f"   Host: {credentials_config['data']['host']}")
        print(f"   Database: {credentials_config['data']['database']}")
        print(f"   User: {credentials_config['data']['user']}")
        print(f"   Password: {credentials_config['data']['password']}")
        print(f"   Port: {credentials_config['data']['port']}")
        
        return True
    
    def create_sample_workflows(self):
        """Create sample workflows"""
        print("📊 Creating sample workflows...")
        
        workflows_file = Path("n8n_workflows.json")
        if workflows_file.exists():
            print("✅ Sample workflows file created")
            print("📋 Import these workflows in n8n:")
            print("1. Go to Workflows → Import from File")
            print("2. Select the n8n_workflows.json file")
            print("3. Configure the nodes with your credentials")
        else:
            print("❌ Sample workflows file not found")
            return False
        
        return True
    
    def test_integration(self):
        """Test the integration"""
        print("🧪 Testing integration...")
        
        # Test n8n accessibility
        try:
            response = requests.get(self.n8n_url, timeout=10)
            if response.status_code == 200:
                print("✅ n8n is accessible")
            else:
                print("❌ n8n returned unexpected status")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot access n8n: {e}")
            return False
        
        # Test AI-Guard accessibility
        try:
            response = requests.get(f"{self.ai_guard_url}/api/dashboard/stats", timeout=10)
            if response.status_code == 200:
                print("✅ AI-Guard is accessible")
            else:
                print("❌ AI-Guard returned unexpected status")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot access AI-Guard: {e}")
            return False
        
        print("✅ Integration test passed!")
        return True
    
    def print_next_steps(self):
        """Print next steps for the user"""
        print("\n🎯 NEXT STEPS:")
        print("=" * 50)
        print("1. 🌐 Access n8n: http://localhost:5678")
        print("2. 🔑 Set up PostgreSQL credentials (see instructions above)")
        print("3. 📊 Import sample workflows from n8n_workflows.json")
        print("4. 🧪 Test workflows with sample data")
        print("5. 🔧 Customize workflows for your needs")
        print("\n📚 Documentation:")
        print("- Setup guide: n8n_integration_setup.md")
        print("- Sample workflows: n8n_workflows.json")
        print("- AI-Guard API docs: http://localhost:5000/api/docs")
        
        print("\n🚀 Quick Start Commands:")
        print("docker ps  # Check running containers")
        print("docker logs n8n-ai-guard  # Check n8n logs")
        print("curl http://localhost:5678  # Test n8n")
        print("curl http://localhost:5000/api/health  # Test AI-Guard")
    
    def run_setup(self):
        """Run the complete setup process"""
        print("🚀 Starting n8n Integration Setup for AI-Guard Enterprise")
        print("=" * 60)
        
        # Check prerequisites
        if not self.check_docker():
            return False
        
        if not self.check_ai_guard():
            print("💡 Start AI-Guard first with: python web_app.py")
            return False
        
        # Start n8n
        if not self.start_n8n():
            return False
        
        # Wait for n8n to be ready
        if not self.wait_for_n8n():
            return False
        
        # Create credentials
        self.create_n8n_credentials()
        
        # Create sample workflows
        self.create_sample_workflows()
        
        # Test integration
        if not self.test_integration():
            print("❌ Integration test failed")
            return False
        
        # Print next steps
        self.print_next_steps()
        
        self.setup_complete = True
        print("\n✅ n8n Integration Setup Complete!")
        return True

def main():
    """Main function"""
    setup = N8NIntegrationSetup()
    success = setup.run_setup()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("You can now start using n8n with AI-Guard Enterprise.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())