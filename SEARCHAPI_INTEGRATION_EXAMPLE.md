# SearchAPI Integration Example with Expert Domain Analysis
# This shows how the SearchAPI domain search and Expert AI analysis are integrated into your UBO Trace Engine
# Note: Duplicate domains are automatically filtered out - only the first occurrence is kept
# Expert AI agent provides confidence scores and domain rankings

# 1. Environment Setup
# Add to your .env file:
# SEARCHAPI_API_KEY=your_searchapi_api_key_here
# AGENT_EXPERT_DOMAIN=68f0ffd5a0dfaa3e0726523c
# SESSION_EXPERT_DOMAIN=68f0ffd5a0dfaa3e0726523c-losfuwfwcd

# 2. API Request Example
# POST /api/v1/trace
{
  "entity": "Louis Dreyfus Company Metals MEA DMCC",
  "ubo_name": "Liu Jianfeng", 
  "location": "UAE",
  "domain_name": "louisdreyfus.com"
}

# 3. Execute Trace
# POST /api/v1/trace/{trace_id}/execute

# 4. Get Results with SearchAPI Data
# GET /api/v1/trace/{trace_id}/summary

# Expected Response Structure with SearchAPI Integration:
{
  "trace_id": "uuid",
  "entity": "Louis Dreyfus Company Metals MEA DMCC",
  "ubo_name": "Liu Jianfeng",
  "location": "UAE",
  "overall_status": "completed",
  "stage_results": [
    {
      "stage": "stage_1a",
      "status": "completed",
      "facts": [...],
      "summary": "...",
      "apollo_enrichment": {...},
      "apollo_insights": {...},
      "searchapi_domain_search": {
        "success": true,
        "domains": [
          {
            "position": 1,
            "source": "Louis Dreyfus Company",
            "domain": "www.ldc.com",
            "snippet": "Official Communications: Legitimate emails from LDC will come from an email address with our company domain \"@ldc.com\"..."
          },
          {
            "position": 2,
            "source": "Louis Dreyfus Company",
            "domain": "www.ldc.com",
            "snippet": "Louis Dreyfus Company MEA Trading DMCC 99..."
          }
        ],
        "total_results": 10,
        "search_query": "Louis Dreyfus Company Metals MEA DMCC Liu Jianfeng official website domain",
        "search_params": {
          "company_name": "Louis Dreyfus Company Metals MEA DMCC",
          "ubo_name": "Liu Jianfeng",
          "location": "UAE",
          "country_code": "ae"
        }
      },
      "searchapi_domain_ownership": {
        "success": true,
        "domain": "louisdreyfus.com",
        "ownership_results": [...],
        "total_results": 5,
        "search_query": "site:louisdreyfus.com Louis Dreyfus Company Metals MEA DMCC Liu Jianfeng owner director"
      },
      "searchapi_related_domains": {
        "success": true,
        "related_domains": [...],
        "total_results": 8,
        "search_query": "Louis Dreyfus Company Metals MEA DMCC Liu Jianfeng UAE subsidiary parent company website domain"
      },
      "expert_domain_analysis": {
        "success": true,
        "expert_analysis": {
          "overall_confidence": 85,
          "domain_rankings": [
            {
              "domain": "ldc.com",
              "confidence": 95,
              "summary": "Primary corporate domain with high confidence",
              "reasoning": "Official domain, matches company name, verified content"
            },
            {
              "domain": "www.ldc.com",
              "confidence": 90,
              "summary": "Main website domain",
              "reasoning": "Consistent with corporate branding and official communications"
            }
          ],
          "confidence_scores": {
            "ldc.com": 95,
            "www.ldc.com": 90,
            "ae.kompass.com": 75
          },
          "analysis_summary": "Strong domain verification with high confidence in primary corporate domain. All major domains are legitimate and properly associated with the company.",
          "recommendations": [
            "Focus on ldc.com as primary domain for verification",
            "Verify subdomain relationships for regional operations",
            "Check domain ownership records for additional validation"
          ]
        },
        "raw_response": "Full Expert AI response...",
        "processing_time_ms": 2500
      }
    }
  ]
}

# 5. Key Benefits of SearchAPI Integration:
# - Structured domain search results with position, source, domain, snippet
# - Geographic targeting with location and country code
# - Domain ownership verification
# - Related domains discovery
# - Enhanced UBO tracing with web search capabilities
# - Complements existing Lyzr AI and Apollo.io services

# 6. Testing Commands:
# Run the test script: python test_searchapi_integration.py
# Use curl commands from: searchapi_test_commands.sh
# Test with Postman using the provided curl commands
