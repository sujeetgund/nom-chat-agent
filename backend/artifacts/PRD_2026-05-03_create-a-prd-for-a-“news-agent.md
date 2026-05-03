## 1. Overview  
The **News Agent** is an automated daily system that runs every morning to collect, extract, and curate **trending AI news** from a configurable set of popular media websites. It performs a web discovery step limited to the **last 24 hours**, scrapes the relevant articles with graceful failure handling, ranks and filters results for relevance, deduplicates near-identical stories, and generates **concise, faithful summaries** grounded in the scraped content. Each day the user receives a structured briefing containing **top headlines (3–7)**, per-item summaries, “why it matters,” and **source links for verification**, while maintaining a **history log** of recent runs for transparency and auditability.

---

## 2. Goals & Non-Goals  

### Goals
- Automatically produce a **daily morning briefing** for the user.
- Discover and prioritize **trending AI-related news** (AI, generative AI, LLMs, AI policy, research breakthroughs).
- Scrape and extract key article fields: **title, publisher, publish time, main text/key paragraphs**.
- Generate summaries that are **faithful to the source**; avoid fabrication.
- Deduplicate near-duplicate stories and keep the **best/most complete source** per cluster.
- Present results in a clear, readable format with **links back to sources**.
- Maintain run **history** (at least **N days**) including success/failure metrics and outputs.
- Provide configurability for **target websites**, **keywords**, **time window**, and **notification method**.

### Non-Goals
- Not a real-time news feed; it is **daily (once per day)**.
- Not building a general-purpose web crawler for all websites on the internet.
- Not guaranteeing coverage of every AI story; focus is **curation quality** over exhaustive scraping.
- Not building a full “personalized” recommender beyond keyword/topic relevance for MVP.
- Not guaranteeing full compatibility with every website’s DOM/layout (graceful degradation is acceptable).

---

## 3. User Stories  
- **As a user (Sujeet),** I want a daily morning summary of the most important trending AI news **so that** I can catch up quickly without searching.  
- **As a user (Sujeet),** I want each news item to include a brief summary and a “why it matters” note **so that** I can understand significance fast and verify via source links.  
- **As a user (Sujeet),** I want the briefing to avoid near-duplicate stories **so that** I don’t waste time reading repeated coverage.  
- **As an admin,** I want to configure the target media websites and keyword filters **so that** the briefing matches my interests and scope.  
- **As an admin,** I want to control the time window (default last 24 hours) **so that** the briefing stays fresh and aligned with the daily run.  
- **As an admin,** I want to view run logs and statistics (articles found/scraped/summarized) **so that** I can troubleshoot failures and improve quality.  
- **As a user (Sujeet),** I want the system to clearly indicate when an article lacks sufficient context for summarization **so that** I can trust the briefing’s accuracy.  

---

## 4. Functional Requirements  

### A) Scheduling & Inputs
1. **Daily Scheduler:** Trigger the pipeline once per day in the morning (timezone configurable; default pending decision).
2. **Configurable Target Sites:** Allow user/admin to maintain a list of target popular media websites.
3. **Optional Keyword Filters:** Support keyword lists (default includes “AI” plus closely related categories).
4. **Configurable Time Window:** Default to “last 24 hours,” but allow adjustment via configuration.
5. **Notification Method (TBD):** Route the final report to the selected delivery channel (email/Slack/dashboard—open question).

### B) Web Discovery / Search (last 24 hours only)
6. Use web search to locate relevant articles limited to the configured time window (default last 24 hours).
7. Constrain discovery to items likely belonging to the configured target websites (via domain filtering and/or search constraints).
8. Store discovered candidate list (URLs + metadata as returned by search) for traceability.

### C) Scraping & Extraction
9. For each candidate URL, attempt extraction of:
   - title  
   - publisher/site name  
   - publish time  
   - main text (or key paragraphs)  
10. Handle common page layouts (e.g., article body extraction, stripping nav/ads) using robust heuristics.
11. **Graceful failure:** If extraction fails (blocked, malformed HTML, empty body), mark item with failure reason and continue pipeline.
12. Produce an “extracted context” blob used for summarization; do not summarize from missing/insufficient text.

