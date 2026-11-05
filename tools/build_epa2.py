"""EPA-IS-2 Protect: secure API authentication (docx), trust architecture (docx), control matrix (xlsx), secure metadata transfer (docx)."""
import os
from openpyxl import Workbook
from common import *
from data import *
import diagrams as D

F = os.path.join(OUT, "EPA-IS-2")
os.makedirs(F, exist_ok=True)

# ================================================================== A2-1 Secure API design – authentication (US-2.1)
d = new_doc("Secure API Design – Authentication", "Who may talk to whom across the on-prem ↔ cloud boundary, and how they prove it",
            "A2-1", "US-2.1 Authenticate component communication", f"{who(VESANJA)}; reviewed by {who(EFE)}")
d.add_heading("1. Design goal", 1)
para(d, "The Metadata API (SYS-9) is the only bridge between the trusted on-premises core (Z2) and the untrusted cloud AI zone (Z5). "
        "This design makes sure that only known components talk to each other, and that every request is allowed for a specific purpose "
        "and – where relevant – for a specific user. Main risks addressed: R1 (manipulated AI agent), R2 (unauthenticated API), "
        "R3 (agent misused to read other students' grades). What data may cross the bridge is defined in A2-4.")
para(d, "Principles: zero trust between zones · deny by default · least privilege · defence in depth · fail closed · everything logged.", italic=True)

d.add_heading("2. Communicating components and trust relationships (AC1)", 1)
CC = [
    ("CC1", "User browser → Web portal (SYS-8)", "Z0 → Z1", "None (untrusted)", "HTTPS (TLS 1.3) through a web application firewall; single sign-on at SYS-4 with MFA"),
    ("CC2", "Web portal (SYS-8) → student systems (SYS-1, SYS-2, SYS-7)", "Z1 → Z2", "Portal trusted only for the logged-in user's data", "Mutual TLS; one service account per function; the user's identity is passed on and checked"),
    ("CC3", "AI agents (SYS-10, SYS-11) → Metadata API (SYS-9)", "Z5 → Z4", "Low – cloud is untrusted", "Mutual TLS (certificate per agent) + OAuth2 token valid for 5 minutes"),
    ("CC4", "Agent acting for a user → Metadata API (SYS-9)", "Z5 → Z4", "Low; must prove which user it works for", "The OAuth2 token contains both the agent and the user; only that user's rights apply"),
    ("CC5", "Metadata API (SYS-9) → MCP service (SYS-5)", "Z4 → Z2", "Medium – gateway is run by MUDT", "Mutual TLS; MCP checks token, rights and user again (no blind trust)"),
    ("CC6", "MCP service (SYS-5) → databases", "Z2 internal", "High", "Read-only access per tool; separate service account per tool; no write rights"),
    ("CC7", "Reporting dashboard (SYS-16) ← Metadata API (SYS-9)", "Z4 → Z5", "Low", "OAuth2 token that may only read aggregated reports"),
    ("CC8", "Agents → AI model / vector DB (SYS-12, SYS-13)", "Z5 internal", "Low", "Cloud identity per workload; private network endpoints; no public access"),
    ("CC9", "All components → audit logging (SYS-6)", "all → Z3", "Write-only", "TLS; components can write logs but never read or delete them"),
    ("CC10", "Administrators → servers / cloud console", "Z0 → Z3", "High privilege", "VPN + MFA + admin jump host; admin rights only when needed; sessions recorded"),
]
table(d, ["ID", "Communication", "Zones", "Trust relationship", "Authentication"], CC, widths=(1.1, 4.6, 1.7, 3.8, 5.8), font=8.5)

d.add_heading("3. Authentication decisions and justification (AC2)", 1)
table(d, ["Decision", "Why (risk reduced)", "Rejected alternative and reason"], [
    ("Mutual TLS on every connection between zones (CTL-01)", "Both sides prove who they are with a certificate; unknown callers and eavesdroppers are stopped (R2).",
     "Normal TLS only: encrypts, but does not identify the caller. IP allow-list only: an IP address is not an identity."),
    ("OAuth2 with tokens valid for only 5 minutes; no static API keys (CTL-02)",
     "A stolen token stops working within minutes (R1, R2).",
     "Static API keys: valid for months and shared – exactly what made the incident in EPA-IS-3 possible."),
    ("Tokens are added by the system, never shown to the AI model (CTL-02)",
     "Even a manipulated AI cannot leak a token it never saw (R1).",
     "Putting the token into the AI's instructions: convenient, but prompt injection can make the AI reveal it."),
    ("Agent requests carry the user's identity (CTL-04)", "MCP checks the rights of the real user, so a student cannot use the agent to read others' grades (R3).",
     "Agent uses one powerful account for everyone: simpler, but any user could reach any data through the agent."),
    ("MFA for all users, phishing-resistant security keys for staff and admins (CTL-03)", "A stolen password alone is not enough (R4, R6).",
     "SMS codes: can be intercepted (SIM swap, phishing pages)."),
], widths=(4.6, 6.2, 6.2), font=8.5)

