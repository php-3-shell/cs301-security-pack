"""EPA-IS-1 Assess: risk concept map (docx), asset register (xlsx), risk register (xlsx), threat model (docx)."""
import os
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font
from common import *
from data import *
import diagrams as D

F = os.path.join(OUT, "EPA-IS-1")
os.makedirs(F, exist_ok=True)
LVL = {1: "Low", 2: "Medium", 3: "High"}

# ------------------------------------------------------------------ diagrams
CHAINS = [
    ("A1-1_cm_R2", "Concept map 1 (Workshop 1) – unauthenticated Metadata API", "TA1 External attacker",
     "Missing authentication on the Metadata API (SYS-9)", "E5 Student analytics / learning metadata (via SYS-9 Metadata API)",
     "Unauthorised access to learning data", "Data disclosure, GDPR consequences, loss of trust (E11)",
     "CTL-02 OAuth2 authentication + CTL-01 mutual TLS", "R2"),
    ("A1-4_cm_R1", "Concept map 2 – AI agent manipulated by prompt injection", "TA3 Prompt injector (hidden text in uploaded document)",
     "Agent treats retrieved text as instructions; too many rights; token visible to the AI",
     "E1 Student personal data, E4 learning records, E8 agent token",
     "Bulk disclosure of student records through the agent", "Mass GDPR breach, 72 h notification, loss of trust",
     "CTL-04 least privilege, CTL-07 AI agent safeguards, CTL-06 rate limits", "R1"),
    ("A1-4_cm_R3", "Concept map 3 – student misuses the agent to read grades", "TA2 Curious student",
     "MCP service does not check for which user the agent asks (no per-record access check)",
     "E2 Grades and assessment records",
     "Student reads other students' grades", "Privacy breach between students, complaints, GDPR breach",
     "CTL-04 role-based access: requests carry the user's identity, every record is checked", "R3"),
]
for key, title, t, v, a, r, i, c, rid in CHAINS:
    D.concept_map(os.path.join(F, f"{key}.png"), title, t, v, a, r, i, c, rid)
D.heat_map(os.path.join(F, "A1-3_risk_heat_map.png"))

def concept_maps(d, chains):
    for key, title, *_, rid in chains:
        d.add_heading(title, 2)
        image(d, os.path.join(F, f"{key}.png"), 16.5)
        r = get(RISKS, rid)
        para(d, f"60-second explanation: {r[1]} The threat is '{r[2]}', not the risk itself. The vulnerability is: {r[3].lower()}. "
                f"Inherent rating L{r[6]} × I{r[8]} = {r[6]*r[8]} ({priority(r[6]*r[8])}). Treatment: {r[11]}.", size=9.5)

# ------------------------------------------------------------------ A1-1 docx (US-1.1)
d = new_doc("Risk Concept Map", "System context and the risk concept chain applied to the MUDT platform",
            "A1-1", "US-1.1 Identify critical assets", f"{who(EFE)}; reviewed by {who(EGON)}")
d.add_heading("1. Purpose", 1)
para(d, "This artefact answers: what are we protecting, and how do the six risk concepts connect? "
        "It is the starting point for the asset register (A1-2), the threat model (A1-4) and the risk register (A1-3).")
bullets(d, ["**Asset** – something valuable (information, service, reputation).",
            "**Threat** – a potential cause of harm (an actor or an event).",
            "**Vulnerability** – a weakness that a threat can exploit.",
            "**Risk** – the possible harmful outcome when a threat exploits a vulnerability of an asset (measured as likelihood × impact).",
            "**Impact** – the consequence for the organisation if the risk happens.",
            "**Control** – a measure that reduces likelihood or impact.",
            "Rule from the lecture: Threat ≠ Risk, and 'missing authentication' is a vulnerability, not a threat."])
d.add_heading("2. System context (architecture evidence)", 1)
para(d, "Source: CS301 Session 1, slides 5 and 8 (MUDT AI Learning Assistant Platform architecture and use cases). "
        "The platform is split into three zones: an on-premises university data centre (trusted), a cloud AI platform (untrusted) "
        "and a controlled bridge – the Metadata API – that may only transfer approved reporting data.")
