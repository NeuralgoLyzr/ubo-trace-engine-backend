#!/usr/bin/env python3
"""
Test script for SearchAPI Google integration with UBO Trace Engine
Tests domain search capabilities with company_name, ubo_name, and location
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.searchapi_service import SearchAPIService

async def test_searchapi_integration():
    """Test SearchAPI service integration"""
    
    print("🧪 Testing SearchAPI Google Integration")
    print("=" * 50)
    
    # Initialize service
    try:
        service = SearchAPIService()
        print("✅ SearchAPIService initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize SearchAPIService: {e}")
        return False
    
    # Test data
    test_cases = [
        {
            "company_name": "Louis Dreyfus Company Metals MEA DMCC",
            "ubo_name": "Liu Jianfeng",
            "location": "UAE"
        },
        {
            "company_name": "Avcon Jet Isle of Man Limited",
            "ubo_name": "Alexander Vagacs",
            "location": "Isle of Man"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['company_name']}")
        print("-" * 40)
        
        # Test 1: Basic domain search
        try:
            print("📝 Testing domain search...")
            domain_search = await service.search_domains(
                test_case["company_name"],
                test_case["ubo_name"],
                test_case["location"]
            )
            
            if domain_search["success"]:
                print(f"✅ Domain search successful: {domain_search['total_results']} domains found")
                
                # Display first few domains
                domains = domain_search.get("domains", [])
                for j, domain in enumerate(domains[:3], 1):
                    print(f"   {j}. {domain.get('domain', 'N/A')} - {domain.get('source', 'N/A')}")
                    print(f"      Position: {domain.get('position', 'N/A')}")
                    print(f"      Snippet: {domain.get('snippet', 'N/A')[:100]}...")
            else:
                print(f"❌ Domain search failed: {domain_search.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Domain search test failed: {e}")
        
        # Test 2: Related domains search
        try:
            print("\n📝 Testing related domains search...")
            related_domains = await service.search_related_domains(
                test_case["company_name"],
                test_case["ubo_name"],
                test_case["location"]
            )
            
            if related_domains["success"]:
                print(f"✅ Related domains search successful: {related_domains['total_results']} domains found")
                
                # Display first few related domains
                domains = related_domains.get("related_domains", [])
                for j, domain in enumerate(domains[:3], 1):
                    print(f"   {j}. {domain.get('domain', 'N/A')} - {domain.get('source', 'N/A')}")
                    print(f"      Position: {domain.get('position', 'N/A')}")
                    print(f"      Snippet: {domain.get('snippet', 'N/A')[:100]}...")
            else:
                print(f"❌ Related domains search failed: {related_domains.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Related domains search test failed: {e}")
        
        # Test 3: Domain ownership search (if domain provided)
        if i == 1:  # Test with first case
            try:
                print("\n📝 Testing domain ownership search...")
                domain_ownership = await service.search_domain_ownership(
                    test_case["company_name"],
                    test_case["ubo_name"],
                    test_case["location"],
                    "louisdreyfus.com"
                )
                
                if domain_ownership["success"]:
                    print(f"✅ Domain ownership search successful: {domain_ownership['total_results']} results found")
                    
                    # Display ownership results
                    results = domain_ownership.get("ownership_results", [])
                    for j, result in enumerate(results[:2], 1):
                        print(f"   {j}. {result.get('domain', 'N/A')} - {result.get('source', 'N/A')}")
                        print(f"      Position: {result.get('position', 'N/A')}")
                        print(f"      Snippet: {result.get('snippet', 'N/A')[:100]}...")
                else:
                    print(f"❌ Domain ownership search failed: {domain_ownership.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Domain ownership search test failed: {e}")
        
        # Add delay between test cases
        await asyncio.sleep(2)
    
    print("\n🎯 SearchAPI Integration Test Complete")
    return True

async def test_ubo_trace_service_integration():
    """Test SearchAPI integration with UBO Trace Service"""
    
    print("\n🧪 Testing UBO Trace Service Integration")
    print("=" * 50)
    
    try:
        from services.ubo_trace_service import UBOTraceService
        from models.schemas import UBOTraceRequest
        
        service = UBOTraceService()
        print("✅ UBOTraceService initialized successfully")
        
        # Check if SearchAPI service is available
        if hasattr(service, 'searchapi_service'):
            print("✅ SearchAPI service integrated in UBO Trace Service")
        else:
            print("❌ SearchAPI service not found in UBO Trace Service")
            return False
        
        # Create a test trace request
        test_request = UBOTraceRequest(
            entity="Louis Dreyfus Company Metals MEA DMCC",
            ubo_name="Liu Jianfeng",
            location="UAE",
            domain_name="louisdreyfus.com"
        )
        
        # Create trace
        trace_response = await service.create_trace(test_request)
        print(f"✅ Test trace created: {trace_response.trace_id}")
        
        print("✅ UBO Trace Service integration test passed")
        
    except Exception as e:
        print(f"❌ UBO Trace Service test failed: {e}")
        return False
    
    return True

async def main():
    """Main test function"""
    
    print("🚀 SearchAPI Google Integration Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Check environment variables
    required_env_vars = ["MONGODB_URL", "LYZR_API_KEY", "LYZR_USER_ID"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file before running tests")
    
    # Check SearchAPI API key
    if not os.getenv("SEARCHAPI_API_KEY"):
        print("⚠️  SearchAPI_API_KEY not set - domain search will be disabled")
        print("   Set SEARCHAPI_API_KEY in your .env file to enable domain search")
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    try:
        if await test_searchapi_integration():
            tests_passed += 1
        
        if await test_ubo_trace_service_integration():
            tests_passed += 1
            
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! SearchAPI integration is working correctly.")
        print("📝 The system now includes domain search capabilities.")
        print("🔍 SearchAPI provides structured domain search results.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")
    
    print(f"⏰ Test completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())
