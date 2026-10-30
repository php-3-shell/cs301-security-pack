"""Fill the lecturer's CS301 template pack (keeps its formatting) and return the task list for the README."""
import copy, os, re
from docx import Document
from common import *

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "00-Delivery", "original", "CS301_Agile_Delivery_Templates_EPA_original.docx")
E, V = who(EGON), who(VESANJA)
P1, P2, P3 = "EPA-IS-1/", "EPA-IS-2/", "EPA-IS-3/"
CM, AR, RR = P1 + "A1-1_Risk_Concept_Map_and_Threat_Model.docx", P1 + "A1-2_Asset_Register.xlsx", P1 + "A1-3_Risk_Register.xlsx"
API, TA, CMX = P2 + "A2-1_Secure_API_Design.docx", P2 + "A2-2_Trust_Architecture.docx", P2 + "A2-3_Control_Matrix.xlsx"
TL, RC, RM = P3 + "A3-1_Incident_Timeline.xlsx", P3 + "A3-2_Root_Cause_Review.docx", P3 + "A3-3_Remediation_Roadmap.xlsx"

# story: (owner, reviewer, branch, evidence, [task descriptions], [task evidence])
STORIES = {
    "US-1.1": (E, V, "feature/us-1-1-assets", f"{CM} (§2, §3); {AR}",
               ["Analyse lecture architecture (slides 5, 8): list components, zones, users, assumptions",
                "Build asset register: essential/supporting assets, CIA ratings with justification, owners; draw concept map 1",
                "Review: check asset IDs vs architecture and risk register, CIA consistency"],
               [CM + " §2", AR, AR]),
    "US-1.2": (V, E, "feature/us-1-2-threat-model", f"{CM} (§4)",
               ["Identify threat actors, goals, entry points and trust boundaries",
                "Write attack paths AP1–AP8 and concept maps 2–3",
                "Review: attack paths link to assets/risks; no unverified vulnerability claims"],
               [CM + " §4.1–4.3", CM + " §4.4", CM]),
    "US-1.3": (E, V, "feature/us-1-3-risk-register", RR,
               ["Write risk statements R1–R12 (threat + vulnerability + asset + impact)",
                "Score L × I with rationale, set priority, initial treatment; heat map",
                "Review: consistent scoring, cross-reference to controls A2-3"],
               [RR, RR, RR]),
    "US-2.1": (V, E, "feature/us-2-1-authentication", f"{API} (§2–4, §7); {CMX}",
               ["List communicating components CC1–CC10 and trust relationships",
                "Design authentication (mTLS, OAuth2, OBO, MFA) and authorisation scopes; failure conditions",
                "Review: design matches control matrix C01–C06"],
               [API + " §2", API + " §3–4, §7", CMX]),
    "US-2.2": (E, V, "feature/us-2-2-metadata-transfer", f"{API} (§5–6, §8); {CMX}",
               ["Classify data; define allowed/prohibited data across the bridge",
                "Specify endpoints, confidentiality/integrity controls, logging and alerts",
                "Review: allow-list vs asset register; assumptions and alternatives recorded"],
               [API + " §5.1", API + " §5–6", API + " §8"]),
    "US-2.3": (V, E, "feature/us-2-3-trust-architecture", f"{TA}; {CMX}",
               ["Define trust zones Z0–Z5 and flow register F1–F10",
                "Draw trust architecture; map preventive/detective/corrective controls per layer; build control matrix",
                "Review: dependencies/failure paths; every risk has controls (coverage sheet)"],
               [TA + " §1", TA + " §2; " + CMX, TA + " §3–4"]),
    "US-3.1": (E, V, "feature/us-3-1-incident-timeline", TL,
               ["Collect and register evidence EV-01–EV-11 and IoCs",
                "Order events with timestamps; mark fact/inferred; write incident narrative",
                "Review: timeline consistent with evidence and attack path AP1"],
               [TL + " (Evidence, IoC)", TL + " (Timeline, Summary)", TL]),
    "US-3.2": (V, E, "feature/us-3-2-root-cause", RC,
               ["Separate events from causes; five-whys analysis",
                "Write root causes RC1–RC6 with evidence and control gaps; contributing factors",
                "Review: alternative explanations and uncertainty recorded"],
               [RC + " §1–2", RC + " §3–4", RC + " §5"]),
    "US-3.3": (E, V, "feature/us-3-3-remediation", RM,
               ["Derive actions for containment, recovery and long-term remediation",
                "Build roadmap RM-01–RM-16 with owners, order, dependencies; residual risk",
                "Review: every root cause and risk addressed; residual risk acknowledged"],
               [RM, RM, RM + " (Residual risk)"]),
}
EPIC_OWNER = {"EPIC-1": E, "EPIC-2": V, "EPIC-3": E}
STATUS_STORY, STATUS_TASK, SHA = "Review (draft complete, awaiting team review)", "Review", "[SHA after commit]"

