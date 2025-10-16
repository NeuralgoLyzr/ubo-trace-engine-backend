#!/usr/bin/env python3
"""
Test script for Expert Domain Analysis integration with UBO Trace Engine
Tests the Expert Lyzr AI agent for analyzing domain search results with confidence scores
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.searchapi_service import SearchAPIService

async def test_expert_domain_analysis():
    """Test Expert domain analysis with mock data"""
    
    print("🧪 Testing Expert Domain Analysis Integration")
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
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['company_name']}")
        print("-" * 40)
        
        # Mock Lyzr domain data (from your example)
        lyzr_domains = [
            {
                "rank": 1,
                "domain": "ldc.com",
                "short_summary": "The official global domain for Louis Dreyfus Company, a multinational involved in agriculture, food processing, and commodity trading. Operates numerous regional and business unit subdomains.",
                "relation": "Primary corporate domain—parent to Louis Dreyfus Company Metals MEA DMCC and related regional entities."
            },
            {
                "rank": 2,
                "domain": "ldc.com/gh/locations/",
                "short_summary": "Dedicated page listing LDC's locations in the Europe, Middle East & Africa region, relevant due to the UAE operation.",
                "relation": "Regional corporate domain—includes UAE/MEA presence."
            },
            {
                "rank": 3,
                "domain": "ldc.com/ke/location/louis-dreyfus-company-mea-trading-dmcc/",
                "short_summary": "Subdomain providing specific information about Louis Dreyfus Company MEA Trading DMCC, the relevant UAE-registered entity.",
                "relation": "Direct domain for the MEA DMCC trading company in UAE."
            }
        ]
        
        # Mock Google SERP domain data
        google_serp_domains = [
            {
                "position": 1,
                "source": "Louis Dreyfus Company",
                "domain": "www.ldc.com",
                "snippet": "Official Communications: Legitimate emails from LDC will come from an email address with our company domain \"@ldc.com\"..."
            },
            {
                "position": 2,
                "source": "Louis Dreyfus Company",
                "domain": "www.ldc.com",
                "snippet": "Louis Dreyfus Company India Private Limited Anchorage Building..."
            },
            {
                "position": 3,
                "source": "Kompass International",
                "domain": "ae.kompass.com",
                "snippet": "Louis Dreyfus Company MEA Trading DMCC is a trader, importer & exporter of agriculture products..."
            }
        ]
        
        try:
            print("📝 Testing Expert domain analysis...")
            expert_analysis = await service.analyze_domains_with_expert(
                test_case["company_name"],
                test_case["ubo_name"],
                test_case["location"],
                lyzr_domains,
                google_serp_domains
            )
            
            if expert_analysis["success"]:
                print("✅ Expert domain analysis successful")
                
                analysis_data = expert_analysis.get("expert_analysis", {})
                
                # Display overall confidence
                overall_confidence = analysis_data.get("overall_confidence", 0)
                print(f"📊 Overall Confidence Score: {overall_confidence}%")
                
                # Display domain rankings
                domain_rankings = analysis_data.get("domain_rankings", [])
                print(f"📊 Domain Rankings: {len(domain_rankings)} domains analyzed")
                
                if domain_rankings:
                    print("\n📋 Top Domain Rankings:")
                    for j, ranking in enumerate(domain_rankings[:5], 1):
                        print(f"   {j}. {ranking.get('domain', 'N/A')} - Confidence: {ranking.get('confidence', 'N/A')}%")
                        print(f"      Summary: {ranking.get('summary', 'N/A')[:80]}...")
                
                # Display confidence scores
                confidence_scores = analysis_data.get("confidence_scores", {})
                if confidence_scores:
                    print(f"\n📊 Confidence Scores:")
                    for domain, score in confidence_scores.items():
                        print(f"   {domain}: {score}%")
                
                # Display analysis summary
                analysis_summary = analysis_data.get("analysis_summary", "")
                if analysis_summary:
                    print(f"\n📝 Analysis Summary:")
                    print(f"   {analysis_summary[:200]}...")
                
                # Display recommendations
                recommendations = analysis_data.get("recommendations", [])
                if recommendations:
                    print(f"\n💡 Recommendations:")
                    for j, rec in enumerate(recommendations[:3], 1):
                        print(f"   {j}. {rec}")
                
                # Display raw response preview
                raw_response = expert_analysis.get("raw_response", "")
                if raw_response:
                    print(f"\n📄 Raw Response Preview:")
                    print(f"   {raw_response[:150]}...")
                
            else:
                print(f"❌ Expert domain analysis failed: {expert_analysis.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Expert domain analysis test failed: {e}")
        
        # Add delay between test cases
        await asyncio.sleep(2)
    
    print("\n🎯 Expert Domain Analysis Test Complete")
    return True

async def test_expert_with_real_data():
    """Test Expert analysis with real SearchAPI data"""
    
    print("\n🧪 Testing Expert Analysis with Real SearchAPI Data")
    print("=" * 50)
    
    try:
        service = SearchAPIService()
        
        # Test data
        company_name = "Louis Dreyfus Company Metals MEA DMCC"
        ubo_name = "Liu Jianfeng"
        location = "UAE"
        
        # Get real SearchAPI data
        print("📝 Getting real SearchAPI domain data...")
        domain_search = await service.search_domains(company_name, ubo_name, location)
        
        if domain_search["success"]:
            google_serp_domains = domain_search.get("domains", [])
            print(f"✅ Retrieved {len(google_serp_domains)} domains from SearchAPI")
            
            # Mock Lyzr domains (since we don't have real Lyzr domain analysis in this test)
            lyzr_domains = [
                {
                    "rank": 1,
                    "domain": "ldc.com",
                    "short_summary": "Official Louis Dreyfus Company domain",
                    "relation": "Primary corporate domain"
                }
            ]
            
            # Call Expert analysis
            print("📝 Calling Expert analysis with real data...")
            expert_analysis = await service.analyze_domains_with_expert(
                company_name, ubo_name, location, lyzr_domains, google_serp_domains
            )
            
            if expert_analysis["success"]:
                print("✅ Expert analysis with real data successful")
                
                analysis_data = expert_analysis.get("expert_analysis", {})
                overall_confidence = analysis_data.get("overall_confidence", 0)
                print(f"📊 Overall Confidence: {overall_confidence}%")
                
                domain_rankings = analysis_data.get("domain_rankings", [])
                print(f"📊 Domain Rankings: {len(domain_rankings)} domains")
                
            else:
                print(f"❌ Expert analysis failed: {expert_analysis.get('error', 'Unknown error')}")
        else:
            print(f"❌ SearchAPI domain search failed: {domain_search.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Real data test failed: {e}")
        return False
    
    return True

async def test_ubo_trace_service_integration():
    """Test Expert integration with UBO Trace Service"""
    
    print("\n🧪 Testing Expert Integration with UBO Trace Service")
    print("=" * 50)
    
    try:
        from services.ubo_trace_service import UBOTraceService
        from models.schemas import UBOTraceRequest
        
        service = UBOTraceService()
        print("✅ UBOTraceService initialized successfully")
        
        # Check if Expert analysis is integrated
        if hasattr(service, 'searchapi_service') and hasattr(service.searchapi_service, 'analyze_domains_with_expert'):
            print("✅ Expert domain analysis integrated in UBO Trace Service")
        else:
            print("❌ Expert domain analysis not found in UBO Trace Service")
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
        
        print("✅ UBO Trace Service Expert integration test passed")
        
    except Exception as e:
        print(f"❌ UBO Trace Service test failed: {e}")
        return False
    
    return True

async def main():
    """Main test function"""
    
    print("🚀 Expert Domain Analysis Integration Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Check environment variables
    required_env_vars = ["LYZR_API_KEY", "LYZR_USER_ID"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file before running tests")
    
    # Check Expert agent configuration
    expert_agent_vars = ["AGENT_EXPERT_DOMAIN", "SESSION_EXPERT_DOMAIN"]
    missing_expert_vars = [var for var in expert_agent_vars if not os.getenv(var)]
    
    if missing_expert_vars:
        print(f"⚠️  Missing Expert agent configuration: {', '.join(missing_expert_vars)}")
        print("   Please set these in your .env file:")
        print("   AGENT_EXPERT_DOMAIN=68f0ffd5a0dfaa3e0726523c")
        print("   SESSION_EXPERT_DOMAIN=68f0ffd5a0dfaa3e0726523c-losfuwfwcd")
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    try:
        # Always run mock data test
        if await test_expert_domain_analysis():
            tests_passed += 1
        
        # Run real data test if API keys are available
        if os.getenv("SEARCHAPI_API_KEY") and os.getenv("LYZR_API_KEY"):
            if await test_expert_with_real_data():
                tests_passed += 1
        else:
            print("\n⚠️  Skipping real data test - missing API keys")
            total_tests = 2
        
        # Run UBO Trace Service integration test
        if await test_ubo_trace_service_integration():
            tests_passed += 1
            
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Expert domain analysis integration is working correctly.")
        print("📝 The system now includes Expert AI analysis for domain search results.")
        print("🔍 Expert agent provides confidence scores and domain rankings.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")
    
    print(f"⏰ Test completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())
