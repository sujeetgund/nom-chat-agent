## 1. Overview  
The Meeting Agent is a user-controlled PC-side assistant that, when turned on, begins listening to the user’s meeting audio, records and (optionally) transcribes it, and produces clean, end-of-meeting minutes (summary, decisions, and action items). The workflow is “through my PC”: the agent captures audio from the computer’s audio output/input path while the user is actively in a meeting, then automatically generates minutes when the user stops the session or when the meeting ends. The product prioritizes privacy and consent transparency, clear retention controls, strong accuracy expectations, and lightweight integration hooks for common tools (Zoom/Google Meet/Slack) without requiring them for the core experience.

---

## 2. Goals & Non-Goals  

### Goals
- **On-device/PC audio capture** triggered by a simple power-on/on-off mode.
- **Automatic transcription** from captured audio (using an on-device option where feasible, otherwise via a secure cloud inference pipeline).
- **End-of-meeting minutes generation** including:
  - Meeting summary
  - Decisions
  - Action items (with owners if available)
- **Minutes formatting** that’s immediately readable and ready to paste/share.
- **User control** via start/stop behavior:
  - Begin listening on power-on
  - End minutes when user stops or meeting ends
- **Privacy-first consent UX** during recording (explicit messaging before and while recording).
- **Retention transparency**: define what is stored, for how long, and what is deletable.
- **Optional integrations** as helpful add-ons (e.g., importing context from Zoom/Meet/Slack), but primary workflow remains “through my PC audio.”

### Non-Goals
- Building a complex multi-agent architecture with shared hidden reasoning or full system context.
- Auto-posting minutes to every integration without user confirmation.
- Perfect speaker diarization/attribution in every environment (best-effort with clear accuracy messaging).
- Replacing professional transcription/recording compliance tools.
- Continuous background listening when the agent is off.

---

## 3. User Stories (As a ___, I want ___ so that ___)

1. **As a meeting participant, I want to turn the Meeting Agent on with one toggle so that it starts capturing audio immediately when I join.**  
2. **As a meeting participant, I want clear on-screen recording status so that I know when audio is being captured.**  
3. **As a meeting participant, I want a consent/notice prompt before recording begins so that I can inform others and comply with my environment’s expectations.**  
4. **As a user, I want to stop the agent at any time so that the system knows when the meeting ends and doesn’t keep listening.**  
5. **As a user, I want minutes to be generated at the end of the meeting so that I don’t have to manually summarize.**  
6. **As a user, I want minutes formatted with “Summary / Decisions / Action Items” so that I can quickly share follow-up information.**  
7. **As a user, I want to review and edit minutes before saving/sharing so that I can correct mis-transcriptions.**  
8. **As a privacy-conscious user, I want to control audio/transcript retention and deletion so that my data isn’t stored indefinitely.**  
9. **As a power user, I want optional integrations (e.g., import meeting title from Zoom/Meet) so that minutes are labeled correctly.**  
10. **As a user, I want metrics about transcription quality (confidence/uncertainty cues) so that I can trust or verify the content where needed.**

---

## 4. Functional Requirements  

### A) Audio Capture & Session Control
1. **Power-on starts capture:** When the agent is turned on, it begins capturing audio from the PC meeting audio source.  
2. **Power-off stops capture:** When turned off, capture stops and an end-of-meeting minutes generation workflow begins.  
3. **Recording indicator:** Always-visible UI status showing “Listening/Recording” vs “Stopped.”  
4. **Audio source selection (first-run + settings):**
   - Default to a common “system audio output” capture mode (varies by OS)
   - Allow user to choose microphone vs system audio where possible
5. **Meeting-end detection (optional):** If supported reliably:
   - Detect prolonged silence or lack of audio frames and propose “Meeting likely ended—generate minutes?”  
   - User can confirm or continue recording.
6. **User confirmation on stop:** When user stops, show “Generating minutes…” and allow cancel only if generation is not started (or limited cancellation rules).

### B) Transcription
7. **Transcription pipeline:** Convert recorded audio to text (best-effort) with timestamps.  
8. **Speaker labeling (best effort):** If diarization is available, label speakers (e.g., Speaker 1/2).  
9. **Language detection (if applicable):** Detect primary language or allow user selection.  
10. **Partial transcription (optional):** During meeting, optionally show live transcript preview (can be disabled by privacy settings).

### C) Minutes Generation (End-of-Meeting)
11. **Minutes schema generation:** Produce a structured minutes document containing:
   - Title / meeting metadata (if available)
   - Executive summary
   - Decisions (bulleted)
   - Action items (table/list with owner, due date if detected, and task)
   - Open questions / follow-ups (optional section)
