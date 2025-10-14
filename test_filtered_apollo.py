#!/usr/bin/env python3
"""
Test script to verify filtered Apollo.ai responses
Shows only relevant information aligned with UBO trace project
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

async def test_filtered_apollo_responses():
    """Test filtered Apollo.ai responses"""
    
    print("🎯 Testing Filtered Apollo.ai Responses")
    print("=" * 60)
    
    # Create and execute a trace
    print("1. Creating and executing trace...")
    
    # Create trace
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
            print(f"❌ Failed to create trace: {create_response.text}")
            return
            
        trace_data = create_response.json()
        trace_id = trace_data["trace_id"]
        print(f"✅ Created trace: {trace_id}")
    
    # Execute trace
    async with httpx.AsyncClient(timeout=300.0) as client:
        execute_response = await client.post(f"{BASE_URL}/trace/{trace_id}/execute")
        
        if execute_response.status_code != 200:
            print(f"❌ Failed to execute trace: {execute_response.text}")
            return
            
        summary = execute_response.json()
        print(f"✅ Trace execution completed")
    
    # Analyze filtered Apollo data
    stage_results = summary.get("stage_results", [])
    
    for i, stage_result in enumerate(stage_results):
        stage_name = stage_result.get("stage", f"stage_{i+1}")
        print(f"\n{'='*60}")
        print(f"📊 STAGE: {stage_name.upper()}")
        print(f"{'='*60}")
        
        # Apollo Enrichment Data
        apollo_enrichment = stage_result.get("apollo_enrichment", {})
        if apollo_enrichment:
            print(f"\n🔍 FILTERED APOLLO ENRICHMENT DATA:")
            print(f"{'─'*50}")
            
            # Entity Search Results
            entity_search = apollo_enrichment.get("entity_search", {})
            if entity_search:
                print(f"\n📋 ENTITY SEARCH RESULTS:")
                print(f"   Success: {entity_search.get('success', False)}")
                print(f"   Relevant Results: {entity_search.get('total_results', 0)}")
                
                organizations = entity_search.get("organizations", [])
                if organizations:
                    print(f"   Relevant Organizations Found: {len(organizations)}")
                    
                    for j, org in enumerate(organizations):
                        print(f"\n   🏢 Relevant Organization {j+1}:")
                        print(f"      Name: {org.get('name', 'N/A')}")
                        print(f"      Website: {org.get('website', 'N/A')}")
                        print(f"      Industry: {org.get('industry', 'N/A')}")
                        print(f"      Employee Count: {org.get('employee_count', 'N/A')}")
                        print(f"      Founded Year: {org.get('founded_year', 'N/A')}")
                        
                        location = org.get('location', {})
                        if location:
                            print(f"      Location: {location.get('city', 'N/A')}, {location.get('state', 'N/A')}, {location.get('country', 'N/A')}")
                        
                        contact = org.get('contact', {})
                        if contact:
                            print(f"      Phone: {contact.get('phone', 'N/A')}")
                            print(f"      LinkedIn: {contact.get('linkedin', 'N/A')}")
                        
                        description = org.get('description')
                        if description:
                            print(f"      Description: {description[:100]}...")
                else:
                    print(f"   ⚠️  No relevant organizations found")
            
            # UBO Search Results
            ubo_search = apollo_enrichment.get("ubo_search", {})
            if ubo_search:
                print(f"\n👤 UBO SEARCH RESULTS:")
                print(f"   Success: {ubo_search.get('success', False)}")
                print(f"   Relevant Results: {ubo_search.get('total_results', 0)}")
                
                people = ubo_search.get("people", [])
                if people:
                    print(f"   Relevant People Found: {len(people)}")
                    
                    for j, person in enumerate(people):
                        print(f"\n   👤 Relevant Person {j+1}:")
                        print(f"      Name: {person.get('name', 'N/A')}")
                        print(f"      Title: {person.get('title', 'N/A')}")
                        print(f"      Email: {person.get('email', 'N/A')}")
                        print(f"      Phone: {person.get('phone', 'N/A')}")
                        print(f"      LinkedIn: {person.get('linkedin', 'N/A')}")
                        print(f"      Seniority: {person.get('seniority', 'N/A')}")
                        
                        organization = person.get('organization', {})
                        if organization:
                            print(f"      Organization: {organization.get('name', 'N/A')}")
                            print(f"      Org Industry: {organization.get('industry', 'N/A')}")
                            print(f"      Org Website: {organization.get('website', 'N/A')}")
                else:
                    print(f"   ⚠️  No relevant people found")
            
            # Domain Search Results
            domain_search = apollo_enrichment.get("domain_search", {})
            if domain_search:
                print(f"\n🌐 DOMAIN SEARCH RESULTS:")
                print(f"   Success: {domain_search.get('success', False)}")
                print(f"   Relevant Results: {domain_search.get('total_results', 0)}")
                
                organizations = domain_search.get("organizations", [])
                if organizations:
                    print(f"   Relevant Domain Organizations: {len(organizations)}")
                    
                    for j, org in enumerate(organizations):
                        print(f"\n   🌐 Domain Organization {j+1}:")
                        print(f"      Name: {org.get('name', 'N/A')}")
                        print(f"      Website: {org.get('website', 'N/A')}")
                        print(f"      Industry: {org.get('industry', 'N/A')}")
                        print(f"      Employee Count: {org.get('employee_count', 'N/A')}")
                else:
                    print(f"   ⚠️  No relevant domain organizations found")
            
            # Enrichment Summary
            enrichment_summary = apollo_enrichment.get("enrichment_summary", {})
            if enrichment_summary:
                print(f"\n📊 ENRICHMENT SUMMARY:")
                print(f"   Entity Found: {enrichment_summary.get('entity_found', False)}")
                print(f"   UBO Found: {enrichment_summary.get('ubo_found', False)}")
                print(f"   Domain Verified: {enrichment_summary.get('domain_verified', False)}")
                print(f"   Total Relevant Matches: {enrichment_summary.get('total_matches', 0)}")
        
        # Apollo Insights Data
        apollo_insights = stage_result.get("apollo_insights", {})
        if apollo_insights:
            print(f"\n🎯 FILTERED APOLLO INSIGHTS:")
            print(f"{'─'*50}")
            
            # Entity Verification
            entity_verification = apollo_insights.get("entity_verification", {})
            if entity_verification:
                print(f"\n🏢 ENTITY VERIFICATION:")
                print(f"   Verified: {entity_verification.get('verified', False)}")
                print(f"   Confidence Score: {entity_verification.get('confidence_score', 0)}%")
                
                company_details = entity_verification.get("company_details", {})
                if company_details:
                    print(f"   Relevant Company Details:")
                    print(f"      Name: {company_details.get('name', 'N/A')}")
                    print(f"      Industry: {company_details.get('industry', 'N/A')}")
                    print(f"      Employee Count: {company_details.get('employee_count', 'N/A')}")
                    print(f"      Website: {company_details.get('website', 'N/A')}")
            
            # UBO Verification
            ubo_verification = apollo_insights.get("ubo_verification", {})
            if ubo_verification:
                print(f"\n👤 UBO VERIFICATION:")
                print(f"   Verified: {ubo_verification.get('verified', False)}")
                print(f"   Confidence Score: {ubo_verification.get('confidence_score', 0)}%")
                
                person_details = ubo_verification.get("person_details", {})
                if person_details:
                    print(f"   Relevant Person Details:")
                    print(f"      Name: {person_details.get('name', 'N/A')}")
                    print(f"      Title: {person_details.get('title', 'N/A')}")
                    print(f"      Email: {person_details.get('email', 'N/A')}")
                    print(f"      Organization: {person_details.get('organization', {}).get('name', 'N/A')}")
            
            # Domain Verification
            domain_verification = apollo_insights.get("domain_verification", {})
            if domain_verification:
                print(f"\n🌐 DOMAIN VERIFICATION:")
                print(f"   Verified: {domain_verification.get('verified', False)}")
                print(f"   Confidence Score: {domain_verification.get('confidence_score', 0)}%")
                
                domain_details = domain_verification.get("domain_details", {})
                if domain_details:
                    print(f"   Relevant Domain Details:")
                    print(f"      Name: {domain_details.get('name', 'N/A')}")
                    print(f"      Website: {domain_details.get('website', 'N/A')}")
                    print(f"      Industry: {domain_details.get('industry', 'N/A')}")
            
            # Overall Confidence
            overall_confidence = apollo_insights.get("overall_confidence", 0)
            print(f"\n📈 OVERALL CONFIDENCE: {overall_confidence}%")

async def main():
    """Main test function"""
    try:
        await test_filtered_apollo_responses()
        print(f"\n{'='*60}")
        print("🎉 Filtered Apollo.ai Response Analysis Complete!")
        print("✅ Only relevant information aligned with UBO trace project is shown")
        print(f"{'='*60}")
    except Exception as e:
        print(f"\n❌ Analysis failed with error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
