## 1. Executive Summary
We will build a cross-platform “AI Meeting Note-taking Agent” that **listens to the user’s PC audio** during meetings (without joining as a bot participant) and produces a **single Markdown (.md) file** containing structured notes. The solution will work for **Google Meet, Zoom, and Microsoft Teams** by relying on **system audio capture / mic loopback** rather than native platform integrations. It will provide **near-real-time transcription** and then a **post-meeting summarization** that extracts **bullet points, key decisions, and action items (owner + due date when available)**, with **timestamps** when feasible.

---

## 2. Problem Statement
Users currently capture meeting notes manually or rely on solutions that require joining as a participant/bot or tight calendar/platform integrations. This creates gaps in coverage and usability across meeting platforms. The project must:
- Capture speech from meetings on **Google Meet, Zoom, and Microsoft Teams** reliably.
- Transcribe in **real-time or near-real-time**.
- Generate a **single structured Markdown** output with:
  - **Overview**
  - **Bullets**
  - **Decisions**
  - **Action Items** (owner + due date when mentioned)
- Operate with **English only** and **baseline security** (no special data handling; external AI services allowed).

---

## 3. Proposed Solution
### High-Level Architecture
1. **Audio Capture Layer (PC-side)**
   - Capture meeting audio via **system audio capture** or **mic loopback** (user-configurable).
   - Resample/encode to a transcription-friendly format (e.g., 16kHz mono PCM/Opus).

2. **Streaming Transcription Service**
   - Send audio chunks to a speech-to-text model for **near-real-time transcription**.
   - Maintain an in-memory transcript timeline with timestamps and speaker-agnostic segments (optionally diarization if supported/available).

3. **Meeting Session Manager**
   - Detect meeting start/stop (user-controlled “Start/Stop Recording” MVP; later optional smart detection).
   - Buffer transcript text and segment timestamps for later summarization.
   - Store raw transcript temporarily during the session (in memory; disk optional based on constraints).

4. **Post-Meeting Summarization Agent (LLM)**
   - After the user stops recording, call an LLM with:
     - Transcript segments (with timestamps)
     - Strict output schema requirements
   - The agent generates a single Markdown file with:
     - `# Overview`
     - `## Bullets` (bullets with timestamps when feasible)
     - `## Decisions` (decision statements with timestamps)
     - `## Action Items` table/list with **Owner**, **Due Date**, **Action**, **Source timestamps** (when available)

5. **Markdown Export**
   - Output one `.md` file per meeting session.
   - Include session metadata (date/time captured; language; transcription model identifier where appropriate).

### Output Schema (MVP)
- **Bullets**: `- [timestamp] <bullet text>`
- **Decisions**: `- [timestamp] <decision text>`
- **Action Items** (Markdown table preferred):
  - `| [timestamp] | Owner | Due Date | Action Item |`

### LLM Prompting / Extraction Strategy (MVP)
- Use a **schema-constrained prompt**:
  - “Identify decisions” vs “identify action items” explicitly.
  - Extract **owner** from phrasing (“John will…”, “Sarah owns…”, “Bob to…”) and fall back to “Unassigned” if not found.
  - Extract **due date** only when explicitly mentioned; normalize dates where possible (e.g., “next Friday” → ISO date if context allows; otherwise keep original phrase).
- Provide the model with **timestamped transcript snippets** so it can cite approximate timing.

---

## 4. Scope and Deliverables
### Deliverables (as requested)
1. **Architecture and Implementation Plan**
   - Audio capture approach per OS (Windows/macOS/Linux) with user instructions.
   - Streaming transcription pipeline and transcript segment storage format.
   - Summarization and Markdown generation design.
   - Integration plan for external AI services (speech-to-text + LLM).

2. **Timeline and Cost Estimate**
   - Cost section provided separately per your instruction.

3. **Milestones for MVP then iterate**
   - MVP includes core capture → transcript → Markdown summary.
   - Iterations add diarization, better start/stop detection, quality improvements.

### MVP Scope (What we will build first)
- Cross-platform desktop app (or at minimum: Windows + macOS for MVP; Linux optional depending on constraints).
- System audio capture / mic loopback configuration UI.
- Near-real-time transcription display (live transcript pane).
- Post-meeting summarization into a **single Markdown** output with:
  - Overview, Bullets, Decisions, Action Items (Owner + Due Date when mentioned)
- Timestamping:
  - Include timestamps for bullets/decisions/action items when the model can map statements to transcript segments.

### Iteration Scope (Phase 2/3)
- Optional speaker diarization (if available from transcription provider).
- Meeting start/stop automation (detect silence, hotkey, or app focus heuristics).
- Better action-item normalization (date parsing improvements, consistent owner naming).
- Export options (Notion/Google Docs) can be added later, but not required for this brief.

---

