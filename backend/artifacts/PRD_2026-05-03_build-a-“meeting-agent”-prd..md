## 1. Overview  
The **Meeting Agent** is an on-device (or hybrid) assistant that Sujeet can quickly start when joining a meeting. Once enabled, it listens to Sujeet’s PC audio in a non-disruptive way, performs **near-real-time speech-to-text**, and generates **concise, timestamped bullet notes** emphasizing **decisions, action items, names, and deadlines**. Each meeting has its own **session lifecycle** (start/stop and automatic reset) and outputs an easy-to-share summary (at minimum: copy to clipboard; optionally integrations like email or notes apps). The product prioritizes **user consent and privacy**, with configurable options for local processing vs cloud assistance, the ability to disable recording, and clear retention controls.

---

## 2. Goals & Non-Goals  

### Goals  
- Provide **near-real-time transcription** from PC audio without requiring meeting platform plug-ins.  
- Generate **brevity-optimized bullet-point notes** including:
  - Key decisions
  - Action items (owner + due date if present)
  - Names of attendees/speakers if available
  - Deadlines/timeframes when explicitly stated  
- Offer **per-meeting session management**:
  - Manual start/stop
  - Automatic reset safeguards (e.g., inactivity/timeouts)
- Display output in a structured format:
  - **Timestamped bullets**
  - Separate **Action Items** section  
- Enable **export/share**:
  - Copy to clipboard (must-have)
  - Optional: email / notes app / Slack / Google Doc integration  
- Implement strong **privacy/security UX**:
  - Explicit consent before listening
  - “Disable recording” mode
  - Retention controls (including short default retention)
  - Clear indication of when the agent is listening  
- Keep performance impact low:
  - Minimal CPU usage
  - No disruption to audio playback or meeting communication  
- Support high weekly usage (12–15 meetings/week) with low setup time.

### Non-Goals  
- Fully automated “meeting minutes” that capture every word; the target is **concise** notes.  
- Perfect diarization/speaker attribution in all cases (unless explicitly required).  
- Building native integrations into every meeting platform (Zoom/Teams/etc.) as a first milestone.  
- Transcribing and summarizing confidential data without user consent—this is explicitly UX-gated.  
- Real-time collaboration (multi-user editing) in the first version.  
- Guaranteeing legal/compliance outcomes without a defined compliance matrix and admin policies.

---

## 3. User Stories  
- **As Sujeet,** I want to turn the Meeting Agent on with a single click when I join a meeting so that it starts listening immediately.  
- **As Sujeet,** I want the agent to stop listening when I end or manually stop the session so that it does not capture extra audio.  
- **As Sujeet,** I want near-real-time transcription converted into concise bullet notes so that I can quickly understand what happened.  
- **As Sujeet,** I want the output to include timestamped bullets so that I can reference specific moments later.  
- **As Sujeet,** I want an “Action Items” section that extracts owners and deadlines (if present) so I can follow up without rewriting.  
- **As Sujeet,** I want to copy the meeting summary to clipboard with formatting preserved so that I can paste into my notes.  
- **As Sujeet,** I want an option to disable recording / store minimal data so that I can control privacy for sensitive meetings.  
- **As an Admin/Company policy owner,** I want retention and processing mode controls so that we comply with internal rules.  
- **As Sujeet,** I want the agent to automatically reset between meetings (e.g., after inactivity) so that I don’t have to manage edge cases.  

---

## 4. Functional Requirements  

### A) Audio Capture & Session Lifecycle  
1. Provide a **start** and **stop** control in a lightweight UI (tray/toolbar button or similar).  
2. Support **per-meeting sessions**:
   - Create a new session on manual start.
   - End session on manual stop.
   - Auto-stop on inactivity timeout (configurable; default e.g., 15 minutes).  
3. Detect/handle common edge cases:
   - Meeting app switches audio devices
   - Short “preview” conversations before the official meeting starts  
4. Ensure **no interference** with meeting audio (capture only; no playback).  
5. Offer modes:
   - **Listen-only with no storage** (recommended default)
   - Optional **transcript storage** for the meeting session

### B) Real-time / Near-real-time Transcription  
6. Transcribe speech from captured PC audio with a target mode of **near-real-time** updates to the UI.  
7. Support configured **transcription language(s)** (default likely English; additional languages via settings).  
8. Provide transcript text internally to power summarization; UI may show incremental transcript optionally (toggle).

