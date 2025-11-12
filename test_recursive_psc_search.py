#!/usr/bin/env python3
"""
Test script for recursive natural PSC search endpoint
"""
import asyncio
import httpx
import json
import time

API_BASE_URL = "http://localhost:8000"

async def test_recursive_psc_search():
    """Test the recursive natural PSC search endpoint"""
    
    request_data = {
        "company_name": "Philippine Coastal Storage & Pipeline Corporation",
        "location": "Philippines",
        "max_depth": 3
    }
    
    print("=" * 80)
    print("Testing Recursive Natural PSC Search Endpoint")
    print("=" * 80)
    print(f"Request: {json.dumps(request_data, indent=2)}")
    print("=" * 80)
    print("\nSending request...\n")
    
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/recursive-natural-psc-search",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            elapsed_time = time.time() - start_time
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Time: {elapsed_time:.2f} seconds")
            print("=" * 80)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\nSuccess: {result.get('success')}")
                print(f"Total Found: {result.get('total_found', 0)}")
                print(f"Total Processed: {result.get('total_processed', 0)}")
                print(f"Processing Time: {result.get('processing_time_ms', 0)}ms")
                
                if result.get('natural_psc_candidates'):
                    print(f"\nNatural PSC Candidates ({len(result['natural_psc_candidates'])}):")
                    print("-" * 80)
                    for idx, candidate in enumerate(result['natural_psc_candidates'], 1):
                        print(f"\n{idx}. {candidate.get('candidate')}")
                        print(f"   Confidence: {candidate.get('confidence', 'N/A')}")
                        print(f"   UBO Type: {candidate.get('ubo_type', 'N/A')}")
                        if candidate.get('evidence'):
                            print(f"   Evidence: {candidate['evidence'][:200]}...")
                        if candidate.get('source_url'):
                            print(f"   Source: {candidate['source_url']}")
                else:
                    print("\nNo natural PSC candidates found.")
                
                if result.get('error'):
                    print(f"\nError: {result['error']}")
            else:
                print(f"Error Response: {response.text}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_recursive_psc_search())

