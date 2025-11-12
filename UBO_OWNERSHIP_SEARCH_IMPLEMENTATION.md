# UBO Ownership Search Implementation

This document explains the new UBO ownership search feature that uses Google Search API (via SearchAPI.io) and analyzes results with a Lyzr agent.

## Overview

The UBO ownership search feature:
1. Searches Google for UBO ownership information using a specific query format
2. Extracts `organic_results` and `related_questions` from the search results
3. Sends these results to a Lyzr agent for analysis

## Implementation Details

### 1. Service Method

**File**: `services/searchapi_service.py`

**Method**: `search_ubo_ownership(company_name: str, location: Optional[str] = None)`

**Search Query Format**:
```
{company_name} "ultimate beneficial owner" OR "shareholder" OR "ownership" "stake holding"
```

**Example**:
```
Louis Dreyfus Company Metals MEA DMCC "ultimate beneficial owner" OR "shareholder" OR "ownership" "stake holding"
```

### 2. API Endpoint

**Endpoint**: `POST /api/v1/search-ubo-ownership`

**Parameters**:
- `company_name` (required): Company name to search
- `location` (optional): Location/jurisdiction for geographic targeting

### 3. Response Structure

```json
{
  "success": true,
  "organic_results": [
    {
      "position": 1,
      "title": "Result Title",
      "link": "https://example.com",
      "source": "Source Name",
      "domain": "example.com",
      "snippet": "Result snippet text...",
      ...
    }
  ],
  "related_questions": [
    {
      "question": "Question text",
      "answer": "Answer text",
      ...
    }
  ],
  "lyzr_analysis": {
    "success": true,
    "analysis": "Analysis content from Lyzr agent",
    "raw_response": "Raw response from Lyzr agent",
    "processing_time_ms": 2500
  },
  "search_query": "Company Name \"ultimate beneficial owner\" OR \"shareholder\" OR \"ownership\" \"stake holding\"",
  "total_organic_results": 10,
  "total_related_questions": 4
}
```

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# SearchAPI Google Settings
SEARCHAPI_API_KEY=your_searchapi_api_key_here

# Lyzr API Settings (already configured)
LYZR_API_KEY=sk-default-LBs7UhBD3Z90Zt7w7WdIYs724U5YVPuK
LYZR_USER_ID=workspace2@wtw.com

# UBO Ownership Analysis Agent (already configured in settings.py)
AGENT_UBO_OWNERSHIP_ANALYSIS=69090013f6473313aec6de8f
SESSION_UBO_OWNERSHIP_ANALYSIS=69090013f6473313aec6de8f-fb9akwo3kx
```

### Settings (utils/settings.py)

The following settings are already configured:

```python
# UBO Ownership Analysis Agent (for Google Search results)
agent_ubo_ownership_analysis: str = "69090013f6473313aec6de8f"
session_ubo_ownership_analysis: str = "69090013f6473313aec6de8f-fb9akwo3kx"
```

## Usage Examples

### 1. Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/search-ubo-ownership?company_name=Louis+Dreyfus+Company+Metals+MEA+DMCC&location=UAE" \
  -H "Content-Type: application/json"
```

### 2. Using Python

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/search-ubo-ownership",
        params={
            "company_name": "Louis Dreyfus Company Metals MEA DMCC",
            "location": "UAE"
        }
    )
    result = response.json()
    print(f"Found {result['total_organic_results']} organic results")
    print(f"Found {result['total_related_questions']} related questions")
    
    if result['lyzr_analysis']['success']:
        print(f"Lyzr Analysis: {result['lyzr_analysis']['analysis']}")
```

### 3. Direct Service Usage

```python
from services.searchapi_service import SearchAPIService

service = SearchAPIService()
result = await service.search_ubo_ownership(
    company_name="Louis Dreyfus Company Metals MEA DMCC",
    location="UAE"
)

if result["success"]:
    print(f"Organic Results: {len(result['organic_results'])}")
    print(f"Related Questions: {len(result['related_questions'])}")
    
    if result["lyzr_analysis"]["success"]:
        print(f"Analysis: {result['lyzr_analysis']['analysis']}")
```

## Workflow

1. **Google Search**: 
   - Calls SearchAPI.io with the formatted query
   - Extracts `organic_results` and `related_questions` from response

2. **Lyzr Analysis**:
   - Builds message with company_name, organic_results, and related_questions
   - Sends to Lyzr agent (ID: `69090013f6473313aec6de8f`)
   - Returns analysis along with raw response

3. **Response**:
   - Returns combined results with search data and Lyzr analysis

## Error Handling

The service handles errors gracefully:

- **Missing API Key**: Returns `success: false` with error message
- **API Failures**: Catches exceptions and returns error details
- **Empty Results**: Returns empty arrays with `success: true`
- **Lyzr Agent Not Configured**: Returns `lyzr_analysis.success: false` with error message

## Key Features

✅ **Specific Query Format**: Targets UBO ownership information with precise search terms  
✅ **Geographic Targeting**: Supports location-based search results  
✅ **Structured Data Extraction**: Extracts only relevant fields (organic_results, related_questions)  
✅ **AI Analysis**: Uses Lyzr agent to analyze and interpret search results  
✅ **Error Resilience**: Graceful handling of API failures  
✅ **Comprehensive Response**: Returns both raw search data and AI analysis  

## Notes

- The search query uses specific terms: "ultimate beneficial owner", "shareholder", "ownership", "stake holding"
- Location is optional - defaults to "United States" if not provided
- The Lyzr agent receives both organic_results and related_questions for comprehensive analysis
- Processing time is tracked for the Lyzr analysis step
- The service works without Lyzr agent configured, but analysis will be skipped

## Related Files

- `services/searchapi_service.py` - Main implementation
- `api/endpoints.py` - API endpoint integration
- `utils/settings.py` - Configuration settings

