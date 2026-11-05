"""EPA-IS-3 Investigate: incident timeline (xlsx), root-cause review (docx), remediation roadmap (xlsx)."""
import os
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font, Alignment
from common import *
from data import *
import diagrams as D

F = os.path.join(OUT, "EPA-IS-3")
os.makedirs(F, exist_ok=True)
EXERCISE = ("EXERCISE SCENARIO: INC-2026-001 is a simulated incident built from the lecture scenario (slides 25–28: 'a cloud AI agent "
            "requests student records 10,000 times in one hour'). Names, IPs (RFC 5737 documentation range) and hashes are fictitious.")

# ------------------------------------------------------------------ evidence + timeline
EVIDENCE = [
    ("EV-01", "Document upload log (sensitive data storage C7)", "C7 → C6", "Upload of CS301_Week5_Summary.pdf by pseudonym p_19c4e0aa from usual campus IP"),
    ("EV-02", "Vector DB ingestion log (C13)", "Cloud logs", "File chunked and embedded; 14 chunks"),
    ("EV-03", "Tutor chat transcript + retrieval trace (C10/C11)", "Orchestrator", "Student question, retrieved chunk IDs, agent answer"),
    ("EV-04", "Agent tool-call trace (C11)", "Orchestrator", "http_request POST with Authorization header to external domain"),
    ("EV-05", "Metadata API gateway access log (C9)", "C6 / SIEM", "10,000 requests, client tutor-agent, source IP 203.0.113.45"),
    ("EV-06", "MCP query log (C5)", "C6 / SIEM", "Queries to legacy student-list tool; records returned per call"),
    ("EV-07", "Cloud egress / flow log (Z5)", "Cloud logs", "Outbound HTTPS from agent workload to notes-sync[.]example"),
    ("EV-08", "Cloud monitoring alert (C14)", "C14", "'API usage 40× baseline' cost/usage alert"),
    ("EV-09", "SOC ticket and analyst notes", "Ticket system", "Triage decisions and timestamps"),
    ("EV-10", "Change records (token revocation, endpoint disabled, IP block)", "Change system", "Containment actions"),
    ("EV-11", "Copy of the malicious PDF (quarantined)", "Forensic store", "Hidden white-text instruction on page 3"),
]
# timestamp, event, phase (diagram), IR phase, evidence, fact/inferred/assumption, asset, IoC, confidence
TIMELINE = [
    ("2026-11-16 21:47", "Malicious PDF 'CS301_Week5_Summary.pdf' uploaded to course shared-notes area; page 3 contains hidden instruction text", "Attack", "Initial access / delivery", "EV-01, EV-11", "Fact", "E6, E4", "File name, SHA-256 (EV-11)", "High"),
    ("2026-11-16 22:05", "Document-search agent indexes the PDF into the vector DB without content review", "Attack", "Delivery", "EV-02", "Fact", "S12", "–", "High"),
    ("2026-11-17 08:12", "A different student asks the tutor agent to 'summarise week 5'; the poisoned chunk is retrieved into the context", "Attack", "Execution (prompt injection)", "EV-03", "Fact", "E9", "Chunk ID ch_5521", "High"),
    ("2026-11-17 08:12", "Tutor agent follows the hidden instruction: uses its generic http_request tool to POST its Authorization header (30-day static token) to notes-sync[.]example", "Attack", "Credential access – token disclosure", "EV-04, EV-07", "Fact", "E8", "Domain notes-sync[.]example; token jti tut-agt-7781", "High"),
    ("2026-11-17 08:13", "Agent answers the student normally; the injection told it to stay silent – nobody notices", "Attack", "Defence evasion", "EV-03", "Fact", "E9", "–", "High"),
    ("2026-11-17 08:31", "First API call with the stolen token from 203.0.113.45 (not a cloud IP), user agent python-requests/2.31, to legacy endpoint GET /v1/students", "Attack", "Token theft → API abuse", "EV-05", "Fact", "S9, E8", "IP 203.0.113.45; UA python-requests/2.31", "High"),
    ("2026-11-17 08:31–09:30", "≈10,000 paginated requests (~2.8/s); MCP returns names, e-mail, matriculation no. and enrolments of ≈11,800 students", "Attack", "Collection / exfiltration", "EV-05, EV-06", "Fact (volume); Inferred (attacker kept the data)", "E1", "Request rate; endpoint /v1/students", "High / Medium"),
    ("2026-11-17 09:23", "Cloud monitoring raises usage/cost alert 'API calls 40× baseline' – no gateway security alert existed", "Detection", "Detection", "EV-08", "Fact", "–", "–", "High"),
    ("2026-11-17 09:41", "SOC analyst confirms token used from a non-cloud IP; incident opened (severity high)", "Detection", "Analysis", "EV-09", "Fact", "–", "–", "High"),
    ("2026-11-17 09:48", "Containment: token revoked, tutor-agent client disabled at gateway, IP blocked, legacy /v1/students endpoint switched off", "Response", "Containment", "EV-10", "Fact", "S9", "–", "High"),
    ("2026-11-17 10:05", "PDF quarantined, its chunks deleted from vector DB, http_request tool removed from all agents", "Response", "Containment / eradication", "EV-10, EV-11", "Fact", "S12, S10", "–", "High"),
    ("2026-11-17 11:30", "Classified as personal-data breach; DPO informed; logs exported and hashed for evidence; 72 h clock starts", "Response", "Analysis / legal", "EV-09", "Fact", "E11", "–", "High"),
    ("2026-11-18", "Scope check: no other token used from new IPs in 30 days of logs; uploader account shows no sign of compromise", "Response", "Analysis", "EV-05, EV-01", "Inferred", "E8", "–", "Medium"),
    ("2026-11-19 16:00", "Notification to supervisory authority (GDPR Art. 33), within 72 h", "Response", "Notification", "EV-09", "Fact", "E11", "–", "High"),
    ("2026-11-20", "Affected students informed (Art. 34) with phishing warning, because names + e-mails enable targeted phishing", "Recovery", "Communication", "EV-09", "Fact", "E1, E11", "–", "High"),
    ("2026-11-24", "Tutor agent back online in restricted mode (materials only, no personal data); remediation roadmap started", "Recovery", "Recovery", "EV-10", "Fact", "E9", "–", "High"),
]
IOCS = [
    ("IP address", "203.0.113.45", "Source of all abusive API calls", "Blocked at gateway"),
    ("Domain", "notes-sync[.]example", "Destination the agent sent its token to", "Blocked in cloud egress / DNS"),
    ("User agent", "python-requests/2.31", "Scripted client, never used by MUDT agents", "Alert rule"),
    ("Token ID (jti)", "tut-agt-7781", "Stolen tutor-agent token", "Revoked"),
    ("File", "CS301_Week5_Summary.pdf, SHA-256 9f2c…e41a (exercise value)", "Carrier of the prompt injection", "Quarantined; hash blocked on upload"),
    ("Behaviour", "> 500 records/hour for one client; requests from non-cloud IP with agent token", "Bulk extraction pattern", "New alert C16"),
]

