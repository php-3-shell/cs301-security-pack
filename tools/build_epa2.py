"""EPA-IS-2 Protect: secure API design (docx), trust architecture (docx), control matrix (xlsx)."""
import os
from openpyxl import Workbook
from common import *
from data import *
import diagrams as D

F = os.path.join(OUT, "EPA-IS-2")
os.makedirs(F, exist_ok=True)

# ================================================================== A2-1 Secure API design
d = new_doc("Secure Metadata API Design", "Authenticated component communication and protected metadata transfer across the on-prem ↔ cloud boundary",
            "A2-1", "US-2.1 Authenticate component communication · US-2.2 Secure metadata transfer",
            f"{who(VESANJA)} – authentication (US-2.1); {who(EGON)} – metadata transfer (US-2.2)")

d.add_heading("1. Design goal", 1)
para(d, "The Metadata API (C9) is the only bridge between the trusted on-premises core (Z2) and the untrusted cloud AI zone (Z5). "
        "The design must ensure that (a) only known, authenticated components talk to each other, (b) every request is authorised for "
        "a specific purpose and – where relevant – for a specific end user, and (c) only approved, minimised data crosses the boundary. "
        "Main risks addressed: R1 (prompt-injected agent), R2 (unauthenticated API), R3 (confused deputy), R5 (over-sharing).")
para(d, "Design principles: zero trust between zones · deny by default · least privilege · data minimisation (GDPR Art. 5) · "
        "defence in depth · fail closed · everything logged.", italic=True)

d.add_heading("2. Communicating components and trust relationships (US-2.1 AC1)", 1)
CC = [
    ("CC1", "User browser → Web portal (C8)", "Z0 → Z1", "None (untrusted)", "HTTPS TLS 1.3 via WAF; OIDC login at C4; MFA (FIDO2 for staff)"),
    ("CC2", "Web portal (C8) → SIS/Grades/Storage (C1, C2, C7)", "Z1 → Z2", "Portal service identity trusted for user-scoped reads", "mTLS + DB service account per function; user identity passed and checked"),
    ("CC3", "Agent orchestrator / agents (C10, C11) → Metadata API (C9)", "Z5 → Z4", "Low – cloud is untrusted", "mTLS (client cert per workload) + OAuth2 client credentials; sender-constrained 5-min token"),
    ("CC4", "Agent acting for a user → Metadata API (C9)", "Z5 → Z4", "Low; must prove user context", "OAuth2 token exchange (on-behalf-of): token contains user ID + agent ID; scope narrowed"),
    ("CC5", "Metadata API (C9) → MCP service (C5)", "Z4 → Z2", "Medium – gateway is controlled by MUDT", "mTLS with gateway certificate; MCP re-validates token, scope and user (no implicit trust)"),
    ("CC6", "MCP service (C5) → SIS / Grade DB / Storage", "Z2 internal", "High", "Read-only DB views per tool; separate service account per tool; no write rights"),
    ("CC7", "Reporting dashboard (C16) ← Metadata API (C9)", "Z4 → Z5", "Low", "Pull via OAuth2 client credentials, scope report:read-aggregates only"),
    ("CC8", "Agents → LLM inference / vector DB (C12, C13)", "Z5 internal", "Low", "Cloud workload identity (IAM role), private endpoints, no public access"),
    ("CC9", "All components → Audit logging (C6)", "all → Z3", "Write-only", "TLS; append-only ingestion; components cannot read or delete logs"),
    ("CC10", "Administrators → servers / cloud console", "Z0 → Z3", "High privilege", "VPN + FIDO2 MFA + PAM jump host; just-in-time rights; session recording"),
]
table(d, ["ID", "Communication", "Zones", "Trust relationship", "Authentication mechanism"], CC, widths=(1.1, 4.6, 1.7, 3.8, 5.8), font=8.5)

d.add_heading("3. Authentication decisions and justification (US-2.1 AC2)", 1)
table(d, ["Decision", "Why (risk reduced)", "Rejected alternative and reason"], [
    ("Mutual TLS on every cross-zone call (C01)", "Both sides prove identity with certificates; stops unknown callers and man-in-the-middle (R2).",
     "Server-only TLS: encrypts but does not identify the client. IP allow-list only: IPs in cloud change and do not prove identity."),
    ("OAuth2 client credentials, 5-minute tokens, audience-bound, bound to the mTLS certificate (C02)",
     "A stolen token expires quickly and cannot be used from another machine without the private key (R1, R2).",
     "Static API keys: long-lived, shared, cannot be scoped per agent – exactly what made the token theft in AP1 useful."),
    ("Token exchange on-behalf-of the user (C03)", "MCP knows which user an agent works for and checks the user's own rights (R3 confused deputy).",
     "Agent uses its own broad service account for every user: simpler but lets any user reach any data through the agent."),
    ("Tokens and secrets never enter the LLM context; the tool runtime adds them (C10, C14)",
     "Even a fully manipulated model cannot reveal a token it never saw (R1).",
     "Passing headers through the prompt/tool description: convenient for developers, exposes secrets to prompt injection."),
    ("Phishing-resistant MFA for staff and admins (C04)", "Password theft alone is not enough (R4, R6).",
     "SMS one-time codes: vulnerable to SIM-swap and real-time phishing proxies."),
], widths=(4.6, 6.2, 6.2), font=8.5)