d.add_heading("4. Authorisation design (role-based access, least privilege)", 1)
para(d, "Every request is checked twice: at the gateway (may this client call this endpoint?) and in the MCP service "
        "(may this user see this specific record?). Default is deny.")
table(d, ["Client / agent", "Allowed", "Explicitly denied"], [
    ("Tutor agent", "Read course materials of the user's courses; read the user's own progress", "Grades, lists of students, any change of data, free Internet access"),
    ("Document-search agent", "Read and search course materials", "Submissions of other users, any personal data"),
    ("Learning-insights agent (lecturer)", "Course statistics for the lecturer's own courses (groups of 10 or more)", "Data about individual students, other courses"),
    ("Reporting agent (scheduled)", "Read aggregated reports", "Any data about individual students"),
    ("Reporting dashboard (SYS-16)", "Read aggregated reports", "Everything else"),
], widths=(4.0, 7.0, 6.0), font=8.5)

d.add_heading("5. Failure conditions and residual risk (AC3)", 1)
table(d, ["Failure", "Behaviour", "Residual risk"], [
    ("Identity provider (SYS-4) unavailable", "Fail closed: no new tokens; existing tokens expire within 5 min", "AI features unavailable; accepted – the on-prem portal still works"),
    ("Certificate expired", "Connection refused", "Outage; reduced by automatic renewal and expiry alerts"),
    ("Token and certificate stolen together (cloud server fully taken over)", "Attacker can call the API until access is revoked", "Limited by narrow rights, 500 records/hour quota and alerts – damage capped, not zero"),
    ("Prompt injection still manipulates an agent", "Agent can only use its own narrow rights", "Wrong answers or misuse within its rights – accepted with monitoring (R1 residual)"),
    ("Gateway outage", "Cloud features unavailable; on-prem continues", "Accepted; the on-prem core does not depend on the cloud"),
], widths=(4.6, 5.6, 6.8), font=8.5)

d.add_heading("6. Reflected in the control artefacts (AC4)", 1)
table(d, ["Design element", "Risks", "Controls (A2-3)", "Shown in"], [
    ("Component authentication (sections 2–3)", "R1, R2", "CTL-01, CTL-02, CTL-03", "A2-2 flows F2, F4, F5, F10"),
    ("Authorisation and least privilege (section 4)", "R1, R3", "CTL-04", "A2-2 flows F3, F5, F7"),
    ("Failure handling (section 5)", "R1, R8", "CTL-06, CTL-11, CTL-15", "A2-2 layers 2, 4, 5"),
], widths=(6.0, 2.5, 4.5, 4.0), font=8.5)
save_doc(d, "EPA-IS-2/A2-1_Secure_API_Authentication.docx")

# ================================================================== A2-4 Secure API design – metadata transfer (US-2.2)
d = new_doc("Secure API Design – Metadata Transfer", "Which data may cross the on-prem ↔ cloud boundary, and how it is protected and monitored",
            "A2-4", "US-2.2 Secure metadata transfer", f"{who(EGON)}; reviewed by {who(VESANJA)}")
d.add_heading("1. Design goal", 1)
para(d, "Only approved, minimised data may leave the on-premises core through the Metadata API (SYS-9). "
        "This follows GDPR data minimisation: send the cloud only what it really needs. Main risks addressed: R5 (too much personal data "
        "in the cloud), R2 and R3 (data disclosure), R1 and R8 (detecting misuse). Who may call the API is defined in A2-1.")

d.add_heading("2. Allowed and prohibited data (AC1)", 1)
table(d, ["Class", "Examples", "May cross to cloud?"], [
    ("Public", "Course titles, public module handbook", "Yes"),
    ("Internal", "Course materials approved by the lecturer, deadlines", "Yes – after lecturer approval for AI use"),
    ("Confidential – pseudonymised / aggregated", "Learning progress per pseudonym, course statistics (groups of 10 or more)", "Yes – only allow-listed fields"),
    ("Confidential – identifying", "Names, e-mail, matriculation number, individual grades, chat history linked to a person", "No"),
    ("Strictly confidential", "Grade database, health/disability information, research data, passwords and keys, unreleased exam questions", "Never"),
], widths=(4.5, 8.5, 4.0), font=8.5)