def short(t): return t.split(" ", 1)[1] if " " in t else t
D.incident_timeline(os.path.join(F, "A3-1_incident_timeline.png"), [
    ("16 Nov 21:47", "Malicious PDF\nuploaded", "Attack"), ("16 Nov 22:05", "PDF indexed\ninto vector DB", "Attack"),
    ("17 Nov 08:12", "Agent reads PDF,\nleaks its token", "Attack"), ("08:31", "Token used from\n203.0.113.45", "Attack"),
    ("08:31–09:30", "10,000 requests\n≈11,800 records", "Attack"), ("09:23", "Cloud usage\nalert", "Detection"),
    ("09:41", "SOC confirms\nincident", "Detection"), ("09:48", "Token revoked,\nendpoint off", "Response"),
    ("10:05", "PDF quarantined,\nhttp tool removed", "Response"), ("19 Nov", "Authority\nnotified (Art. 33)", "Response"),
    ("20 Nov", "Students\ninformed", "Recovery"), ("24 Nov", "Restricted\nrestart", "Recovery")])

wb = Workbook()
meta = f"Artefact A3-1 · US-3.1 · owner {who(VESANJA)} · reviewed by {who(EFE)} · {VERSION} · {DATE}"
ws = wb.active; ws.title = "Summary"
ws["A1"] = "A3-1 Incident Timeline – INC-2026-001"; ws["A1"].font = Font(bold=True, size=14, color=ACCENT)
ws["A2"] = meta; ws["A2"].font = Font(italic=True, size=9, color="595959")
summary = [
    ("Scenario note", EXERCISE),
    ("Incident narrative", "A malicious PDF with hidden instructions was uploaded to a course notes area and indexed for AI search. The next day, the tutor agent "
     "retrieved it while answering a normal student question, followed the hidden instruction and sent its own long-lived API token to an external domain. "
     "18 minutes later the attacker used the token from an outside IP to call a legacy Metadata API endpoint and downloaded identifying data of about 11,800 students "
     "in ≈10,000 requests. The abuse was noticed only after 52 minutes through a cloud cost/usage alert, and contained 96 minutes after the token leak."),
    ("Attack chain (lecture slide 27)", "Malicious prompt → token disclosure → token theft → API abuse → data exfiltration → log evidence → alert → containment → remediation"),
    ("Affected assets", "E1 student personal data, E8 agent token, E9 tutoring service, E11 reputation; supporting S9 gateway, S10 agents, S12 vector DB"),
    ("Key times", "Token leaked 08:12 · abuse started 08:31 · detected 09:23 (dwell 71 min) · contained 09:48 · authority notified 19 Nov 16:00 (< 72 h)"),
    ("Linked risk", "R1 (prompt-injected agent, score 20 Critical) – attack path AP1 in A1-1; R5 over-sharing (legacy endpoint)"),
    ("Root causes / remediation", "EPA-IS-3/A3-2_Root_Cause_Review.docx · EPA-IS-3/A3-3_Remediation_Roadmap.xlsx"),
]
for k, (a, b) in enumerate(summary, 4):
    ws.cell(k, 1, a).font = Font(bold=True); ws.cell(k, 2, b).alignment = Alignment(wrap_text=True, vertical="top")
    ws.cell(k, 1).alignment = Alignment(vertical="top")