d.add_heading("4. Authorisation design", 1)
para(d, "Every request is checked twice: at the gateway (is this client allowed to call this endpoint with this scope?) and at the MCP service "
        "(is this user/agent allowed to see this specific object?). Default is deny.")
table(d, ["Client / agent", "Allowed scopes", "Explicitly denied"], [
    ("Tutor agent", "materials:read (course the user is enrolled in), progress:read:self (OBO only)", "grades:*, students:list, any write, generic HTTP tool"),
    ("Document-search agent", "materials:read, materials:search", "submissions of other users, any personal data"),
    ("Learning-insights agent (lecturer)", "analytics:read:course-aggregate (k ≥ 10, OBO lecturer of that course)", "individual-level records, other courses"),
    ("Reporting agent (scheduled)", "report:read-aggregates", "any per-student endpoint"),
    ("Reporting dashboard (C16)", "report:read-aggregates", "everything else"),
], widths=(4.0, 7.0, 6.0), font=8.5)
para(d, "Object-level rule in MCP (C05): a request for progress of student X is allowed only if the OBO token subject = X, "
        "or the subject is a lecturer of a course X is enrolled in and the endpoint returns aggregates only.", italic=True)

d.add_heading("5. Metadata transfer specification (US-2.2)", 1)
d.add_heading("5.1 Data classification and boundary rule (US-2.2 AC1)", 2)
table(d, ["Class", "Examples", "May cross to cloud?"], [
    ("Public", "Course titles, public module handbook", "Yes"),
    ("Internal", "Course materials approved by the lecturer, deadlines", "Yes – after lecturer approval for AI use"),
    ("Confidential – pseudonymised / aggregated", "Engagement metrics per pseudonym, course-level statistics (k ≥ 10)", "Yes – only via allow-listed fields"),
    ("Confidential – identifying", "Names, e-mail, matriculation number, individual grades, chat history linked to identity", "No"),
    ("Strictly confidential", "Grade database, health/disability adjustments, research data, credentials, unreleased exam questions", "Never"),
], widths=(4.5, 8.5, 4.0), font=8.5)
d.add_heading("5.2 Endpoints", 2)
table(d, ["Endpoint", "Purpose", "Returned fields (allow-list)", "Scope", "Limits"], [
    ("GET /v1/courses/{courseId}/materials", "Course material metadata and approved content for RAG", "materialId, title, version, approvedForAI, contentHash", "materials:read", "60 req/min"),
    ("GET /v1/me/progress", "Own learning progress for tutor personalisation", "pseudoId, courseId, modulesCompleted, nextDeadline", "progress:read:self (OBO)", "60 req/min, 1 subject"),
    ("GET /v1/courses/{courseId}/analytics", "Aggregated engagement for lecturers", "courseId, week, activeLearners, avgCompletion (k ≥ 10)", "analytics:read:course-aggregate", "30 req/min"),
    ("GET /v1/reports/{reportId}", "Coordinator reports", "aggregate metrics only; signed (JWS)", "report:read-aggregates", "10 req/min"),
], widths=(4.4, 3.6, 4.6, 2.6, 1.8), font=8)
para(d, "There is deliberately no endpoint that lists students or returns grades. Grades are shown only in the on-prem portal (CC2). "
        "Hard quota for every client: 500 records per hour; requests above the quota are blocked and alerted (C09, C16).", italic=True)
d.add_heading("5.3 Example response (pseudonymised)", 2)
p = d.add_paragraph()
r = p.add_run('{ "pseudoId": "p_7f3a91c2", "courseId": "CS301", "modulesCompleted": 4,\n  "nextDeadline": "2026-11-20", "_class": "confidential-pseudonymised" }')
r.font.name = "Courier New"; r.font.size = Pt(9)
note(d, "pseudoId = HMAC-SHA256(matriculationNo, secret key). The key stays in the on-prem vault (S17), so the cloud cannot reverse it (C08).")

