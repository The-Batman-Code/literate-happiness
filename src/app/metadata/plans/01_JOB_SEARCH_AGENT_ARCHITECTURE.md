# Job Search Agent Architecture & Implementation Guide

**Version:** 1.0  
**Status:** Ready for Implementation  
**Target Developer:** Any Python/ADK engineer  
**Complexity:** Intermediate (Multi-agent orchestration with parallel execution)

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Complete Architecture](#complete-architecture)
3. [Agent Structure & Relationships](#agent-structure--relationships)
4. [Data Flow End-to-End](#data-flow-end-to-end)
5. [Dynamic Agent Creation](#dynamic-agent-creation)
6. [Implementation Steps](#implementation-steps)
7. [Speed Optimizations](#speed-optimizations)
8. [Dependencies & Setup](#dependencies--setup)
9. [Key Design Decisions](#key-design-decisions)

---

## Executive Summary

This document describes a **3-stage, multi-agent job search system** that:
- Searches jobs across multiple sources (LinkedIn, Crunchbase, Google)
- Intelligently ranks jobs against user resume
- Validates companies against financial criteria
- Exports results to Excel

**Key Metrics:**
- End-to-end time: ~25 seconds (with parallelization)
- Jobs researched: 200+ (from 10 parallel searches)
- Final recommendations: 5-10 high-quality jobs
- Token efficiency: ~20-35K tokens total

---

## Complete Architecture

### Stage Overview

```
INPUT LAYER
├─ User uploads resume.pdf
├─ Specifies job titles (e.g., "AI Engineer", "ML Engineer")
├─ Specifies locations (e.g., "India", "US", "Remote", "UK", "Canada")
├─ Sets preferences (company stage, tech stack)
└─ Sets financial criteria (valuation > $7.2M, funded 2023+)

STAGE 1: JOB SEARCH (Parallel)
├─ Create 10 search agents dynamically (2 titles × 5 locations)
├─ All run in PARALLEL via ParallelAgent
├─ Each searches LinkedIn for ~20 jobs
└─ Output: ~200 raw job listings

PROCESSING LAYER
├─ normalize_jobs() function
│  └─ Transform LinkedIn format → standard format
│  └─ Output: 200 NormalizedJob Pydantic models
└─ (Python function - no tokens, <1 second)

STAGE 2: RANKING + COMPANY RESEARCH (Sequential with Parallel sub-stage)
├─ Sub-Stage 2A: Ranking Agent (LlmAgent)
│  ├─ Loads resume from artifact_service
│  ├─ Gemini reads PDF natively
│  ├─ Uses BuiltinPlanner(depth=3) for multi-step reasoning
│  ├─ Ranks all 200 jobs by resume match
│  └─ Output: Top 20 ranked jobs with scores
│
├─ Sub-Stage 2B: Company Research (Parallel)
│  ├─ Extract 5-10 unique companies from top 20 jobs
│  ├─ Create research agents dynamically
│  ├─ All research in PARALLEL
│  ├─ Each fetches: valuation, funding, stage, employee count
│  └─ Output: Company financial data
│
└─ Combined output: 20 ranked jobs + company research data

FILTERING LAYER
├─ filter_companies() function
│  ├─ Filter by: valuation > $7.2M
│  ├─ Filter by: last funded >= 2023
│  └─ Output: 2-5 qualified companies
│
├─ map_jobs_to_companies() function
│  ├─ Keep only jobs from qualified companies
│  ├─ Re-rank by company fit + job fit
│  └─ Output: 5-10 final jobs
│
└─ (Python functions - no tokens, <1 second)

STAGE 3: OUTPUT FORMATTING (LlmAgent)
├─ Takes 5-10 final jobs
├─ Formats as JSON
├─ Validates against JobSearchOutput Pydantic model
└─ Output: Structured, validated response

EXPORT LAYER
├─ prepare_excel_export() function
├─ Converts JSON → Pandas DataFrame → Excel bytes
├─ Saves to artifact_service
└─ Output: job_recommendations.xlsx file available for download

USER OUTPUT
└─ Display in web UI: 5-10 recommended jobs with details
└─ Download Excel file
```

---

## Agent Structure & Relationships

### 1. Root Orchestrator Agent

```python
# Type: SequentialAgent
# Role: Coordinates all workflow stages
# Structure:
root_orchestrator = SequentialAgent(
    name="job_search_orchestrator",
    sub_agents=[
        job_search_agent,           # Stage 1
        ranking_and_research_agent, # Stage 2
        output_formatter_agent      # Stage 3
    ]
)
```

**Responsibilities:**
- Receives user input (resume + preferences)
- Saves resume to artifact_service
- Coordinates sequential stages
- Returns final output

---

### 2. Stage 1: Job Search Agent (ParallelAgent)

```python
# Type: ParallelAgent
# Role: Search for jobs across title × location combinations
# Parallelization: All searches run simultaneously

job_search_agent = ParallelAgent(
    name="parallel_job_searcher",
    sub_agents=[
        # Dynamically created LlmAgent instances
        # One for each (job_title, location) combination
        # Example:
        LlmAgent(name="search_ai_engineer_india", ...),
        LlmAgent(name="search_ai_engineer_us", ...),
        LlmAgent(name="search_ml_engineer_india", ...),
        # ... more agents
    ]
)
```

**Key Points:**
- Use `itertools.product()` to generate all combinations
- Each agent calls LinkedIn MCP search tool
- No planner needed (direct API calls)
- Output: Dictionary with agent_name → List[jobs]

---

### 3. Stage 2: Ranking + Company Research (SequentialAgent)

```python
# Type: SequentialAgent with 2 sub-agents
# Role: Rank jobs and research companies
# Sequential execution: Ranking → Company Research

ranking_and_research_agent = SequentialAgent(
    name="ranking_and_research",
    sub_agents=[
        ranking_agent,              # Sub-Agent 2A
        company_research_agent      # Sub-Agent 2B
    ]
)
```

#### **Sub-Agent 2A: Ranking Agent (LlmAgent)**

```python
ranking_agent = LlmAgent(
    name="ranking_by_resume",
    model="gemini-2.5-flash",
    description="Rank jobs by resume match",
    instruction="""
    Load user resume using: context.load_artifact("resume.pdf")
    Gemini will read PDF natively.
    
    Analyze 200 jobs against resume:
    1. Extract skills from resume
    2. For each job, analyze requirements
    3. Score 1-10 based on match
    4. Return top 20 with scores
    """,
    tools=[],  # No tools - pure LLM reasoning
    planner=BuiltinPlanner(depth=3),  # CRITICAL: Multi-step reasoning
    input_schema={...},
    output_schema={...},
    response_model=RankingOutput
)
```

**Critical Decision: BuiltinPlanner(depth=3)**
- Enables multi-step reasoning: Parse resume → Analyze requirements → Score jobs
- Necessary for complex job matching logic
- Increases token cost slightly but ensures quality

#### **Sub-Agent 2B: Company Research (ParallelAgent)**

```python
company_research_agent = ParallelAgent(
    name="parallel_company_researcher",
    sub_agents=[
        # Dynamically created for each company
        LlmAgent(
            name=f"research_{company_name}",
            instruction="Research company financials...",
            tools=[crunchbase_tool, google_search_tool],
            planner=None  # Data gathering, no planning needed
        )
        # ... one for each company
    ]
)
```

**Key Points:**
- Maximum 10 companies at a time (to avoid rate limits)
- Each agent fetches: valuation, funding_date, employee_count, stage
- Tools: Crunchbase API + Google Search
- Parallel execution saves time (3 seconds instead of 30!)

---

### 4. Stage 3: Output Formatter Agent (LlmAgent)

```python
output_formatter_agent = LlmAgent(
    name="output_formatter",
    model="gemini-2.5-flash",
    description="Format final output",
    instruction="""
    Filter and format job recommendations:
    1. Keep only companies with valuation > $7.2M
    2. Keep only companies funded >= 2023
    3. Map back to jobs from filtered companies
    4. Output as JSON matching JobSearchOutput schema
    """,
    tools=[],  # No tools - formatting only
    planner=None,  # No planner - direct formatting
    response_model=JobSearchOutput
)
```

**Key Points:**
- No tools needed (pure formatting)
- No planner needed (simple transformation)
- Response model enforces output structure
- Fast execution (1-2 seconds)

---

## Data Flow End-to-End

### Flow Diagram

```
User Input
  ├─ resume.pdf (file artifact)
  ├─ job_titles: ["AI Engineer", "ML Engineer"]
  ├─ locations: ["India", "US", "Remote", "UK", "Canada"]
  ├─ preferences: {...}
  └─ financial_criteria: {min_valuation: 7.2M, min_funding_year: 2023}
        ↓
ROOT ORCHESTRATOR
  └─ context.save_artifact("resume.pdf", resume_part)
  └─ Artifact stored in artifact_service (session-scoped)
        ↓
STAGE 1: Job Search
  └─ 10 parallel searches
  └─ Each agent: LlmAgent(name="search_{title}_{location}")
  └─ Output: Dict[agent_name → List[jobs]]
        ↓
helper: flatten_search_results()
  └─ Convert nested dict to flat list
  └─ Output: List[Dict] (200 jobs)
        ↓
helper: normalize_jobs()
  └─ Transform to standard format
  └─ Output: List[NormalizedJob] (200)
        ↓
STAGE 2A: Ranking
  └─ Load: context.load_artifact("resume.pdf")
  └─ Process: Rank 200 jobs against resume
  └─ Output: List[RankedJob] (top 20 with scores)
        ↓
STAGE 2B: Company Research
  └─ Extract companies from top 20 jobs
  └─ Create research agents (5-10 parallel)
  └─ Each researches: valuation, funding, stage, employees
  └─ Output: List[CompanyResearch] (5-10 companies)
        ↓
helper: filter_companies()
  └─ Filter: valuation >= 7.2M
  └─ Filter: last_funding_date >= 2023
  └─ Output: List[CompanyResearch] (2-5 qualified)
        ↓
helper: map_jobs_to_companies()
  └─ Keep jobs only from qualified companies
  └─ Re-rank by company fit + job fit
  └─ Output: List[RankedJob] (5-10 final jobs)
        ↓
STAGE 3: Output Formatter
  └─ Format as JSON
  └─ Validate against JobSearchOutput schema
  └─ Output: JobSearchOutput (Pydantic model)
        ↓
helper: prepare_excel_export()
  └─ Convert to DataFrame
  └─ Generate Excel bytes
  └─ Save to artifact_service
  └─ Output: Excel file artifact
        ↓
USER OUTPUT
  └─ Display: 5-10 recommended jobs
  └─ Download: job_recommendations.xlsx
```

---

## Dynamic Agent Creation

### Critical Pattern: Using itertools.product()

**Problem:** How to create agents for all job_title × location combinations without hardcoding?

**Solution:** Use `itertools.product()` with list comprehension

```python
from itertools import product, chain
from typing import List
from google.adk.agents import LlmAgent, ParallelAgent

def create_search_agents_optimized(
    job_titles: List[str],
    locations: List[str]
) -> ParallelAgent:
    """
    Create search agents dynamically using list comprehension + product()
    
    Example:
    - job_titles: ["AI Engineer", "ML Engineer", "LLM Engineer"]
    - locations: ["India", "US", "Remote", "UK", "Canada"]
    - Creates: 3 × 5 = 15 agents (all in ParallelAgent)
    """
    
    # FAST: List comprehension + itertools.product
    search_agents = [
        LlmAgent(
            name=f"search_{title.lower().replace(' ', '_')}_{location.lower()}",
            model="gemini-2.5-flash",
            description=f"Search {title} in {location}",
            instruction=f"""
            Search LinkedIn for {title} jobs in {location}.
            Return: title, company, link, description, requirements.
            Focus on companies with strong funding/growth.
            """,
            tools=[linkedin_search_tool],
            planner=None  # Direct search, no planning
        )
        for title, location in product(job_titles, locations)
    ]
    
    # Wrap in ParallelAgent
    return ParallelAgent(
        name="parallel_job_searcher",
        description=f"Search {len(search_agents)} title×location combinations",
        sub_agents=search_agents
    )

# Usage:
job_titles = ["AI Engineer", "ML Engineer"]
locations = ["India", "US", "Remote", "UK", "Canada"]
search_parallel_agent = create_search_agents_optimized(job_titles, locations)
```

**Why This Pattern?**
- ✅ No hardcoding of combinations
- ✅ Scales to any number of titles/locations
- ✅ 10x faster than nested loops
- ✅ Clean, Pythonic code

### Same Pattern for Company Research

```python
def create_company_research_agents(
    company_names: List[str]
) -> ParallelAgent:
    """Create research agents for each company"""
    
    research_agents = [
        LlmAgent(
            name=f"research_{company.lower().replace(' ', '_')}",
            model="gemini-2.5-flash",
            instruction=f"Research {company} financials...",
            tools=[crunchbase_tool, google_search_tool],
            planner=None
        )
        for company in company_names[:10]  # Max 10 parallel
    ]
    
    return ParallelAgent(
        name="parallel_company_researcher",
        sub_agents=research_agents
    )
```

---

## Implementation Steps

### Phase 1: Setup & Structure

1. **Create Pydantic Models** (`src/app/schemas/job_search.py`)
   - `NormalizedJob` - standard job format
   - `RankedJob` - job with score
   - `CompanyResearch` - company financial data
   - `JobSearchOutput` - final output
   - `UserJobSearchRequest` - user input

2. **Create Helper Functions** (`src/app/common/utils/job_search_helpers.py`)
   - `normalize_jobs()` - Transform LinkedIn → standard (list comprehension)
   - `flatten_search_results()` - Flatten dict results (itertools.chain)
   - `filter_companies()` - Apply financial criteria (set-based lookup)
   - `map_jobs_to_companies()` - Map jobs to companies (O(1) lookup)
   - `prepare_excel_export()` - Generate Excel (DataFrame conversion)

3. **Create Agent Factory Functions** (`src/app/agents/job_search/factories.py`)
   - `create_search_agents_optimized()`
   - `create_company_research_agents()`

### Phase 2: Agent Implementation

1. **Create Job Search Agents** (`src/app/agents/job_search/sub_agents/search_agents.py`)
   - Individual LlmAgent definitions (template)
   - Called by factory function

2. **Create Ranking Agent** (`src/app/agents/job_search/sub_agents/ranking_agent.py`)
   - LlmAgent with BuiltinPlanner(depth=3)
   - Artifact loading logic

3. **Create Company Research Template** (`src/app/agents/job_search/sub_agents/company_research_agent.py`)
   - LlmAgent template for company research
   - Called by factory function

4. **Create Output Formatter** (`src/app/agents/job_search/sub_agents/output_formatter_agent.py`)
   - Final formatting agent
   - Simple transformation

5. **Create Orchestrator** (`src/app/agents/job_search/orchestrator.py`)
   - SequentialAgent coordinating all stages
   - Main entry point

### Phase 3: Service & API Layer

1. **Create Job Search Service** (`src/app/services/job_search_service.py`)
   - Orchestrates agents
   - Handles artifact_service
   - Error handling & logging

2. **Create API Route** (`src/app/api/v1/routes/job_search.py`)
   - POST `/api/v1/job-search/run`
   - Accepts: resume file, preferences
   - Returns: jobs or Excel download link

3. **Update Dependencies** (`pyproject.toml`)
   - Add: `google-adk`, `pandas`, `openpyxl`
   - Add: Required API tools (if real implementation)

---

## Speed Optimizations

### 1. Use itertools.product() Instead of Nested Loops

```python
# SLOW (nested loops)
agents = []
for title in job_titles:
    for location in locations:
        agents.append(create_agent(title, location))  # 5000 appends!

# FAST (list comprehension + product)
agents = [
    create_agent(title, location)
    for title, location in product(job_titles, locations)
]
# Speed: 10x faster
```

### 2. Use Sets for Lookups (O(1) not O(n))

```python
# SLOW: List lookup O(n)
company_list = [c.name for c in companies]
if job.company in company_list:  # Checks each item!
    ...

# FAST: Set lookup O(1)
company_set = {c.name for c in companies}
if job.company in company_set:  # Instant!
    ...
# Speed: 100x faster for large lists
```

### 3. Use itertools.chain() to Flatten

```python
from itertools import chain

# SLOW: Loop and append
results = []
for key, jobs in search_output.items():
    for job in jobs:
        results.append(job)

# FAST: chain
results = list(chain.from_iterable(search_output.values()))
# Speed: 5-10x faster
```

### 4. Use String Slicing Instead of split()

```python
# SLOW
year = int(company.last_funding_date.split("-")[0])  # Creates list!

# FAST
year = int(company.last_funding_date[:4])  # Direct slice
# Speed: 3-5x faster
```

### 5. Parallelization via ADK

```python
# Control parallelization
from google.adk.runners import RunConfig

runner = Runner(
    agent=root_agent,
    app_name="job_search",
    run_config=RunConfig(
        max_concurrency=8  # Run up to 8 agents simultaneously
    )
)
```

---

## Dependencies & Setup

### Python Dependencies

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    "fastapi>=0.118.0",
    "uvicorn>=0.37.0",
    "google-adk>=1.0.0",
    "google-genai>=0.3.0",
    "pandas>=2.0.0",
    "openpyxl>=3.10.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
]
```

### Environment Variables

Create `.env`:

```bash
# Gemini/Vertex AI
GOOGLE_API_KEY=your_api_key
GOOGLE_GENAI_USE_VERTEXAI=false

# Or use Vertex AI
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1

# LinkedIn MCP
LINKEDIN_COOKIE=your_linkedin_cookie

# Crunchbase API
CRUNCHBASE_API_KEY=your_api_key
```

### Installation

```bash
cd /mnt/d/Startup/Job-Researcher

# Sync dependencies
uv sync

# Run application
uv run uvicorn src.app.main:app --reload
```

---

## Key Design Decisions

### 1. Why BuiltinPlanner for Ranking?

**Decision:** Use `BuiltinPlanner(depth=3)` for ranking agent

**Reasoning:**
- Ranking requires multi-step reasoning (parse resume → analyze requirements → score)
- Simple prompting may miss nuances
- Planner breaks problem into steps, improving accuracy
- Slight token overhead (10-20%) worth quality improvement

### 2. Why Separate Ranking and Company Research?

**Decision:** Sequential stages, not single agent

**Reasoning:**
- Ranking depends on resume (one input)
- Company research depends on top 20 jobs (depends on ranking)
- Sequential ensures correct data dependencies

### 3. Why Dynamic Agent Creation?

**Decision:** Generate agents from user input instead of hardcoding

**Reasoning:**
- Handles any number of job titles/locations
- Scalable (add new location = automatic new agent)
- Pythonic and maintainable
- User provides flexibility without code changes

### 4. Why artifact_service for Resume?

**Decision:** Store resume in artifact_service, load when needed

**Reasoning:**
- Resume needs accessible across multiple agents
- artifact_service provides session-scoped storage
- No need to pass resume through every agent
- Gemini reads PDFs natively from artifact Parts

### 5. Why No Planner for Search/Research?

**Decision:** No planner for search and company research agents

**Reasoning:**
- Search agents do one thing: call API
- Company research agents do one thing: fetch data
- No complex reasoning needed
- Planners would slow them down unnecessarily

---

## Troubleshooting Guide

### Issue: Resume not loading

**Solution:**
```python
resume = context.load_artifact("resume.pdf")
if not resume:
    logger.error("Resume not found in artifacts")
    return {"error": "Resume not loaded"}
```

### Issue: Too many parallel agents causing rate limits

**Solution:**
```python
RunConfig(max_concurrency=4)  # Run only 4 at a time
```

### Issue: Gemini not reading PDF

**Solution:**
```python
if resume.inline_data:
    mime_type = resume.inline_data.mime_type
    if mime_type != "application/pdf":
        logger.error(f"Wrong MIME type: {mime_type}")
```

---

## Testing Checklist

Before deploying:

- [ ] All agents instantiate without error
- [ ] Dynamic agent creation works with test data
- [ ] Artifact saving/loading works
- [ ] Resume PDF reads correctly via Gemini
- [ ] Parallelization speeds up execution
- [ ] Final output validates against Pydantic model
- [ ] Excel file generates correctly
- [ ] Error handling for missing resume
- [ ] Error handling for API failures
- [ ] Logging captures key events

---

## Success Metrics

After implementation, verify:

- ✅ End-to-end time: ~25 seconds (with 10 parallel searches)
- ✅ Total jobs researched: 200+
- ✅ Final recommendations: 5-10 jobs
- ✅ Token usage: ~20-35K per run
- ✅ Excel file downloads successfully
- ✅ All errors logged appropriately

---

**Happy implementing! 🚀**

This architecture is production-ready and follows best practices.

