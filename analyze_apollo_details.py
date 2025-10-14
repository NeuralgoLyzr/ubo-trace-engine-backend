#!/usr/bin/env python3
"""
Detailed Apollo.ai Response Analysis
Shows all possible details coming from Apollo.ai API responses
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

async def analyze_apollo_response_details():
    """Analyze all Apollo.ai response details"""
    
    print("🔍 Detailed Apollo.ai Response Analysis")
    print("=" * 80)
    
    # Create and execute a trace to get Apollo data
    print("1. Creating and executing trace to get Apollo data...")
    
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
    
    # Analyze Apollo data from each stage
    stage_results = summary.get("stage_results", [])
    
    for i, stage_result in enumerate(stage_results):
        stage_name = stage_result.get("stage", f"stage_{i+1}")
        print(f"\n{'='*80}")
        print(f"📊 STAGE: {stage_name.upper()}")
        print(f"{'='*80}")
        
        # Apollo Enrichment Data
        apollo_enrichment = stage_result.get("apollo_enrichment", {})
        if apollo_enrichment:
            print(f"\n🔍 APOLLO ENRICHMENT DATA:")
            print(f"{'─'*50}")
            
            # Entity Search Results
            entity_search = apollo_enrichment.get("entity_search", {})
            if entity_search:
                print(f"\n📋 ENTITY SEARCH RESULTS:")
                print(f"   Success: {entity_search.get('success', False)}")
                print(f"   Total Results: {entity_search.get('total_results', 0)}")
                
                organizations = entity_search.get("organizations", [])
                if organizations:
                    print(f"   Organizations Found: {len(organizations)}")
                    
                    for j, org in enumerate(organizations[:3]):  # Show first 3
                        print(f"\n   🏢 Organization {j+1}:")
                        print(f"      ID: {org.get('id', 'N/A')}")
                        print(f"      Name: {org.get('name', 'N/A')}")
                        print(f"      Website: {org.get('website_url', 'N/A')}")
                        print(f"      Industry: {org.get('industry', 'N/A')}")
                        print(f"      Founded Year: {org.get('founded_year', 'N/A')}")
                        print(f"      Employee Count: {org.get('estimated_num_employees', 'N/A')}")
                        print(f"      Annual Revenue: {org.get('annual_revenue', 'N/A')}")
                        print(f"      Phone: {org.get('phone', 'N/A')}")
                        print(f"      Address: {org.get('street_address', 'N/A')}")
                        print(f"      City: {org.get('city', 'N/A')}")
                        print(f"      State: {org.get('state', 'N/A')}")
                        print(f"      Country: {org.get('country', 'N/A')}")
                        print(f"      Postal Code: {org.get('postal_code', 'N/A')}")
                        print(f"      LinkedIn: {org.get('linkedin_url', 'N/A')}")
                        print(f"      Facebook: {org.get('facebook_url', 'N/A')}")
                        print(f"      Twitter: {org.get('twitter_url', 'N/A')}")
                        print(f"      Description: {org.get('short_description', 'N/A')[:100]}...")
                        
                        # Technologies
                        technologies = org.get('technologies', [])
                        if technologies:
                            print(f"      Technologies: {', '.join(technologies[:5])}")
                        
                        # Keywords
                        keywords = org.get('keywords', [])
                        if keywords:
                            print(f"      Keywords: {', '.join(keywords[:5])}")
                
                # Search Parameters
                search_params = entity_search.get("search_params", {})
                if search_params:
                    print(f"\n   🔍 Search Parameters:")
                    for key, value in search_params.items():
                        print(f"      {key}: {value}")
            
            # UBO Search Results
            ubo_search = apollo_enrichment.get("ubo_search", {})
            if ubo_search:
                print(f"\n👤 UBO SEARCH RESULTS:")
                print(f"   Success: {ubo_search.get('success', False)}")
                print(f"   Total Results: {ubo_search.get('total_results', 0)}")
                
                people = ubo_search.get("people", [])
                if people:
                    print(f"   People Found: {len(people)}")
                    
                    for j, person in enumerate(people[:3]):  # Show first 3
                        print(f"\n   👤 Person {j+1}:")
                        print(f"      ID: {person.get('id', 'N/A')}")
                        print(f"      Name: {person.get('name', 'N/A')}")
                        print(f"      First Name: {person.get('first_name', 'N/A')}")
                        print(f"      Last Name: {person.get('last_name', 'N/A')}")
                        print(f"      Email: {person.get('email', 'N/A')}")
                        print(f"      Phone: {person.get('phone_numbers', [{}])[0].get('raw_number', 'N/A') if person.get('phone_numbers') else 'N/A'}")
                        print(f"      Title: {person.get('title', 'N/A')}")
                        print(f"      Department: {person.get('department', 'N/A')}")
                        print(f"      Seniority: {person.get('seniority', 'N/A')}")
                        print(f"      LinkedIn: {person.get('linkedin_url', 'N/A')}")
                        print(f"      Twitter: {person.get('twitter_url', 'N/A')}")
                        print(f"      Facebook: {person.get('facebook_url', 'N/A')}")
                        print(f"      Photo: {person.get('photo_url', 'N/A')}")
                        
                        # Organization details
                        organization = person.get('organization', {})
                        if organization:
                            print(f"      Organization: {organization.get('name', 'N/A')}")
                            print(f"      Org Industry: {organization.get('industry', 'N/A')}")
                            print(f"      Org Website: {organization.get('website_url', 'N/A')}")
                        
                        # Employment history
                        employment_history = person.get('employment_history', [])
                        if employment_history:
                            print(f"      Employment History:")
                            for emp in employment_history[:2]:  # Show first 2
                                print(f"         - {emp.get('title', 'N/A')} at {emp.get('organization_name', 'N/A')}")
                
                # Search Parameters
                search_params = ubo_search.get("search_params", {})
                if search_params:
                    print(f"\n   🔍 Search Parameters:")
                    for key, value in search_params.items():
                        print(f"      {key}: {value}")
            
            # Domain Search Results
            domain_search = apollo_enrichment.get("domain_search", {})
            if domain_search:
                print(f"\n🌐 DOMAIN SEARCH RESULTS:")
                print(f"   Success: {domain_search.get('success', False)}")
                print(f"   Total Results: {domain_search.get('total_results', 0)}")
                
                organizations = domain_search.get("organizations", [])
                if organizations:
                    print(f"   Organizations Found: {len(organizations)}")
                    
                    for j, org in enumerate(organizations[:2]):  # Show first 2
                        print(f"\n   🌐 Domain Organization {j+1}:")
                        print(f"      ID: {org.get('id', 'N/A')}")
                        print(f"      Name: {org.get('name', 'N/A')}")
                        print(f"      Website: {org.get('website_url', 'N/A')}")
                        print(f"      Industry: {org.get('industry', 'N/A')}")
                        print(f"      Employee Count: {org.get('estimated_num_employees', 'N/A')}")
                        print(f"      Annual Revenue: {org.get('annual_revenue', 'N/A')}")
                        print(f"      Description: {org.get('short_description', 'N/A')[:100]}...")
                
                # Search Parameters
                search_params = domain_search.get("search_params", {})
                if search_params:
                    print(f"\n   🔍 Search Parameters:")
                    for key, value in search_params.items():
                        print(f"      {key}: {value}")
            
            # Enrichment Summary
            enrichment_summary = apollo_enrichment.get("enrichment_summary", {})
            if enrichment_summary:
                print(f"\n📊 ENRICHMENT SUMMARY:")
                print(f"   Entity Found: {enrichment_summary.get('entity_found', False)}")
                print(f"   UBO Found: {enrichment_summary.get('ubo_found', False)}")
                print(f"   Domain Verified: {enrichment_summary.get('domain_verified', False)}")
                print(f"   Total Matches: {enrichment_summary.get('total_matches', 0)}")
        
        # Apollo Insights Data
        apollo_insights = stage_result.get("apollo_insights", {})
        if apollo_insights:
            print(f"\n🎯 APOLLO INSIGHTS:")
            print(f"{'─'*50}")
            
            # Entity Verification
            entity_verification = apollo_insights.get("entity_verification", {})
            if entity_verification:
                print(f"\n🏢 ENTITY VERIFICATION:")
                print(f"   Verified: {entity_verification.get('verified', False)}")
                print(f"   Confidence Score: {entity_verification.get('confidence_score', 0)}%")
                
                company_details = entity_verification.get("company_details", {})
                if company_details:
                    print(f"   Company Details:")
                    print(f"      Name: {company_details.get('name', 'N/A')}")
                    print(f"      Industry: {company_details.get('industry', 'N/A')}")
                    print(f"      Employee Count: {company_details.get('estimated_num_employees', 'N/A')}")
                    print(f"      Annual Revenue: {company_details.get('annual_revenue', 'N/A')}")
                    print(f"      Founded: {company_details.get('founded_year', 'N/A')}")
                    print(f"      Website: {company_details.get('website_url', 'N/A')}")
                    print(f"      LinkedIn: {company_details.get('linkedin_url', 'N/A')}")
            
            # UBO Verification
            ubo_verification = apollo_insights.get("ubo_verification", {})
            if ubo_verification:
                print(f"\n👤 UBO VERIFICATION:")
                print(f"   Verified: {ubo_verification.get('verified', False)}")
                print(f"   Confidence Score: {ubo_verification.get('confidence_score', 0)}%")
                
                person_details = ubo_verification.get("person_details", {})
                if person_details:
                    print(f"   Person Details:")
                    print(f"      Name: {person_details.get('name', 'N/A')}")
                    print(f"      Title: {person_details.get('title', 'N/A')}")
                    print(f"      Email: {person_details.get('email', 'N/A')}")
                    print(f"      LinkedIn: {person_details.get('linkedin_url', 'N/A')}")
                    print(f"      Organization: {person_details.get('organization', {}).get('name', 'N/A')}")
            
            # Domain Verification
            domain_verification = apollo_insights.get("domain_verification", {})
            if domain_verification:
                print(f"\n🌐 DOMAIN VERIFICATION:")
                print(f"   Verified: {domain_verification.get('verified', False)}")
                print(f"   Confidence Score: {domain_verification.get('confidence_score', 0)}%")
                
                domain_details = domain_verification.get("domain_details", {})
                if domain_details:
                    print(f"   Domain Details:")
                    print(f"      Name: {domain_details.get('name', 'N/A')}")
                    print(f"      Website: {domain_details.get('website_url', 'N/A')}")
                    print(f"      Industry: {domain_details.get('industry', 'N/A')}")
                    print(f"      Employee Count: {domain_details.get('estimated_num_employees', 'N/A')}")
            
            # Overall Confidence
            overall_confidence = apollo_insights.get("overall_confidence", 0)
            print(f"\n📈 OVERALL CONFIDENCE: {overall_confidence}%")
        
        # Error handling
        if apollo_enrichment.get("error"):
            print(f"\n❌ APOLLO ERROR: {apollo_enrichment.get('error')}")
        
        if apollo_insights.get("error"):
            print(f"\n❌ APOLLO INSIGHTS ERROR: {apollo_insights.get('error')}")

async def main():
    """Main analysis function"""
    try:
        await analyze_apollo_response_details()
        print(f"\n{'='*80}")
        print("🎉 Apollo.ai Response Analysis Complete!")
        print("📊 All possible Apollo.ai details have been displayed above")
        print(f"{'='*80}")
    except Exception as e:
        print(f"\n❌ Analysis failed with error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
