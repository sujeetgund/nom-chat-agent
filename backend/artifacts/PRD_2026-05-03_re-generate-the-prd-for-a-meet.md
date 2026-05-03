## 1. Overview  
The Meeting Agent listens to a user’s meeting audio directly from their PC when the agent is turned on, transcribes what was spoken, and at the end produces clear meeting minutes (key points, decisions, action items, and follow-up notes). The product is designed to reduce the manual effort and “messy outputs” associated with post-hoc summarization by combining reliable audio capture, robust transcription, and structured minutes generation. Integrations with tools like Zoom/Google Meet/Slack are optional; the primary workflow is PC audio capture on power-on, aligned with the “Meeting Summarizer Agent – Get the Minutes, Not the Mess” Newton on Mars KB pattern: audio/transcripts → key points/decisions/tasks → meeting summary & follow-up document.

---

## 2. Goals & Non-Goals  

### Goals
- **PC audio capture on demand:** Start listening when the user turns the agent on; stop based on user action (or explicit stop control).
- **Accurate transcription:** Convert meeting speech into text with speaker attribution where feasible.
- **Minutes generation at end of meeting:** Produce structured minutes including:
  - Summary
  - Decisions
  - Action items (owner + due date if mentioned)
  - Open questions / follow-ups
- **Good UX for control & review:** Clear indicators for recording state and where the final minutes appear.
- **Privacy-first behavior:** Obtain consent, clearly communicate recording and processing, and provide retention controls.
- **Reliable operation:** Handle common meeting issues (silence, interruptions, noisy audio) gracefully.
- **Measurable quality:** Track transcript and summary quality via analytics and user feedback.

### Non-Goals
- No fully automated “join meetings” automation (i.e., the agent does not control conferencing platforms as a primary requirement).
- No guaranteed perfect speaker identification in all environments.
- No live meeting co-pilot (real-time summaries) unless later phased.
- No legal compliance certifications (e.g., HIPAA/FINRA) unless required by a later compliance scope.
- No “email/calendar scheduling” features as a primary workflow.

---

## 3. User Stories  
- **As a meeting participant,** I want to turn the agent on and have it listen to the meeting on my PC so that I can get minutes without manual note-taking.  
- **As a meeting organizer,** I want to stop the agent when the meeting ends so that it generates a complete set of minutes for that meeting session.  
- **As an end user,** I want the minutes to appear in a clear document format so that I can copy, share, or reference decisions and action items.  
- **As a privacy-conscious user,** I want to understand when recording is happening and how my data is used so that I feel confident using the agent.  
- **As a team lead,** I want action items extracted with owners/dates when mentioned so that follow-up work is trackable.  
- **As a frequent meeting attendee,** I want consistent formatting across meetings so that reviewing minutes is fast.  
- **As a user with noisy audio,** I want the agent to still produce useful minutes even when transcription quality is imperfect so that I’m not blocked by audio issues.  

---

## 4. Functional Requirements  

### A. Agent Controls & Start/Stop Behavior
1. **Power-on start trigger (primary):**  
   - When the user turns the agent **On**, the system begins capturing audio from the selected PC audio source.
2. **Explicit stop trigger (end of meeting):**  
   - The user can stop recording using a visible control (e.g., “End meeting” button).
3. **Recording state UX:**  
   - The UI must clearly show recording status (e.g., “Recording…”) and elapsed time.
4. **Multiple meetings per session:**  
   - If the user stops and later restarts without app restart, it creates a new meeting session artifact.

### B. PC Audio Capture
5. **Audio source selection:**  
   - Default capture is the user’s system audio; allow selection of microphone/system audio if needed.
6. **Continuous streaming capture while recording:**  
   - Audio is buffered and streamed (or chunked) to the transcription service.
7. **Sample rate & encoding:**  
   - Capture must be compatible with downstream transcription (implementation detail; e.g., 16kHz mono or as supported).

### C. Transcription
8. **Speech-to-text (STT):**  
   - The system transcribes captured audio into time-stamped text.
9. **Speaker labeling (best-effort):**  
   - Provide speaker segmentation and labels when supported (e.g., “Speaker 1/2” or diarization).
10. **Silence handling:**  
   - Ignore long silences and mark gaps so minutes generation uses meaningful content.
11. **Interruption handling:**  
   - If audio is interrupted (muted/unmuted), transcription continues and gaps are preserved.