d.add_heading("2.1 Components", 2)
table(d, ["ID", "Component", "Zone", "Purpose"], COMPONENTS, widths=(1.4, 5.4, 1.3, 8.9))
d.add_heading("2.2 Trust zones", 2)
table(d, ["ID", "Zone", "Trust level", "Content"], ZONES, widths=(1.2, 4.3, 3.5, 8.0))
d.add_heading("2.3 Users and use cases", 2)
table(d, ["ID", "User group", "Main use cases"], USERS, widths=(1.2, 4.3, 11.5))
para(d, "The full trust-zone diagram is in EPA-IS-2/A2-2_Trust_Architecture.docx.", italic=True)
d.add_heading("2.4 Assumptions", 2)
table(d, ["ID", "Assumption (to be confirmed with MUDT)"], ASSUMPTIONS, widths=(1.2, 15.8))
d.add_heading("3. Risk concept map", 1)
para(d, "The map follows the chain from the lecture (slides 20–22): a threat exploits a vulnerability that exists in an asset; "
        "together they create a risk, which leads to an impact; a control reduces the risk by closing or limiting the vulnerability. "
        "This is the Workshop 1 scenario. The threat model (A1-4) applies the same chain to the two highest AI-specific risks.")
concept_maps(d, CHAINS[:1])
d.add_heading("4. Cross-references", 1)
bullets(d, ["Asset IDs E1–E11 and S1–S22 → EPA-IS-1/A1-2_Asset_Register.xlsx",
            "Threat actors, attack paths and concept maps 2–3 → EPA-IS-1/A1-4_Threat_Model.docx",
            "Risk IDs R1–R12 → EPA-IS-1/A1-3_Risk_Register.xlsx",
            "Control IDs CTL-01–CTL-16 → EPA-IS-2/A2-3_Control_Matrix.xlsx"])
save_doc(d, "EPA-IS-1/A1-1_Risk_Concept_Map.docx")

# ------------------------------------------------------------------ A1-4 docx (US-1.2)
d = new_doc("Threat Model", "Threat actors, entry points, trust boundaries and attack paths", "A1-4",
            "US-1.2 Identify threats and attack paths", f"{who(VESANJA)}; reviewed by {who(EFE)}")
d.add_heading("1. Purpose", 1)
para(d, "This artefact answers: who could attack the MUDT platform, where could they get in, and which path would lead them to the "
        "valuable assets? It uses the components (SYS-1–SYS-16), zones (Z0–Z5) and assets (E1–E11) from A1-1 and A1-2.")
d.add_heading("2. Threat actors and goals", 1)
table(d, ["ID", "Actor", "Motivation", "Goals", "Capability", "Targeted assets"], ACTORS, widths=(1.1, 3.4, 2.4, 5.6, 2.2, 2.3))
d.add_heading("3. Entry points", 1)
table(d, ["ID", "Entry point", "Crosses", "Used by"], ENTRY_POINTS, widths=(1.2, 9.0, 3.0, 3.8))
d.add_heading("4. Trust boundaries", 1)
table(d, ["ID", "Boundary", "Zones", "Required enforcement"], BOUNDARIES, widths=(1.2, 4.6, 3.2, 8.0))
note(d, "TB5 is special for AI systems: it is not a network boundary but the boundary between data and instructions inside the AI model. "
        "Every text an agent reads (uploaded documents, retrieved text, user prompts) is untrusted input.")
d.add_heading("5. Attack paths", 1)
para(d, "Attack paths connect an actor through an entry point and a (suspected) weakness to an affected asset. "
        "They are hypotheses for planning controls – they do not claim that the weakness is confirmed (assumption A6).", italic=True)
rows = [(a[0], a[1], a[2], a[3], "\n".join(f"{k+1}. {s}" for k, s in enumerate(a[4])), a[5], a[6], a[7]) for a in ATTACK_PATHS]
table(d, ["ID", "Path", "Actor", "Entry", "Steps", "Assumed weakness", "Assets", "Risks"], rows,
      widths=(1.0, 2.6, 1.3, 1.3, 5.0, 3.0, 1.4, 1.4), font=8)
d.add_heading("6. Concept maps for the top attack paths", 1)
para(d, "The same chain as in A1-1, applied to AP1 (prompt injection, risk R1) and AP3 (agent misused to read grades, risk R3).")
concept_maps(d, CHAINS[1:])
d.add_heading("7. Cross-references", 1)
bullets(d, ["Assets → EPA-IS-1/A1-2_Asset_Register.xlsx · Risks → EPA-IS-1/A1-3_Risk_Register.xlsx",
            "Controls CTL-01–CTL-16 → EPA-IS-2/A2-3_Control_Matrix.xlsx",
            "AP1 is the attack later investigated as incident INC-2026-001 → EPA-IS-3"])
save_doc(d, "EPA-IS-1/A1-4_Threat_Model.docx")