12. **Grounding to transcript:** Minutes must be derived from the captured transcript (with citations/quotes optionally included).  
13. **Uncertainty handling:** If key information is unclear, explicitly mark “Unclear” or “Not specified” rather than guessing.  
14. **Editable output:** Provide UI for user edits before saving/sharing.

### D) Minutes Output & Export
15. **Copy/share:** Provide “Copy to clipboard” and download (Markdown/Doc-friendly format).  
16. **Save to local history:** Store meeting minutes history locally or in the user account based on consent/retention settings.  
17. **Export formats:** At minimum:
   - Markdown
   - Plain text
   - Optional: PDF or DOCX (later milestone)

### E) Integrations (Optional, KB-context inspired)
18. **Read meeting context (optional):**
   - Import meeting title/date from supported tools when user grants permission.
19. **Post-minutes (optional):**
   - Offer “Send to Slack/Confluence” with explicit user confirmation.  
20. **No hard dependency:** Core functionality works without integrations.

### F) Privacy, Consent, and Controls (Core)
21. **Consent notice before recording:** Show a pre-recording notice and require acknowledgement (configurable in settings).  
22. **In-meeting notice:** Provide a persistent indicator (and optionally a small reminder) while listening.  
23. **Retention settings:** User can configure:
   - Audio retention: delete immediately after minutes generation OR retain for X days
   - Transcript retention: similar choices
   - Minutes retention: retain until user deletes (or configurable)
24. **Delete controls:** Per-meeting “Delete all associated data” button.  
25. **Default privacy mode:** Choose safer defaults (e.g., delete audio immediately; retain transcript only if needed).

---

## 5. Non-Functional Requirements  

### Performance
- **Audio capture reliability:** No dropped audio for the typical meeting length (e.g., up to 1–2 hours) under normal system load.  
- **Minutes generation latency target:**  
  - First usable minutes within **30–90 seconds** after meeting stop for typical meetings (e.g., < 60 minutes).  
  - For longer meetings, show progress and completion time estimates.
- **Transcription throughput:** Should keep up with real-time or near-real-time generation (depending on architecture).

### Security
- **Encryption in transit:** TLS for any network calls.  
- **Encryption at rest (if any storage):** Strong encryption for transcripts/audio/minutes.  
- **Access control:** User-scoped data access; no cross-user retrieval.  
- **Secure deletion:** Honor retention settings; where technically feasible, ensure deletion of audio/transcripts within defined time.

### Scalability
- **Multi-user scaling:** System should support concurrent users with predictable cost controls.  
- **Graceful degradation:** If transcription service fails, generate “minutes from partial transcript” or provide fallback (“insufficient audio quality” message).

### Reliability & Observability
- **Crash-safe sessions:** If app crashes during recording, resume session metadata and mark meeting as incomplete.  
- **Monitoring:** Track errors at audio capture, transcription, minutes generation, and export stages.

---

## 6. Out of Scope  
- Full compliance workflows for regulated industries (e.g., guaranteed legal admissibility, certified recording).  
- Automatic scheduling features (create meetings, invite attendees).  
- Building an open-ended conversational multi-turn agent that stores a shared long-term memory across meetings.  
- Automatic transcription and minutes generation for multiple meetings simultaneously.  
- Real-time multi-party collaboration editing (document co-authoring).  
- Advanced knowledge-base retrieval across the organization (RAG) beyond optional integration metadata (unless explicitly added later).  
- Automatic “recording consent” distribution to meeting participants (we can show reminders, but not guarantee compliance).

---

## 7. Open Questions  
1. **Audio capture approach by OS:** Which OS targets first (Windows/macOS/Linux)? What exact capture method(s) are feasible for “through my PC”?  
2. **Transcript + minutes generation placement:** On-device vs cloud hybrid—what is the target for privacy and cost?  
3. **Retention defaults:** Should the default be “delete audio immediately after minutes generation” to minimize privacy risk?  
4. **Meeting-end detection reliability:** Do we rely on user stop only, or implement silence-based heuristics? What false-positive tolerance is acceptable?  
5. **Speaker diarization expectations:** How important is speaker labeling in v1, and what accuracy threshold is required?  
6. **Action item extraction rules:** How do we determine owners and due dates (NLP heuristics vs explicit user selection UI)?  
7. **Citations in minutes:** Should the UI show evidence snippets from transcript to improve trust?  
8. **Integration scope:** Which integration(s) first (Zoom, Google Meet, Slack) and whether to use them only for metadata vs deeper context retrieval.  
9. **Editing UX constraints:** Allow full re-generation, or only manual edits?  
10. **Cost/quality tradeoffs:** Which model tiers to use for transcription and summarization under different confidence conditions?

