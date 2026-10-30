# Study Guide – defend your work in the oral presentation

Individual presentation = 60 % of the grade. The lecturer asks unseen questions, mainly these five (slide 17):
**(1) Which risk does this reduce? (2) What assumption does it rely on? (3) What happens if the control fails? (4) Which alternative did you reject, and why? (5) What residual risk remains?**
For each story below, there is a short "what we did" and an answer to all five. Learn the reasoning, not the wording.

**Who presents what:** Egon – US-1.1, 1.3, 2.2, 3.1, 3.3 · Vesanja – US-1.2, 2.1, 2.3, 3.2. Each of you also reviewed the other's stories, so be ready for questions on those too.

---

## The whole story in 60 seconds

MUDT runs an AI learning platform. Sensitive data (students, grades, research) sits **on-premises** (trusted). AI agents and the LLM run in the **cloud** (untrusted). The only bridge is the **Metadata API**, which may carry only approved, minimised data.
We first **assessed** what is valuable and what could go wrong (assets → threats → risks). The top risk was **R1**: a prompt-injected AI agent leaking its token and bulk-reading student data. We then **designed protection**: strong authentication on the bridge, narrow agent permissions, data minimisation, separated zones, layered controls. Finally we **investigated** a simulated incident where exactly R1 happened, because the controls were still only planned. We found its root causes and planned remediation.
Story arc: *risk identified → controls designed → incident shows why they matter → improvement.*

## Key terms (lecture slide 20)

| Term | Meaning | MUDT example |
|---|---|---|
| Asset | Something valuable | Student personal data (E1) |
| Threat | Potential cause of harm | Prompt injector (TA3) |
| Vulnerability | A weakness | Agent sees its own token in its context |
| Risk | Possible harmful outcome = likelihood × impact | Bulk disclosure of student records (R1, 4×5 = 20) |
| Impact | Consequence | GDPR breach, notification, loss of trust |
| Control | Reduces risk | Short-lived tokens, least-privilege scopes (C02, C06) |

Traps: *threat ≠ risk*. *Missing authentication* is a **vulnerability**, not a threat. A **root cause** explains *why* an event was possible. "Token theft" is an event, not a root cause.
**CIA**: Confidentiality (only authorised people see it), Integrity (not changed without authorisation), Availability (usable when needed).
**Preventive / detective / corrective**: stops it / notices it / repairs it.

---

## EPIC 1 – Assess

### US-1.1 Identify critical assets (Egon)
**What we did:** listed components and zones from the lecture architecture. We separated **essential** assets (information/processes with business value, E1–E11) from **supporting** assets (systems, people, suppliers they depend on, S1–S22), then rated each on C, I and A with a justification.
**Why it matters:** attackers usually hit a supporting asset (e.g. the API gateway) to harm an essential one (student data).
1. **Risk reduced:** prevents protecting the wrong things. Every later risk points to an asset ID.
2. **Assumption:** asset owners are roles we proposed and must be confirmed by MUDT. There's a web portal in a DMZ (A1).
3. **If wrong:** a missed asset leaves a blind spot. That's why the register is reviewed and cross-checked against the risk register.
4. **Rejected:** rating only "high/low" overall. Separate C/I/A shows *what kind* of protection is needed: grades need integrity most, chat logs need confidentiality.
5. **Residual:** ratings are judgement calls. Re-identification from "pseudonymised" metadata (E5) remains possible.

### US-1.2 Threats and attack paths (Vesanja)
**What we did:** 6 threat actors with goals, 8 entry points, 7 trust boundaries, 8 attack paths (AP1–AP8) that connect actor → entry → weakness → asset.
**Key insight:** TB5 isn't a network boundary. It's the line between **data and instructions** inside the LLM. Any text an agent reads can try to give it orders (prompt injection).
1. **Risk reduced:** makes R1–R11 concrete, so controls target real paths.
2. **Assumption:** paths are hypotheses. No vulnerability was tested (A6).
3. **If wrong:** an unmodelled path stays unprotected, so detective controls (logging, alerts) are the safety net.
4. **Rejected:** listing only "hackers". Insiders, students, suppliers and plain errors (R12) also matter.
5. **Residual:** new AI attack techniques appear fast, so the model must be updated each sprint.

