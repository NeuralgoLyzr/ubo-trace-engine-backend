# SearchAPI Google Domain Search - Test Commands
# These commands test the SearchAPI integration with your UBO Trace Engine
# Note: Duplicate domains are automatically filtered out - only first occurrence is kept

# Replace YOUR_API_KEY with your actual SearchAPI API key

# 1. Basic Domain Search with All Three Parameters
curl -X GET "https://www.searchapi.io/api/v1/search?engine=google&q=Louis+Dreyfus+Company+Metals+MEA+DMCC+Liu+Jianfeng+official+website+domain&location=United+Arab+Emirates&gl=ae" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

# 2. Domain Search with UBO Name Focus
curl -X GET "https://www.searchapi.io/api/v1/search?engine=google&q=Liu+Jianfeng+Louis+Dreyfus+Company+Metals+MEA+DMCC+UAE+website+domain&location=United+Arab+Emirates&gl=ae" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

# 3. Domain Ownership Verification
curl -X GET "https://www.searchapi.io/api/v1/search?engine=google&q=site:louisdreyfus.com+Louis+Dreyfus+Company+Metals+MEA+DMCC+Liu+Jianfeng+UAE+owner+director&location=United+Arab+Emirates&gl=ae" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

# 4. Related Domains Search
curl -X GET "https://www.searchapi.io/api/v1/search?engine=google&q=Louis+Dreyfus+Company+Metals+MEA+DMCC+Liu+Jianfeng+UAE+subsidiary+parent+company+website+domain&location=United+Arab+Emirates&gl=ae" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

# 5. Test with Different Location (Isle of Man)
curl -X GET "https://www.searchapi.io/api/v1/search?engine=google&q=Avcon+Jet+Isle+of+Man+Limited+Alexander+Vagacs+official+website+domain&location=Isle+of+Man&gl=im" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

# 6. Domain Search with Time Filter
curl -X GET "https://www.searchapi.io/api/v1/search?engine=google&q=Louis+Dreyfus+Company+Metals+MEA+DMCC+Liu+Jianfeng+UAE+website+domain+2023+2024+2025&location=United+Arab+Emirates&gl=ae" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

# 7. Company Registry Domain Search
curl -X GET "https://www.searchapi.io/api/v1/search?engine=google&q=site:companieshouse.gov.uk+Louis+Dreyfus+Company+Metals+MEA+DMCC+Liu+Jianfeng&location=United+Arab+Emirates&gl=ae" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

# 8. UAE Registry Domain Search
curl -X GET "https://www.searchapi.io/api/v1/search?engine=google&q=site:registry.gov+UAE+Louis+Dreyfus+Company+Metals+MEA+DMCC+Liu+Jianfeng&location=United+Arab+Emirates&gl=ae" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

# 9. News Search for Domain Information
curl -X GET "https://www.searchapi.io/api/v1/search?engine=google&q=Louis+Dreyfus+Company+Metals+MEA+DMCC+Liu+Jianfeng+UAE+website+domain+news&tbm=nws&location=United+Arab+Emirates&gl=ae" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

# 10. Comprehensive Domain Search
curl -X GET "https://www.searchapi.io/api/v1/search?engine=google&q=Louis+Dreyfus+Company+Metals+MEA+DMCC+Liu+Jianfeng+UAE+official+website+domain+homepage+corporate&location=United+Arab+Emirates&gl=ae&num=20" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

# Expected Response Structure:
# {
#   "search_metadata": { ... },
#   "search_parameters": { ... },
#   "search_information": { ... },
#   "organic_results": [
#     {
#       "position": 1,
#       "title": "...",
#       "link": "...",
#       "source": "...",
#       "domain": "...",
#       "snippet": "..."
#     }
#   ],
#   "related_questions": [ ... ],
#   "related_searches": [ ... ],
#   "pagination": { ... }
# }

# Integration Test with Your UBO Trace Engine:
# 1. Set SEARCHAPI_API_KEY in your .env file
# 2. Run: python test_searchapi_integration.py
# 3. Create a trace and execute it to see SearchAPI results in the response