---

# Additional PRD Content (as requested)

## Background / Context  
Newton on Mars’s “Meeting Summarizer Agent – Get the Minutes, Not the Mess” highlights a workflow where audio/transcripts are transformed into key points, decisions, and tasks, culminating in clean meeting minutes and follow-up documentation. This PRD aligns with that goal but emphasizes the **user-controlled “through my PC” audio capture** approach rather than requiring meeting-tool specific recording capture. Agent design guidance (avoid complex multi-agent sharing full context) suggests a **single pipeline**: audio → transcript → structured minutes → editable output.

---

## UX/UI Notes (Key Screens & Interactions)  
### 1) Agent Home / Toggle  
- Big toggle: **On / Off**  
- Status label: “Listening” (red dot) or “Not listening” (grey)  
- Secondary text: selected audio source (e.g., “Capturing PC audio: Speakers”)

### 2) Consent & Recording Notice  
- Modal shown when turning on:
  - “Meeting Agent is recording audio from your PC to generate minutes.”
  - “Audio/transcripts retention: [configured default].”
  - “By continuing, you acknowledge responsibility to inform participants per your policies/laws.”
- Button: **Acknowledge & Start**

### 3) In-Meeting View  
- Compact floating panel (optional):
  - Live transcript preview toggle (default off for privacy)
  - Timer: meeting duration  
  - “Stop” button

### 4) Minutes Results  
- Structured sections:
  - **Minutes (Summary)**  
  - **Decisions** (bulleted)  
  - **Action Items** (table: Task | Owner | Due | Notes)  
- “Confidence/Unclear” tags if info missing.
- Buttons:
  - **Edit**
  - **Copy**
  - **Export**
  - **Delete meeting data**

### 5) Settings  
- Retention controls:
  - Audio: Immediate delete / delete after N days
  - Transcript: keep / delete after N days
  - Minutes: keep until user deletes (or N days)
- Audio source selection per OS.
- Integration toggles.

---

## System Workflow (End-to-End)  
1. **User turns agent On**  
2. Consent modal shown → user acknowledges  
3. **Audio capture starts** from selected PC audio source  
4. Audio is buffered/streamed to the transcription pipeline (architecture dependent)  
5. On user **Stop** (or meeting-end detection + user confirmation):
   - capture finalizes
   - audio is packaged
6. **Transcription** runs or finalizes
7. **Minutes generation** runs:
   - transcript → structured summary/decisions/action items  
8. UI shows **Minutes results**
9. User reviews/edits and exports  
10. **Retention policy** is applied (delete audio/transcripts as configured)

---

## Data Model (Rough)  

### Entities
- **User**
- **MeetingSession**
  - `session_id`
  - `user_id`
  - `started_at`, `ended_at`
  - `audio_source` (system audio/mic)
  - `status` (recording, transcribing, generating, completed, failed)
  - `device_metadata` (optional)
  - `integration_metadata` (title/provider IDs if available)
- **AudioArtifact**
  - `audio_id`
  - `session_id`
  - `storage_uri` (if retained)
  - `duration_ms`
  - `checksum`
  - `retention_policy_applied`
- **TranscriptArtifact**
  - `transcript_id`
  - `session_id`
  - `language`
  - `segments[]` (text, start_ms, end_ms, speaker_label optional)
  - `confidence_stats`
- **MinutesDocument**
  - `minutes_id`
  - `session_id`
  - `version`
  - `summary_text`
  - `decisions[]` (text + optional “evidence quote”)
  - `action_items[]` (task, owner, due_date, notes, status)
  - `uncertainty_flags[]`
- **UserEdits**
  - `minutes_id`
  - `diff/patch` or full edited document
- **RetentionRecord**
  - `session_id`
  - `audio_delete_at`, `transcript_delete_at`, `minutes_delete_at`
  - `audit_trail`

---

## Edge Cases & Handling  
- **Poor audio quality / echo:** show warning; generate minutes with uncertainty tags; possibly suggest improving audio source.  
- **No transcript available:** if transcription fails, return “Unable to generate minutes due to transcription failure.” Offer retry if user allows re-processing.  
- **User stops early:** generate partial minutes; clearly label as “Partial.”  
- **Multiple meetings back-to-back:** user stop boundary defines sessions; we can optionally “Auto-split” only if reliable.  
- **Sensitive content:** remind about confidentiality; ensure retention settings default to minimizing stored data.  
- **System clock/timezone mismatch:** ensure minutes metadata uses local time at generation and/or session start.

