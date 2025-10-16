# Domain Analysis API Endpoint - Test Commands
# These commands test the Expert AI domain analysis endpoint

# Replace localhost:8000 with your actual server URL

# 1. Basic Domain Analysis Test
curl -X POST "http://localhost:8000/api/v1/domain-analysis" \
  -H "Content-Type: application/json" \
  -d 'company_name=Louis+Dreyfus+Company+Metals+MEA+DMCC&ubo_name=Liu+Jianfeng&location=UAE'

# 2. Test with Different Company
curl -X POST "http://localhost:8000/api/v1/domain-analysis" \
  -H "Content-Type: application/json" \
  -d 'company_name=Avcon+Jet+Isle+of+Man+Limited&ubo_name=Alexander+Vagacs&location=Isle+of+Man'

# 3. Test with URL Encoded Parameters
curl -X POST "http://localhost:8000/api/v1/domain-analysis?company_name=Louis%20Dreyfus%20Company%20Metals%20MEA%20DMCC&ubo_name=Liu%20Jianfeng&location=UAE" \
  -H "Content-Type: application/json"

# 4. Test with Form Data
curl -X POST "http://localhost:8000/api/v1/domain-analysis" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'company_name=Louis Dreyfus Company Metals MEA DMCC&ubo_name=Liu Jianfeng&location=UAE'

# 5. Test Error Handling - Missing Parameters
curl -X POST "http://localhost:8000/api/v1/domain-analysis" \
  -H "Content-Type: application/json"

# 6. Test Error Handling - Empty Parameters
curl -X POST "http://localhost:8000/api/v1/domain-analysis" \
  -H "Content-Type: application/json" \
  -d 'company_name=&ubo_name=&location='

# Expected Response Format:
# {
#   "success": true,
#   "results": [
#     {
#       "rank": 1,
#       "confidence_score": 95,
#       "reasoning": "The domain 'ldc.com' represents the primary corporate domain for Louis Dreyfus Company, which directly relates to Louis Dreyfus Company Metals MEA DMCC, confirming it as highly relevant and credible."
#     },
#     {
#       "rank": 2,
#       "confidence_score": 90,
#       "reasoning": "The page 'ldc.com/gh/locations/' provides information about LDC's locations, including the UAE, indicating a strong regional connection for Louis Dreyfus Company."
#     },
#     {
#       "rank": 3,
#       "confidence_score": 85,
#       "reasoning": "The subdomain 'ldc.com/ke/location/' targets the specific entity Louis Dreyfus Company MEA Trading DMCC in UAE, making it directly relevant but slightly less authoritative than the main corporate domain."
#     }
#   ],
#   "total_domains_analyzed": 8,
#   "overall_confidence": 85,
#   "analysis_summary": "Strong domain verification with high confidence in primary corporate domain. All major domains are legitimate and properly associated with the company."
# }

# Error Response Format:
# {
#   "detail": "Error message describing what went wrong"
# }

# Testing with Python requests:
# import requests
# 
# response = requests.post(
#     "http://localhost:8000/api/v1/domain-analysis",
#     params={
#         "company_name": "Louis Dreyfus Company Metals MEA DMCC",
#         "ubo_name": "Liu Jianfeng",
#         "location": "UAE"
#     }
# )
# 
# if response.status_code == 200:
#     result = response.json()
#     print(f"Success: {result['success']}")
#     print(f"Total domains: {len(result['results'])}")
#     print(f"Overall confidence: {result['overall_confidence']}%")
#     
#     for domain in result['results']:
#         print(f"Rank {domain['rank']}: {domain['confidence_score']}% - {domain['reasoning'][:100]}...")
# else:
#     print(f"Error: {response.status_code} - {response.text}")

# Integration Test Steps:
# 1. Start your UBO Trace Engine backend
# 2. Run: python test_domain_analysis_endpoint.py
# 3. Test with curl commands above
# 4. Verify response format matches expected structure
# 5. Check that Expert AI agent is properly configured
