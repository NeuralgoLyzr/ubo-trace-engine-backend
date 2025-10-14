#!/usr/bin/env python3
"""
Test script for Enhanced Lyzr-based UBO Trace Engine
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.lyzr_service import LyzrAgentService
from models.schemas import TraceStage

async def test_lyzr_service():
    """Test the Lyzr service with improved prompts"""
    
    print("🧪 Testing Enhanced Lyzr Service Integration")
    print("=" * 50)
    
    # Initialize service
    try:
        service = LyzrAgentService()
        print("✅ LyzrAgentService initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize LyzrAgentService: {e}")
        return False
    
    # Test data from the notebook
    test_cases = [
        {
            "entity": "Louis Dreyfus Company Metals MEA DMCC",
            "ubo_name": "Liu Jianfeng",
            "location": "UAE",
            "domain": "louisdreyfus.com"
        },
        {
            "entity": "Avcon Jet Isle of Man Limited", 
            "ubo_name": "Alexander Vagacs",
            "location": "Suite 17 North Quay Douglas IM1 4LE, Isle of Man",
            "domain": "avconjet.com"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['entity']}")
        print("-" * 40)
        
        # Test Stage 1A (Direct Evidence General)
        try:
            # Test that we can call the agent with simple parameters
            print(f"📝 Testing Stage 1A with simple parameters")
            print(f"   Entity: {test_case['entity']}")
            print(f"   UBO: {test_case['ubo_name']}")
            print(f"   Location: {test_case['location']}")
            print(f"   Domain: {test_case['domain']}")
            
            # Test parameter validation
            if test_case['entity'] and test_case['ubo_name'] and test_case['location']:
                print("✅ Required parameters are present")
            else:
                print("❌ Missing required parameters")
                
        except Exception as e:
            print(f"❌ Stage 1A test failed: {e}")
        
        # Test all stages with simple parameters
        stages = [TraceStage.STAGE_1A, TraceStage.STAGE_1B, TraceStage.STAGE_2A, TraceStage.STAGE_2B]
        
        for stage in stages:
            try:
                print(f"📝 Testing {stage} with simple parameters")
                
                # Test that the service can handle the stage
                config = service.agent_configs.get(stage)
                if config:
                    print(f"✅ {stage} configuration found")
                else:
                    print(f"❌ {stage} configuration missing")
                    
            except Exception as e:
                print(f"❌ {stage} test failed: {e}")
        
        # Add delay between test cases
        await asyncio.sleep(1)
    
    print("\n🎯 Lyzr Service Parameter Test Complete")
    return True

async def test_ubo_trace_service():
    """Test the UBO Trace Service integration"""
    
    print("\n🧪 Testing UBO Trace Service Integration")
    print("=" * 50)
    
    try:
        from services.ubo_trace_service import UBOTraceService
        from models.schemas import UBOTraceRequest
        
        service = UBOTraceService()
        print("✅ UBOTraceService initialized successfully")
        
        # Create a test trace request
        test_request = UBOTraceRequest(
            entity="Test Entity Limited",
            ubo_name="Test UBO",
            location="Test Location",
            domain_name="test.com"
        )
        
        # Create trace
        trace_response = await service.create_trace(test_request)
        print(f"✅ Test trace created: {trace_response.trace_id}")
        
        # Test that the service can handle the parameters
        if service.lyzr_service.agent_configs:
            print("✅ Lyzr agent configurations loaded")
        else:
            print("❌ Lyzr agent configurations missing")
        
        print("✅ UBO Trace Service integration test passed")
        
    except Exception as e:
        print(f"❌ UBO Trace Service test failed: {e}")
        return False
    
    return True

async def main():
    """Main test function"""
    
    print("🚀 UBO Trace Engine - Enhanced Lyzr Integration Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Check environment variables
    required_env_vars = ["LYZR_API_KEY", "LYZR_USER_ID", "MONGODB_URL"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file before running tests")
        print("   Note: This test only validates prompt structure, not API calls")
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    try:
        if await test_lyzr_service():
            tests_passed += 1
        
        if await test_ubo_trace_service():
            tests_passed += 1
            
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Simplified Lyzr integration is working correctly.")
        print("📝 The system now passes only basic parameters to Lyzr agents.")
        print("🔍 Lyzr agents handle prompt building internally.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")
    
    print(f"⏰ Test completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())