---

## Analytics / Metrics  
### Product Metrics
- **Activation rate:** % of installs that turn agent on for at least one session  
- **Session completion rate:** % of sessions that reach minutes generation  
- **Minutes acceptance:** % of minutes where user edits/copies/exports  
- **Retention usage:** % choosing immediate delete vs longer retention

### Quality Metrics (Operational + UX)
- **Transcription success rate** and average WER proxy (if available) / confidence distribution  
- **Generation latency percentiles** (p50/p90)  
- **User-reported accuracy score** (thumbs up/down + optional text feedback)  

### Safety/Compliance Signals
- **Consent acknowledgement rate**
- **Delete usage rate**
- **Error types** tied to audio capture permissions (OS-level)

---

## Security / Privacy Details (More Explicit)  
- **Explicit consent**: consent modal on start; persistent indicator while recording.  
- **Data minimization defaults**: default retention aims to delete audio immediately after minutes generation.  
- **Role-based access**: only the user can access their session data.  
- **Audit logs**: retention deletions and access events recorded (internally).  
- **Compliance posture**: include in-app messaging that users are responsible for informing meeting participants and following local policies.

---

## Rough Cost Estimate (Typical Range)  
Costs vary heavily by OS targets, on-device vs cloud, model choice, and integration depth. Below are **ballpark** estimates for a v1 meeting summarizer workflow like this:

### Team & Timeline (example v1: 12–16 weeks)
- 1 Product/Project lead (part-time to full-time)
- 1–2 Engineers (audio capture + pipeline + UI)
- 1 ML/NLP engineer (transcription + summarization tuning)
- 1 Designer (UX, consent UX, minutes UI)
- QA support

### Engineering/Build Cost (rough)
- **$120k–$250k** for MVP (single OS, basic capture, cloud transcription/summarization, no deep integrations)  
- **$250k–$450k** for stronger v1 (two OS targets, robust capture selection, diarization best-effort, editable minutes, retention controls)  
- **$450k–$700k+** if you add reliable integration with Zoom/Meet plus transcript import/export flows and advanced export formats

### Ongoing Variable Costs (order-of-magnitude)
- **Transcription + summarization inference** costs per minute of audio and per generated document.  
- Expect costs scale with:
  - meeting duration
  - number of retries
  - whether you retain and re-process audio

*(If you share expected monthly active users + avg meeting duration, I can provide a tighter per-month estimate.)*

---

## Milestones (Suggested)  
1. **M1 (Weeks 1–3): Discovery + Prototype**
   - consent UX, minutes formatting spec, audio capture feasibility on target OS
2. **M2 (Weeks 4–7): Audio Capture + Session UI**
   - On/Off toggle, recording indicator, stop flow
   - Capture artifacts and playback/debug tooling
3. **M3 (Weeks 8–10): Transcription Pipeline**
   - transcription integration, transcript segments, confidence reporting
4. **M4 (Weeks 11–13): Minutes Generation**
   - structured minutes schema, decisions/action extraction, uncertainty handling
   - editable minutes UI
5. **M5 (Weeks 14–16): Retention + Security + QA**
   - retention settings, delete controls, encryption, audit trail
   - performance/latency tuning and edge-case testing

---

## Acceptance Criteria (MVP)  
1. **Recording control works:** Turning agent on starts audio capture; turning off stops capture within acceptable delay.  
2. **Consent is shown:** User sees consent notice and recording indicator before capture begins.  
3. **Minutes output exists:** After stop, minutes are generated containing at least:
   - Summary
   - Decisions section (may be empty with explanation if none)
   - Action items section (may be empty with explanation if none)
4. **Minutes are formatted cleanly:** Output matches the minutes template and is copy/export ready.  
5. **Retention controls function:** User-configured retention settings are applied; delete meeting data removes stored audio/transcripts/minutes according to policy.  
6. **Accuracy transparency:** If transcription is poor or missing, the system clearly indicates inability to generate complete minutes rather than fabricating content.  
7. **Performance within target:** For a typical meeting length (e.g., 30–60 min), minutes generation completes within the defined latency target (e.g., p90 < 2–3 minutes depending on architecture).  
8. **Security baseline:** Encryption in transit enforced; user data access is isolated.

---

If you tell me (1) target OS(es), (2) whether you want audio deletion immediately by default, and (3) typical meeting length/user volume, I can refine the architecture decision and produce a more precise cost + milestone plan.