ws.column_dimensions["A"].width = 26; ws.column_dimensions["B"].width = 120
img = XLImage(os.path.join(F, "A3-1_incident_timeline.png")); img.width, img.height = 1100, 358; ws.add_image(img, "A13")
sheet(wb, "Timeline", ["#", "Timestamp (UTC)", "Event", "Incident phase", "Evidence", "Fact / inferred / assumption", "Affected asset", "Indicator", "Confidence"],
      [(k + 1, t[0], t[1], t[3], t[4], t[5], t[6], t[7], t[8]) for k, t in enumerate(TIMELINE)],
      [4, 18, 64, 22, 12, 18, 12, 28, 11], title="Ordered events", meta=meta)
sheet(wb, "Evidence register", ["ID", "Evidence", "Source / location", "What it shows"], EVIDENCE, [8, 46, 18, 70],
      title="Evidence register (exports hashed with SHA-256 and stored read-only)", meta=meta)
sheet(wb, "Indicators (IoC)", ["Type", "Value", "Meaning", "Action"], IOCS, [16, 52, 40, 30], title="Indicators of compromise", meta=meta)
save_wb(wb, "EPA-IS-3/A3-1_Incident_Timeline.xlsx")

# ------------------------------------------------------------------ root causes
ROOT = [
    ("RC1", "Secrets exposed to the model; token long-lived and not bound to its owner",
     "The tool configuration passed the Authorization header through the agent context; the token was a static 30-day key usable from any IP.",
     "EV-04 shows the header in the tool call; EV-05 shows the same jti used from 203.0.113.45", "C02, C10, C14", "R1"),
    ("RC2", "Excessive agent capability (no least privilege)",
     "The tutor agent had a generic http_request tool and the broad scope students:read, which it never needed for tutoring.",
     "Agent configuration export; EV-04, EV-06", "C06, C30", "R1, R3"),
    ("RC3", "Untrusted content treated as instructions",
     "Uploaded documents were indexed for AI use without review, and nothing separated retrieved text from instructions.",
     "EV-01, EV-02, EV-11 (hidden text)", "C10, C11", "R1"),
    ("RC4", "Over-exposed API (no data minimisation)",
     "A legacy pilot endpoint /v1/students returned identifying fields; no allow-list or pseudonymisation existed at the gateway.",
     "EV-05, EV-06", "C07, C08", "R2, R5"),
    ("RC5", "Missing detection and limits",
     "No per-client quota and no gateway volume alert; detection came by chance from a cost alert after 71 minutes.",
     "EV-08, EV-09", "C09, C16", "R1, R8"),
    ("RC6", "Unrestricted egress from the cloud zone",
     "Agents could connect to any Internet domain, so the token could leave the platform.",
     "EV-07", "C30", "R1"),
]
CONTRIB = [
    ("Process", "No security review of agent tool configuration before go-live; pilot endpoint never decommissioned (change management gap)."),
    ("People", "Developers were not trained on prompt-injection risks; lecturers unaware that shared notes feed the AI."),
    ("Governance", "No owner for AI-agent security; no IR playbook for agent or token compromise (C21)."),
]