### D. Minutes Generation
12. **End-of-meeting minutes generation pipeline:**  
   - Upon stop, the system processes the transcript to generate minutes.
13. **Structured minutes output:**  
   - Include:
     - Meeting title (best-effort; user can edit)
     - Date/time (from client)
     - Attendees (optional; infer best-effort if diarization names are available)
     - Agenda/summary (1–3 paragraphs)
     - Decisions (bullet list)
     - Action items (table with Task, Owner, Due date, Notes)
     - Open questions / follow-ups
     - Key discussion points (optional section)
14. **User-edit and regenerate (optional but recommended):**  
   - Provide a way to edit generated minutes and optionally “Regenerate” with the same transcript.

### E. Output Format & Delivery
15. **Minutes storage & retrieval:**  
   - Minutes are saved under a meeting session ID.
16. **Document formats:**  
   - Provide at least one of: HTML view in-app + downloadable text/markdown; optionally PDF export later.
17. **Share/export:**  
   - Copy-to-clipboard and download supported (e.g., .md/.txt). Email/Slack integration optional.

### F. UX Notes (required behaviors)
18. **Where user indicates start/stop:**  
   - Start: turning the agent on (primary)  
   - Stop: prominent “End meeting” action in agent UI (secondary)
19. **Where minutes appear:**  
   - A “Meetings” tab (or notifications) shows completed minutes immediately after generation completes.

---

## 5. Non-Functional Requirements  

### Performance
- **End-to-end generation latency:**  
  - Target: minutes generation completes within **60–120 seconds** for typical meetings (e.g., 30–60 minutes audio), assuming streaming transcription is available.  
- **Real-time recording stability:**  
  - Audio capture must not drop for short network hiccups; system should queue/retry chunks.
- **Transcript completeness:**  
  - For normal audio, target **≥ 90% word coverage** (measured as recall vs. human reference in sampling tests).

### Accuracy Expectations
- **Transcription word error rate (WER):**  
  - Target WER for clean audio: **< 10–15%**; for noisy audio: **graceful degradation** without catastrophic failure.
- **Minutes quality:**  
  - Target that action items and decisions are “useful” (user-rated) for **≥ 80%** of meetings in internal evaluation; formal thresholds set after pilot.

### Reliability & Availability
- **Uptime:**  
  - Target **99.9%** service availability for transcription + minutes generation.
- **Graceful failure:**  
  - If transcription fails mid-way, system must still attempt minutes generation from available transcript and clearly label partial output.

### Scalability
- **Concurrent users:**  
  - Support growth from pilot to production with autoscaling (e.g., transcription workers scale independently from generation workers).
- **Batch processing:**  
  - Minutes generation is a batch job per meeting session; should scale horizontally.

### Security / Privacy (also covered in Data Handling section)
- **Encryption in transit and at rest** for all audio/transcript/minutes data.
- **Least-privilege access** internally (auditing, role-based access).

---

## 6. Out of Scope  
- No live, minute-by-minute meeting summarization (unless future phase).
- No automatic calendar invites or scheduling.
- No guaranteed identification of specific attendee names without user-provided mapping.
- No platform-level integration as a hard requirement (Zoom/Meet/Slack integrations are optional).
- No transcription for external conference recording file ingestion unless explicitly added later (current scope is PC capture).
- No compliance-specific controls beyond standard enterprise best practices (unless required later).

---

## 7. Open Questions  
1. **Audio capture source defaults:**  
   - Should the agent capture **system audio** by default, or **microphone**? What OS support is assumed (Windows/macOS)?
2. **Start/stop UX details:**  
   - Is “turn on” enough for recording immediately, or do we need a confirmation (“Start listening”)?
3. **Meeting metadata:**  
   - Should users enter meeting title/date/attendees manually, or rely purely on inference?
4. **Speaker labeling:**  
   - Do we need diarization accuracy thresholds, and can we map speakers to attendee names?
5. **Retention policy:**  
   - Default retention: keep for 30 days? delete after download? configurable by user?
6. **Data residency / compliance:**  
   - Any constraints by region, or required certifications?
7. **Minutes regeneration:**  
   - When a user edits, do we store edit history and versioning?
8. **Cost/quality trade-offs:**  
   - Do we use a single STT model or switch by audio quality?

---

