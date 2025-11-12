# UBO Trace Engine - Quick Reference Card

## 🚀 Agent IDs & Configuration

| Stage | Agent ID | Purpose | Time Scope |
|-------|----------|---------|------------|
| **Stage 1A** | `68e8dd6c3e9645375cfcfd86` | Multi-Stage Perplexity Search Engine - 1A | All-time |
| **Stage 1B** | `68ec33428be660f19f91cf3e` | Direct Evidence (Time-Scoped) | Jan 2023 - Present |
| **Stage 2A** | `68ec3536de8385f5b4326896` | Indirect Links (Structural) | All-time |
| **Stage 2B** | `68ec36368d106b3b3abba21b` | Indirect Links (Recent 2 years) | Jan 2023 - Present |
| **Domain Search** | `68edec6f9bc72912ffb59215` | Domain Search | N/A |
| **Domain Confidence** | `68f0ffd5a0dfaa3e0726523c` | Domain Search Confidence Score | N/A |

---

## 📊 Stage Characteristics

### Stage 1A: Multi-Stage Perplexity Search Engine - 1A
- ✅ Independent corporate-ownership investigator
- ✅ Verified registry filings
- ✅ Director/beneficial-owner records
- ✅ Official documents linking UBO to entity
- ✅ Publication dates required
- ✅ Exact source URLs
- ✅ Summary ≤500 characters

### Stage 1B: Direct Evidence (Time-Scoped)
- ⏰ Time-scoped: Jan 2023 - Present
- 🔍 Recent ownership filings
- 📅 Recent appointments
- 📊 Updated government databases
- ✅ Dated facts with exact source URLs

### Stage 2A: Indirect Links (Structural)
- 🔗 Layered ownership structures
- 🏢 Subsidiaries, holding firms
- 📊 Trusts, SPVs
- 👤 Nominee directors
- ✅ Verified, source-backed facts

### Stage 2B: Indirect Links (Recent 2 years)
- ⏰ Time-scoped: Jan 2023 - Present
- 🔄 Recent restructurings
- 📝 Trust amendments
- 🔀 Transfers, M&A
- 💼 Fund vehicles, affiliated directors

---

## 🔄 Execution Flow

```
1. Create Trace (POST /api/v1/trace)
   ↓
2. Execute Trace (POST /api/v1/trace/{trace_id}/execute)
   ↓
3. Stage 1A Execution (with parallel enrichments)
   ├─→ Lyzr Agent Call
   ├─→ Apollo Enrichment (parallel)
   ├─→ SearchAPI Domain Search (parallel)
   └─→ Expert Domain Analysis (parallel)
   ↓
4. Stage 1B Execution (same structure)
   ↓
5. Stage 2A Execution (same structure)
   ↓
6. Stage 2B Execution (same structure)
   ↓
7. Aggregate Results
   ├─→ Combine all stage results
   ├─→ Remove duplicates
   └─→ Calculate statistics
   ↓
8. Generate Summary
   └─→ Determine connection status
   ↓
9. Return Summary (GET /api/v1/trace/{trace_id}/summary)
```

---

## ⏱️ Performance Metrics

| Metric | Value |
|--------|-------|
| **Stage 1A Time** | ~45-60 seconds |
| **Stage 1B Time** | ~45-60 seconds |
| **Stage 2A Time** | ~45-60 seconds |
| **Stage 2B Time** | ~45-60 seconds |
| **Total Trace Time** | ~3-5 minutes |
| **Retry Attempts** | 3-4 per stage |
| **Retry Delay** | 5 seconds |
| **API Timeout** | 60-120 seconds |

---

## 🔌 Integration Endpoints

| Service | Endpoint | Purpose |
|---------|----------|---------|
| **Lyzr AI** | `https://agent-prod.studio.lyzr.ai/v3/inference/chat/` | Primary AI agent calls |
| **SearchAPI** | `https://www.searchapi.io/api/v1/search` | Google SERP domain search |
| **Apollo.io** | `https://api.apollo.io/v1/mixed_people/search` | People/company enrichment |
| **MongoDB** | `mongodb://localhost:27017` | Trace persistence |

---

## 📋 Request Format

```json
{
    "entity": "Company Name",
    "ubo_name": "Person Name",  // Optional
    "location": "UAE",  // Optional
    "domain_name": "example.com"  // Optional
}
```

---

## 📊 Response Format

### Connection Status Logic
```
if has_direct_evidence:
    → "DIRECT CONNECTION"
elif has_indirect_evidence:
    → "INDIRECT CONNECTION ONLY"
else:
    → "NO CONNECTION"
```

### Fact Format
```
"Fact (date) - Verified URL"
Example: "Liu Jianfeng appointed as director (Jan 15, 2023) - https://verified-source.com/document123"
```