d = new_doc("Root-Cause Review – INC-2026-001", "Why the incident was possible and why controls did not stop it", "A3-2",
            "US-3.2 Determine root causes", f"{who(EGON)}; reviewed by {who(VESANJA)}")
note(d, EXERCISE)
d.add_heading("1. Immediate events vs root causes", 1)
para(d, "'Token theft' is an event. A root cause explains why the event was possible and why controls did not stop it (lecture slide 28). "
        "We therefore separate what happened (timeline A3-1) from the conditions that enabled it.")
table(d, ["Level", "Statement"], [
    ("Visible event", "≈11,800 student records were extracted through the Metadata API with a stolen agent token."),
    ("Immediate cause", "The tutor agent obeyed hidden instructions in a retrieved document and sent its token to an external domain."),
    ("Root causes", "RC1–RC6 below: design and control gaps that made each step of the chain possible."),
    ("Contributing factors", "Process, people and governance gaps (section 4)."),
], widths=(4.0, 13.0))
d.add_heading("2. Five whys", 1)
for k, (q, a) in enumerate([
    ("Why were student records disclosed?", "An attacker called the Metadata API with a valid tutor-agent token."),
    ("Why did the attacker have a valid token?", "The agent sent it out after being prompt-injected, and the token was long-lived and usable from anywhere (RC1, RC6)."),
    ("Why could the agent send it out and why did it obey?", "It saw the token in its context, had a generic HTTP tool and treated retrieved text as instructions (RC1, RC2, RC3)."),
    ("Why could the token read identifying student data in bulk?", "The token had a broad scope, a legacy endpoint returned identifying fields, and there was no quota (RC2, RC4, RC5)."),
    ("Why did nobody stop it for 71 minutes?", "No gateway volume alert existed; only a cost alert eventually fired (RC5)."),
], 1):
    p = d.add_paragraph(style="List Number"); p.add_run(q + " ").bold = True; p.add_run(a)