# Additional Required Content (requested by brief)

## Background + Problem Statement  
Meeting note-taking is time-consuming and inconsistent, especially in fast-moving discussions where decisions and action items are easy to miss. Traditional approaches—manual notes or post-meeting summarization—often produce messy outputs lacking structured action items, owners, and clear decisions. The Newton on Mars KB case study (“Meeting Summarizer Agent – Get the Minutes, Not the Mess”) highlights a pattern: capture audio/transcripts → extract key points/decisions/tasks → generate a clean summary & follow-up document. This PRD specifies an agent that captures meeting audio from the user’s PC when enabled, and reliably generates structured meeting minutes at the end.

---

## UX Notes (detailed)  
- **Start interaction (power-on):**
  - User turns the agent **On** from a tray/app toggle.
  - UI shows: “Listening…” + timer + selected audio source (system vs mic).
- **Stop interaction:**
  - Prominent **“End meeting”** button (or keyboard shortcut) to stop capture.
  - UI shows: “Processing… minutes will appear when done.”
- **Minutes visibility:**
  - Minutes appear in a **Meetings** list with status:
    - “Capturing”
    - “Transcribing”
    - “Generating minutes”
    - “Ready”
  - Click a meeting to view minutes; provide “Download” and “Copy” actions.

---

## System Workflow / Architecture Outline  

1. **Client (User PC)**
   - Audio capture module (system audio/mic selection)
   - Agent UI (start/stop state)
   - Meeting session manager (creates session ID, timestamps)
2. **Ingestion Layer**
   - Chunked audio upload (secure, resumable)
3. **Transcription Service**
   - Speech-to-text with timestamps
   - Optional diarization/speaker segmentation
4. **Minutes Generation Service**
   - Prompting/LLM summarization over transcript
   - Structured extraction:
     - Decisions
     - Action items (with heuristic extraction of owners/dates if mentioned)
     - Open questions
   - Output formatting to minutes template
5. **Storage**
   - Store audio (optional depending on retention policy), transcript, and final minutes
6. **Client Delivery**
   - Polling/websocket updates for job status
   - Minutes rendered in-app and downloadable

**Optional integrations (phase/extension):**
- If user uses Zoom/Meet/Slack, allow importing transcripts or posting minutes to those platforms. Primary workflow remains PC audio capture.

---

## Data Handling (privacy / consent / retention / security)  

### Consent & Transparency
- **Explicit user consent on first run:** show a consent screen:
  - “Recording audio from your PC during meetings when the agent is On”
  - “Audio and transcript are processed to generate minutes”
- **In-session transparency:** recording indicator always visible.

### Retention
- Proposed default policy (needs confirmation):
  - **Audio**: delete after transcription (or after N days, e.g., 7–30 days)
  - **Transcript**: retain for **N days** (e.g., 30) or until user deletes
  - **Minutes**: retain longer (e.g., 180 days) or until user deletes/export
- Users can configure retention (e.g., “delete automatically after download”).

### Security
- **Encryption in transit:** TLS for all client↔service communications.
- **Encryption at rest:** storage encryption for transcripts/minutes.
- **Access control:** role-based access, audit logs.
- **PII minimization:** avoid unnecessary retention of raw audio if not needed.
- **Data segregation:** per-tenant/user separation.
- **Abuse controls:** prevent retrieval of other users’ meetings; secure job IDs.

---

## Edge Cases (and expected behavior)  
- **Noisy audio / echo:**  
  - Provide fallback: continue transcribing but mark minutes with “Some portions may be unclear.”  
- **Multiple speakers / overlapping speech:**  
  - Best-effort diarization; when overlap occurs, allow “Speaker unclear” labels.  
- **Silence / pauses:**  
  - Do not treat silence as end; ignore short silences during transcription; preserve longer gaps.
- **User interruption (pauses, goes off-mic):**  
  - Continue or segment transcript; minutes generation uses available content.
- **Partial meetings (user ends early):**  
  - Minutes are generated for the recorded duration; minutes clearly state “Partial meeting” if duration < threshold (e.g., < 10 minutes) or if user indicates it.
- **Agent turned on accidentally mid-conversation:**  
  - Provide UI to rename meeting and optionally delete session.
- **Network drop mid-capture:**  
  - Client buffers audio chunks; retries upload; if data loss occurs, minutes are generated with a clear quality note.