d.add_heading("3. Endpoints", 1)
table(d, ["Endpoint", "Purpose", "Returned fields (allow-list)", "Limit"], [
    ("GET /v1/courses/{courseId}/materials", "Approved course materials for AI search", "materialId, title, version, approvedForAI", "60 requests/min"),
    ("GET /v1/me/progress", "The user's own progress, for tutoring", "pseudoId, courseId, modulesCompleted, nextDeadline", "60 requests/min, own data only"),
    ("GET /v1/courses/{courseId}/analytics", "Course statistics for lecturers", "courseId, week, activeLearners, avgCompletion (only groups ≥ 10)", "30 requests/min"),
    ("GET /v1/reports/{reportId}", "Coordinator reports", "Aggregated numbers only; digitally signed", "10 requests/min"),
], widths=(4.8, 4.2, 5.8, 2.2), font=8)
para(d, "There is deliberately no endpoint that lists students or returns grades – grades are only shown in the on-prem portal. "
        "Every client also has a hard quota of 500 records per hour; above it, requests are blocked and an alert is raised (CTL-06, CTL-11).", italic=True)
d.add_heading("3.1 Example response (pseudonymised)", 2)
p = d.add_paragraph()
r = p.add_run('{ "pseudoId": "p_7f3a91c2", "courseId": "CS301", "modulesCompleted": 4,\n  "nextDeadline": "2026-11-20" }')
r.font.name = "Courier New"; r.font.size = Pt(9)
note(d, "pseudoId is created from the matriculation number with a secret key that stays on-prem, so the cloud cannot turn it back into a real ID.")

d.add_heading("4. Confidentiality and integrity controls (AC2)", 1)
table(d, ["Control", "Protects", "How"], [
    ("CTL-01 TLS 1.3 (mutual)", "Confidentiality + integrity in transit", "Encryption and identity check on every connection"),
    ("CTL-05 Data minimisation", "Confidentiality", "Gateway drops every field not on the allow-list and blocks e-mails / matriculation numbers; pseudonyms instead of IDs; statistics only for groups ≥ 10"),
    ("Digitally signed reports", "Integrity", "The dashboard checks the signature before showing a report, so changed numbers are detected"),
    ("CTL-09 Encryption at rest", "Confidentiality in the cloud", "Cloud storage and vector DB encrypted with keys controlled by MUDT"),
    ("Input validation", "Integrity", "Fixed parameters and types only; no free query language"),
], widths=(4.5, 4.0, 8.5), font=8.5)

d.add_heading("5. Logging and monitoring (AC3)", 1)
para(d, "Every gateway and MCP decision creates one log entry in the tamper-proof audit log in Z3 (CTL-10): time (UTC), client, agent, "
        "user pseudonym, source IP, endpoint, decision (allowed/denied), number of records, token ID. No personal data and no content in logs.")
table(d, ["Alert (CTL-11)", "Threshold", "Why"], [
    ("Unusual volume per client", "> 500 records/hour or 3× the normal level", "Detects bulk data theft as in INC-2026-001"),
    ("Token used from a new IP address", "Any", "Sign of a stolen token"),
    ("Many denied requests", "> 20 in 5 minutes", "Probing or a manipulated agent"),
    ("Allow-list blocked a field", "Any", "Bug or attempt to send too much data (R5)"),
], widths=(5.5, 5.0, 6.5), font=8.5)

d.add_heading("6. Assumptions and alternatives (AC4)", 1)
bullets(d, ["**Assumption:** the cloud provider offers private network connections and an EU region (A2, A3).",
            "**Assumption:** lecturers mark which materials are approved for AI use.",
            "**Assumption:** a data processing agreement with the cloud/AI provider is in place (CTL-16).",
            "**Rejected – run the AI model fully on-prem:** removes the cloud boundary, but too expensive for MUDT now.",
            "**Rejected – VPN tunnel only:** encrypts the network but allows broad access and does not check each request.",
            "**Rejected – flexible query API (e.g. GraphQL):** free queries make the allow-list and quotas much harder to enforce.",
            "**Considered – fully anonymised data only:** safest, but personal tutoring would not work; used for the reporting agent."])