d.add_heading("3. Root causes and control gaps", 1)
table(d, ["ID", "Root cause", "Explanation", "Supporting evidence", "Missing controls", "Risks"], ROOT, widths=(1.1, 3.4, 5.4, 3.6, 1.9, 1.6), font=8.5)
d.add_heading("4. Contributing factors", 1)
table(d, ["Category", "Factor"], CONTRIB, widths=(3.0, 14.0))
d.add_heading("5. Uncertainty and alternative explanations", 1)
table(d, ["Alternative hypothesis", "Evidence for / against", "Conclusion", "Confidence"], [
    ("Token leaked another way (CI logs, developer laptop)", "Against: EV-04 shows the token leaving at 08:12:41 and first misuse 18 min later from a new IP.", "Rejected", "High"),
    ("Uploader's account was compromised", "Against: upload from usual device and campus IP (EV-01). For: uploader denies knowing the content.", "Open – could also be a document copied from the Internet; referred to student conduct office", "Medium"),
    ("Other agent tokens also stolen", "No other new-IP token use in 30 days of logs; log retention limits older checks.", "Unlikely", "Medium"),
    ("Data not kept by attacker", "Cannot be proven either way.", "Treated as disclosed for GDPR notification", "Low"),
], widths=(4.2, 6.8, 4.0, 2.0), font=8.5)
d.add_heading("6. Lessons learned", 1)
bullets(d, ["Risk R1 was rated Critical in Sprint 1 (A1-3), but its controls were still only 'planned' – risk assessment without implementation does not protect.",
            "The model cannot be trusted to protect secrets; protection must sit outside the LLM (tokens, scopes, gateway, egress).",
            "Detection must be built for security, not cost: per-client volume alerts would have cut dwell time from 71 to < 5 minutes.",
            "New control C30 (egress allow-list) was added to the control matrix A2-3 as a result of this review."])
save_doc(d, "EPA-IS-3/A3-2_Root_Cause_Review.docx")

