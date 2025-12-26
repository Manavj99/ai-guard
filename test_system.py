#!/usr/bin/env python3
"""
Test script to verify AI-Guard system functionality
"""

import requests
import json
import time

def test_system():
    """Test the AI-Guard system functionality."""
    base_url = "http://localhost:5000"
    
    print("🚀 Testing AI-Guard Enterprise System")
    print("=" * 50)
    
    # Test 1: Basic connectivity
    print("\n1. Testing basic connectivity...")
    try:
        response = requests.get(base_url, timeout=5)
        print(f"   ✅ Status Code: {response.status_code}")
        print(f"   ✅ Content Length: {len(response.content)} bytes")
        print(f"   ✅ Response contains login form: {'login' in response.text.lower()}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    # Test 2: Authentication system
    print("\n2. Testing authentication system...")
    try:
        # Test admin login
        login_data = {
            'username': 'admin',
            'password': 'Kc@12345'
        }
        
        session = requests.Session()
        login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        
        if login_response.status_code == 302:  # Redirect after successful login
            print("   ✅ Admin login successful (redirect received)")
            
            # Test dashboard access
            dashboard_response = session.get(f"{base_url}/")
            if dashboard_response.status_code == 200:
                print("   ✅ Dashboard access successful")
            else:
                print(f"   ⚠️  Dashboard access issue: {dashboard_response.status_code}")
        else:
            print(f"   ❌ Admin login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Authentication test failed: {e}")
    
    # Test 3: API endpoints (without authentication - should get 401)
    print("\n3. Testing API security...")
    try:
        api_response = requests.get(f"{base_url}/api/dashboard/stats")
        if api_response.status_code == 401:
            print("   ✅ API security working (401 for unauthorized access)")
        else:
            print(f"   ⚠️  API security issue: {api_response.status_code}")
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
    
    # Test 4: Test with authenticated session
    print("\n4. Testing authenticated API access...")
    try:
        session = requests.Session()
        
        # Login first
        login_data = {'username': 'admin', 'password': 'Kc@12345'}
        login_response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        
        if login_response.status_code == 302:
            # Test dashboard stats API
            stats_response = session.get(f"{base_url}/api/dashboard/stats")
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                print("   ✅ Dashboard stats API working")
                print(f"   📊 Projects: {stats_data.get('projects', {}).get('total', 'N/A')}")
                print(f"   📈 Health: {stats_data.get('projects', {}).get('health_percentage', 'N/A')}%")
            else:
                print(f"   ❌ Dashboard stats API failed: {stats_response.status_code}")
            
            # Test KPIs API
            kpis_response = session.get(f"{base_url}/api/analytics/kpis")
            if kpis_response.status_code == 200:
                kpis_data = kpis_response.json()
                print(f"   ✅ KPIs API working - {len(kpis_data)} KPIs active")
            else:
                print(f"   ❌ KPIs API failed: {kpis_response.status_code}")
            
            # Test metrics API
            metrics_response = session.get(f"{base_url}/api/monitoring/metrics")
            if metrics_response.status_code == 200:
                metrics_data = metrics_response.json()
                print(f"   ✅ Metrics API working - {len(metrics_data)} metrics collected")
            else:
                print(f"   ❌ Metrics API failed: {metrics_response.status_code}")
                
    except Exception as e:
        print(f"   ❌ Authenticated API test failed: {e}")
    
    # Test 5: User role testing
    print("\n5. Testing user roles...")
    try:
        # Test viewer role (should get 401 for admin endpoints)
        viewer_session = requests.Session()
        viewer_login = {'username': 'viewer', 'password': 'Kc@1234567'}
        viewer_response = viewer_session.post(f"{base_url}/login", data=viewer_login, allow_redirects=False)
        
        if viewer_response.status_code == 302:
            # Test admin-only endpoint
            users_response = viewer_session.get(f"{base_url}/api/users")
            if users_response.status_code == 401:
                print("   ✅ Role-based access control working (viewer blocked from admin endpoints)")
            else:
                print(f"   ⚠️  Role-based access issue: {users_response.status_code}")
        else:
            print(f"   ❌ Viewer login failed: {viewer_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ User role test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 System testing completed!")
    print("\n📋 NEXT STEPS:")
    print("1. 🌐 Access your system at: http://localhost:5000")
    print("2. 🔐 Login with admin credentials: admin / Kc@12345")
    print("3. 📊 Explore the dashboard and analytics")
    print("4. 👥 Test different user roles")
    print("5. 💾 Plan database integration for Phase 2")

if __name__ == "__main__":
    test_system()
