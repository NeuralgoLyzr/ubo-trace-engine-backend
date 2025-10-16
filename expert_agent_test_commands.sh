# Expert Domain Analysis - Direct API Test Commands
# These commands test the Expert Lyzr AI agent directly for domain analysis

# Replace YOUR_API_KEY with your actual Lyzr API key
# Agent ID: 68f0ffd5a0dfaa3e0726523c
# Session ID: 68f0ffd5a0dfaa3e0726523c-losfuwfwcd

# 1. Basic Expert Domain Analysis Test
curl -X POST 'https://agent-prod.studio.lyzr.ai/v3/inference/chat/' \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_API_KEY' \
  -d '{
    "user_id": "workspace2@wtw.com",
    "agent_id": "68f0ffd5a0dfaa3e0726523c",
    "session_id": "68f0ffd5a0dfaa3e0726523c-losfuwfwcd",
    "message": "company_name: Louis Dreyfus Company Metals MEA DMCC , UBO_name: Liu Jianfeng  , location: UAE

lyzr_agent_domains:{
  \"companies\": [
    {
      \"rank\": 1,
      \"domain\": \"ldc.com\",
      \"short_summary\": \"The official global domain for Louis Dreyfus Company, a multinational involved in agriculture, food processing, and commodity trading. Operates numerous regional and business unit subdomains.\",
      \"relation\": \"Primary corporate domain—parent to Louis Dreyfus Company Metals MEA DMCC and related regional entities.\"
    },
    {
      \"rank\": 2,
      \"domain\": \"ldc.com/gh/locations/\",
      \"short_summary\": \"Dedicated page listing LDC's locations in the Europe, Middle East & Africa region, relevant due to the UAE operation.\",
      \"relation\": \"Regional corporate domain—includes UAE/MEA presence.\"
    },
    {
      \"rank\": 3,
      \"domain\": \"ldc.com/ke/location/louis-dreyfus-company-mea-trading-dmcc/\",
      \"short_summary\": \"Subdomain providing specific information about Louis Dreyfus Company MEA Trading DMCC, the relevant UAE-registered entity.\",
      \"relation\": \"Direct domain for the MEA DMCC trading company in UAE.\"
    }
  ]
}

google_serp_domain:{
  \"domains\": [
    {
      \"position\": 1,
      \"source\": \"Louis Dreyfus Company\",
      \"domain\": \"www.ldc.com\",
      \"snippet\": \"Official Communications: Legitimate emails from LDC will come from an email address with our company domain @ldc.com...\"
    },
    {
      \"position\": 2,
      \"source\": \"Louis Dreyfus Company\",
      \"domain\": \"www.ldc.com\",
      \"snippet\": \"Louis Dreyfus Company India Private Limited Anchorage Building...\"
    },
    {
      \"position\": 3,
      \"source\": \"Kompass International\",
      \"domain\": \"ae.kompass.com\",
      \"snippet\": \"Louis Dreyfus Company MEA Trading DMCC is a trader, importer & exporter of agriculture products...\"
    }
  ]
}"
  }'

# 2. Test with Different Company
curl -X POST 'https://agent-prod.studio.lyzr.ai/v3/inference/chat/' \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_API_KEY' \
  -d '{
    "user_id": "workspace2@wtw.com",
    "agent_id": "68f0ffd5a0dfaa3e0726523c",
    "session_id": "68f0ffd5a0dfaa3e0726523c-losfuwfwcd",
    "message": "company_name: Avcon Jet Isle of Man Limited , UBO_name: Alexander Vagacs  , location: Isle of Man

lyzr_agent_domains:{
  \"companies\": [
    {
      \"rank\": 1,
      \"domain\": \"avconjet.com\",
      \"short_summary\": \"Official website for Avcon Jet, a private jet charter and aviation services company.\",
      \"relation\": \"Primary corporate domain for Avcon Jet Isle of Man Limited.\"
    }
  ]
}

google_serp_domain:{
  \"domains\": [
    {
      \"position\": 1,
      \"source\": \"Avcon Jet\",
      \"domain\": \"www.avconjet.com\",
      \"snippet\": \"Avcon Jet provides private jet charter services and aviation solutions...\"
    }
  ]
}"
  }'

# 3. Test with Minimal Data
curl -X POST 'https://agent-prod.studio.lyzr.ai/v3/inference/chat/' \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: YOUR_API_KEY' \
  -d '{
    "user_id": "workspace2@wtw.com",
    "agent_id": "68f0ffd5a0dfaa3e0726523c",
    "session_id": "68f0ffd5a0dfaa3e0726523c-losfuwfwcd",
    "message": "company_name: Test Company Limited , UBO_name: John Smith  , location: UK

lyzr_agent_domains:{
  \"companies\": []
}

google_serp_domain:{
  \"domains\": [
    {
      \"position\": 1,
      \"source\": \"Test Company\",
      \"domain\": \"www.testcompany.com\",
      \"snippet\": \"Test Company Limited official website...\"
    }
  ]
}"
  }'

# Expected Response Structure:
# {
#   "response": "JSON response with confidence scores and rankings",
#   "choices": [...],
#   "usage": {...}
# }

# Expected Expert Analysis Response:
# {
#   "overall_confidence": 85,
#   "domain_rankings": [
#     {
#       "domain": "ldc.com",
#       "confidence": 95,
#       "summary": "Primary corporate domain with high confidence",
#       "reasoning": "Official domain, matches company name, verified content"
#     }
#   ],
#   "confidence_scores": {
#     "ldc.com": 95,
#     "www.ldc.com": 90,
#     "ae.kompass.com": 75
#   },
#   "analysis_summary": "Strong domain verification with high confidence in primary corporate domain",
#   "recommendations": [
#     "Focus on ldc.com as primary domain",
#     "Verify subdomain relationships",
#     "Check domain ownership records"
#   ]
# }

# Integration Test with Your UBO Trace Engine:
# 1. Set AGENT_EXPERT_DOMAIN and SESSION_EXPERT_DOMAIN in your .env file
# 2. Run: python test_expert_domain_analysis.py
# 3. Create a trace and execute it to see Expert analysis in the response
# 4. Check the expert_domain_analysis field in stage results