d.add_heading("7. Traceability", 1)
table(d, ["Design element", "Risks", "Controls (A2-3)"], [
    ("Allowed data, allow-list, pseudonyms (2–4)", "R2, R3, R5", "CTL-05, CTL-09, CTL-16"),
    ("Encryption in transit (4)", "R2", "CTL-01"),
    ("Quotas, logging and alerts (3, 5)", "R1, R8, R10", "CTL-06, CTL-10, CTL-11"),
], widths=(8.0, 4.0, 5.0), font=8.5)
save_doc(d, "EPA-IS-2/A2-4_Secure_Metadata_Transfer.docx")

# ================================================================== A2-2 Trust architecture
D.trust_architecture(os.path.join(F, "A2-2_trust_architecture.png"))
d = new_doc("Trust Architecture", "Separated trust zones and layered (defence-in-depth) controls", "A2-2",
            "US-2.3 Separate trust zones and design layered architecture", f"{who(EFE)}; reviewed by {who(EGON)}", landscape=True)
d.add_heading("1. Trust zones and permitted flows", 1)
image(d, os.path.join(F, "A2-2_trust_architecture.png"), 24.5)
d.add_heading("1.1 Zone definitions", 2)
table(d, ["ID", "Zone", "Trust level", "Content"], ZONES, widths=(1.5, 5.5, 5.5, 13.0))
d.add_heading("1.2 Flow register (only these flows are allowed – everything else is blocked)", 2)
FLOWS = [
    ("F1", "Users → Web portal (SYS-8)", "Z0 → Z1", "HTTPS (TLS 1.3), web application firewall, DDoS protection", "CTL-06, CTL-12"),
    ("F2", "Portal → Identity provider (SYS-4)", "Z1 → Z2", "Single sign-on with MFA; security keys for staff", "CTL-03"),
    ("F3", "Portal → student systems / grades / storage", "Z1 → Z2", "Mutual TLS, one service account per function, only the user's own data; four-eyes for grade changes", "CTL-04, CTL-13"),
    ("F4", "MCP (SYS-5) ↔ Metadata API (SYS-9)", "Z2 ↔ Z4", "Mutual TLS, allow-listed fields, pseudonyms", "CTL-01, CTL-05"),
    ("F5", "Agents (SYS-10/SYS-11) ↔ Metadata API (SYS-9)", "Z5 ↔ Z4", "Mutual TLS + 5-minute OAuth2 tokens with the user's identity, least privilege, rate limits", "CTL-02, CTL-04, CTL-06"),
    ("F6", "Metadata API → Reporting dashboard (SYS-16)", "Z4 → Z5", "Signed aggregated reports only", "CTL-05"),
    ("F7", "MCP → databases", "Z2 internal", "Read-only access per tool", "CTL-04"),
    ("F8", "Core → offline backups", "Z2 → Z3", "One-way, separate backup account, offline copy", "CTL-14"),
    ("F9", "All components → audit log (gateway shown)", "all → Z3", "Write-only, tamper-proof", "CTL-10"),
    ("F10", "Admins → jump host", "Z0 → Z3", "VPN + MFA + jump host, sessions recorded", "CTL-03, CTL-13"),
]
table(d, ["ID", "Flow", "Zones", "Protection", "Controls"], FLOWS, widths=(1.3, 6.5, 2.6, 11.0, 4.1))
para(d, "Blocked by design: Z1 → databases directly; Z5 → Z2 directly; Internet → Z3; cloud agents → any destination not on the egress allow-list; "
        "any flow carrying grades (SYS-2) or research data (SYS-3) out of Z2.", bold=True)

d.add_heading("2. Layered controls (defence in depth)", 1)
para(d, "If one layer fails, the next layer still limits the damage. The table shows for each layer which controls prevent, detect or correct an attack.")
LAYERS = [
    ("1 People and suppliers", "CTL-16 training, supplier contracts", "CTL-13 four-eyes check on grade changes", "CTL-15 incident response plan"),
    ("2 Identity", "CTL-02 short-lived tokens, CTL-03 MFA", "CTL-11 alert: token used from new IP", "CTL-15 revoke tokens"),
    ("3 Network / zones", "CTL-08 segmentation, firewalls, egress allow-list", "CTL-11 network anomaly alerts", "Isolate zone, block IP"),
    ("4 API gateway", "CTL-01 mutual TLS, CTL-05 data allow-list, CTL-06 rate limits", "CTL-10 gateway audit log", "CTL-15 kill-switch per client"),
    ("5 AI agents", "CTL-04 least privilege, CTL-07 AI agent safeguards", "CTL-11 usage monitoring", "CTL-15 switch off agent, remove document"),
    ("6 Data", "CTL-05 pseudonyms, CTL-09 encryption at rest", "CTL-12 configuration checks (no public storage)", "CTL-14 restore from offline backup"),
    ("7 Platform and software", "CTL-12 patching, signed builds; CTL-13 protected admin access", "CTL-12 dependency checks, anti-malware", "Rebuild from signed software"),
]
table(d, ["Layer", "Preventive", "Detective", "Corrective"], LAYERS, widths=(4.5, 9.0, 6.0, 6.0))

