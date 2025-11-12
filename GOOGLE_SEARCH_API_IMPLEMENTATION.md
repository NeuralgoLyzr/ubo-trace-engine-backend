# Google Search API Implementation (SearchAPI.io)

This document explains how Google Search API is implemented and used in the UBO Trace Engine through the SearchAPI.io service.

## Overview

The SearchAPI service provides Google search capabilities for domain discovery, ownership verification, and related domain analysis. It uses the SearchAPI.io API to access Google search results in a structured format.

## Implementation

### 1. Service Location
**File**: `services/searchapi_service.py`

### 2. Key Components

#### **SearchAPIService Class**

Main service class that handles all Google search operations through SearchAPI.io.

**Initialization:**
```python
class SearchAPIService:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.searchapi_api_key  # From .env
        self.base_url = "https://www.searchapi.io/api/v1/search"
        self.timeout = 30.0
```

### 3. Main Methods

#### **A. Domain Search**
```python
async def search_domains(company_name: str, ubo_name: str, location: str) -> Dict[str, Any]
```

**Purpose**: Search for company domains using Google search

**Search Query Format**: 
```
"{company_name} {ubo_name} official website domain"
```

**API Parameters**:
- `engine`: "google"
- `q`: Search query
- `location`: Location string (e.g., "United Arab Emirates")
- `gl`: Country code (e.g., "ae" for UAE)
- `hl`: Language ("en")
- `num`: Number of results (20)

**Returns**:
```json
{
  "success": true,
  "domains": [
    {
      "position": 1,
      "source": "Company Name",
      "domain": "example.com",
      "snippet": "Snippet text from search result"
    }
  ],
  "total_results": 10,
  "search_query": "query string",
  "search_params": {...}
}
```

**Features**:
- Automatic duplicate domain filtering (case-insensitive)
- Extracts only essential fields: position, source, domain, snippet
- Geographic targeting based on location

#### **B. Domain Ownership Search**
```python
async def search_domain_ownership(company_name: str, ubo_name: str, location: str, domain: str) -> Dict[str, Any]
```

**Purpose**: Search for ownership information on a specific domain

**Search Query Format**: 
```
"site:{domain} {company_name} {ubo_name} owner director"
```

**Use Case**: Verify domain ownership by searching within a specific domain

**Returns**: Similar structure to `search_domains()` but focused on ownership results

#### **C. Related Domains Search**
```python
async def search_related_domains(company_name: str, ubo_name: str, location: str) -> Dict[str, Any]
```

**Purpose**: Find related domains (subsidiaries, parent companies, etc.)

**Search Query Format**: 
```
"{company_name} {ubo_name} {location} subsidiary parent company website domain"
```

**Use Case**: Discover corporate structure through related domains

#### **D. Expert Domain Analysis**
```python
async def analyze_domains_with_expert(company_name: str, ubo_name: str, location: str, 
                                       lyzr_domains: List[Dict], google_serp_domains: List[Dict]) -> Dict[str, Any]
```

**Purpose**: Analyze domain search results using Expert Lyzr AI agent for confidence scores and rankings

**Input**: 
- Lyzr agent domain results
- Google SERP domain results

**Returns**:
```json
{
  "success": true,
  "expert_analysis": {
    "overall_confidence": 85,
    "domain_rankings": [
      {
        "domain": "example.com",
        "confidence": 95,
        "reasoning": "Official domain, matches company name",
        "rank": 1
      }
    ],
    "confidence_scores": {...},
    "analysis_summary": "...",
    "recommendations": [...]
  },
  "raw_response": "...",
  "processing_time_ms": 2500
}
```

#### **E. API Endpoint Integration**
```python
async def analyze_domains_for_api(company_name: str, ubo_name: str, location: str) -> Dict[str, Any]
```

**Purpose**: Combined domain analysis method for API endpoint usage

**Workflow**:
1. Gets Lyzr domain analysis results
2. Gets Google SERP domains from SearchAPI
3. Calls Expert agent for analysis
4. Returns formatted results

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# SearchAPI Google Settings
SEARCHAPI_API_KEY=your_searchapi_api_key_here

# Expert Domain Analysis (Optional)
AGENT_EXPERT_DOMAIN=68f0ffd5a0dfaa3e0726523c
SESSION_EXPERT_DOMAIN=68f0ffd5a0dfaa3e0726523c-losfuwfwcd
```

### Settings (utils/settings.py)

```python
# SearchAPI Google settings
searchapi_api_key: str = ""  # Optional - for domain search enhancement
searchapi_timeout: int = 30
```

## Usage Examples

### 1. Basic Domain Search

```python
from services.searchapi_service import SearchAPIService

service = SearchAPIService()
result = await service.search_domains(
    company_name="Louis Dreyfus Company Metals MEA DMCC",
    ubo_name="Liu Jianfeng",
    location="UAE"
)