### C) Summarization & Bullet Extraction  
9. Generate **timestamped bullet points** throughout the meeting (streaming or periodic updates, e.g., every 30–60 seconds).  
10. Extract and structure:
   - Decisions (who/what, if inferable)
   - Action items (imperative tasks)
   - Names (speaker labels or entity extraction if diarization is off)  
11. Identify deadlines/timeframes when explicitly mentioned and include them in bullets and the action items table.  
12. Optimize for brevity:
   - Cap bullets per update (configurable; default conservative)
   - Prefer high-salience statements over filler

### D) Output Format & Export/Share  
13. Provide an output view with:
   - **Timestamped Notes** section (bullets)
   - **Action Items** section (list or structured rows: task, owner, due date, status placeholder)  
14. Provide **copy to clipboard** export in readable formatting (Markdown-like bullets).  
15. Optional integrations:
   - Email draft (or send)
   - Integration with notes apps or document tools (Google Docs/Notion)
   - Slack message formatting  
16. Include a “meeting summary saved” confirmation per session.

### E) Privacy, Consent, and Controls  
17. Consent UX:
   - Show a clear consent prompt describing what is captured and why before starting to listen.
   - Provide an explicit “Allow” action; default state is **off**.  
18. Listening indicator:
   - Visible UI indicator (e.g., “Listening…” with timer).  
19. Recording/disabling controls:
   - “Disable recording/storage” option (audio never persisted; transcripts may be ephemeral per policy).  
20. Retention controls:
   - Default retention policy (e.g., 24 hours for transcript/audio; or no retention by default if feasible).  
21. Provide “Delete meeting data” action per session.  
22. Provide admin settings (if enterprise):
   - Processing mode preference (local vs cloud)
   - Retention duration
   - Disabling cloud entirely (cloud off switch)

### F) Performance & Reliability  
23. Maintain a stable experience for 12–15 meetings/week:
   - Reliable start/stop
   - No long blocking operations on click  
24. Graceful failure:
   - If transcription fails, provide error and still allow manual notes copy
   - Avoid repeated prompts; follow a clear retry strategy

---

## 5. Non-Functional Requirements  

### Performance  
- **Latency target (initial):** UI bullet updates within **5–20 seconds** of spoken content (near-real-time).  
- CPU impact constraint: keep average CPU usage low (target **<10–20%** on typical developer laptops; exact measurement TBD per OS).  
- Memory footprint: avoid large buffering; streaming processing preferred.  
- Audio capture reliability: minimal glitches; handle device changes.

### Security & Privacy  
- Consent-first: agent must not listen without explicit user action.  
- Data minimization:
  - Default to **no audio retention**
  - Transcripts retention strictly controlled  
- If using cloud inference/transcription:
  - Encrypt in transit (TLS) and at rest
  - Signed requests, scoped access tokens
  - Avoid logging raw transcript content in application logs  
- Local processing option must be supported where feasible to reduce exposure.

### Scalability  
- Expected usage: 12–15 meetings/week per active user; initial scale likely single-digit to low hundreds of users.  
- System must handle concurrent sessions if multiple users/devices exist (but likely one session per device at a time).  
- Backend (if any) must autoscale based on transcription/summarization workload.

### Accessibility & Usability  
- Clear readable UI for timestamps, action items, and copy button.  
- Provide keyboard support for key actions (start/stop/copy).  

---

## 6. Out of Scope  
- Native browser/meeting-plugin extensions for every platform in initial release (e.g., no Zoom marketplace app first).  
- Perfect diarization/speaker labeling in all scenarios (unless required later).  
- Automated email sending or posting to third-party tools without user review/confirmation (initially draft-only).  
- Automatic calendar integration to detect meeting start/end.  
- Live meeting video/visual understanding.  
- Advanced compliance workflows (legal hold, eDiscovery) unless explicitly requested and funded.

---

## 7. Open Questions  
1. **Meeting platform(s) & OS**: Which platforms must work first (Zoom/Teams/Google Meet/other)? Target OS for v1 (Windows/macOS)?  
2. **Audio routing approach**:  
   - Can we capture system audio reliably on each OS without user configuring “stereo mix” or virtual devices?  
   - Are virtual audio devices acceptable?  
