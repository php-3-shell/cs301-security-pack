"""Diagram generation (matplotlib) – writes PNGs into the repo next to their artefacts."""
import os, textwrap
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(__file__), ".mpl"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from common import OUT, priority, PRIO_FILL
from data import RISKS

COL = {"ASSET": "#2E75B6", "THREAT": "#C00000", "VULNERABILITY": "#ED7D31",
       "RISK": "#7030A0", "IMPACT": "#595959", "CONTROL": "#2E7D32"}

def _box(ax, x, y, w, h, head, body, color):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.01,rounding_size=0.02",
                                fc="white", ec=color, lw=2.2))
    ax.add_patch(FancyBboxPatch((x - w / 2, y + h / 2 - 0.055), w, 0.055, boxstyle="square,pad=0", fc=color, ec=color))
    ax.text(x, y + h / 2 - 0.0275, head, ha="center", va="center", color="white", fontsize=10, weight="bold")
    ax.text(x, y - 0.025, "\n".join(textwrap.fill(b, 30) for b in body.split("\n")), ha="center", va="center", fontsize=8.6, wrap=True, linespacing=1.3)

def _arrow(ax, p, q, label, rad=0.0, color="#333333", lpos=0.5, loff=(0, 0.018)):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14, lw=1.5, color=color,
                                 connectionstyle=f"arc3,rad={rad}"))
    mx, my = p[0] + (q[0] - p[0]) * lpos + loff[0], p[1] + (q[1] - p[1]) * lpos + loff[1]
    ax.text(mx, my, label, ha="center", va="center", fontsize=8.2, style="italic",
            bbox=dict(fc="white", ec="none", pad=1.2))

def concept_map(path, title, t, v, a, r, i, c, risk_id):
    fig, ax = plt.subplots(figsize=(11, 6.2)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.5, 0.97, title, ha="center", fontsize=13, weight="bold", color="#1F4E5F")
    W, H = 0.25, 0.25
    P = {"THREAT": (0.15, 0.70), "VULNERABILITY": (0.5, 0.70), "ASSET": (0.85, 0.70),
         "CONTROL": (0.15, 0.22), "RISK": (0.5, 0.22), "IMPACT": (0.85, 0.22)}
    for k, body in (("THREAT", t), ("VULNERABILITY", v), ("ASSET", a), ("CONTROL", c), ("RISK", r + f"\n[{risk_id}]"), ("IMPACT", i)):
        _box(ax, *P[k], W, H, k, body, COL[k])
    e = W / 2
    _arrow(ax, (P["THREAT"][0] + e, 0.72), (P["VULNERABILITY"][0] - e, 0.72), "exploits")
    _arrow(ax, (P["VULNERABILITY"][0] + e, 0.72), (P["ASSET"][0] - e, 0.72), "exists in")
    _arrow(ax, (P["THREAT"][0], 0.825), (P["ASSET"][0], 0.825), "targets", rad=-0.18, lpos=0.5, loff=(0, 0.075))
    _arrow(ax, (0.5, 0.575), (0.5, 0.345), "together create", loff=(0.075, 0))
    _arrow(ax, (P["ASSET"][0] - 0.03, 0.575), (P["RISK"][0] + e, 0.30), "is exposed to", lpos=0.45, loff=(0.02, 0.02))
    _arrow(ax, (P["RISK"][0] + e, 0.22), (P["IMPACT"][0] - e, 0.22), "leads to")
    _arrow(ax, (P["CONTROL"][0] + e, 0.22), (P["RISK"][0] - e, 0.22), "reduces", color=COL["CONTROL"])
    _arrow(ax, (P["CONTROL"][0] + 0.03, 0.345), (P["VULNERABILITY"][0] - e, 0.62), "closes / limits", color=COL["CONTROL"],
           lpos=0.5, loff=(-0.03, 0.02))
    ax.text(0.5, 0.03, "Threat ≠ Risk · the attacker is the threat, the weakness is the vulnerability, "
            "the harmful outcome for the asset is the risk", ha="center", fontsize=8.5, color="#404040")
    fig.savefig(path, dpi=170, bbox_inches="tight"); plt.close(fig); print("diagram", os.path.relpath(path, OUT))