# ------------------------------------------------------------------ A1-2 asset register
wb = Workbook()
meta = f"Artefact A1-2 · US-1.1 · owner {who(EFE)} · reviewed by {who(EGON)} · {VERSION} · {DATE}"
rows = [(e[0], e[1], e[2], e[3], e[4], LVL[e[5]], LVL[e[6]], LVL[e[7]], LVL[max(e[5:8])], e[8], e[9], e[10], e[11],
         ", ".join(r[0] for r in RISKS if e[0] in r[4].replace(" ", "").split(","))) for e in ESSENTIAL]
sheet(wb, "Essential assets", ["ID", "Asset", "Type", "Description", "Business value", "C", "I", "A", "Overall criticality",
                               "CIA justification", "Asset owner (to confirm)", "Where (components)", "Depends on (supporting)", "Linked risks"],
      rows, [6, 26, 13, 34, 34, 8, 8, 8, 11, 46, 22, 14, 16, 14], title="A1-2 Asset Register – Essential assets", meta=meta, first=True)
rows = [(s[0], s[1], s[2], s[3], LVL[s[4]], LVL[s[5]], LVL[s[6]], s[7]) for s in SUPPORTING]
sheet(wb, "Supporting assets", ["ID", "Supporting asset", "Component", "Supports", "C", "I", "A", "Notes"], rows,
      [6, 50, 12, 16, 8, 8, 8, 46], title="A1-2 Asset Register – Supporting assets", meta=meta)
sheet(wb, "Method", ["Item", "Explanation"], [
    ("Essential vs supporting", "Essential assets carry the business value (information and processes). Supporting assets are the systems, networks, people and suppliers that essential assets depend on. An attacker usually attacks a supporting asset to harm an essential one."),
    ("CIA scale", "Low = limited harm; Medium = noticeable harm to students or operations; High = legal breach, serious harm or loss of academic trust."),
    ("Overall criticality", "Highest of the three CIA values."),
    ("Asset owner", "Role accountable for the asset. Names to be confirmed with MUDT during product discovery."),
    ("Architecture evidence", "Components SYS-1–SYS-16 and zones Z0–Z5 from Session 1 slide 5; see A1-1 section 2."),
    ("Assumptions", "; ".join(f"{a[0]}: {a[1]}" for a in ASSUMPTIONS)),
], [24, 120], title="A1-2 Method, scales and assumptions", meta=meta)
save_wb(wb, "EPA-IS-1/A1-2_Asset_Register.xlsx")

# ------------------------------------------------------------------ A1-3 risk register
wb = Workbook()
meta = f"Artefact A1-3 · US-1.3 · owner {who(EGON)} · reviewed by {who(VESANJA)} · {VERSION} · {DATE}"
order = sorted(RISKS, key=lambda r: -r[6] * r[8])
rows = [(k + 1, r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[6] * r[8], priority(r[6] * r[8]), r[10], r[11], r[12], r[13], r[14])
        for k, r in enumerate(order)]
ws = sheet(wb, "Risk register", ["Rank", "Risk ID", "Risk statement", "Threat", "Vulnerability", "Assets", "Impact", "L", "Likelihood rationale",
                                 "I", "Impact rationale", "Score", "Priority", "Treatment option", "Initial treatment", "Controls (A2-3)", "Risk owner", "Attack path"],
           rows, [6, 7, 46, 18, 34, 11, 30, 5, 40, 5, 34, 7, 10, 12, 40, 18, 18, 9], title="A1-3 Risk Register – MUDT platform",
           meta=meta, prio_col=12, first=True)
sheet(wb, "Scoring method", ["Scale", "1", "2", "3", "4", "5"], [
    ("Likelihood", "Rare", "Unlikely", "Possible", "Likely", "Almost certain"),
    ("Impact", "Negligible", "Minor", "Moderate", "Major", "Severe"),
    ("Priority bands", "1–4 Low", "5–9 Medium", "10–15 High", "16–25 Critical", ""),
    ("Rule", "Score = L × I (5×5 matrix, lecture slide 35). Ratings are inherent (before new controls). Every number has a written rationale.", "", "", "", ""),
    ("Consistency", "Same scales for all risks; ties ordered by impact. Ratings reviewed by second team member (four-eyes).", "", "", "", ""),
], [16, 30, 16, 16, 16, 16], title="A1-3 Scoring method", meta=meta)
hm = wb.create_sheet("Heat map")
hm["A1"] = "Inherent risk heat map"; hm["A1"].font = Font(bold=True, size=14, color=ACCENT)
img = XLImage(os.path.join(F, "A1-3_risk_heat_map.png")); img.width, img.height = 600, 503; hm.add_image(img, "A3")
save_wb(wb, "EPA-IS-1/A1-3_Risk_Register.xlsx")
