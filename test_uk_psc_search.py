"""
Test script for UK PSC Search endpoint
"""
import asyncio
import json
import httpx

async def test_uk_psc_search():
    """Test UK PSC search endpoint"""
    print("Testing UK PSC Search Endpoint...")
    
    # API endpoint (adjust URL as needed)
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/uk-psc-search"
    
    # Test request
    request_data = {
        "company_name": "Kobbie Holdco Limited"
    }
    
    print(f"\nRequest: {json.dumps(request_data, indent=2)}\n")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                endpoint,
                json=request_data
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\nSuccess: {result.get('success')}")
                print(f"Iterations: {result.get('iterations')}")
                print(f"Processing Time: {result.get('processing_time_ms')}ms")
                
                if result.get('natural_psc'):
                    psc = result['natural_psc']
                    print(f"\nNatural PSC Found:")
                    print(f"  Name: {psc.get('name')}")
                    print(f"  Age: {psc.get('age')}")
                    print(f"  Nationality: {psc.get('nationality')}")
                    print(f"  Country of Residence: {psc.get('country_of_residence')}")
                    print(f"  Company Number: {psc.get('company_number')}")
                    print(f"  Iteration: {psc.get('iteration')}")
                    print(f"  Address: {json.dumps(psc.get('address', {}), indent=4)}")
                    print(f"  Identification: {json.dumps(psc.get('identification', {}), indent=4)}")
                    print(f"  Natures of Control: {psc.get('natures_of_control', [])}")
                else:
                    print(f"\nError: {result.get('error')}")
                
                print("\n✓ Test completed successfully!")
                return result
            else:
                print(f"\n✗ Request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_uk_psc_search())

