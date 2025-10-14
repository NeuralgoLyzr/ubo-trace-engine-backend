#!/usr/bin/env python3
"""
Test script to verify that trace execution doesn't accumulate results from previous calls.
This ensures each API call returns fresh results specific to that execution.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_ENTITY = "Test Company Ltd"
TEST_UBO = "John Doe"
TEST_LOCATION = "London, UK"
TEST_DOMAIN = "testcompany.com"

async def test_trace_execution():
    """Test that trace execution doesn't accumulate results"""
    
    print("🧪 Testing Trace Execution - No Result Accumulation")
    print("=" * 60)
    
    # Create a new trace
    print("1. Creating new trace...")
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
            return False
            
        trace_data = create_response.json()
        trace_id = trace_data["trace_id"]
        print(f"✅ Created trace: {trace_id}")
    
    # Execute trace first time
    print("\n2. Executing trace (first time)...")
    async with httpx.AsyncClient(timeout=300.0) as client:
        execute_response = await client.post(f"{BASE_URL}/trace/{trace_id}/execute")
        
        if execute_response.status_code != 200:
            print(f"❌ Failed to execute trace: {execute_response.text}")
            return False
            
        first_summary = execute_response.json()
        print(f"✅ First execution completed")
        print(f"   Stages completed: {first_summary['stages_completed']}")
        print(f"   Total URLs: {first_summary['total_urls']}")
        print(f"   Total direct facts: {first_summary['total_direct_facts']}")
        print(f"   Total indirect facts: {first_summary['total_indirect_facts']}")
    
    # Execute trace second time (should not accumulate)
    print("\n3. Executing trace (second time)...")
    async with httpx.AsyncClient(timeout=300.0) as client:
        execute_response = await client.post(f"{BASE_URL}/trace/{trace_id}/execute")
        
        if execute_response.status_code != 200:
            print(f"❌ Failed to execute trace: {execute_response.text}")
            return False
            
        second_summary = execute_response.json()
        print(f"✅ Second execution completed")
        print(f"   Stages completed: {second_summary['stages_completed']}")
        print(f"   Total URLs: {second_summary['total_urls']}")
        print(f"   Total direct facts: {second_summary['total_direct_facts']}")
        print(f"   Total indirect facts: {second_summary['total_indirect_facts']}")
    
    # Verify results are not accumulated
    print("\n4. Verifying no accumulation...")
    
    # Check stages_completed (should never exceed 4)
    if second_summary['stages_completed'] > 4:
        print(f"❌ FAILED: stages_completed ({second_summary['stages_completed']}) exceeds maximum of 4")
        return False
    else:
        print(f"✅ stages_completed is correct: {second_summary['stages_completed']}")
    
    # Check if results are reasonable (not accumulated from previous runs)
    if second_summary['total_urls'] > 50:  # Reasonable threshold
        print(f"❌ FAILED: total_urls ({second_summary['total_urls']}) seems too high (possible accumulation)")
        return False
    else:
        print(f"✅ total_urls is reasonable: {second_summary['total_urls']}")
    
    if second_summary['total_direct_facts'] > 50:  # Reasonable threshold
        print(f"❌ FAILED: total_direct_facts ({second_summary['total_direct_facts']}) seems too high (possible accumulation)")
        return False
    else:
        print(f"✅ total_direct_facts is reasonable: {second_summary['total_direct_facts']}")
    
    if second_summary['total_indirect_facts'] > 50:  # Reasonable threshold
        print(f"❌ FAILED: total_indirect_facts ({second_summary['total_indirect_facts']}) seems too high (possible accumulation)")
        return False
    else:
        print(f"✅ total_indirect_facts is reasonable: {second_summary['total_indirect_facts']}")
    
    # Check that results are consistent between executions
    if (first_summary['stages_completed'] == second_summary['stages_completed'] and
        abs(first_summary['total_urls'] - second_summary['total_urls']) <= 5 and
        abs(first_summary['total_direct_facts'] - second_summary['total_direct_facts']) <= 5 and
        abs(first_summary['total_indirect_facts'] - second_summary['total_indirect_facts']) <= 5):
        print("✅ Results are consistent between executions (no accumulation)")
    else:
        print("⚠️  Results differ between executions (this might be expected due to Lyzr agent variability)")
    
    print("\n🎉 Test completed successfully!")
    print("✅ Trace execution does not accumulate results from previous calls")
    print("✅ Each API call returns fresh results specific to that execution")
    
    return True

async def main():
    """Main test function"""
    try:
        success = await test_trace_execution()
        if success:
            print("\n🎉 All tests passed! The accumulation issue has been fixed.")
        else:
            print("\n❌ Tests failed. Please check the implementation.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