def trust_architecture(path):
    fig, ax = plt.subplots(figsize=(15, 8.6)); ax.set_xlim(0, 15); ax.set_ylim(0, 8.6); ax.axis("off")
    def zone(x, y, w, h, label, fc, ec):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc=fc, ec=ec, lw=2, ls="-"))
        ax.text(x + 0.12, y + h - 0.12, label, ha="left", va="top", fontsize=10, weight="bold", color=ec)
    def comp(x, y, cid, name, w=1.9, h=0.62, ec="#1F4E5F"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc="white", ec=ec, lw=1.3))
        ax.text(x + w / 2, y + h / 2, f"{cid}\n{name}", ha="center", va="center", fontsize=7.6, linespacing=1.15)
        return (x, y, w, h)
    ax.text(7.5, 8.45, "MUDT platform – trust zones, components and controlled flows", ha="center", fontsize=14, weight="bold", color="#1F4E5F")
    zone(0.1, 0.4, 2.2, 7.6, "Z0 Internet / users\n(untrusted)", "#F7F7F7", "#7F7F7F")
    zone(2.6, 4.9, 1.9, 3.1, "Z1 DMZ", "#FFF4E5", "#C55A11")
    zone(4.8, 2.9, 4.2, 5.1, "Z2 On-prem core (trusted)", "#E8F3EA", "#2E7D32")
    zone(2.6, 0.4, 6.4, 2.2, "Z3 Security & management (restricted)", "#EEF0F7", "#3B4A8C")
    zone(9.3, 2.9, 1.7, 5.1, "Z4 Bridge", "#FDEDEC", "#C00000")
    zone(11.3, 0.4, 3.6, 7.6, "Z5 Cloud (untrusted)", "#EAF1FB", "#2E75B6")
    users = [("U1", "Students"), ("U2", "Lecturers"), ("U3", "Coordinators"), ("U4", "Admins")]
    for k, (u, n) in enumerate(users):
        comp(0.3, 6.4 - k * 1.25, u, n, w=1.8)
    comp(2.6 + 0.1, 5.6, "C8", "Web portal\n+ WAF", w=1.7)
    core = {"C4": ("Identity provider\n(SSO, MFA)", 5.0, 6.9), "C1": ("Student info\nsystem", 7.0, 6.9),
            "C2": ("Grade DB", 5.0, 5.95), "C3": ("Research\nrepository", 7.0, 5.95),
            "C7": ("Sensitive data\nstorage", 5.0, 5.0), "C5": ("MCP service\n(tools for agents)", 7.0, 4.0)}
    for cid, (n, x, y) in core.items(): comp(x, y, cid, n)
    comp(6.9, 0.75, "C6", "Audit logging / SIEM\n(WORM)", w=1.9)
    comp(4.9, 0.75, "S18", "Immutable\nbackups", w=1.7)
    comp(2.8, 0.75, "PAM", "Admin jump host\n(VPN + FIDO2)", w=1.9)
    comp(9.42, 4.6, "C9", "Secure API\ngateway –\nMetadata API", w=1.46, h=1.3, ec="#C00000")
    ax.text(10.15, 3.55, "mTLS · OAuth2\nallow-list · DLP\nrate limit · audit", ha="center", fontsize=7.2, color="#C00000")
    cloud = [("C10", "Agent orchestrator"), ("C11", "AI agents"), ("C12", "LLM inference"),
             ("C13", "Vector DB"), ("C15", "Cloud storage (CMK)"), ("C16", "Reporting dashboard"), ("C14", "Cloud monitoring")]
    for k, (cid, n) in enumerate(cloud):
        comp(12.0, 6.95 - k * 0.98, cid, n, w=2.3, h=0.6)
    def flow(p, q, lab, color="#333333", rad=0.0, lp=0.5):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="<|-|>" if lab.startswith("F") and "↔" in lab else "-|>",
                                     mutation_scale=12, lw=1.5, color=color, connectionstyle=f"arc3,rad={rad}"))
        mx, my = p[0] + (q[0] - p[0]) * lp, p[1] + (q[1] - p[1]) * lp
        ax.text(mx, my, lab.replace("↔", ""), fontsize=7.5, weight="bold", color=color, ha="center", va="center",
                bbox=dict(fc="white", ec=color, boxstyle="round,pad=0.15", lw=0.8))
    flow((2.1, 6.0), (2.7, 5.9), "F1")
    flow((4.4, 6.0), (5.0, 7.15), "F2", lp=0.45)
    flow((4.4, 5.75), (5.0, 6.2), "F3", lp=0.55)
    flow((8.9, 4.3), (9.42, 5.0), "F4↔", color="#C00000")
    flow((12.0, 7.2), (10.88, 5.5), "F5↔", color="#C00000", lp=0.5)
    flow((10.88, 4.75), (12.0, 2.35), "F6", color="#C00000", lp=0.5)
    flow((7.95, 4.62), (7.95, 5.95), "F7", lp=0.5)
    flow((5.95, 5.0), (5.75, 1.37), "F8", color="#3B4A8C", lp=0.55)
    flow((10.15, 3.4), (8.3, 1.37), "F9", color="#3B4A8C", lp=0.4)
    flow((2.1, 2.95), (3.3, 1.37), "F10", color="#3B4A8C", lp=0.6)
    ax.text(0.15, 0.08, "No direct route: Z1 → databases · Z5 → Z2 · Internet → Z3.  Grades (C2) and research data (C3) never leave Z2.  "
            "Arrows = permitted flows, see flow register F1–F10.", fontsize=8.4, color="#404040")
    fig.savefig(path, dpi=160, bbox_inches="tight"); plt.close(fig); print("diagram", os.path.relpath(path, OUT))