if result["success"]:
    print(f"Found {result['total_results']} domains")
    for domain in result["domains"]:
        print(f"  {domain['position']}. {domain['domain']}")
```

### 2. Domain Ownership Verification

```python
ownership_result = await service.search_domain_ownership(
    company_name="Louis Dreyfus Company",
    ubo_name="Liu Jianfeng",
    location="UAE",
    domain="louisdreyfus.com"
)

if ownership_result["success"]:
    print(f"Found {ownership_result['total_results']} ownership results")
```

### 3. Related Domains Discovery

```python
related_result = await service.search_related_domains(
    company_name="Louis Dreyfus Company",
    ubo_name="Liu Jianfeng",
    location="UAE"
)

if related_result["success"]:
    print(f"Found {related_result['total_results']} related domains")
```

### 4. Complete Domain Analysis (API Endpoint)

```python
analysis_result = await service.analyze_domains_for_api(
    company_name="Louis Dreyfus Company",
    ubo_name="Liu Jianfeng",
    location="UAE"
)

if analysis_result["success"]:
    print(f"Overall Confidence: {analysis_result['overall_confidence']}%")
    for result in analysis_result["results"]:
        print(f"  {result['rank']}. {result['domain']} - {result['confidence_score']}%")
```

## API Endpoint Usage

### Endpoint: `/api/v1/analyze-domains`

**Method**: POST

**Request**:
```json
{
  "company_name": "Louis Dreyfus Company Metals MEA DMCC",
  "ubo_name": "Liu Jianfeng",
  "location": "UAE"
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "domain": "ldc.com",
      "confidence_score": 95,
      "reasoning": "Official domain, matches company name, verified content"
    }
  ],
  "total_domains_analyzed": 15,
  "overall_confidence": 85,
  "analysis_summary": "Strong domain verification with high confidence..."
}
```

## Integration with UBO Trace

The SearchAPI service is integrated into the UBO Trace workflow:

1. **During Trace Execution**: Domain search results are included in stage results
2. **In Trace Summary**: SearchAPI data appears in `searchapi_domain_search`, `searchapi_domain_ownership`, and `searchapi_related_domains` fields
3. **Expert Analysis**: Combined with Lyzr agent results for comprehensive domain analysis

### Example Trace Response Structure

```json
{
  "trace_id": "uuid",
  "stage_results": [
    {
      "stage": "stage_1a",
      "searchapi_domain_search": {
        "success": true,
        "domains": [...],
        "total_results": 10
      },
      "searchapi_domain_ownership": {...},
      "searchapi_related_domains": {...},
      "expert_domain_analysis": {...}
    }
  ]
}
```

## Helper Methods

### Location Mapping

The service includes helper methods for location conversion:

#### `_get_country_code(location: str) -> str`
Converts location strings to ISO country codes:
- "UAE" → "ae"
- "United Kingdom" → "gb"
- "United States" → "us"

#### `_get_searchapi_location(location: str) -> str`
Converts to SearchAPI-compatible location strings:
- "uae" → "United Arab Emirates"
- "uk" → "United Kingdom"

## Error Handling

The service handles errors gracefully:

- **Missing API Key**: Returns `success: false` with appropriate error message
- **API Failures**: Catches exceptions and returns error details
- **Empty Results**: Returns empty arrays with `success: true`

## Testing

### Test Scripts

1. **test_searchapi_integration.py**: Full integration testing
2. **test_domain_deduplication.py**: Tests duplicate filtering
3. **searchapi_test_commands.sh**: cURL commands for manual testing

### Manual Testing with cURL

```bash
# Basic Domain Search
curl -X GET "https://www.searchapi.io/api/v1/search?engine=google&q=Company+Name+UBO+Name+official+website+domain&location=United+Arab+Emirates&gl=ae" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

## Key Features

✅ **Geographic Targeting**: Location-based search results  
✅ **Duplicate Filtering**: Automatic removal of duplicate domains  
✅ **Multiple Search Types**: Domain search, ownership verification, related domains  
✅ **Expert AI Analysis**: Confidence scoring and ranking through Lyzr Expert agent  
✅ **Structured Results**: Clean, consistent data format  
✅ **Error Resilience**: Graceful handling of API failures  
✅ **Integration Ready**: Seamlessly integrates with existing UBO trace workflow  

## Notes

- SearchAPI.io provides access to Google search results without CAPTCHA
- API key is optional - service works without it but domain search will be disabled
- Duplicate domains are filtered based on normalized domain names (case-insensitive)
- Results are limited to essential fields for efficiency
- Timeout is set to 30 seconds by default

## Related Files

- `services/searchapi_service.py` - Main implementation
- `api/endpoints.py` - API endpoint integration
- `utils/settings.py` - Configuration settings
- `SEARCHAPI_INTEGRATION_EXAMPLE.md` - Integration examples
- `searchapi_test_commands.sh` - Test commands
- `test_searchapi_integration.py` - Integration tests