### US-1.3 Prioritise risks (Egon)
**What we did:** 12 risk statements (threat + vulnerability + asset + impact). Scored likelihood × impact on the 5×5 matrix from slide 35 with written reasons, then set priority and initial treatment.
**Top risks:** R1 = 20 (Critical), R3 and R4 = 16 (Critical).
1. **Risk reduced:** focuses limited effort on the worst risks first.
2. **Assumption:** the scales and bands from slide 35. Ratings are inherent (before new controls).
3. **If scoring is wrong:** a risk is under-treated. Mitigated by a four-eyes review and written rationale for every number.
4. **Rejected:** a purely numeric score without rationale. The lecturer explicitly wants the reasoning ("document rationale, not only the number").
5. **Residual:** scores are subjective. After controls, R1 drops to 2×4 = 8 (Medium), not zero.

---

## EPIC 2 – Protect

### US-2.1 Authenticate component communication (Vesanja)
**What we did:** listed 10 communication paths (CC1–CC10). Chose **mTLS** (both sides prove identity), **OAuth2 client credentials with 5-minute tokens bound to the certificate**, **on-behalf-of tokens** carrying the end user, and **FIDO2 MFA** for staff.
1. **Risk reduced:** R2 (unauthenticated API), R1 (stolen token is useless after 5 minutes or from another machine), R3 (on-behalf-of lets MCP check the real user).
2. **Assumption:** the cloud supports workload identity and private connectivity. The identity provider is well protected.
3. **If it fails:** identity provider down → fail closed (AI features stop, the on-prem portal still works). Certificate expiry → outage, so automatic rotation and alerts.
4. **Rejected:** static API keys (long-lived and shared, exactly what made the incident possible). IP allow-lists alone (an IP isn't an identity). SMS codes (phishable).
5. **Residual:** if the whole cloud host is taken over, the attacker can use the token until it's revoked. Damage is capped by scopes, quotas and alerts.

### US-2.2 Secure metadata transfer (Egon)
**What we did:** a data classification with a clear rule for what may cross to the cloud. Grades, names and research data **never** do. Only allow-listed fields pass, with **keyed pseudonyms** (HMAC, key stays on-prem) and **k-anonymity ≥ 10** for aggregates. Every request is logged without payloads, and alerts fire on volume (> 500 records/h).
1. **Risk reduced:** R5 (over-sharing / GDPR data minimisation), R2, R3, plus detection for R1.
2. **Assumption:** lecturers mark materials approved for AI. The cloud can't reverse the pseudonyms because it never gets the key.
3. **If it fails:** a wrong filter rule could over-share. Filter-hit monitoring and quarterly data-flow review catch it.
4. **Rejected:** fully on-prem LLM (too expensive now), VPN only (no per-request identity), GraphQL (too flexible to allow-list).
5. **Residual:** pseudonymised data can sometimes be re-identified by combining it with other data.

### US-2.3 Trust zones and layered architecture (Vesanja)
**What we did:** 6 zones (Z0–Z5), a flow register (F1–F10) where *everything else is blocked*, 7 defence-in-depth layers with preventive/detective/corrective controls, failure paths for each single point of failure, and a control matrix (C01–C30) with a risk × control coverage check.
1. **Risk reduced:** contains a compromise. A fully compromised cloud zone still has no route into the core (R1, R2, R9).
2. **Assumption:** network rules are enforced as drawn. There's no hidden extra route between cloud and core (A3).
3. **If one layer fails:** the next layer still limits damage. Example: the gateway is bypassed, but MCP re-checks every token and object.
4. **Rejected:** a flat network trusting anything "internal". One foothold would reach everything.
5. **Residual:** the identity provider and gateway are critical dependencies. They're heavily protected but remain high-value targets.

---

## EPIC 3 – Investigate (simulated incident INC-2026-001)

### US-3.1 Reconstruct attack timeline (Egon)
**What happened:** a PDF with hidden text was uploaded and indexed. The tutor agent read it, followed the instruction and sent out its 30-day token. The attacker used the token from 203.0.113.45 for about 10,000 requests and got about 11,800 student records. A cloud cost alert fired after 71 minutes, and containment came at 96 minutes. The authority was notified within 72 hours (GDPR Art. 33).
**Method:** each event has a timestamp, evidence ID (EV-01–EV-11), and is marked **fact / inferred / assumption**.
1. **Risk:** R1. The timeline shows the attack path AP1 actually happening.
2. **Assumption:** log clocks are synchronised (UTC). The logs weren't tampered with (stored append-only).
3. **If evidence is missing:** the event is marked "inferred" with lower confidence instead of being presented as fact.
4. **Rejected:** a story without evidence references. It couldn't be verified or defended.
5. **Residual uncertainty:** whether the attacker kept the data. We assume yes for notification.

### US-3.2 Determine root causes (Vesanja)
**Root causes:** RC1 secrets visible to the model, plus long-lived unbound tokens. RC2 excessive agent rights. RC3 untrusted content treated as instructions. RC4 over-exposed legacy endpoint. RC5 no quotas or security alerts. RC6 unrestricted internet egress. Contributing factors: no security review of agent configuration, pilot endpoint never removed, no training, no owner.
**Method:** five whys, then mapping each cause to the missing controls from the control matrix.
1. **Risk:** R1 and R5. It explains *why* the risk materialised.
2. **Assumption:** the uploader's account wasn't compromised. This is still open, so it's recorded as uncertain.
3. **If we stop at the event:** fixing only "that token" leaves every cause in place, and the attack repeats with a new document.
4. **Rejected hypothesis:** token leaked via CI logs. The tool trace shows it leaving at 08:12:41, and misuse started 18 minutes later from a new IP.
5. **Residual:** prompt injection can't be fully prevented at model level. Defence must sit outside the model.

### US-3.3 Recommend corrective actions (Egon)
**What we did:** 16 actions in 4 phases: containment 0–24 h, recovery 1–7 days, short term ≤ 30 days, long term ≤ 1 semester. Each has a root cause, risk, control, owner role, dependency, target date and success measure, plus a residual risk table (before/after).
1. **Risk:** R1 goes from 20 to 8, R2 from 15 to 5, R3 from 16 to 6, R5 from 12 to 6.
2. **Assumption:** budget and staff exist for the short-term actions. The order respects dependencies (e.g. new tokens before scopes).
3. **If an action is late:** the containment measures (restricted tutor mode, removed tools, quotas) keep exposure low meanwhile.
4. **Rejected:** shutting down the AI platform permanently. That removes the business value, and the risk can be reduced to an acceptable level.
5. **Residual:** an attacker could still misuse an agent within its narrow scope (≤ 500 pseudonymised records/hour). This must be formally accepted by the risk owner.

---

## Likely transfer questions – quick answers

- *Why is the cloud "untrusted" if MUDT pays for it?* We don't control its staff, hardware or other tenants, and agents process untrusted text. So we assume compromise and minimise what it holds.
- *Encryption vs authentication?* Encryption keeps data secret in transit. Authentication proves who is talking. TLS without client authentication still accepts anyone.
- *Why short-lived tokens if we have mTLS?* Defence in depth. A token alone is useless without the key, and expires in 5 minutes even if both leak.
- *Mitigation vs remediation?* Mitigation reduces the immediate damage (revoke the token). Remediation removes the cause (redesign the token handling).
- *How does this map to NIST CSF?* Govern/Identify = Epic 1, Protect = Epic 2, Detect/Respond/Recover = Epic 3. Every control in A2-3 has its CSF function.