# ------------------------------------------------------------------ remediation roadmap
RM = [
    ("RM-01", "Containment (0–24 h)", "Revoke stolen token, disable tutor-agent client, block IP and domain", "RC1, RC6", "R1", "C22", "IT Security Officer", "–", "2026-11-17", "Done – no further calls from IoCs"),
    ("RM-02", "Containment (0–24 h)", "Disable legacy /v1/students endpoint", "RC4", "R2, R5", "C07", "Head of Development", "–", "2026-11-17", "Done – endpoint returns 404"),
    ("RM-03", "Containment (0–24 h)", "Quarantine PDF, purge its vector-DB chunks, remove http_request tool from all agents", "RC2, RC3", "R1", "C06, C10", "Head of Digital Learning", "–", "2026-11-17", "Done"),
    ("RM-04", "Recovery (1–7 days)", "Rotate all agent and service credentials; check for persistence in orchestrator", "RC1", "R1, R11", "C14, C22", "Cloud Platform Owner", "RM-01", "2026-11-21", "100 % credentials rotated"),
    ("RM-05", "Recovery (1–7 days)", "Re-index vector DB with lecturer-approved materials only; restart tutor in restricted mode", "RC3", "R1", "C10, C11", "Head of Digital Learning", "RM-03", "2026-11-24", "Only approved sources in index"),
    ("RM-06", "Recovery (1–7 days)", "GDPR notifications (Art. 33/34) and student phishing warning", "–", "R1", "C21", "Data Protection Officer", "–", "2026-11-20", "Notified within 72 h"),
    ("RM-07", "Short term (≤ 30 days)", "Replace static keys with 5-min sender-constrained OAuth2 tokens; keep tokens outside the model context", "RC1", "R1, R2", "C01, C02, C14", "Head of Development", "RM-04", "2026-12-15", "No static keys left; pen-test token replay fails"),
    ("RM-08", "Short term (≤ 30 days)", "Least-privilege tool allow-list and scopes per agent", "RC2", "R1, R3", "C06", "Head of Digital Learning", "RM-07", "2026-12-15", "Each agent ≤ its documented scopes (A2-1 §4)"),
    ("RM-09", "Short term (≤ 30 days)", "Gateway schema allow-list and outbound filter", "RC4", "R2, R5", "C07", "Head of Development", "RM-02", "2026-12-15", "Filter test: identifying fields blocked"),
    ("RM-10", "Short term (≤ 30 days)", "Per-client quotas (500 records/h) and volume / new-IP alerts in SIEM", "RC5", "R1, R8", "C09, C16", "IT Security Officer", "–", "2026-12-01", "Replay of incident triggers alert < 5 min"),
    ("RM-11", "Short term (≤ 30 days)", "Egress allow-list for cloud zone", "RC6", "R1, R11", "C30", "Cloud Platform Owner", "–", "2026-12-01", "Agents cannot reach unlisted domains"),
    ("RM-12", "Long term (≤ 1 semester)", "On-behalf-of tokens and object-level checks in MCP", "RC2", "R3", "C03, C05", "Head of Development", "RM-07", "2027-02-28", "Confused-deputy test fails"),
    ("RM-13", "Long term (≤ 1 semester)", "Pseudonymisation (HMAC) and k-anonymity for all metadata", "RC4", "R5", "C08", "Data Protection Officer", "RM-09", "2027-02-28", "No direct identifiers in cloud zone"),
    ("RM-14", "Long term (≤ 1 semester)", "Material approval workflow + prompt-injection filtering + human approval for bulk actions", "RC3", "R1", "C10, C11", "Head of Digital Learning", "RM-05", "2027-01-31", "Quarterly red-team prompt-injection test passes"),
    ("RM-15", "Long term (≤ 1 semester)", "Security review gate for new AI features; decommission process for pilot endpoints", "Process", "R1, R5", "C21", "IT Security Officer", "–", "2027-01-31", "Gate used for every release"),
    ("RM-16", "Long term (≤ 1 semester)", "IR playbook for agent/token compromise; training for developers and lecturers", "People, Governance", "R1, R4", "C21, C24", "IT Security Officer", "–", "2027-02-28", "Tabletop exercise completed"),
]
wb = Workbook()
meta = f"Artefact A3-3 · US-3.3 · owner {who(EFE)} · reviewed by {who(EGON)} · {VERSION} · {DATE}"
sheet(wb, "Roadmap", ["ID", "Phase", "Action", "Root cause", "Risks", "Controls (A2-3)", "Owner (role)", "Depends on", "Target", "Success measure / status"],
      RM, [7, 20, 58, 14, 10, 14, 22, 11, 12, 36], title="A3-3 Remediation Roadmap – INC-2026-001", meta=meta, first=True)
RES = [("R1", 4, 5, 2, 4, "Quota caps damage to ≤ 500 pseudonymised records/h; injection still possible but token and scopes limited"),
       ("R2", 3, 5, 1, 5, "mTLS + OAuth2 make unauthenticated access very unlikely; impact unchanged if it happens"),
       ("R3", 4, 4, 2, 3, "OBO + object checks; residual through bugs in authorisation logic"),
       ("R5", 3, 4, 2, 3, "Allow-list + pseudonymisation; residual re-identification risk")]
sheet(wb, "Residual risk", ["Risk", "L before", "I before", "Score before", "L after", "I after", "Score after", "Priority after", "Residual risk explanation"],
      [(r, l, i, l * i, l2, i2, l2 * i2, priority(l2 * i2), why) for r, l, i, l2, i2, why in RES],
      [7, 9, 9, 11, 9, 9, 11, 13, 70], title="Residual risk after roadmap (to be accepted by risk owners)", meta=meta, prio_col=7)
save_wb(wb, "EPA-IS-3/A3-3_Remediation_Roadmap.xlsx")
