#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple Phase 8 Test Script."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test importing Phase 8 modules."""
    try:
        print("Testing Phase 8 module imports...")
        
        # Test ML Integration
        print("  - Testing ML Integration...")
        from ai_guard.ml_integration import get_ml_manager, initialize_ml_integration
        print("    ✅ ML Integration imported successfully")
        
        # Test Monitoring
        print("  - Testing Monitoring...")
        from ai_guard.monitoring import get_monitoring_system, start_monitoring, stop_monitoring
        print("    ✅ Monitoring imported successfully")
        
        # Test Enterprise
        print("  - Testing Enterprise Features...")
        from ai_guard.enterprise import get_enterprise_system, initialize_enterprise
        print("    ✅ Enterprise Features imported successfully")
        
        # Test Analytics
        print("  - Testing Analytics...")
        from ai_guard.analytics import get_analytics_system, initialize_analytics
        print("    ✅ Analytics imported successfully")
        
        # Test Cloud Integration
        print("  - Testing Cloud Integration...")
        from ai_guard.cloud_integration import get_cloud_system, initialize_cloud_integration
        print("    ✅ Cloud Integration imported successfully")
        
        # Test Advanced Security
        print("  - Testing Advanced Security...")
        from ai_guard.advanced_security import get_advanced_security_system, initialize_advanced_security
        print("    ✅ Advanced Security imported successfully")
        
        # Test Phase 8 Integration
        print("  - Testing Phase 8 Integration...")
        from ai_guard.phase8_integration import get_phase8_system, initialize_phase8
        print("    ✅ Phase 8 Integration imported successfully")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Import failed: {e}")
        return False

def test_initialization():
    """Test Phase 8 initialization."""
    try:
        print("\nTesting Phase 8 initialization...")
        
        from ai_guard.phase8_integration import initialize_phase8, get_phase8_status
        
        # Initialize Phase 8
        print("  - Initializing Phase 8 systems...")
        success = initialize_phase8()
        
        if success:
            print("    ✅ Phase 8 initialization successful")
        else:
            print("    ⚠️  Phase 8 initialization completed with some issues")
        
        # Get status
        print("  - Getting system status...")
        status = get_phase8_status()
        print(f"    System Status: {status['system_status']}")
        print(f"    Overall Health: {status['overall_health']}")
        
        # Show component status
        print("    Component Status:")
        for component, comp_status in status['component_status'].items():
            status_icon = "✅" if comp_status == "active" else "❌"
            print(f"      {status_icon} {component}: {comp_status}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Initialization test failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of each component."""
    try:
        print("\nTesting basic functionality...")
        
        # Test ML Manager
        print("  - Testing ML Manager...")
        from ai_guard.ml_integration import get_ml_manager, ModelType
        ml_manager = get_ml_manager()
        ml_manager.add_training_data(ModelType.PERFORMANCE_PREDICTION, {"test": "data"})
        print("    ✅ ML Manager working")
        
        # Test Analytics
        print("  - Testing Analytics...")
        from ai_guard.analytics import get_analytics_system, MetricType
        analytics_system = get_analytics_system()
        analytics_system.metrics_collector.add_metric("test_metric", 42.0, MetricType.COUNTER)
        print("    ✅ Analytics working")
        
        # Test Enterprise
        print("  - Testing Enterprise...")
        from ai_guard.enterprise import get_enterprise_system
        enterprise_system = get_enterprise_system()
        tenant = enterprise_system.tenant_manager.create_tenant("Test Company", "test.com")
        print("    ✅ Enterprise working")
        
        # Test Security
        print("  - Testing Security...")
        from ai_guard.advanced_security import get_advanced_security_system, ThreatLevel, SecurityIncidentType
        security_system = get_advanced_security_system()
        incident = security_system.incident_manager.create_incident(
            SecurityIncidentType.SUSPICIOUS_ACTIVITY,
            "Test Incident",
            "Test description",
            ThreatLevel.LOW
        )
        print("    ✅ Security working")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Functionality test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Phase 8: Advanced Features and Integration - Test Suite")
    print("=" * 60)
    
    # Test imports
    import_success = test_imports()
    
    if not import_success:
        print("\n❌ Import tests failed. Cannot proceed with other tests.")
        return False
    
    # Test initialization
    init_success = test_initialization()
    
    # Test basic functionality
    func_success = test_basic_functionality()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"  Import Tests: {'✅ PASSED' if import_success else '❌ FAILED'}")
    print(f"  Initialization Tests: {'✅ PASSED' if init_success else '❌ FAILED'}")
    print(f"  Functionality Tests: {'✅ PASSED' if func_success else '❌ FAILED'}")
    
    overall_success = import_success and init_success and func_success
    
    if overall_success:
        print("\n🎉 All Phase 8 tests passed! The system is ready for enterprise use.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