### D) Filtering & Ranking
13. Compute a relevance score based on:
   - topic match (AI + related categories)  
   - keyword overlap / semantic similarity (implementation detail TBD)  
   - newsworthiness signals (lightweight heuristics; e.g., presence of AI keywords in title/lead, recency, and source quality weighting)
14. Exclude:
   - irrelevant topics  
   - low-quality pages (e.g., thin content, broken extracts, promotional pages)  
15. Output a ranked list and select the top candidate set for summarization.

### E) Summarization (faithful + grounded)
16. Generate a short per-item summary (1–3 sentences) grounded in the extracted content.
17. If extracted context is insufficient to support a faithful summary, label the summary as:
   - “insufficient source context”  
   and avoid generating speculative/fabricated details.
18. Generate an additional sentence for **“why it matters / relevance”** grounded in the article context.

### F) Deduplication & Clustering
19. Identify near-duplicate stories across candidates (same event reported by multiple outlets, syndicated copies, or paraphrased re-posts).
20. Cluster duplicates and select **one** representative per cluster using a “best completeness” rule:
   - prefers more complete extracts, higher relevance score, and/or more reliable publish time.
21. Preserve discarded items as metadata (for audit) but do not show them in the final top 3–7 list.

### G) Presentation (daily report format)
22. Produce a structured report containing **3–7 top headlines**.
23. For each item in the report, include:
   - headline/title  
   - publisher  
   - publish time (as extracted)  
   - 1–3 sentence summary  
   - 1 sentence “why it matters” / relevance  
   - source URL link (clickable)
24. Clearly indicate items with insufficient context (if any are included) and avoid hiding failures silently.

### H) Observability & Logging
25. Log per-run pipeline statistics:
   - number found via search  
   - number attempted to scrape  
   - number successfully extracted  
   - number summarized  
   - number deduplicated/clusters created  
   - error counts (by stage, if possible)
26. Log each article’s processing status with reason codes (e.g., blocked_by_robots, parse_error, empty_body, summarization_insufficient_context).
27. Capture a minimal audit trail linking: discovered URL → extracted context snapshot hash/ID → summary output.

### I) Configurability (Admin/User)
28. Provide an interface/config mechanism to update:
   - target sites list  
   - keywords  
   - time window  
   - notification method (TBD)
29. Validate configuration inputs and report misconfigurations without breaking the daily job.

---

## 5. Non-Functional Requirements  

### Performance
- **Daily completion target (MVP):** Generate and deliver the report within **60–90 minutes** from scheduled start under normal conditions (configurable concurrency limits).
- **Timeouts & retries:**  
  - scraping attempts per URL must have strict timeouts  
  - retry transient failures up to a small fixed number (e.g., 1–2)  
- **Throughput target (example):** Handle ~**50–150** discovered candidates per day (scales based on configuration).

### Reliability
- Daily job must complete even with partial failures.
- If the job fails entirely, send a failure notification stating the reason category and last successful stage (and fall back to last good report if feasible).

### Safety / Accuracy
- Summaries must be grounded in extracted content.
- Must refuse/withhold when context is insufficient (“insufficient source context”).
- Avoid quoting or inventing details not present in extracted text.

### Security
- Secure storage of config and any credentials for delivery channels.
- URL handling must prevent SSRF-style attacks (e.g., block internal IP ranges; restrict to http/https; validate allowed domains).
- Logging must avoid storing sensitive content unnecessarily (e.g., avoid full scraped text in logs).

### Scalability
- Pipeline should support increasing target sites/keywords without redesign.
- Use asynchronous processing for scraping and summarization stages where possible.
- Deduplication must be efficient enough for daily candidate volumes (approx. 100s items).

### Compliance
- Respect **robots.txt** and site terms “as feasible”:
  - implement robots.txt checks before scraping
  - include a compliance mode to skip disallowed paths
- If direct scraping is blocked, fall back to alternative extraction methods only when allowed (implementation TBD).

---