### Summary Statistics
- `total_urls`: Total unique URLs found
- `total_direct_facts`: Count of direct evidence facts
- `total_indirect_facts`: Count of indirect evidence facts
- `connection_status`: Overall connection determination
- `stages_completed`: Number of stages completed (0-4)

---

## ⚠️ Error Handling

| Error Type | Handling |
|------------|----------|
| **API Call Failure** | Retry 3-4 times with 5s delay |
| **Zero Results** | Retry with different query |
| **Timeout** | Retry with extended timeout |
| **Network Error** | Retry with exponential backoff |
| **Stage Failure** | Continue other stages, mark as failed |

---

## 🔍 Key Statistics Per Stage

### Stage 1A Output
- Direct connections: `direct_connections[]`
- URLs found: `urls_found[]`
- Facts: `facts[]` (with dates and URLs)
- Summary: `summary` (≤500 chars)

### Stage 1B Output
- Same as Stage 1A, but time-filtered

### Stage 2A Output
- Indirect connections: `indirect_connections[]`
- URLs found: `urls_found[]`
- Facts: `facts[]` (with dates and URLs)
- Summary: `summary` (≤500 chars)

### Stage 2B Output
- Same as Stage 2A, but time-filtered

---

## 🎯 Key Differentiators

1. **Multi-Stage Specialized Investigation**
   - Each stage optimized for specific evidence type
   - Clear separation of direct vs indirect
   - Historical vs recent evidence

2. **Parallel Enrichment**
   - Apollo.io people search
   - SearchAPI domain search
   - Expert domain analysis
   - All run in parallel per stage

3. **Time-Scoped Analysis**
   - Stage 1A/2A: All-time historical evidence
   - Stage 1B/2B: Recent evidence (2023-present)
   - Comprehensive coverage

4. **Verified Sources**
   - All facts include exact source URLs
   - Publication dates required
   - Human-readable format

5. **Confidence Scoring**
   - Domain analysis with confidence scores
   - Ranked results by credibility
   - Reasoning provided for each score

---

## 📈 Use Case Examples

### Example 1: Complete UBO Trace
```bash
# 1. Create trace
POST /api/v1/trace
{
    "entity": "Louis Dreyfus Company Metals MEA DMCC",
    "ubo_name": "Liu Jianfeng",
    "location": "UAE"
}

# 2. Execute trace
POST /api/v1/trace/{trace_id}/execute

# 3. Get summary
GET /api/v1/trace/{trace_id}/summary
```

### Example 2: Domain Analysis
```bash
POST /api/v1/analyze-company-domains
{
    "company_name": "Company Name",
    "ubo_name": "Person Name",
    "address": "Company Address"
}
```

### Example 3: UBO Search
```bash
POST /api/v1/search-ubo
{
    "company_name": "Company Name",
    "location": "UAE",
    "include_full_analysis": true
}
```

---

## 🛠️ Technical Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI Agents**: Lyzr AI (Perplexity-powered)
- **External APIs**: SearchAPI, Apollo.io
- **Frontend**: React (TypeScript)
- **API Format**: RESTful JSON

---

## 📝 Quick Facts

- **Total Stages**: 4 (1A, 1B, 2A, 2B)
- **Parallel Enrichments**: 3 per stage (Apollo, SearchAPI, Expert)
- **Retry Logic**: 3-4 attempts per stage
- **Zero-Result Detection**: Automatic retry
- **Connection Status**: 3-tier (Direct, Indirect Only, No Connection)
- **Fact Format**: "Fact (date) - Verified URL"
- **Summary Length**: ≤500 characters
- **Database Collections**: `ubo_traces`, `trace_results`

---

## 🎯 Key Talking Points

1. **Why 4 Stages?**
   - Specialization: Each stage optimized for specific evidence type
   - Time-scoping: Historical vs recent evidence
   - Direct vs Indirect: Clear separation for comprehensive coverage

2. **Parallel Processing**
   - Reduces total execution time
   - Independent data sources
   - Better coverage
   - Fault tolerance

3. **Retry Logic**
   - Handles transient API issues
   - Improves result quality
   - Zero-result detection and retry
   - Better user experience

4. **Verified Sources**
   - All facts include exact source URLs
   - Publication dates required
   - Human-readable format
   - Machine-parseable structure

5. **Confidence Scoring**
   - Domain analysis with confidence scores
   - Ranked results by credibility
   - Reasoning provided for each score
   - Transparent evaluation

---

## 🔗 Quick Links

- **API Docs**: `http://localhost:8000/docs`
- **Solution Flow**: `SOLUTION_FLOW_DEEP_DIVE.md`
- **Presentation Outline**: `DEEP_DIVE_PRESENTATION_OUTLINE.md`
- **Backend Code**: `/Users/abhishekkumar/Desktop/ubo-trace-engine-backend/`
- **Frontend Code**: `/Users/abhishekkumar/Desktop/ubo-trace-engine-frontend/`

---

**Keep this handy during your deep dive call!** 📚