d.add_heading("5.4 Confidentiality and integrity controls (US-2.2 AC2)", 2)
table(d, ["Control", "Protects", "How"], [
    ("C01 mTLS / TLS 1.3", "C + I in transit", "Encryption and mutual authentication on every hop"),
    ("C07 Schema allow-list + outbound filter", "C (minimisation)", "Gateway drops any field not in the allow-list; pattern checks block e-mails/matriculation numbers"),
    ("C08 Pseudonymisation + k-anonymity", "C", "Keyed HMAC pseudonyms; aggregates suppressed when group < 10"),
    ("JWS signature on reports", "I", "Reports signed by gateway key; dashboard verifies signature before display"),
    ("C13 Encryption at rest with customer-managed keys", "C at rest in cloud", "Cloud storage and vector DB encrypted with MUDT-controlled keys"),
    ("Input validation", "I", "Strict types, max lengths, no free-text query language (no GraphQL/SQL passthrough)"),
], widths=(5.0, 3.0, 9.0), font=8.5)

d.add_heading("6. Logging and monitoring (US-2.2 AC3)", 1)
para(d, "Every gateway and MCP decision produces one log event, sent to the append-only audit log in Z3 (C15). "
        "Fields: timestamp (UTC), clientId, agentId, OBO subject (pseudonym), source IP, certificate fingerprint, endpoint, scope, "
        "decision (allow/deny), records returned, response size, token ID (jti). No payloads and no personal data in logs (C26).")
table(d, ["Alert (C16)", "Threshold", "Why"], [
    ("Volume anomaly per client", "> 500 records/hour or > 3× 7-day baseline", "Detects bulk extraction such as INC-2026-001"),
    ("Token used from new IP / certificate mismatch", "Any", "Indicates token theft"),
    ("Denied requests burst", "> 20 denies in 5 min", "Probing or manipulated agent"),
    ("Outbound filter hit", "Any blocked field", "Indicates over-sharing bug or exfiltration attempt (R5)"),
    ("Off-hours admin access to gateway config", "Any", "Insider / admin compromise (R6)"),
], widths=(5.5, 5.0, 6.5), font=8.5)

d.add_heading("7. Failure conditions and residual risk (US-2.1 AC3)", 1)
table(d, ["Failure", "Behaviour", "Residual risk"], [
    ("Identity provider (C4) unavailable", "Fail closed: no new tokens; existing tokens expire within 5 min", "Availability loss of AI features; accepted – grades/portal still usable with cached SSO sessions"),
    ("Certificate expired", "Connection refused", "Outage; mitigated by automatic rotation and expiry alerts (C14)"),
    ("Token stolen together with workload key (full cloud host compromise)", "Attacker can call API until token/cert revoked", "Limited by scopes, 500 records/hour quota and alerting – damage capped, not zero"),
    ("Outbound filter rule wrong", "Data could be over-shared", "Detected by filter-hit monitoring and quarterly data-flow review"),
    ("Prompt injection still manipulates agent", "Agent can only use its narrow scopes", "Agent may give wrong answers or misuse its own data scope – accepted with monitoring (R1 residual)"),
    ("Gateway outage", "Cloud features unavailable; on-prem continues", "Accepted; on-prem core does not depend on cloud"),
], widths=(4.6, 5.6, 6.8), font=8.5)

d.add_heading("8. Assumptions and alternatives (US-2.2 AC4)", 1)
bullets(d, ["**Assumption:** cloud provider offers private connectivity and workload identity (A2, A3).",
            "**Assumption:** lecturers mark which materials are approved for AI use.",
            "**Alternative rejected – run the LLM fully on-prem:** removes the cloud boundary but too expensive and not scalable for MUDT now; reconsider for strictly confidential use cases.",
            "**Alternative rejected – VPN tunnel only:** encrypts the network but grants broad network access and no per-request identity.",
            "**Alternative rejected – GraphQL API:** flexible queries make allow-listing and quotas much harder.",
            "**Alternative considered – synthetic or fully anonymised data only:** safest, but tutor personalisation would not work; kept for reporting agent."])