def heat_map(path):
    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    cmap = {"Low": "#A9D18E", "Medium": "#FFE699", "High": "#F4B183", "Critical": "#FF7C80"}
    for L in range(1, 6):
        for I in range(1, 6):
            s = L * I
            ax.add_patch(plt.Rectangle((I - 0.5, L - 0.5), 1, 1, fc=cmap[priority(s)], ec="white", lw=2))
            ax.text(I + 0.38, L + 0.36, str(s), fontsize=7, color="#555555", ha="right", va="top")
    cells = {}
    for r in RISKS: cells.setdefault((r[6], r[8]), []).append(r[0])
    for (L, I), ids in cells.items():
        ax.text(I, L - 0.05, "\n".join(", ".join(ids[k:k + 2]) for k in range(0, len(ids), 2)),
                ha="center", va="center", fontsize=9, weight="bold")
    ax.set_xlim(0.5, 5.5); ax.set_ylim(0.5, 5.5)
    ax.set_xticks(range(1, 6), ["1 Negligible", "2 Minor", "3 Moderate", "4 Major", "5 Severe"], fontsize=8)
    ax.set_yticks(range(1, 6), ["1 Rare", "2 Unlikely", "3 Possible", "4 Likely", "5 Almost\ncertain"], fontsize=8)
    ax.set_xlabel("Impact →"); ax.set_ylabel("Likelihood →")
    ax.set_title("Inherent risk heat map (L × I) – MUDT platform", fontsize=11, weight="bold", color="#1F4E5F")
    for sp in ax.spines.values(): sp.set_visible(False)
    fig.savefig(path, dpi=160, bbox_inches="tight"); plt.close(fig); print("diagram", os.path.relpath(path, OUT))

def incident_timeline(path, events):
    """events: list of (label_time, short_text, phase)."""
    phase_col = {"Attack": "#C00000", "Detection": "#ED7D31", "Response": "#2E75B6", "Recovery": "#2E7D32"}
    fig, ax = plt.subplots(figsize=(16, 5.2)); ax.axis("off")
    n = len(events); ax.set_xlim(-0.6, n - 0.4); ax.set_ylim(-1.7, 1.7)
    ax.plot([-0.4, n - 0.6], [0, 0], color="#404040", lw=2)
    for k, (t, txt, ph) in enumerate(events):
        up = 1 if k % 2 == 0 else -1
        c = phase_col[ph]
        ax.plot([k, k], [0, 0.45 * up], color=c, lw=1.4); ax.scatter([k], [0], s=70, color=c, zorder=3)
        ax.text(k, 0.52 * up, f"{t}\n{txt}", ha="center", va="bottom" if up > 0 else "top", fontsize=7.6,
                bbox=dict(fc="white", ec=c, boxstyle="round,pad=0.3"), linespacing=1.2)
    for k, (ph, c) in enumerate(phase_col.items()):
        ax.scatter([k * 1.6], [-1.62], s=60, color=c); ax.text(k * 1.6 + 0.12, -1.62, ph, va="center", fontsize=9)
    ax.set_title("INC-2026-001 – reconstructed timeline (exercise scenario, times UTC)", fontsize=12, weight="bold", color="#1F4E5F")
    fig.savefig(path, dpi=160, bbox_inches="tight"); plt.close(fig); print("diagram", os.path.relpath(path, OUT))