## 6. Out of Scope  
- No continuous real-time monitoring; only **daily** runs.  
- No user-specific personalization beyond topic/keyword relevance in MVP.  
- No posting to social platforms or building a public “news page” unless chosen for notification/presentation later.  
- No building a full citation graph across all articles.  
- No guaranteed extraction accuracy for every target site; best-effort with clear failure messaging is acceptable.  
- No long-term archival of full scraped article bodies unless explicitly decided (see Open Questions).

---

## 7. Open Questions  
1. **Delivery channel (TBD):** Email vs Slack vs in-app dashboard? What is the preferred UX?  
2. **Timezone:** What “morning” means for Sujeet (and whether timezone is configurable per user)?  
3. **Exact set of “popular media websites”:** Which sites are in the initial configurable list? Who maintains it?  
4. **Level of detail:** Do we want only the brief summary + why-it-matters, or also include 1–2 bullet key takeaways per item?  
5. **Scraped text storage:**  
   - Store full scraped text for traceability, or only extracted/summary artifacts?  
6. **Deduplication strategy details:** What threshold defines “near-duplicate” for MVP?  
7. **Compliance approach:** Are there specific constraints (e.g., strict robots-only; user consent; allowlist-only domain scraping)?  
8. **Search provider:** Which web search mechanism will be used (internal service vs third-party)? Any rate limits/quotas?

---

## UX / Output Format (MVP Mock Description)  
**Daily Email/Message Layout (or dashboard card list):**  
- Header: “Daily AI News Brief — {Date}”  
- 3–7 items, each with:
  - **Headline** (Publisher — Publish Time)  
  - **Summary (1–3 sentences)**  
  - **Why it matters (1 sentence)**  
  - **Source link** (domain visible, clickable)  
- Footer:
  - “This briefing covers AI topics published in the last 24 hours.”  
  - Optional: “Some items may be marked ‘insufficient source context’ if source text couldn’t be extracted.”

---

## System Architecture Overview (High Level)  
1. **Scheduler / Orchestrator**  
   - Triggers daily pipeline with run configuration.
2. **Discovery (Search Engine Adapter)**  
   - Performs web search constrained to the time window and target domains.
3. **Candidate Store (Staging Data)**  
   - Stores discovered URLs + metadata.
4. **Scraper & Extractor Workers**  
   - For each URL: robots compliance check → fetch → parse → extract title/publish time/body.
5. **Ranking & Filtering Service**  
   - Scores relevance, removes low-quality/irrelevant.
6. **Deduplication Service**  
   - Clusters near duplicates and selects best representatives.
7. **Summarization Service (Grounded)**  
   - Produces summaries from extracted context; enforces “insufficient context” safeguard.
8. **Report Builder**  
   - Renders final 3–7 item brief in chosen output format.
9. **Notification Service (TBD)**  
   - Delivers report to email/Slack/dashboard.
10. **Observability & History Store**  
   - Persists run logs + outputs for recent N days.

---

## Data Model (MVP)  
- **Run**
  - `run_id`, `scheduled_at`, `timezone`, `time_window_start`, `time_window_end`
  - `config_snapshot` (target sites, keywords)
  - `status` (success/partial_failure/failure)
  - metrics: `found_count`, `scrape_attempted`, `extracted_count`, `summarized_count`, `cluster_count`
- **CandidateArticle**
  - `candidate_id`, `run_id`
  - `url`, `domain`
  - `search_metadata` (title/snippet/published_at if available)
  - `scrape_status` + `failure_reason`
  - `extracted_title`, `publisher`, `published_at_extracted`
  - `extracted_context_ref` (ID or hash; optionally store text)
- **DedupCluster**
  - `cluster_id`, `run_id`
  - `representative_candidate_id`
  - list of member candidates (IDs)
- **FinalItem**
  - `final_item_id`, `run_id`, `cluster_id`
  - `headline`, `publisher`, `published_at`
  - `summary`, `why_it_matters`
  - `source_url`
  - `context_quality` (ok / insufficient_source_context)

---