3. **Diarization**: Is speaker labeling required? If yes, how accurate is “good enough” (and is it worth the cost/latency)?  
4. **Latency target**: What is the acceptable delay for bullet updates (e.g., 5s vs 30s)?  
5. **Languages**: Primary transcript language(s)? Any need for multilingual meetings?  
6. **Output destination**: On-screen only for v1, or must be directly exportable to a specific system (Notion/Google Docs/Slack/email)?  
7. **Compliance constraints**:
   - Is cloud processing allowed?
   - Required retention period (e.g., 0 days, 24 hours, 30 days)
   - Any admin controls required (SOC2/GDPR/HIPAA-like constraints)?
8. **Local vs cloud**: What is the allowed split? For example:
   - Local transcription + cloud summarization  
   - Or local all-in-one  
   - Or cloud everything with strict retention  
9. **Transcript visibility**: Should Sujeet see full transcript or only bullets?  
10. **Action item extraction requirements**: Do we need owner extraction with named entities, or is “who/what” optional?

---

## UX Requirements (additional detail)  

### Main UI  
- Persistent small control:
  - **Start Listening** button
  - **Stop** button  
- Clear state:
  - “Not listening” (default)
  - “Listening to meeting audio” + running timer  
- Post-meeting results:
  - Timestamped bullet notes
  - Action Items section with extracted due dates and owners (if present)
  - Copy button + optional share buttons

### Consent UX  
- Before first listening each session (or at least first use):
  - Explain: “The agent will capture your PC audio while enabled to produce notes.”
  - Explain: “Choose whether to retain transcript/audio based on your privacy setting.”
  - Provide: Allow / Cancel toggle
- If a user disables recording/storage, explain exactly what is stored (e.g., “No audio stored; transcript stored for X hours” or “transcript not stored”).

### Feedback & Controls  
- On start, show a short countdown or “Listening now.”  
- On stop, show:
  - “Generating summary…” indicator
  - Estimated completion time (or immediate update if streaming finalization is fast)
- Provide “Delete this meeting” / “Change privacy mode” controls.

---

## System Architecture Outline  

### Client (Windows/macOS app)  
1. **Audio Capture Module**  
   - Captures system audio or meeting audio routed from PC.  
   - Streams audio frames to transcription pipeline.  
2. **Session Manager**  
   - Handles start/stop, inactivity timeout, session IDs, and resets.  
3. **Transcription Engine (local or client-side streaming)**
   - Option A: Local ASR model (on-device)  
   - Option B: Stream audio (or partial text) to cloud ASR  
4. **Summarization Engine**
   - Converts transcript chunks into bullet notes and action items.
   - Runs locally or via cloud LLM with strict prompt templates.  
5. **UI Layer**
   - Live bullets update and final formatted summary for export.  
6. **Data Handling Layer**
   - Implements retention settings, local encryption (if storage), and deletion.

### Backend (optional, depending on architecture)  
- **Summarization API** (if not fully local)  
- **Authentication & policy enforcement** (enterprise admin settings)  
- **Retention & audit logs** (store minimal metadata; never raw audio unless allowed)

### Data Flow (typical)  
- Start session → capture audio stream → ASR outputs incremental text → summarizer updates bullet list → user reviews → copy/export → retention policy deletes remaining stored artifacts.

---

## Data Handling & Security  

### Data Types  
- Audio stream (sensitive)
- Transcripts (sensitive-derived)
- Summaries (derived)
- Metadata (timestamps, session IDs)

### Processing Modes  
- **Local mode (preferred for privacy):**
  - Audio captured and processed on-device.
  - Summaries available on-device.
  - Optional ephemeral transcript buffers.
- **Cloud mode (if needed for quality/performance):**
  - Stream audio chunks over TLS or stream partial text.
  - Short-lived storage with deletion on completion (subject to retention policy).
  - Data access restricted by least privilege.

### Retention Defaults  
- Default to **no audio retention**.  
- Transcript and derived summaries:
  - Option A: ephemeral (deleted after meeting ends + short window)
  - Option B: retained for X hours/days (configurable)
- Provide explicit “Delete now” and confirm deletion.

### Encryption  
- In transit: TLS  
- At rest (if any storage): platform keychain + encrypted local storage; encrypted server storage.

### Compliance Hooks  
- Admin-controlled toggles:
  - Disable cloud processing
  - Set retention duration
  - Enforce “no storage” policy