def tasks():
    out = []
    for us, (own, rev, br, _, descs, evs) in STORIES.items():
        x, y = us[3:].split(".")
        for k, (dsc, ev) in enumerate(zip(descs, evs), 1):
            out.append((f"TASK-{x}.{y}.{k}", us, dsc, own if k < 3 else rev, br, ev))
    return out

def set_text(cell, text):
    p0 = cell.paragraphs[0]
    for p in cell.paragraphs[1:]: p._p.getparent().remove(p._p)
    runs = p0.runs
    if runs:
        runs[0].text = text
        for r in runs[1:]: r._r.getparent().remove(r._r)
    else:
        p0.add_run(text)

def label(row): return row.cells[0].text.strip()

def fill():
    doc = Document(SRC)
    T = {t[0]: t for t in tasks()}
    story = None
    for t in doc.tables:
        first = t.rows[0].cells[0].text.strip()
        rows = {label(r): r for r in t.rows}
        if first == "Team information":
            set_text(rows["Team name"].cells[1], TEAM_NAME)
            set_text(rows["Repository"].cells[1], REPO)
            set_text(rows["Members"].cells[1], f"{E}; {V}")
            set_text(rows["Coordinator"].cells[1], EGON)
            set_text(rows["Semester"].cells[1], "Winter semester 2026/27")
        elif first == "Epic field":
            eid = rows["Epic ID"].cells[1].text.strip()
            set_text(rows["Epic owner"].cells[1], EPIC_OWNER[eid])
        elif first == "Task ID" and len(t.columns) == 6:
            for r in t.rows[1:]:
                tid = r.cells[0].text.strip(); tk = T[tid]
                for i, v in enumerate([tk[2], tk[3], tk[5], SHA, STATUS_TASK], 1): set_text(r.cells[i], v)
        elif first == "Student":
            log = t
        elif first == "Question":
            set_text(rows["Participants"].cells[1], f"{EGON}, {VESANJA}")
            for q in ("What helped learning?", "What blocked progress?", "What will we change next sprint?", "Backlog changes agreed"):
                set_text(rows[q].cells[1], "[Complete together at the sprint review – Week 4 / 8 / 12]")
    # story tables: pair them with the preceding heading "US-x.y - ..."
    body = doc.element.body
    cur = None
    for el in body.iterchildren():
        tag = el.tag.split("}")[1]
        if tag == "p":
            txt = "".join(x.text or "" for x in el.iter() if x.tag.endswith("}t"))
            m = re.match(r"(US-\d\.\d) ", txt)
            if m: cur = m.group(1)
        elif tag == "tbl" and cur:
            from docx.table import Table
            t = Table(el, doc._body); rows = {label(r): r for r in t.rows}
            if "Story owner" in rows:
                own, rev, br, ev, *_ = STORIES[cur]
                set_text(rows["Story owner"].cells[1], own)
                set_text(rows["Evidence paths"].cells[1], ev)
                set_text(rows["Status"].cells[1], STATUS_STORY)
                cur = None
    # contribution log: one row per task
    tmpl = copy.deepcopy(log.rows[1]._tr)
    for r in list(log.rows[1:]): r._tr.getparent().remove(r._tr)
    for tid, us, dsc, own, br, ev in tasks():
        tr = copy.deepcopy(tmpl); log._tbl.append(tr)
        row = log.rows[-1]
        for i, v in enumerate([own, tid, br, SHA, ev, dsc]): set_text(row.cells[i], v)
    # checklist: tick only what is already true without Git
    done = ("All user stories contain acceptance criteria", "All artefact IDs and file paths are cross-referenced")
    for p in doc.paragraphs:
        if p.text.startswith("☐") and any(s in p.text for s in done):
            for r in p.runs:
                if "☐" in r.text: r.text = r.text.replace("☐", "☑"); break
    path = os.path.join(OUT, "00-Delivery", "CS301_Agile_Delivery_Templates_EPA_filled.docx")
    os.makedirs(os.path.dirname(path), exist_ok=True); doc.save(path); print("wrote", os.path.relpath(path, OUT))

if __name__ == "__main__":
    fill()