## Integration Points  
- **Web Search Provider** (adapter): returns candidate URLs and metadata.
- **Robots Compliance / Fetching Layer**: robots.txt resolver + HTTP client with caching.
- **Scraping/Parsing Library**: DOM extraction heuristics.
- **LLM Summarization**: summarization + groundedness enforcement (implementation TBD).
- **Notification Service**: email/Slack/dashboard API (TBD).
- **Storage**: database for runs/history; object storage optional for extracted text (open question).

---

## Edge Cases  
- **No relevant results** found within 24 hours → deliver a “no strong matches” message and optionally broaden keywords (only if configured).
- **Robots disallow** for a target site → skip and note in logs; optionally try discovery results from allowed pages only.
- **Publish time missing** → attempt extraction; if still missing, show “publish time unavailable.”
- **Extraction yields generic boilerplate** (e.g., photo captions only) → mark as low-quality; avoid summarizing.
- **Dedup clustering mistakes** (two distinct articles on similar topics) → keep representative with best completeness; log cluster composition for review.
- **Summarization failure** (model errors/timeouts) → mark item as failed and exclude from top list or include placeholder with reason (prefer exclusion in MVP).

---

## Metrics / KPIs  
**Quality & Coverage**
- `brief_items_count` per day (target 3–7)
- `extraction_success_rate` = extracted_count / scrape_attempted
- `summary_success_rate` = summarized_count / extracted_count
- `dedup_reduction_ratio` = raw_candidates / final_items (indicates dedup effectiveness)
- `insufficient_context_rate` (share of included items marked insufficient)

**Reliability**
- `daily_job_success_rate`
- average and p95 pipeline duration (from schedule start to delivery)

**User Trust**
- “Link verification” rate is difficult to measure; alternatively track whether users click links (if instrumentation available).

---

## Rough Cost Estimate (Typical, Knowledge-Based Ranges)  
> Note: Costs vary heavily by hosting, model usage, scraping volume, and integration complexity. These are **order-of-magnitude** estimates for an MVP of the system described.

1. **Engineering (MVP build)**  
   - ~6–10 weeks for 1–2 engineers: **$30k–$90k** (depending on team rate and scope depth for scraping + summarization + delivery integration).
2. **LLM / Summarization Compute**  
   - Daily runs (~1/day) with ~20–50 summarized items: often **$5–$50/day** depending on model choice, token sizes, and whether full extracted text is used.
   - Rough MVP monthly: **$150–$1,500+ / month**.
3. **Web fetching / scraping infrastructure**  
   - Mostly low cost but can rise with concurrency, storage, and rate-limiting; rough MVP monthly: **$50–$500 / month**.
4. **Storage & Database**  
   - Storing structured run logs and extracted metadata: low; rough MVP monthly: **$10–$200 / month**.
5. **Third-party services (search, email/Slack APIs)**  
   - Search provider and notifications can add **$50–$1,000 / month** depending on usage tiers.

**Total MVP ballpark (first 1–2 months):** **~$40k–$120k** plus ongoing monthly compute/service costs.

---

## Timeline (Suggested)  
- **Week 1:** Requirements finalization + architecture + initial target sites list + UX/output decisions (especially timezone + notification channel).  
- **Week 2–3:** Build scheduler, discovery adapter, storage schema, and scraping/extraction with robots compliance.  
- **Week 4:** Implement ranking/filtering + dedup clustering.  
- **Week 5:** Add grounded summarization with “insufficient context” behavior + report renderer.  
- **Week 6:** Observability dashboards/logs + end-to-end dry run.  
- **Week 7:** Beta with limited target sites; iterate extraction/summarization quality.  
- **Week 8:** Launch MVP + stabilize costs and performance.

---

## Deliverables / Artifacts  
- PRD (this document)  
- Output/UX spec + sample briefing with 3–7 items  
- Data model & schema migration plan  
- System architecture diagram (components + data flow)  
- Pipeline run logs specification (status codes, metrics)  
- Compliance approach doc (robots handling + allowlist strategy)  
- Metrics/KPI dashboard design  
- MVP rollout plan and fallback behaviors

---

If you answer the open questions (especially **delivery channel**, **timezone**, and the **initial target sites list**), I can refine the MVP assumptions, acceptance criteria, and the first-week build plan.