---

## Metrics & Acceptance Criteria  

### Functional Accuracy  
- **Action items extraction quality**:
  - ≥70% of clearly stated action items appear in the Action Items section in v1 (measured via labeled evaluation set).  
- **Decision capture**:
  - ≥60% of “decided” statements appear as decision bullets.

### Latency & Responsiveness  
- Near-real-time bullet updates within target:
  - p95 UI update latency ≤ **20 seconds** (configurable; set per pilot results).  
- Start/stop responsiveness:
  - Start action completes in ≤ **1 second** and audio capture begins within a defined tolerance.

### Reliability  
- Session lifecycle correctness:
  - Auto-stop triggers correctly after inactivity in ≥95% of test cases.
- No audio disruption:
  - Users report “no impact to meeting audio” across a usability pilot (qualitative threshold + basic automated checks).

### Privacy/Trust  
- Consent gating:
  - Agent never captures audio before explicit consent.
- Retention:
  - Verified deletion behavior matches configured retention window within tolerance.

---

## Milestones (Suggested)  

1. **M0 – Discovery & Prototype (2–3 weeks)**  
   - Confirm OS/platform targets, audio capture feasibility, consent UX wireframes  
   - Spike ASR + summarization approach (local vs cloud)  
2. **M1 – MVP Audio → Transcript → Bullet Notes (4–6 weeks)**  
   - Start/stop + inactivity timeout  
   - Near-real-time transcript and periodic bullet updates  
   - Timestamped bullets + action items extraction (basic)  
3. **M2 – Export/Share + Privacy Controls (3–4 weeks)**  
   - Copy to clipboard formatting  
   - Consent UX refinement  
   - “Disable recording/storage” and retention/delete controls  
4. **M3 – Integrations & Polish (3–6 weeks)** *(optional based on scope)*  
   - Notion/Google Docs/Slack/email draft support  
   - Better diarization if required  
   - Performance tuning on target devices  
5. **M4 – Beta, Measurement, and Compliance Validation (3–5 weeks)**  
   - Pilot with Sujeet and 5–20 users  
   - Evaluate metrics, latency, and privacy compliance acceptance  
   - Admin controls (if enterprise) finalized

---

## Initial Cost Estimate (v1)  

> Assumptions for estimation (please adjust once architecture is decided):  
- Users: **1–10 beta users**, scaling to **100 users** by ~3–6 months (optional).  
- Meetings per user: **12–15/week** → ~15/week average.  
- Avg meeting duration: **45 minutes** (typical).  
- Total meeting minutes per user/week: 45 * 15 = **675 minutes/week** (~11.25 hours/week).  
- Wording: Costs below assume either **local ASR** with **cloud summarization**, or **cloud ASR** as an alternative.  

### A) Option 1 (Recommended Privacy): Local ASR + Cloud Summarization  
**What it means:** transcription happens on-device; only transcript text (or chunks) is sent for bullet/action item generation.  
- Cloud compute cost is mostly LLM calls; audio bandwidth is minimized.

**Cloud usage estimate (per meeting):**  
- Transcript chunking every ~1 minute → ~45 chunks/meeting (typical)  
- But cost can be reduced by summarizing only partials (e.g., every 5 minutes) + final summary.  
- Assume:  
  - **9 summary calls** per meeting (every ~5 minutes)  
  - **1 final call** per meeting  
  - Total ~**10 LLM calls/meeting**

**Token sizing (rough):**  
- Summarization input ~1–2k tokens per chunk (varies a lot)  
- Assume average **1.5k input + 500 output tokens per call**  
- Per meeting: 10 calls → ~**15k input + 5k output tokens**  
- Total weekly tokens per user: meetings/week 15 → **225k input + 75k output tokens/week**

**Illustrative monthly cost at 100 users**  
- Meetings/month per user: 15 * ~4.3 = **64.5**  
- Total calls/month (100 users): 64.5 * 10 * 100 = **64,500 LLM calls/month**  
- LLM pricing varies widely by provider/model. Using a generic blended estimate:  
  - **$0.10 per 1M input tokens** and **$0.20 per 1M output tokens** (placeholder)  
- If per call average tokens: input 1.5k, output 0.5k  
  - Input tokens/call: 1.5k → total input tokens = 64,500 * 1.5k = **96.75M**  
  - Output tokens/call: 0.5k → total output tokens = 64,500 * 0.5k = **32.25M**  