d.add_heading("3. Dependencies and failure paths (US-2.3 AC3)", 1)
table(d, ["Dependency / single point of failure", "Failure path", "How the architecture contains it"], [
    ("Identity provider SYS-4", "SYS-4 taken over → attacker creates tokens for anyone", "SYS-4 in the protected core; admin access only via jump host with MFA; alerts on unusual token creation"),
    ("Metadata API SYS-9", "Gateway taken over → allow-list bypassed", "MCP checks every token and record again (no blind trust); logs are written to Z3, out of the attacker's reach"),
    ("Cloud zone Z5", "Whole cloud zone taken over", "The cloud only holds pseudonymised/approved data; no route into Z2; kill-switch at the gateway"),
    ("Audit log SYS-6", "Attacker deletes evidence", "Tamper-proof storage, separate admin accounts"),
    ("Backups S18", "Ransomware encrypts backups", "Offline copy, separate credentials, regular restore tests"),
    ("Pseudonymisation key", "Key leaks → pseudonyms can be traced back", "Key stays in the on-prem vault, never sent to the cloud, changed yearly"),
], widths=(5.5, 7.0, 13.0))

d.add_heading("4. Risk cross-reference (US-2.3 AC4)", 1)
rows = []
for r in sorted(RISKS, key=lambda r: -r[6] * r[8]):
    toks = [t.strip().split(" ")[0] for c in r[12].split(", ") for t in get(CONTROLS, c)[5].split(",")]
    comp_zone = {k[0]: k[2] for k in COMPONENTS}
    zones = {comp_zone[t] for t in toks if t in comp_zone} | {t for t in toks if t[:1] == "Z" and t[1:2].isdigit()}
    rows.append((r[0], r[1], f"{r[6] * r[8]} {priority(r[6] * r[8])}", r[12], ", ".join(sorted(zones)) or "organisation-wide"))
table(d, ["Risk", "Statement", "Score", "Controls in this architecture", "Zones enforcing"], rows, widths=(1.3, 11.0, 2.4, 6.5, 4.3), font=8, prio_col=None)
save_doc(d, "EPA-IS-2/A2-2_Trust_Architecture.docx")

# ================================================================== A2-3 Control matrix
wb = Workbook()
meta = f"Artefact A2-3 · US-2.1/2.2/2.3 · owner {who(EFE)} · reviewed by {who(EGON)} · {VERSION} · {DATE}"
rows = [(c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], "Planned") for c in CONTROLS]
sheet(wb, "Control matrix", ["ID", "Control", "Type", "Function", "NIST CSF 2.0", "Where (component/zone)", "Risks reduced", "Story", "Status"],
      rows, [6, 62, 14, 18, 20, 24, 18, 9, 10], title="A2-3 Control Matrix", meta=meta, first=True)
rids = [r[0] for r in RISKS]
mrows = []
for c in CONTROLS:
    linked = c[6].replace(" ", "").split(",")
    mrows.append([c[0]] + ["●" if r in linked else "" for r in rids])
mrows.append(["# controls"] + [sum(1 for c in CONTROLS if r in c[6].replace(" ", "").split(",")) for r in rids])
ws = sheet(wb, "Risk × control", ["Control"] + rids, mrows, [12] + [6] * len(rids), title="Which control reduces which risk", meta=meta)
from collections import Counter
cnt = Counter(c[3] for c in CONTROLS); tcnt = Counter(c[2] for c in CONTROLS)
sheet(wb, "Coverage summary", ["Dimension", "Value", "Count"],
      [("Function", k, v) for k, v in cnt.items()] + [("Type", k, v) for k, v in tcnt.items()] +
      [("Risk without control", ", ".join(r for r in rids if not any(r in c[6].replace(" ", "").split(",") for c in CONTROLS)) or "none", 0)],
      [22, 30, 8], title="Coverage check", meta=meta)
save_wb(wb, "EPA-IS-2/A2-3_Control_Matrix.xlsx")