d.add_heading("9. Traceability", 1)
table(d, ["Design element", "Risks", "Controls", "Story"], [
    ("Component authentication (sections 2–3)", "R1, R2", "C01, C02, C04, C14", "US-2.1"),
    ("Authorisation and OBO (section 4)", "R1, R3", "C03, C05, C06", "US-2.1"),
    ("Data allow-list, pseudonymisation (5)", "R3, R5", "C07, C08, C13, C25", "US-2.2"),
    ("Logging and alerting (6)", "R1, R8, R10", "C15, C16, C26", "US-2.2"),
], widths=(6.5, 3.0, 4.5, 3.0), font=8.5)
save_doc(d, "EPA-IS-2/A2-1_Secure_API_Design.docx")

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
    ("F1", "Users → Web portal (C8)", "Z0 → Z1", "HTTPS 443, TLS 1.3, WAF, DDoS protection", "C27, C29"),
    ("F2", "Portal → Identity provider (C4)", "Z1 → Z2", "OIDC; MFA; FIDO2 for staff", "C04"),
    ("F3", "Portal → SIS / grades / storage", "Z1 → Z2", "mTLS, per-function service accounts, user-scoped queries; four-eyes for grade changes", "C05, C23"),
    ("F4", "MCP (C5) ↔ Metadata API (C9)", "Z2 ↔ Z4", "mTLS, allow-listed fields, pseudonymisation", "C01, C07, C08"),
    ("F5", "Agents (C10/C11) ↔ Metadata API (C9)", "Z5 ↔ Z4", "mTLS + 5-min OAuth2 tokens, OBO, scopes, rate limits", "C02, C03, C06, C09"),
    ("F6", "Metadata API → Reporting dashboard (C16)", "Z4 → Z5", "Signed aggregate reports only", "C07, C08"),
    ("F7", "MCP → data stores", "Z2 internal", "Read-only views per tool", "C05, C06"),
    ("F8", "Core → immutable backups", "Z2 → Z3", "One-way, backup service account, offline copy", "C20"),
    ("F9", "All components → audit log / SIEM (gateway shown)", "all → Z3", "Append-only, no read-back", "C15, C26"),
    ("F10", "Admins → jump host", "Z0 → Z3", "VPN + FIDO2 + PAM, session recording", "C04, C19"),
]
table(d, ["ID", "Flow", "Zones", "Protection", "Controls"], FLOWS, widths=(1.3, 6.5, 2.6, 11.0, 4.1))
para(d, "Blocked by design: Z1 → databases directly; Z5 → Z2 directly; Internet → Z3; any flow carrying grades (C2) or research data (C3) out of Z2.", bold=True)

d.add_heading("2. Layered controls (defence in depth)", 1)
para(d, "If one layer fails, the next layer still limits the damage. The table shows for each layer which controls prevent, detect or correct an attack.")
LAYERS = [
    ("1 Governance and people", "C24 training, C25 supplier DPA, C11 human approval", "C23 four-eyes audit trail", "C21 incident response plan"),
    ("2 Identity", "C02 short-lived tokens, C03 OBO, C04 FIDO2 MFA, C14 secrets vault", "C16 token-from-new-IP alert", "C22 token revocation"),
    ("3 Network / zones", "C12 segmentation, private interconnect, C27 DDoS protection", "C16 network anomaly alerts", "Isolate zone / block IP"),
    ("4 API gateway", "C01 mTLS, C07 allow-list, C09 rate limits", "C15 gateway logs", "C22 kill-switch per client"),
    ("5 AI agents", "C06 least-privilege tools, C10 injection defences, C28 grounding", "C14/C16 usage monitoring", "C22 disable agent, quarantine document"),
    ("6 Data", "C08 pseudonymisation, C13 encryption at rest", "C17 posture scans for public storage", "C20 restore from immutable backup"),
    ("7 Platform and supply chain", "C18 signed builds, C29 patching, C19 PAM", "C29 EDR, C18 dependency scans", "Rebuild from signed artefacts"),
]
table(d, ["Layer", "Preventive", "Detective", "Corrective"], LAYERS, widths=(4.5, 9.0, 6.0, 6.0))

d.add_heading("3. Dependencies and failure paths (US-2.3 AC3)", 1)
table(d, ["Dependency / single point of failure", "Failure path", "How the architecture contains it"], [
    ("Identity provider C4", "C4 compromised → attacker issues tokens for any identity", "C4 in Z2 core, admin only via PAM; FIDO2; tokens audience-bound; alerts on unusual token issuance"),
    ("Metadata API C9", "Gateway compromised → filter bypass", "MCP re-checks every token and object (no implicit trust); outbound filter also in MCP; logs written to Z3"),
    ("Cloud zone Z5", "Full cloud compromise", "Cloud only ever holds pseudonymised/approved data; no route into Z2; kill-switch at gateway"),
    ("Audit log C6", "Attacker deletes evidence", "WORM storage, separate admin accounts, log forwarding"),
    ("Backups S18", "Ransomware encrypts backups", "Offline immutable copy, separate credentials, quarterly restore test"),
    ("HMAC pseudonymisation key", "Key leaks → pseudonyms reversible", "Key in on-prem vault, never sent to cloud, annual rotation"),
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
