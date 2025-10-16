#!/usr/bin/env python3
"""
Test script for Company Domain Analysis integration
"""

import asyncio
import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.lyzr_service import LyzrAgentService
from models.schemas import CompanyDomainAnalysisRequest

async def test_company_domain_analysis():
    """Test the company domain analysis functionality"""
    
    print("🧪 Testing Company Domain Analysis Integration")
    print("=" * 50)
    
    try:
        # Initialize the service
        lyzr_service = LyzrAgentService()
        print("✅ LyzrAgentService initialized successfully")
        
        # Test data from the example
        test_data = {
            "company_name": "Block Industrial Crewe Limited",
            "ubo_name": "Alan Samuel Waxman",
            "address": "3rd Floor 37 Esplanade St Helier JE1 1AD, Jersey"
        }
        
        print(f"\n📊 Testing with sample data:")
        print(f"   Company: {test_data['company_name']}")
        print(f"   UBO: {test_data['ubo_name']}")
        print(f"   Address: {test_data['address']}")
        
        # Call the analysis method
        print(f"\n🚀 Calling Lyzr AI agent...")
        result = await lyzr_service.analyze_company_domains(
            company_name=test_data["company_name"],
            ubo_name=test_data["ubo_name"],
            address=test_data["address"]
        )
        
        # Display results
        print(f"\n📈 Analysis Results:")
        print(f"   Success: {result.success}")
        print(f"   Processing Time: {result.processing_time_ms}ms")
        print(f"   Companies Found: {len(result.companies)}")
        
        if result.success and result.companies:
            print(f"\n🏢 Company Domains:")
            for i, company in enumerate(result.companies, 1):
                print(f"   {i}. {company.domain}")
                print(f"      Rank: {company.rank}")
                print(f"      Summary: {company.short_summary}")
                print(f"      Relation: {company.relation}")
                print()
        elif result.error:
            print(f"   ❌ Error: {result.error}")
        else:
            print(f"   ⚠️  No companies found")
        
        # Test the request model
        print(f"\n🔧 Testing Request Model:")
        request = CompanyDomainAnalysisRequest(**test_data)
        print(f"   Request created: {request.company_name}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoint():
    """Test the API endpoint directly"""
    
    print(f"\n🌐 Testing API Endpoint")
    print("=" * 30)
    
    try:
        import httpx
        
        # Test data
        test_data = {
            "company_name": "Block Industrial Crewe Limited",
            "ubo_name": "Alan Samuel Waxman", 
            "address": "3rd Floor 37 Esplanade St Helier JE1 1AD, Jersey"
        }
        
        # Assuming the server is running on localhost:8000
        base_url = "http://localhost:8000"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"📡 Sending POST request to {base_url}/analyze-company-domains")
            
            response = await client.post(
                f"{base_url}/analyze-company-domains",
                json=test_data
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success: {result.get('success', False)}")
                print(f"   ⏱️  Processing Time: {result.get('processing_time_ms', 0)}ms")
                print(f"   🏢 Companies Found: {len(result.get('companies', []))}")
                
                if result.get('companies'):
                    print(f"\n   📋 Company Domains:")
                    for company in result.get('companies', [])[:3]:  # Show first 3
                        print(f"      • {company.get('domain', 'N/A')} (Rank: {company.get('rank', 0)})")
                
                return True
            else:
                print(f"   ❌ Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    
    print("🚀 Starting Company Domain Analysis Tests")
    print("=" * 60)
    
    # Test 1: Direct service call
    service_success = await test_company_domain_analysis()
    
    # Test 2: API endpoint (optional - only if server is running)
    api_success = await test_api_endpoint()
    
    # Summary
    print(f"\n📊 Test Summary:")
    print(f"   Service Test: {'✅ PASSED' if service_success else '❌ FAILED'}")
    print(f"   API Test: {'✅ PASSED' if api_success else '❌ FAILED'}")
    
    if service_success:
        print(f"\n🎉 Integration is working correctly!")
        print(f"   You can now use the /analyze-company-domains endpoint")
        print(f"   Expected request format:")
        print(f"   {{")
        print(f"     \"company_name\": \"Company Name\",")
        print(f"     \"ubo_name\": \"UBO Name\",")
        print(f"     \"address\": \"Company Address\"")
        print(f"   }}")
    else:
        print(f"\n⚠️  Integration needs attention. Check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())
