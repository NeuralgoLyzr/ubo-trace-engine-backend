"""
Test script for UBO Search endpoint
"""
import asyncio
import json
from services.ubo_search_service import UBOSearchService
from models.schemas import UBOSearchRequest

async def test_ubo_search():
    """Test UBO search service"""
    print("Testing UBO Search Service...")
    
    # Create request
    request = UBOSearchRequest(
        company_name="Louis Dreyfus Company Metals MEA DMCC",
        location="Dubai, UAE",
        include_full_analysis=False
    )
    
    print(f"\nRequest: {request.company_name}")
    print(f"Location: {request.location}")
    print(f"Full Analysis: {request.include_full_analysis}\n")
    
    # Initialize service
    service = UBOSearchService()
    
    try:
        result = await service.search_ubo(request)
        
        print(f"Success: {result.success}")
        print(f"Entity: {result.entity}")
        print(f"Processing Time: {result.processing_time_ms}ms")
        
        if result.error:
            print(f"Error: {result.error}")
        
        if result.domain_info:
            print(f"\nDomain: {result.domain_info.domain}")
        
        if result.probable_ubos:
            print(f"\nProbable UBOs: {result.probable_ubos}")
        
        if result.confidence:
            print(f"Confidence: {result.confidence}")
        
        if result.cross_candidates:
            print(f"\nCross-Verified Candidates: {len(result.cross_candidates)}")
            for candidate in result.cross_candidates[:3]:
                print(f"  - {candidate.candidate} ({candidate.confidence})")
        
        print("\n✓ Test completed successfully!")
        return result
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_ubo_search())

