#!/usr/bin/env python3
"""
UBO Trace Engine Backend - Test Script
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TRACE = {
    "entity": "Louis Dreyfus Company Metals MEA DMCC",
    "ubo_name": "Liu Jianfeng",
    "location": "UAE",
    "domain_name": "louisdreyfus.com"
}

async def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200

async def test_create_trace():
    """Test creating a UBO trace"""
    print("\n📝 Testing trace creation...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/trace",
            json=TEST_TRACE
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            trace_data = response.json()
            print(f"Trace ID: {trace_data['trace_id']}")
            return trace_data['trace_id']
        else:
            print(f"Error: {response.text}")
            return None

async def test_execute_trace(trace_id):
    """Test executing a UBO trace"""
    print(f"\n🚀 Testing trace execution for {trace_id}...")
    async with httpx.AsyncClient(timeout=300) as client:  # 5 minute timeout
        response = await client.post(f"{BASE_URL}/api/v1/trace/{trace_id}/execute")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            summary = response.json()
            print(f"Connection Status: {summary['connection_status']}")
            print(f"Direct Evidence: {summary['has_direct_evidence']}")
            print(f"Indirect Evidence: {summary['has_indirect_evidence']}")
            print(f"Total URLs: {summary['total_urls']}")
            print(f"Processing Time: {summary['total_processing_time_ms']}ms")
            return True
        else:
            print(f"Error: {response.text}")
            return False

async def test_get_trace_summary(trace_id):
    """Test getting trace summary"""
    print(f"\n📊 Testing trace summary retrieval for {trace_id}...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/trace/{trace_id}/summary")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            summary = response.json()
            print(f"Stages Completed: {summary['stages_completed']}/{summary['total_stages']}")
            print(f"Overall Status: {summary['overall_status']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False

async def test_get_traces():
    """Test getting all traces"""
    print("\n📋 Testing trace listing...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/traces")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            traces = response.json()
            print(f"Total Traces: {len(traces)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False

async def test_get_stats():
    """Test getting trace statistics"""
    print("\n📈 Testing trace statistics...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/traces/stats")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"Total Traces: {stats['total_traces']}")
            print(f"Status Counts: {stats['status_counts']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False

async def main():
    """Run all tests"""
    print("🧪 UBO Trace Engine Backend - Test Suite")
    print("=" * 50)
    
    # Test health check
    health_ok = await test_health_check()
    if not health_ok:
        print("❌ Health check failed. Make sure the server is running.")
        return
    
    # Test trace creation
    trace_id = await test_create_trace()
    if not trace_id:
        print("❌ Trace creation failed.")
        return
    
    # Test trace execution (this will take time)
    print("\n⏳ Executing trace (this may take 2-3 minutes)...")
    execution_ok = await test_execute_trace(trace_id)
    
    # Test summary retrieval
    if execution_ok:
        await test_get_trace_summary(trace_id)
    
    # Test other endpoints
    await test_get_traces()
    await test_get_stats()
    
    print("\n✅ Test suite completed!")
    print(f"📝 Trace ID for manual testing: {trace_id}")

if __name__ == "__main__":
    asyncio.run(main())