- Compute cost ≈ (96.75M/1M)*$0.10 + (32.25M/1M)*$0.20  
  - ≈ 96.75*$0.10 + 32.25*$0.20  
  - ≈ **$9.68 + $6.45 = ~$16/month** (LLM-only)  
- Add API overhead, logging, monitoring, and buffering: **+ $50–$300/month**  
- **Estimated total cloud cost (100 users): ~$100–$500/month**  

**One-time costs / tooling**  
- Development + evaluation time (team cost not included here)  
- Minor: CI/CD, monitoring, secrets: **$20–$100/month**

**Pros:** lowest cloud cost; best privacy story.  
**Cons:** on-device ASR performance may vary; local model size/CPU/GPU constraints.

---

### B) Option 2: Cloud ASR + Cloud Summarization  
**What it means:** audio is streamed to a cloud transcription service; summaries derived similarly.

**Assumptions:**  
- 1 meeting = 45 minutes = 0.75 hours  
- Audio minutes per user per month: 675 minutes/week * ~4.3 = **2,902 minutes/month**  
- At 100 users: **290,200 audio minutes/month** (~4,836 hours/month)

**Cost drivers:** ASR priced per minute and/or per second; bandwidth also matters.

**Illustrative estimate:**  
- If transcription costs ~**$0.006–$0.03 per audio minute** (varies heavily by provider):  
- Lower bound: 290,200 * $0.006 ≈ **$1,741/month**  
- Upper bound: 290,200 * $0.03 ≈ **$8,706/month**  
- LLM summarization on top (similar to Option 1, potentially fewer because transcript text comes for free but still token-cost): **$100–$500/month**  

**Estimated total cloud cost (100 users): ~$1.8k–$9.2k/month**  
**Pros:** potentially better transcription quality and less client compute.  
**Cons:** privacy risk, bandwidth costs, and compliance complexity.

---

### C) Storage Costs (Audio/Transcript Retention)  
If we default to **no audio retention** and short transcript retention:  
- Near-zero to small storage costs (tens to low hundreds of GB depending on retention).  
- If retention is longer (e.g., 30–90 days) or audio retained, costs rise significantly.

**Example (very rough):**  
- If transcripts only, and keep for 7 days, likely **<$50/month** for early stage; audio retention could become **$100–$1,000+/month** depending on minutes stored and codec.

---

### Cost Summary Table (illustrative)  

| Scenario | Cloud ASR | Cloud Summarization | Storage | Estimated Monthly at 100 users |
|---|---:|---:|---:|---:|
| A) Local ASR + Cloud Summaries | $0 | ~$100–$500 | $0–$50 | **~$100–$550** |
| B) Cloud ASR + Cloud Summaries | ~$1.8k–$9.2k | ~$100–$500 | $0–$200 | **~$2.0k–$10.0k** |

> **Recommendation for v1:** Option A (local ASR + cloud summarization) unless compliance explicitly forbids cloud for even transcripts; if so, move summarization fully local or ensure transcript never leaves device.

---

## Deliverables Checklist (what this PRD defines)  
- Problem statement, goals/non-goals  
- User stories  
- Functional requirements (grouped by feature area)  
- System architecture outline  
- UX requirements (consent, listening indicator, session controls)  
- Data handling & security model (local vs cloud, retention, deletion)  
- Metrics/acceptance criteria  
- Milestones  
- Detailed (illustrative) cost estimate across architecture options  

---  

If you answer the open questions (especially **OS/platforms**, **local vs cloud allowed**, **diarization requirement**, and **latency target**), I can refine the architecture decision and produce a tighter v1 cost model with concrete token/minute assumptions.

## Cost Estimate

**Development:**
- Estimated effort: 100-170 hours @ $150/hour
- Subtotal: $15,000 - $25,500

**Infrastructure (Monthly, after launch):**
- Cloud compute (AWS/GCP/Azure): $500 - $2,000
- LLM inference and API calls: ~$1,000
- Storage & bandwidth: ~$500-$1,500
- Total monthly (estimate): $2,000 - $4,500

*Note: Costs assume standard cloud pricing and OpenAI/similar LLM APIs. Actual costs vary by scale, traffic, and provider choice.*
