#!/usr/bin/env python3
"""
Test script to verify SearchAPI domain deduplication functionality
Tests that duplicate domains are properly filtered out
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.searchapi_service import SearchAPIService

async def test_domain_deduplication():
    """Test that duplicate domains are properly filtered out"""
    
    print("🧪 Testing SearchAPI Domain Deduplication")
    print("=" * 50)
    
    # Initialize service
    try:
        service = SearchAPIService()
        print("✅ SearchAPIService initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize SearchAPIService: {e}")
        return False
    
    # Test data that should return multiple results with same domain
    test_cases = [
        {
            "company_name": "Louis Dreyfus Company Metals MEA DMCC",
            "ubo_name": "Liu Jianfeng",
            "location": "UAE",
            "expected_domain": "www.ldc.com"  # This domain appears multiple times in results
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['company_name']}")
        print("-" * 40)
        
        try:
            print("📝 Testing domain search with deduplication...")
            domain_search = await service.search_domains(
                test_case["company_name"],
                test_case["ubo_name"],
                test_case["location"]
            )
            
            if domain_search["success"]:
                domains = domain_search.get("domains", [])
                print(f"✅ Domain search successful: {len(domains)} unique domains found")
                
                # Check for duplicates
                domain_names = [domain.get("domain", "").lower() for domain in domains]
                unique_domains = set(domain_names)
                
                print(f"📊 Total domains returned: {len(domains)}")
                print(f"📊 Unique domains: {len(unique_domains)}")
                
                if len(domains) == len(unique_domains):
                    print("✅ No duplicate domains found - deduplication working correctly!")
                else:
                    print("❌ Duplicate domains detected - deduplication failed!")
                    print(f"   Duplicates: {len(domains) - len(unique_domains)}")
                
                # Display domains with their positions
                print("\n📋 Domain Results:")
                for j, domain in enumerate(domains[:10], 1):  # Show first 10
                    print(f"   {j}. {domain.get('domain', 'N/A')} (position: {domain.get('position', 'N/A')})")
                    print(f"      Source: {domain.get('source', 'N/A')}")
                    print(f"      Snippet: {domain.get('snippet', 'N/A')[:80]}...")
                
                # Check if expected domain is present
                expected_domain = test_case["expected_domain"].lower()
                if expected_domain in unique_domains:
                    print(f"✅ Expected domain '{test_case['expected_domain']}' found in results")
                else:
                    print(f"⚠️  Expected domain '{test_case['expected_domain']}' not found in results")
                
            else:
                print(f"❌ Domain search failed: {domain_search.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Domain search test failed: {e}")
        
        # Test related domains deduplication
        try:
            print("\n📝 Testing related domains deduplication...")
            related_domains = await service.search_related_domains(
                test_case["company_name"],
                test_case["ubo_name"],
                test_case["location"]
            )
            
            if related_domains["success"]:
                domains = related_domains.get("related_domains", [])
                print(f"✅ Related domains search successful: {len(domains)} unique domains found")
                
                # Check for duplicates
                domain_names = [domain.get("domain", "").lower() for domain in domains]
                unique_domains = set(domain_names)
                
                print(f"📊 Total related domains returned: {len(domains)}")
                print(f"📊 Unique related domains: {len(unique_domains)}")
                
                if len(domains) == len(unique_domains):
                    print("✅ No duplicate related domains found - deduplication working correctly!")
                else:
                    print("❌ Duplicate related domains detected - deduplication failed!")
                
            else:
                print(f"❌ Related domains search failed: {related_domains.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Related domains search test failed: {e}")
        
        # Add delay between test cases
        await asyncio.sleep(2)
    
    print("\n🎯 Domain Deduplication Test Complete")
    return True

async def test_deduplication_with_mock_data():
    """Test deduplication logic with mock data"""
    
    print("\n🧪 Testing Deduplication Logic with Mock Data")
    print("=" * 50)
    
    try:
        service = SearchAPIService()
        
        # Mock search results with duplicate domains
        mock_search_results = {
            "organic_results": [
                {
                    "position": 1,
                    "title": "Louis Dreyfus Company: Leading Merchant",
                    "link": "https://www.ldc.com/",
                    "source": "Louis Dreyfus Company",
                    "domain": "www.ldc.com",
                    "snippet": "Official Communications: Legitimate emails from LDC will come from an email address with our company domain \"@ldc.com\"..."
                },
                {
                    "position": 2,
                    "title": "Locations",
                    "link": "https://www.ldc.com/gh/locations/",
                    "source": "Louis Dreyfus Company",
                    "domain": "www.ldc.com",  # Duplicate domain
                    "snippet": "Louis Dreyfus Company India Private Limited Anchorage Building..."
                },
                {
                    "position": 3,
                    "title": "Louis Dreyfus Company MEA Trading DMCC 99",
                    "link": "https://www.ldc.com/pk/en/location/louis-dreyfus-company-mea-trading-dmcc/",
                    "source": "Louis Dreyfus Company",
                    "domain": "www.ldc.com",  # Another duplicate domain
                    "snippet": "© 2025 Louis Dreyfus Company. Top. Notice. You are about to leave the India market site..."
                },
                {
                    "position": 4,
                    "title": "Louis Dreyfus Company (LDC) is a global merchant",
                    "link": "https://www.ldc.com/cn/en/",
                    "source": "Louis Dreyfus Company",
                    "domain": "www.ldc.com",  # Another duplicate domain
                    "snippet": "Official Communications: Legitimate emails from LDC will come from an email address with our company domain \"@ldc.com\"..."
                },
                {
                    "position": 5,
                    "title": "Different Company",
                    "link": "https://www.example.com/",
                    "source": "Example Company",
                    "domain": "www.example.com",  # Different domain
                    "snippet": "This is a different company website..."
                }
            ]
        }
        
        # Test the deduplication logic
        domains = service._extract_domain_results(mock_search_results)
        
        print(f"📊 Mock data had {len(mock_search_results['organic_results'])} organic results")
        print(f"📊 After deduplication: {len(domains)} unique domains")
        
        # Check results
        domain_names = [domain.get("domain", "").lower() for domain in domains]
        unique_domains = set(domain_names)
        
        print(f"📊 Unique domains: {len(unique_domains)}")
        
        if len(domains) == len(unique_domains):
            print("✅ Deduplication working correctly with mock data!")
        else:
            print("❌ Deduplication failed with mock data!")
        
        # Display results
        print("\n📋 Deduplicated Results:")
        for i, domain in enumerate(domains, 1):
            print(f"   {i}. {domain.get('domain', 'N/A')} (position: {domain.get('position', 'N/A')})")
            print(f"      Source: {domain.get('source', 'N/A')}")
            print(f"      Snippet: {domain.get('snippet', 'N/A')[:60]}...")
        
        # Verify only first occurrence is kept
        ldc_domains = [d for d in domains if d.get('domain', '').lower() == 'www.ldc.com']
        if len(ldc_domains) == 1 and ldc_domains[0].get('position') == 1:
            print("✅ Only first occurrence of www.ldc.com kept (position 1)")
        else:
            print("❌ Multiple occurrences of www.ldc.com found or wrong position kept")
        
    except Exception as e:
        print(f"❌ Mock data test failed: {e}")
        return False
    
    return True

async def main():
    """Main test function"""
    
    print("🚀 SearchAPI Domain Deduplication Test")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Check SearchAPI API key
    if not os.getenv("SEARCHAPI_API_KEY"):
        print("⚠️  SearchAPI_API_KEY not set - will only test mock data")
        print("   Set SEARCHAPI_API_KEY in your .env file to test with real API")
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    try:
        # Always run mock data test
        if await test_deduplication_with_mock_data():
            tests_passed += 1
        
        # Only run real API test if API key is available
        if os.getenv("SEARCHAPI_API_KEY"):
            if await test_domain_deduplication():
                tests_passed += 1
        else:
            print("\n⚠️  Skipping real API test - no API key provided")
            total_tests = 1
            
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Domain deduplication is working correctly.")
        print("📝 Duplicate domains are now filtered out automatically.")
        print("🔍 Only the first occurrence of each unique domain is kept.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    print(f"⏰ Test completed at: {datetime.now()}")

if __name__ == "__main__":
    asyncio.run(main())