## 5. Timeline
Assuming project kickoff immediately and an MVP-first approach:

- **Week 1: Discovery & Design**
  - Confirm target OS(s), audio capture method, transcription/LLM providers.
  - Define Markdown output format and extraction schema.
  - Draft API contracts between components.

- **Weeks 2–3: Prototype**
  - Implement audio capture + chunking.
  - Integrate streaming transcription and render live transcript.
  - Persist transcript segments in a structured format (text + timestamps).

- **Weeks 4–5: MVP Implementation**
  - Implement post-meeting summarization using schema-constrained LLM prompting.
  - Generate final single Markdown file.
  - Build minimal UI: Start/Stop, audio input selection, output location.

- **Week 6: MVP Validation**
  - Run test meetings across Meet/Zoom/Teams.
  - Evaluate action item extraction accuracy, timestamp mapping quality.
  - Fix transcription/audio issues and prompt tuning.

- **Weeks 7–8: Iteration Readiness**
  - Improve extraction quality (owners/due dates).
  - Add diarization (if feasible) and robustness improvements.
  - Finalize MVP demo and handoff documentation.

---

## 6. Assumptions and Constraints
### Assumptions
- Users can provide meeting audio from the PC via:
  - **System audio capture** (recommended), or
  - **Mic loopback**
- The user will start/stop recording for the MVP (hotkey or UI button).
- English-only output and extraction.

### Constraints
- No “bot participant” integration; audio listening only.
- Baseline security only; no special data handling beyond standard application security practices.
- Real-time transcription quality depends on:
  - Audio capture fidelity,
  - Network latency (for streaming),
  - The transcription provider’s accuracy.

---

## 7. Team / Delivery Approach
### Delivery Model
- **Agile, milestone-driven**, weekly demo checkpoints.
- Build the system in layers so audio/transcription/summarization can be tested independently.

### Recommended Team Roles
- **Solution Architect / Tech Lead**: overall system design, provider integration, schema design.
- **Desktop Engineer**: audio capture, UI, session management, file export.
- **ML/AI Engineer**: prompt engineering, summarization schema enforcement, extraction logic.
- **QA / Test Engineer**: cross-platform audio/transcription testing across Meet/Zoom/Teams.
- **Product/PM (optional)**: requirements refinement and acceptance criteria.

### Approach to Quality
- Create an **evaluation set** of anonymized transcripts representing:
  - Clear vs ambiguous action items,
  - Decisions stated with varying phrasing,
  - Due dates described explicitly vs implicitly.
- Use iterative prompt/schema tuning based on failure patterns.

---

## 8. Risks and Mitigation
1. **Audio capture reliability varies by OS/device**
   - *Mitigation*: Provide clear user setup guidance; allow both system audio and mic loopback; test on target OS versions early.

2. **Latency and transcript stability during streaming**
   - *Mitigation*: Use chunk buffering (e.g., 1–5s chunks), show “partial transcript” live while keeping a more stable transcript for final summarization.

3. **Action item extraction errors (missing owner/due date)**
   - *Mitigation*: Strict extraction rules in the prompt; “Unassigned” fallback; date extraction only when explicit; include transcript citations to reduce hallucination.

4. **Timestamp mapping inaccuracies**
   - *Mitigation*: Generate timestamps from transcript segment boundaries; only include timestamps where confidence is high (otherwise omit or mark “approx.”).

5. **LLM hallucination in structured outputs**
   - *Mitigation*: Schema-constrained prompting, require grounded extraction (“Only use what appears in transcript”); validate output fields and fall back when missing.

---

## 9. Next Steps
1. **Confirm target platforms for MVP** (Windows/macOS/Linux; and minimum supported OS versions).
2. **Select transcription + LLM providers** (or approve the approach to choose based on availability/quality).
3. **Finalize Markdown format** (sample template) and acceptance criteria for:
   - decision detection,
   - action item extraction with owner/due date,
   - timestamp inclusion rules.
4. **Run an audio capture feasibility test** with one representative meeting per platform (Meet/Zoom/Teams) to validate system audio capture.
5. **Kick off Week 1 design** and lock the component interfaces (audio → transcript segments → summarization → Markdown).

If you want, I can also provide a sample Markdown output template and the exact JSON schema we would use internally to force consistent extraction.

## Cost Estimate

**Development:**
- Estimated effort: 120-180 hours @ $150/hour
- Subtotal: $18,000 - $27,000

**Infrastructure (Monthly, after launch):**
- Cloud compute (AWS/GCP/Azure): $500 - $2,000
- LLM inference and API calls: ~$1,000
- Storage & bandwidth: ~$500-$1,500
- Total monthly (estimate): $2,000 - $4,500

*Note: Costs assume standard cloud pricing and OpenAI/similar LLM APIs. Actual costs vary by scale, traffic, and provider choice.*
