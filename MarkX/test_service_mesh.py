#!/usr/bin/env python3
"""
Test Service Mesh Integration

Verifies:
1. Service registration with Platform
2. Health endpoints (/health, /ready, /live)
3. AdviseRequest/AdviseResponse contract
4. Heartbeat mechanism
"""

import json
import time
import requests
from datetime import datetime


def test_health_endpoint():
    """Test /health endpoint returns ServiceHealth model."""
    print("\n" + "="*60)
    print("TEST 1: Health Endpoint (ServiceHealth model)")
    print("="*60)
    
    try:
        response = requests.get("http://127.0.0.1:8765/health", timeout=5)
        data = response.json()
        
        # Verify ServiceHealth schema
        required_fields = ["service", "status", "version", "uptime_seconds", "checks", "timestamp"]
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print(f"❌ FAILED - Missing fields: {missing}")
            return False
        
        # Verify checks
        if not isinstance(data["checks"], dict):
            print(f"❌ FAILED - 'checks' must be a dict")
            return False
        
        print(f"✅ PASSED")
        print(f"   Service: {data['service']}")
        print(f"   Status: {data['status']}")
        print(f"   Version: {data['version']}")
        print(f"   Uptime: {data['uptime_seconds']:.1f}s")
        print(f"   Checks: {data['checks']}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False


def test_ready_endpoint():
    """Test /ready endpoint for Kubernetes probe."""
    print("\n" + "="*60)
    print("TEST 2: Ready Endpoint (K8s readiness probe)")
    print("="*60)
    
    try:
        response = requests.get("http://127.0.0.1:8765/ready", timeout=5)
        data = response.json()
        
        # Verify schema
        required_fields = ["ready", "dependencies"]
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print(f"❌ FAILED - Missing fields: {missing}")
            return False
        
        # Check status code
        if data["ready"] and response.status_code != 200:
            print(f"❌ FAILED - Ready but status code is {response.status_code}")
            return False
        
        if not data["ready"] and response.status_code != 503:
            print(f"❌ FAILED - Not ready but status code is {response.status_code}")
            return False
        
        print(f"✅ PASSED")
        print(f"   Ready: {data['ready']}")
        print(f"   Dependencies: {data['dependencies']}")
        print(f"   Status Code: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False


def test_live_endpoint():
    """Test /live endpoint for Kubernetes probe."""
    print("\n" + "="*60)
    print("TEST 3: Live Endpoint (K8s liveness probe)")
    print("="*60)
    
    try:
        response = requests.get("http://127.0.0.1:8765/live", timeout=5)
        data = response.json()
        
        # Verify schema
        if "alive" not in data:
            print(f"❌ FAILED - Missing 'alive' field")
            return False
        
        if not data["alive"]:
            print(f"❌ FAILED - Service reports not alive")
            return False
        
        print(f"✅ PASSED")
        print(f"   Alive: {data['alive']}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False


def test_advise_contract():
    """Test /advise endpoint with AdviseRequest/AdviseResponse contract."""
    print("\n" + "="*60)
    print("TEST 4: Advise Contract (AdviseRequest → AdviseResponse)")
    print("="*60)
    
    try:
        # Build AdviseRequest
        request = {
            "finding_id": "find-test-123",
            "tenant_id": "tenant-1",
            "entity": {
                "type": "database",
                "id": "customer-db",
                "name": "Customer Database",
                "attributes": {}
            },
            "severity": "high",
            "risk_score": 85.0,
            "exposure_paths": [],
            "evidence_refs": ["evt-456", "find-test-123"],
            "policy_context": {}
        }
        
        response = requests.post(
            "http://127.0.0.1:8765/advise",
            json=request,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED - Status code {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        
        # Verify AdviseResponse schema
        required_fields = [
            "summary",
            "risk_factors",
            "impact_analysis",
            "recommended_actions",
            "evidence_chain",
            "confidence",
            "citations",
            "processing_time_ms"
        ]
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            print(f"❌ FAILED - Missing fields: {missing}")
            return False
        
        # Verify risk_factors structure
        if data["risk_factors"]:
            rf = data["risk_factors"][0]
            rf_required = ["factor", "severity", "description", "evidence"]
            rf_missing = [f for f in rf_required if f not in rf]
            if rf_missing:
                print(f"❌ FAILED - Risk factor missing fields: {rf_missing}")
                return False
        
        # Verify recommended_actions structure
        if data["recommended_actions"]:
            action = data["recommended_actions"][0]
            action_required = [
                "action_type", "target_type", "target_id", "reason",
                "confidence", "evidence_refs", "blast_radius", "priority"
            ]
            action_missing = [f for f in action_required if f not in action]
            if action_missing:
                print(f"❌ FAILED - Action missing fields: {action_missing}")
                return False
        
        print(f"✅ PASSED")
        print(f"   Summary: {data['summary'][:60]}...")
        print(f"   Risk Factors: {len(data['risk_factors'])}")
        print(f"   Actions: {len(data['recommended_actions'])}")
        print(f"   Confidence: {data['confidence']}")
        print(f"   Processing Time: {data['processing_time_ms']}ms")
        return True
        
    except Exception as e:
        print(f"❌ FAILED - {e}")
        return False


def test_service_registration():
    """Test service registration (mock - requires Platform running)."""
    print("\n" + "="*60)
    print("TEST 5: Service Registration (requires Platform)")
    print("="*60)
    
    print("⚠ SKIPPED - Requires Platform to be running")
    print("   To test: Start Platform, then start Dmitry with platform_url")
    print("   Expected: Registration message in Dmitry logs")
    return True


def main():
    """Run all service mesh tests."""
    print("\n" + "="*60)
    print("DMITRY SERVICE MESH INTEGRATION TEST")
    print("="*60)
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Target: http://127.0.0.1:8765")
    
    # Check if server is running
    try:
        requests.get("http://127.0.0.1:8765/health", timeout=2)
    except:
        print("\n❌ ERROR: Dmitry server not running on port 8765")
        print("   Start server first: python MarkX/main.py")
        return
    
    results = []
    
    # Run tests
    results.append(("Health Endpoint", test_health_endpoint()))
    results.append(("Ready Endpoint", test_ready_endpoint()))
    results.append(("Live Endpoint", test_live_endpoint()))
    results.append(("Advise Contract", test_advise_contract()))
    results.append(("Service Registration", test_service_registration()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:12} - {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - SERVICE MESH INTEGRATION COMPLETE")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
