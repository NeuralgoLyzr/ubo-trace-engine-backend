#!/usr/bin/env python3
"""
Test script to verify Apollo.io integration with UBO Trace Engine
Tests data enrichment capabilities and API response structure
"""

import asyncio
import httpx
import json
from typing import Dict, Any, List

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_ENTITY = "Avcon Jet Isle of Man Limited"
TEST_UBO = "Alexander Vagacs"
TEST_LOCATION = "Suite 17 North Quay Douglas IM1 4LE, Isle of Man"
TEST_DOMAIN = "avconjet.com"

async def test_apollo_integration():
    """Test Apollo.io integration with UBO trace engine"""
    
    print("🚀 Testing Apollo.io Integration with UBO Trace Engine")
    print("=" * 60)
    
    # Test 1: Direct Apollo API Test
    print("1. Testing Apollo API directly...")
    await test_apollo_api_direct()
    
    # Test 2: Create and execute trace with Apollo enrichment
    print("\n2. Testing UBO trace with Apollo enrichment...")
    await test_ubo_trace_with_apollo()
    
    # Test 3: Verify Apollo data in response
    print("\n3. Verifying Apollo data in API response...")
    await test_apollo_response_structure()

async def test_apollo_api_direct():
    """Test Apollo API directly"""
    
    try:
        # Test Apollo API key
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": "RMTKfIT6vY_y1YBW38x6Kw"
        }
        
        # Test people search
        search_data = {
            "q": TEST_UBO,
            "page": 1,
            "per_page": 5
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.apollo.io/v1/people/search",
                headers=headers,
                json=search_data
            )
            
            if response.status_code == 200:
                result = response.json()
                people = result.get("people", [])
                print(f"   ✅ Apollo people search successful: {len(people)} results")
                
                if people:
                    first_person = people[0]
                    print(f"   📋 First result: {first_person.get('name', 'N/A')}")
                    print(f"   🏢 Company: {first_person.get('organization', {}).get('name', 'N/A')}")
                    print(f"   📧 Email: {first_person.get('email', 'N/A')}")
            else:
                print(f"   ❌ Apollo API test failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"   ❌ Apollo API test failed: {str(e)}")

async def test_ubo_trace_with_apollo():
    """Test UBO trace execution with Apollo enrichment"""
    
    # Create a new trace
    print("   Creating new trace...")
    async with httpx.AsyncClient() as client:
        create_response = await client.post(
            f"{BASE_URL}/trace",
            json={
                "entity": TEST_ENTITY,
                "ubo_name": TEST_UBO,
                "location": TEST_LOCATION,
                "domain_name": TEST_DOMAIN
            }
        )
        
        if create_response.status_code != 200:
            print(f"   ❌ Failed to create trace: {create_response.text}")
            return None
            
        trace_data = create_response.json()
        trace_id = trace_data["trace_id"]
        print(f"   ✅ Created trace: {trace_id}")
    
    # Execute trace
    print("   Executing trace with Apollo enrichment...")
    async with httpx.AsyncClient(timeout=300.0) as client:
        execute_response = await client.post(f"{BASE_URL}/trace/{trace_id}/execute")
        
        if execute_response.status_code != 200:
            print(f"   ❌ Failed to execute trace: {execute_response.text}")
            return None
            
        summary = execute_response.json()
        print(f"   ✅ Trace execution completed")
        
        return summary

async def test_apollo_response_structure():
    """Test Apollo data structure in API response"""
    
    # Get a completed trace
    summary = await test_ubo_trace_with_apollo()
    if not summary:
        print("   ❌ No trace data available for testing")
        return
    
    print("   Analyzing Apollo data in response...")
    
    # Check stage results
    stage_results = summary.get("stage_results", [])
    if not stage_results:
        print("   ❌ No stage results found")
        return
    
    apollo_enrichment_found = 0
    apollo_insights_found = 0
    
    for i, stage_result in enumerate(stage_results):
        stage_name = stage_result.get("stage", f"stage_{i+1}")
        print(f"\n   Stage {stage_name}:")
        
        # Check Apollo enrichment data
        apollo_enrichment = stage_result.get("apollo_enrichment")
        if apollo_enrichment:
            apollo_enrichment_found += 1
            print(f"     ✅ Apollo enrichment data present")
            
            # Check enrichment summary
            enrichment_summary = apollo_enrichment.get("enrichment_summary", {})
            print(f"     📊 Entity found: {enrichment_summary.get('entity_found', False)}")
            print(f"     👤 UBO found: {enrichment_summary.get('ubo_found', False)}")
            print(f"     🌐 Domain verified: {enrichment_summary.get('domain_verified', False)}")
            print(f"     📈 Total matches: {enrichment_summary.get('total_matches', 0)}")
        else:
            print(f"     ⚠️  No Apollo enrichment data")
        
        # Check Apollo insights
        apollo_insights = stage_result.get("apollo_insights")
        if apollo_insights:
            apollo_insights_found += 1
            print(f"     ✅ Apollo insights present")
            
            # Check confidence scores
            overall_confidence = apollo_insights.get("overall_confidence", 0)
            print(f"     🎯 Overall confidence: {overall_confidence}%")
            
            # Check verification status
            entity_verification = apollo_insights.get("entity_verification", {})
            ubo_verification = apollo_insights.get("ubo_verification", {})
            domain_verification = apollo_insights.get("domain_verification", {})
            
            print(f"     🏢 Entity verified: {entity_verification.get('verified', False)}")
            print(f"     👤 UBO verified: {ubo_verification.get('verified', False)}")
            print(f"     🌐 Domain verified: {domain_verification.get('verified', False)}")
        else:
            print(f"     ⚠️  No Apollo insights data")
    
    # Summary
    print(f"\n   📊 Apollo Integration Summary:")
    print(f"     Stages with enrichment: {apollo_enrichment_found}/{len(stage_results)}")
    print(f"     Stages with insights: {apollo_insights_found}/{len(stage_results)}")
    
    if apollo_enrichment_found > 0 and apollo_insights_found > 0:
        print("   ✅ Apollo integration is working correctly!")
    else:
        print("   ⚠️  Apollo integration may have issues")

async def test_apollo_data_quality():
    """Test the quality and usefulness of Apollo data"""
    
    print("\n4. Testing Apollo data quality...")
    
    summary = await test_ubo_trace_with_apollo()
    if not summary:
        return
    
    stage_results = summary.get("stage_results", [])
    
    for stage_result in stage_results:
        apollo_enrichment = stage_result.get("apollo_enrichment", {})
        apollo_insights = stage_result.get("apollo_insights", {})
        
        if apollo_enrichment and apollo_insights:
            print(f"\n   Stage {stage_result.get('stage', 'unknown')}:")
            
            # Check entity search results
            entity_search = apollo_enrichment.get("entity_search", {})
            if entity_search.get("success"):
                organizations = entity_search.get("organizations", [])
                print(f"     🏢 Found {len(organizations)} organizations")
                
                if organizations:
                    org = organizations[0]
                    print(f"     📋 Organization: {org.get('name', 'N/A')}")
                    print(f"     🌐 Website: {org.get('website_url', 'N/A')}")
                    print(f"     📍 Industry: {org.get('industry', 'N/A')}")
            
            # Check UBO search results
            ubo_search = apollo_enrichment.get("ubo_search", {})
            if ubo_search.get("success"):
                people = ubo_search.get("people", [])
                print(f"     👤 Found {len(people)} people")
                
                if people:
                    person = people[0]
                    print(f"     📋 Person: {person.get('name', 'N/A')}")
                    print(f"     📧 Email: {person.get('email', 'N/A')}")
                    print(f"     💼 Title: {person.get('title', 'N/A')}")

async def main():
    """Main test function"""
    try:
        await test_apollo_integration()
        print("\n🎉 Apollo.io integration testing completed!")
        print("✅ Check the results above to verify integration status")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
