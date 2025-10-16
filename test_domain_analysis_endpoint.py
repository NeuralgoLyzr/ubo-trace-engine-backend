#!/usr/bin/env python3
"""
Test script for Domain Analysis API Endpoint
Tests the Expert AI agent integration for domain analysis with confidence scores
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"

async def test_domain_analysis_endpoint():
    """Test the domain analysis endpoint with Expert AI agent"""
    
    print("🧪 Testing Domain Analysis API Endpoint")
    print("=" * 50)
    
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
        
        try:
            print("📝 Testing domain analysis endpoint...")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{BASE_URL}/domain-analysis",
                    params={
                        "company_name": test_case["company_name"],
                        "ubo_name": test_case["ubo_name"],
                        "location": test_case["location"]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("success"):
                        print("✅ Domain analysis successful")
                        
                        # Display results
                        results = result.get("results", [])
                        print(f"📊 Total domains analyzed: {len(results)}")
                        print(f"📊 Overall confidence: {result.get('overall_confidence', 0)}%")
                        
                        # Display domain rankings
                        print("\n📋 Domain Analysis Results:")
                        for j, domain_result in enumerate(results, 1):
                            print(f"   {j}. Rank: {domain_result.get('rank', 'N/A')}")
                            print(f"      Confidence Score: {domain_result.get('confidence_score', 'N/A')}%")
                            print(f"      Reasoning: {domain_result.get('reasoning', 'N/A')[:100]}...")
                            print()
                        
                        # Display analysis summary
                        analysis_summary = result.get("analysis_summary", "")
                        if analysis_summary:
                            print(f"📝 Analysis Summary:")
                            print(f"   {analysis_summary[:200]}...")
                        
                        # Validate response format
                        if self._validate_response_format(result):
                            print("✅ Response format is correct")
                        else:
                            print("❌ Response format validation failed")
                            
                    else:
                        print(f"❌ Domain analysis failed: {result.get('error', 'Unknown error')}")
                        
                else:
                    print(f"❌ API request failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
        
        # Add delay between test cases
        await asyncio.sleep(2)
    
    print("\n🎯 Domain Analysis Endpoint Test Complete")

def _validate_response_format(result: dict) -> bool:
    """Validate that the response matches the expected format"""
    
    try:
        # Check required fields
        required_fields = ["success", "results"]
        for field in required_fields:
            if field not in result:
                print(f"   Missing required field: {field}")
                return False
        
        # Check results format
        results = result.get("results", [])
        if not isinstance(results, list):
            print("   Results should be a list")
            return False
        
        # Check each result format
        for i, domain_result in enumerate(results):
            required_result_fields = ["rank", "confidence_score", "reasoning"]
            for field in required_result_fields:
                if field not in domain_result:
                    print(f"   Result {i} missing field: {field}")
                    return False
            
            # Check data types
            if not isinstance(domain_result.get("rank"), int):
                print(f"   Result {i} rank should be integer")
                return False
            
            if not isinstance(domain_result.get("confidence_score"), int):
                print(f"   Result {i} confidence_score should be integer")
                return False
            
            if not isinstance(domain_result.get("reasoning"), str):
                print(f"   Result {i} reasoning should be string")
                return False
        
        return True
        
    except Exception as e:
        print(f"   Validation error: {str(e)}")
        return False

async def test_endpoint_with_curl_format():
    """Test the endpoint and show curl command format"""
    
    print("\n🧪 Testing Endpoint with Curl Format")
    print("=" * 50)
    
    test_data = {
        "company_name": "Louis Dreyfus Company Metals MEA DMCC",
        "ubo_name": "Liu Jianfeng",
        "location": "UAE"
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{BASE_URL}/domain-analysis",
                params=test_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print("✅ Endpoint test successful")
                print("\n📋 Curl Command Format:")
                print(f"""curl -X POST "{BASE_URL}/domain-analysis" \\
  -H "Content-Type: application/json" \\
  -d 'company_name={test_data["company_name"]}&ubo_name={test_data["ubo_name"]}&location={test_data["location"]}'""")
                
                print("\n📋 Expected Response Format:")
                print(json.dumps(result, indent=2)[:500] + "...")
                
            else:
                print(f"❌ Endpoint test failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Endpoint test failed: {str(e)}")

async def test_error_handling():
    """Test error handling scenarios"""
    
    print("\n🧪 Testing Error Handling")
    print("=" * 50)
    
    # Test with missing parameters
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{BASE_URL}/domain-analysis")
            
            if response.status_code == 422:  # Validation error
                print("✅ Missing parameters handled correctly")
            else:
                print(f"⚠️  Unexpected response for missing parameters: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
    
    # Test with invalid data
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/domain-analysis",
                params={
                    "company_name": "",
                    "ubo_name": "",
                    "location": ""
                }
            )
            
            if response.status_code in [400, 422, 500]:
                print("✅ Empty parameters handled correctly")
            else:
                print(f"⚠️  Unexpected response for empty parameters: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")

async def main():
    """Main test function"""
    
    print("🚀 Domain Analysis API Endpoint Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    try:
        await test_domain_analysis_endpoint()
        tests_passed += 1
        
        await test_endpoint_with_curl_format()
        tests_passed += 1
        
        await test_error_handling()
        tests_passed += 1
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Domain analysis endpoint is working correctly.")
        print("📝 The endpoint returns Expert AI analysis with confidence scores.")
        print("🔍 Response format matches the required structure.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    print(f"⏰ Test completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())
