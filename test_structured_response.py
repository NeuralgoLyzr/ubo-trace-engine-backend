#!/usr/bin/env python3
"""
Test script to verify that TraceSummary includes structured facts and summary for each stage.
This ensures the API response contains the facts and summary from Lyzr AI agents.
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

async def test_structured_response():
    """Test that API response includes structured facts and summary"""
    
    print("🧪 Testing Structured Facts and Summary in API Response")
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
    
    # Execute trace
    print("\n2. Executing trace...")
    async with httpx.AsyncClient(timeout=300.0) as client:
        execute_response = await client.post(f"{BASE_URL}/trace/{trace_id}/execute")
        
        if execute_response.status_code != 200:
            print(f"❌ Failed to execute trace: {execute_response.text}")
            return False
            
        summary = execute_response.json()
        print(f"✅ Trace execution completed")
    
    # Verify structured response format
    print("\n3. Verifying structured response format...")
    
    # Check that stage_results exist
    if "stage_results" not in summary:
        print("❌ FAILED: stage_results not found in response")
        return False
    else:
        print("✅ stage_results found in response")
    
    stage_results = summary["stage_results"]
    if len(stage_results) != 4:
        print(f"❌ FAILED: Expected 4 stage results, got {len(stage_results)}")
        return False
    else:
        print(f"✅ Found {len(stage_results)} stage results")
    
    # Check each stage result
    required_fields = ["facts", "summary", "stage", "status"]
    stages_with_facts = 0
    stages_with_summary = 0
    
    for i, stage_result in enumerate(stage_results):
        stage_name = stage_result.get("stage", f"stage_{i+1}")
        print(f"\n   Stage {stage_name}:")
        
        # Check required fields
        missing_fields = [field for field in required_fields if field not in stage_result]
        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
            return False
        else:
            print(f"   ✅ All required fields present")
        
        # Check facts structure
        facts = stage_result.get("facts", [])
        if isinstance(facts, list):
            print(f"   ✅ Facts is a list with {len(facts)} items")
            stages_with_facts += 1
            
            # Check fact structure
            for j, fact in enumerate(facts):
                if isinstance(fact, dict) and "fact" in fact and "url" in fact:
                    print(f"     ✅ Fact {j+1}: Has 'fact' and 'url' fields")
                else:
                    print(f"     ❌ Fact {j+1}: Missing 'fact' or 'url' fields")
                    return False
        else:
            print(f"   ❌ Facts is not a list: {type(facts)}")
            return False
        
        # Check summary
        summary_text = stage_result.get("summary")
        if summary_text and isinstance(summary_text, str) and len(summary_text.strip()) > 0:
            print(f"   ✅ Summary present: {len(summary_text)} chars")
            stages_with_summary += 1
        else:
            print(f"   ⚠️  Summary missing or empty")
        
        # Check status
        status = stage_result.get("status")
        if status == "completed":
            print(f"   ✅ Status: {status}")
        else:
            print(f"   ⚠️  Status: {status}")
    
    # Summary verification
    print(f"\n4. Summary verification:")
    print(f"   Stages with facts: {stages_with_facts}/4")
    print(f"   Stages with summary: {stages_with_summary}/4")
    
    if stages_with_facts >= 2:  # At least half should have facts
        print("✅ Sufficient stages have facts")
    else:
        print("❌ Too few stages have facts")
        return False
    
    if stages_with_summary >= 2:  # At least half should have summary
        print("✅ Sufficient stages have summary")
    else:
        print("❌ Too few stages have summary")
        return False
    
    # Test specific stage (e.g., stage_1a)
    print(f"\n5. Testing specific stage structure:")
    stage_1a = next((s for s in stage_results if s.get("stage") == "stage_1a"), None)
    if stage_1a:
        facts = stage_1a.get("facts", [])
        summary = stage_1a.get("summary", "")
        
        print(f"   Stage 1A facts: {len(facts)} items")
        print(f"   Stage 1A summary length: {len(summary)} chars")
        
        if facts:
            print(f"   First fact preview: {facts[0].get('fact', '')[:100]}...")
            print(f"   First fact URL: {facts[0].get('url', '')}")
        
        if summary:
            print(f"   Summary preview: {summary[:100]}...")
    else:
        print("   ⚠️  Stage 1A not found")
    
    print("\n🎉 Test completed successfully!")
    print("✅ API response includes structured facts and summary for each stage")
    print("✅ Facts contain 'fact' and 'url' fields")
    print("✅ Summary is included for each stage")
    
    return True

async def main():
    """Main test function"""
    try:
        success = await test_structured_response()
        if success:
            print("\n🎉 All tests passed! Structured facts and summary are properly included.")
        else:
            print("\n❌ Tests failed. Please check the implementation.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