---

## Metrics & Analytics  
### Product Metrics
- **Adoption**
  - % of users who complete at least one meeting with minutes generation
- **Funnel**
  - Turn-on → start recording → end meeting → minutes ready
- **Reliability**
  - Job success rate for transcription and minutes generation
  - Average time from “End meeting” to minutes ready
- **Engagement**
  - % of meetings where user views minutes
  - % where user downloads/copies minutes
- **Quality feedback**
  - Thumb up/down on minutes
  - “Missing action items” / “Incorrect decisions” tags

### Quality Metrics (offline + sampling)
- **Transcription**
  - WER / CER measured on labeled samples across audio qualities
- **Minutes extraction**
  - Precision/recall for:
    - Decisions identification
    - Action item extraction (task + owner + due date when present)

---

## Milestones & Acceptance Criteria  

### Milestone 1: Prototype Audio Capture + Session Control (Client)
- **Deliverables:** start/stop UX, PC audio capture, meeting session IDs, basic transcription integration.
- **Acceptance criteria:**
  - Turning agent on begins recording within **2 seconds**
  - “End meeting” stops capture and triggers backend job
  - Recording indicator is always visible and accurate

### Milestone 2: End-to-End Transcription + Transcript View
- **Deliverables:** transcription pipeline; transcript displayed with timestamps; basic diarization.
- **Acceptance criteria:**
  - Transcript generated for a 15–30 minute meeting without complete failure
  - Silence and interruptions do not crash processing
  - Transcript is time-ordered and downloadable

### Milestone 3: Minutes Generation (Structured Output)
- **Deliverables:** minutes template generation (summary/decisions/action items/open questions).
- **Acceptance criteria:**
  - Output follows required sections and formatting
  - In internal test sets, action items and decisions are present in **≥ 80%** of meetings where they exist
  - Partial meeting produces a labeled “partial” minutes doc rather than failing

### Milestone 4: Privacy, Retention, and Security Hardening
- **Deliverables:** consent flow, retention controls, encryption, access control audits.
- **Acceptance criteria:**
  - Data deletion works as documented (audio/transcript/minutes)
  - No cross-user access to meeting artifacts
  - Encryption validated in staging

### Milestone 5: Metrics + Beta Launch
- **Deliverables:** analytics events, feedback collection, operational dashboards.
- **Acceptance criteria:**
  - End-to-end job success rate **≥ 95%**
  - Median “minutes ready” time within target (e.g., **< 120s** for standard meetings)
  - User feedback captured for quality improvement

---

## Explicit Assumptions  
- The primary input is **PC audio capture** (system audio by default or selectable).
- The transcription and minutes generation can be done via hosted services with acceptable latency.
- Meetings are typically **30–60 minutes**; longer meetings should still work but may increase processing time.
- Users can tolerate best-effort diarization rather than perfect attendee naming.
- There is a persistent storage layer for meeting artifacts (with retention controls).

---

## Rough Cost Estimate (typical project-level ranges)  
*These are ballpark estimates for a single-team build; actual costs vary by existing infrastructure, model providers, and platform scope.*

### One-time engineering & implementation (3–5 months)
- Client app (audio capture + UI + controls + session management): **$80k–$180k**
- Backend services (ingestion, transcription orchestration, minutes generation pipeline): **$120k–$250k**
- Storage, security, retention controls, analytics instrumentation: **$60k–$150k**
- QA, reliability hardening, beta launch: **$40k–$120k**  
**Estimated engineering total:** **$300k–$700k**

### Ongoing costs (recurring)
- Transcription + LLM minutes generation per minute of audio:
  - Commonly **$0.01–$0.10+ per audio minute** for transcription depending on provider/model; LLM summarization adds additional per-request cost.
- Storage + bandwidth:
  - Audio storage (if retained) and transcript/minutes storage add incremental costs.  
**Estimated ongoing compute total:** depends heavily on usage volume; for early beta (e.g., 1k–10k meetings/month), often **tens of thousands/month** at most unless heavily retained audio is enabled.

### Optional integrations
- Zoom/Google Meet/Slack import/export: **+$30k–$120k** depending on depth and API scope.

---

If you want, I can tailor this PRD to a specific platform scope (Windows vs macOS; system audio support; whether a web app companion is required) and lock the UX start/stop flow more concretely.