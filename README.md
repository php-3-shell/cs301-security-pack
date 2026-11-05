# CS301 Basics of Information Security – Team Artefacts

**Team:** php3shell · **Members:** Egon Hashani (`eszvc`), Vesanja Bregasi (`anja820`), Efe (`A-Efe24`) · **Coordinator:** Egon Hashani
**Repository:** https://github.com/php-3-shell/cs301-security-pack
**Case:** MUDT AI Learning Assistant and Management Platform (hybrid on-premises / cloud, Session 1 slides 5 and 8)
**Review version:** v0.1 draft for team review (2026-10-30)

Analysis chain: **Assess** (assets → threats → risks) → **Protect** (authentication → metadata transfer → trust zones and controls) → **Investigate** (incident INC-2026-001 → root causes → remediation).
All IDs are shared across files: assets `E1–E11`/`S1–S22`, components `C1–C16`, zones `Z0–Z5`, attack paths `AP1–AP8`, risks `R1–R12`, controls `C01–C30`, evidence `EV-01–EV-11`, root causes `RC1–RC6`, actions `RM-01–RM-16`.

## Artefacts

| EPA / Story | Pts | Artefact | Owner | Reviewer | Status |
|---|---|---|---|---|---|
| EPA-IS-1 · US-1.1 Identify critical assets | 5 | `EPA-IS-1/A1-1_Risk_Concept_Map_and_Threat_Model.docx` (§2–3), `EPA-IS-1/A1-2_Asset_Register.xlsx` | Efe | Egon | Review |
| EPA-IS-1 · US-1.2 Threats and attack paths | 8 | `EPA-IS-1/A1-1_Risk_Concept_Map_and_Threat_Model.docx` (§4) | Vesanja | Efe | Review |
| EPA-IS-1 · US-1.3 Prioritise risks | 8 | `EPA-IS-1/A1-3_Risk_Register.xlsx` | Egon | Vesanja | Review |
| EPA-IS-2 · US-2.1 Authenticate component communication | 8 | `EPA-IS-2/A2-1_Secure_API_Design.docx` (§2–4, 7), `EPA-IS-2/A2-3_Control_Matrix.xlsx` | Vesanja | Efe | Review |
| EPA-IS-2 · US-2.2 Secure metadata transfer | 8 | `EPA-IS-2/A2-1_Secure_API_Design.docx` (§5–6, 8), `EPA-IS-2/A2-3_Control_Matrix.xlsx` | Egon | Vesanja | Review |
| EPA-IS-2 · US-2.3 Trust zones and layered architecture | 13 | `EPA-IS-2/A2-2_Trust_Architecture.docx`, `EPA-IS-2/A2-3_Control_Matrix.xlsx` | Efe | Egon | Review |
| EPA-IS-3 · US-3.1 Reconstruct attack timeline | 8 | `EPA-IS-3/A3-1_Incident_Timeline.xlsx` | Vesanja | Efe | Review |
| EPA-IS-3 · US-3.2 Determine root causes | 8 | `EPA-IS-3/A3-2_Root_Cause_Review.docx` | Egon | Vesanja | Review |
| EPA-IS-3 · US-3.3 Recommend corrective actions | 5 | `EPA-IS-3/A3-3_Remediation_Roadmap.xlsx` | Efe | Egon | Review |

Points: Egon 24 · Vesanja 24 · Efe 23 · total 71 (one story per epic each). Task breakdown (27 tasks), branches and contribution log: `00-Delivery/CS301_Agile_Delivery_Templates_EPA_filled.docx`.
Diagrams (`*.png`) are embedded in the documents and kept as separate files.
`tools/` holds the Python scripts that generate all artefacts from one shared data model (`tools/data.py`), so IDs stay consistent: `pip install -r tools/requirements.txt`, then run `build_epa1.py`, `build_epa2.py`, `build_epa3.py`, `fill_template.py`. `00-Delivery/original/` is the unmodified lecturer template.

## Git workflow (each student commits their own tasks)

Commit pattern: `[EPA-IS-x][US-x.y][TASK-x.y.z] action: concise description`

```bash
git checkout -b feature/us-1-1-assets
git add EPA-IS-1/A1-2_Asset_Register.xlsx
git commit -m "[EPA-IS-1][US-1.1][TASK-1.1.2] add: asset register with CIA rationale"
git push -u origin feature/us-1-1-assets      # open PR; the reviewer approves (TASK-x.y.3)
```

After merging, write the short SHA / PR number into the task table and contribution log, then tag the review version:
`git tag sprint-1-review` (Week 4) · `sprint-2-review` (Week 8) · `sprint-3-final` (Week 12).

## Open items before submission

- [ ] Export PDFs (checklist requires them): open each `.docx`/`.xlsx` and choose *File → Export as PDF*. They couldn't be generated automatically because LibreOffice Writer/Calc aren't installed (`sudo dnf install libreoffice-writer libreoffice-calc`, then `soffice --headless --convert-to pdf <file>`).
- [ ] Both members review each other's stories, then commit using the workflow above.
- [ ] Complete the sprint retrospective table at each sprint review.
- [ ] Epics 2 and 3 are drafted early; update them after the Week 5–11 lessons (NIST CSF, attacks, evidence).

## Notes

- Incident INC-2026-001 is a **simulated exercise** based on lecture slides 25–28; IPs, names and hashes are fictitious.
- Vulnerabilities are design hypotheses, not confirmed findings (assumption A6). Asset owners are roles to be confirmed with MUDT.
- AI use: drafted with Claude (AI use encouraged by the lecturer). See `STUDY_GUIDE.md` for the reasoning each member must be able to defend.
