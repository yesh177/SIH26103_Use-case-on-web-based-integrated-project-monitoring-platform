"""
PAIMANA Predictive Risk Intelligence
Module 2B: Phase 3 — Project Identity Resolution

Resolves physical infrastructure project identities across:
- June 2025 Table 7 (1,595 observations)
- July 2025 Table 4 (791 observations)
- July 2026 Table 6 (1,775 observations)

Input: data/interim/canonical_snapshots.csv (4,161 observations)
Outputs:
1. data/interim/project_identity_map.csv
2. data/interim/project_snapshot_panel.csv
"""

from collections import defaultdict, Counter
from pathlib import Path
import csv
import hashlib
import json
import re
import unicodedata
import sys

CANONICAL_SNAPSHOTS_PATH = Path("data/interim/canonical_snapshots.csv")
IDENTITY_MAP_PATH = Path("data/interim/project_identity_map.csv")
PANEL_PATH = Path("data/interim/project_snapshot_panel.csv")

FROZEN_FILES = [
    (Path("data/processed/table7_june_2025_projects.csv"), Path("data/processed/table7_june_2025_projects.sha256")),
    (Path("data/processed/table4_july_2025_projects.csv"), Path("data/processed/table4_july_2025_projects.sha256")),
    (Path("data/processed/table6_july_2026_projects.csv"), Path("data/processed/table6_july_2026_projects.sha256")),
]


def sha256_file(path: Path) -> str:
    """Compute SHA256 of a file in 1MB chunks."""
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def verify_frozen_inputs():
    """Verify frozen inputs remain strictly unchanged."""
    for csv_path, sha_path in FROZEN_FILES:
        expected = sha_path.read_text(encoding="utf-8").split()[0].strip()
        actual = sha256_file(csv_path)
        if actual != expected:
            raise ValueError(f"CRITICAL: Frozen source {csv_path} has been altered!")


def normalize_title_tokens(text: str) -> set:
    """
    Safe deterministic token normalization:
    - Unicode decomposition (NFKD)
    - Lowercasing
    - Stripping punctuation and separators, preserving alphanumeric package/km identifiers
    - Removing generic infrastructure stopwords
    """
    text = unicodedata.normalize("NFKD", text).lower()
    text = re.sub(r"[\(\)\[\]\{\},;:\.\-_\/]", " ", text)
    stopwords = {
        "project", "line", "railway", "new", "doubling", "construction",
        "works", "of", "and", "to", "in", "at", "for", "with", "from",
        "the", "under", "via", "an", "on", "by"
    }
    tokens = set(re.sub(r"\s+", " ", text).strip().split()) - stopwords
    return tokens


def compute_title_overlap(text1: str, text2: str) -> float:
    """
    Compute Jaccard token overlap similarity between two project titles:
    Jaccard = |S1 ∩ S2| / |S1 ∪ S2|
    """
    s1 = normalize_title_tokens(text1)
    s2 = normalize_title_tokens(text2)
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def is_state_compatible(s1: str, s2: str) -> bool:
    """Check administrative state compatibility with multi-state support."""
    s1_clean = s1.lower().strip()
    s2_clean = s2.lower().strip()
    if not s1_clean or not s2_clean:
        return True  # If unpopulated in source (e.g. Sl 447), cannot disqualify
    if s1_clean == s2_clean or s1_clean in s2_clean or s2_clean in s1_clean:
        return True
    w1 = set(re.findall(r"[a-z]+", s1_clean)) - {"multi", "states", "state", "pan", "india", "and"}
    w2 = set(re.findall(r"[a-z]+", s2_clean)) - {"multi", "states", "state", "pan", "india", "and"}
    return bool(w1 & w2)


def is_agency_compatible(a1: str, a2: str) -> bool:
    """Check executing agency compatibility with acronym & bracket matching."""
    a1_clean = a1.lower().strip()
    a2_clean = a2.lower().strip()
    if not a1_clean or not a2_clean:
        return True
    if a1_clean == a2_clean or a1_clean in a2_clean or a2_clean in a1_clean:
        return True
    # Acronyms in brackets or parentheses
    for pat in [r"\[(.*?)\]", r"\((.*?)\)"]:
        for ac in re.findall(pat, a1_clean) + re.findall(pat, a2_clean):
            ac_str = ac.lower().strip()
            if len(ac_str) >= 2 and (ac_str in a1_clean) and (ac_str in a2_clean):
                return True
    return False


def resolve_identities():
    """Execute conservative deterministic identity resolution across snapshots."""
    print("=" * 75)
    print("MODULE 2B: PHASE 3 — PROJECT IDENTITY RESOLUTION")
    print("=" * 75)

    verify_frozen_inputs()
    print("  [OK] Frozen source datasets verified unchanged")

    if not CANONICAL_SNAPSHOTS_PATH.exists():
        raise FileNotFoundError(f"Missing canonical input: {CANONICAL_SNAPSHOTS_PATH}")

    with CANONICAL_SNAPSHOTS_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        observations = list(reader)

    if len(observations) != 4161:
        raise ValueError(f"Expected 4,161 observations, found {len(observations)}")
    print(f"  [OK] Loaded {len(observations)} canonical snapshot observations")

    by_snap = defaultdict(dict)
    for obs in observations:
        snap = obs["source_snapshot"]
        pid = obs["source_project_id"]
        by_snap[snap][pid] = obs

    june_map = by_snap["2025-06"]      # 1,595
    july25_map = by_snap["2025-07"]    # 791
    july26_map = by_snap["2026-07"]    # 1,775

    # -------------------------------------------------------------
    # STEP 1: EXACT_ID MATCHING (July 2025 <-> July 2026)
    # -------------------------------------------------------------
    print()
    print("--- STEP 1: EXACT_ID RESOLUTION (July 2025 <-> July 2026) ---")
    common_pids = sorted(set(july25_map.keys()) & set(july26_map.keys()))
    print(f"  Common PAIMANA project IDs between July 2025 & July 2026: {len(common_pids)}")

    exact_matches = {}  # pid -> (r25, r26, evidence)
    review_exact = {}   # pid -> (r25, r26, reason)

    for pid in common_pids:
        r25 = july25_map[pid]
        r26 = july26_map[pid]

        s_ok = is_state_compatible(r25["state"], r26["state"])
        a_ok = is_agency_compatible(r25["agency"], r26["agency"])
        t_tokens1 = normalize_title_tokens(r25["project_name"])
        t_tokens2 = normalize_title_tokens(r26["project_name"])
        shared_tokens = t_tokens1 & t_tokens2
        sim = compute_title_overlap(r25["project_name"], r26["project_name"])

        if s_ok and a_ok and bool(shared_tokens):
            evidence = (
                f"Identical PAIMANA ID {pid}; "
                f"State compatible ('{r25['state']}' ~ '{r26['state']}'); "
                f"Agency compatible ('{r25['agency']}' ~ '{r26['agency']}'); "
                f"Title overlap {sim:.2f} ({len(shared_tokens)} shared distinctive tokens)"
            )
            exact_matches[pid] = (r25, r26, evidence)
        else:
            reasons = []
            if not s_ok:
                reasons.append(f"State conflict ('{r25['state']}' vs '{r26['state']}')")
            if not a_ok:
                reasons.append(f"Agency divergence ('{r25['agency']}' vs '{r26['agency']}')")
            if not shared_tokens:
                reasons.append("Zero shared distinctive title tokens")
            review_exact[pid] = (r25, r26, "; ".join(reasons))

    print(f"  [OK] EXACT_ID accepted:   {len(exact_matches)} project pairs")
    print(f"  [OK] REVIEW_REQUIRED:     {len(review_exact)} ambiguous pairs flagged (NOT merged)")

    # -------------------------------------------------------------
    # STEP 2: STRONG_MATCH (June 2025 OCMS <-> PAIMANA July 2025 & July 2026)
    # -------------------------------------------------------------
    print()
    print("--- STEP 2: STRONG_MATCH RESOLUTION (June 2025 OCMS <-> PAIMANA) ---")

    # Match June 2025 -> July 2025
    strong_june_to_25 = {}
    for jid, rj in june_map.items():
        cj = float(rj["original_cost_crore"])
        candidates = []
        for pid, r25 in july25_map.items():
            c25 = float(r25["original_cost_crore"])
            if abs(cj - c25) > 0.05:
                continue
            if not is_state_compatible(rj["state"], r25["state"]):
                continue
            if not is_agency_compatible(rj["agency"], r25["agency"]):
                continue
            if rj["approval_date"] and r25["approval_date"] and rj["approval_date"] != r25["approval_date"]:
                continue
            sim = compute_title_overlap(rj["project_name"], r25["project_name"])
            if sim >= 0.85:
                candidates.append((sim, r25))

        if len(candidates) == 1:
            sim, r25 = candidates[0]
            evidence = (
                f"Multi-attribute consensus: State ('{rj['state']}'); Agency ('{rj['agency']}'); "
                f"Cost diff {abs(cj - float(r25['original_cost_crore'])):.2f} Cr; "
                f"Appr Date ('{rj['approval_date']}'); Title Overlap {sim:.2f}; Unique candidate"
            )
            strong_june_to_25[jid] = (r25["source_project_id"], rj, r25, evidence)

    print(f"  [OK] June 2025 <-> July 2025 STRONG_MATCH: {len(strong_june_to_25)} pairs")

    # Match June 2025 -> July 2026
    strong_june_to_26 = {}
    for jid, rj in june_map.items():
        cj = float(rj["original_cost_crore"])
        candidates = []
        for pid, r26 in july26_map.items():
            c26 = float(r26["original_cost_crore"])
            if abs(cj - c26) > 0.05:
                continue
            if not is_state_compatible(rj["state"], r26["state"]):
                continue
            if not is_agency_compatible(rj["agency"], r26["agency"]):
                continue
            if rj["approval_date"] and r26["approval_date"] and rj["approval_date"] != r26["approval_date"]:
                continue
            sim = compute_title_overlap(rj["project_name"], r26["project_name"])
            if sim >= 0.85:
                candidates.append((sim, r26))

        if len(candidates) == 1:
            sim, r26 = candidates[0]
            evidence = (
                f"Multi-attribute consensus: State ('{rj['state']}'); Agency ('{rj['agency']}'); "
                f"Cost diff {abs(cj - float(r26['original_cost_crore'])):.2f} Cr; "
                f"Appr Date ('{rj['approval_date']}'); Title Overlap {sim:.2f}; Unique candidate"
            )
            strong_june_to_26[jid] = (r26["source_project_id"], rj, r26, evidence)

    print(f"  [OK] June 2025 <-> July 2026 STRONG_MATCH: {len(strong_june_to_26)} pairs")

    # -------------------------------------------------------------
    # STEP 3: LONGITUDINAL CLUSTERING & CANONICAL PROJECT KEY ASSIGNMENT
    # -------------------------------------------------------------
    print()
    print("--- STEP 3: CANONICAL PHYSICAL PROJECT KEY ASSIGNMENT ---")

    # Build disjoint-set / adjacency for merged observations
    obs_to_entity = {}       # obs_key -> canonical_project_key
    obs_meta = {}            # obs_key -> (confidence, method, evidence, review_status)

    # First, handle EXACT_ID matches between July 2025 and July 2026
    for pid, (r25, r26, evidence) in exact_matches.items():
        proj_key = f"PROJ-PAIMANA-{pid}"
        k25 = r25["canonical_observation_key"]
        k26 = r26["canonical_observation_key"]
        obs_to_entity[k25] = proj_key
        obs_to_entity[k26] = proj_key
        obs_meta[k25] = ("EXACT_ID", "PAIMANA_CROSS_SNAPSHOT_CORROBORATION", evidence, "ACCEPTED")
        obs_meta[k26] = ("EXACT_ID", "PAIMANA_CROSS_SNAPSHOT_CORROBORATION", evidence, "ACCEPTED")

    # Next, handle June 2025 STRONG_MATCH linkages
    for jid, (target_pid, rj, r25, evidence) in strong_june_to_25.items():
        kj = rj["canonical_observation_key"]
        k25 = r25["canonical_observation_key"]
        proj_key = obs_to_entity.get(k25, f"PROJ-PAIMANA-{target_pid}")
        obs_to_entity[kj] = proj_key
        obs_to_entity[k25] = proj_key
        obs_meta[kj] = ("STRONG_MATCH", "OCMS_PAIMANA_MULTI_ATTRIBUTE_CONSENSUS", evidence, "ACCEPTED")
        if k25 not in obs_meta:
            obs_meta[k25] = ("STRONG_MATCH", "OCMS_PAIMANA_MULTI_ATTRIBUTE_CONSENSUS", evidence, "ACCEPTED")

    for jid, (target_pid, rj, r26, evidence) in strong_june_to_26.items():
        kj = rj["canonical_observation_key"]
        k26 = r26["canonical_observation_key"]
        proj_key = obs_to_entity.get(k26, f"PROJ-PAIMANA-{target_pid}")
        obs_to_entity[kj] = proj_key
        obs_to_entity[k26] = proj_key
        obs_meta[kj] = ("STRONG_MATCH", "OCMS_PAIMANA_MULTI_ATTRIBUTE_CONSENSUS", evidence, "ACCEPTED")
        if k26 not in obs_meta:
            obs_meta[k26] = ("STRONG_MATCH", "OCMS_PAIMANA_MULTI_ATTRIBUTE_CONSENSUS", evidence, "ACCEPTED")

    # Next, handle REVIEW_REQUIRED cases (specifically July 2025/2026 common IDs with divergence)
    for pid, (r25, r26, reason) in review_exact.items():
        k25 = r25["canonical_observation_key"]
        k26 = r26["canonical_observation_key"]
        # Only assign review status if not already part of a valid match
        if k25 not in obs_to_entity:
            obs_to_entity[k25] = f"PROJ-REVIEW-2025-07-{pid}"
            obs_meta[k25] = ("REVIEW_REQUIRED", "AMBIGUOUS_ID_MATCH", f"Identical ID {pid} but {reason}", "PENDING_DOMAIN_REVIEW")
        if k26 not in obs_to_entity:
            obs_to_entity[k26] = f"PROJ-REVIEW-2026-07-{pid}"
            obs_meta[k26] = ("REVIEW_REQUIRED", "AMBIGUOUS_ID_MATCH", f"Identical ID {pid} but {reason}", "PENDING_DOMAIN_REVIEW")

    # Finally, all remaining unlinked observations receive deterministic UNMATCHED keys
    unmatched_count = 0
    for obs in observations:
        k = obs["canonical_observation_key"]
        if k not in obs_to_entity:
            snap = obs["source_snapshot"]
            pid = obs["source_project_id"]
            obs_to_entity[k] = f"PROJ-UNMATCHED-{snap}-{pid}"
            obs_meta[k] = (
                "UNMATCHED",
                "NO_MATCHING_CANDIDATE",
                f"No candidate met Tier 1-3 criteria for snapshot {snap} ID {pid}",
                "NOT_APPLICABLE",
            )
            unmatched_count += 1

    # Validation: exactly 4,161 observations mapped
    if len(obs_to_entity) != 4161:
        raise ValueError(f"Expected 4,161 mappings, found {len(obs_to_entity)}")
    print(f"  [OK] 100% observations mapped: {len(obs_to_entity)} / 4,161")

    # -------------------------------------------------------------
    # STEP 4: WRITE data/interim/project_identity_map.csv
    # -------------------------------------------------------------
    print()
    print("--- STEP 4: GENERATING PROJECT IDENTITY MAP ---")
    identity_map_rows = []
    for obs in observations:
        k = obs["canonical_observation_key"]
        conf, method, ev, rev = obs_meta[k]
        identity_map_rows.append({
            "canonical_observation_key": k,
            "canonical_project_key": obs_to_entity[k],
            "source_snapshot": obs["source_snapshot"],
            "source_table": obs["source_table"],
            "source_project_id": obs["source_project_id"],
            "match_confidence": conf,
            "match_method": method,
            "match_evidence": ev,
            "review_status": rev,
        })

    IDENTITY_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with IDENTITY_MAP_PATH.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "canonical_observation_key",
            "canonical_project_key",
            "source_snapshot",
            "source_table",
            "source_project_id",
            "match_confidence",
            "match_method",
            "match_evidence",
            "review_status",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(identity_map_rows)

    map_sha256 = sha256_file(IDENTITY_MAP_PATH)
    print(f"  [OK] Identity Map saved: {IDENTITY_MAP_PATH} ({len(identity_map_rows)} rows)")
    print(f"       SHA-256: {map_sha256}")

    # -------------------------------------------------------------
    # STEP 5: WRITE data/interim/project_snapshot_panel.csv
    # -------------------------------------------------------------
    print()
    print("--- STEP 5: GENERATING LONGITUDINAL SNAPSHOT PANEL ---")
    panel_rows = []
    for obs in observations:
        k = obs["canonical_observation_key"]
        conf, method, ev, rev = obs_meta[k]
        row = dict(obs)
        row["canonical_project_key"] = obs_to_entity[k]
        row["match_confidence"] = conf
        row["match_method"] = method
        row["match_evidence"] = ev
        row["review_status"] = rev
        panel_rows.append(row)

    # Sort panel by canonical_project_key, then snapshot_date
    panel_rows.sort(key=lambda x: (x["canonical_project_key"], x["snapshot_date"]))

    panel_columns = [
        "canonical_project_key",
        "canonical_observation_key",
        "match_confidence",
        "match_method",
        "match_evidence",
        "review_status",
    ] + [col for col in observations[0].keys() if col != "canonical_observation_key"]

    PANEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PANEL_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=panel_columns)
        writer.writeheader()
        writer.writerows(panel_rows)

    panel_sha256 = sha256_file(PANEL_PATH)
    print(f"  [OK] Panel saved: {PANEL_PATH} ({len(panel_rows)} rows)")
    print(f"       SHA-256: {panel_sha256}")

    # -------------------------------------------------------------
    # SUMMARY METRICS
    # -------------------------------------------------------------
    conf_counts = Counter(r["match_confidence"] for r in identity_map_rows)
    unique_projects = len(set(r["canonical_project_key"] for r in identity_map_rows))

    # Calculate project observation distribution
    proj_obs_count = defaultdict(list)
    for r in identity_map_rows:
        proj_obs_count[r["canonical_project_key"]].append(r["source_snapshot"])

    trajectory_dist = Counter(tuple(sorted(set(snaps))) for snaps in proj_obs_count.values())

    print()
    print("=" * 75)
    print("IDENTITY RESOLUTION SUMMARY METRICS")
    print("=" * 75)
    print(f"  Total Canonical Observations: {len(observations)}")
    print(f"  Resolved Physical Projects:   {unique_projects}")
    print()
    print("  Observations by Confidence Tier:")
    for tier, count in conf_counts.most_common():
        pct = (count / len(observations)) * 100
        print(f"    {tier:<26}: {count:5d} ({pct:5.1f}%)")
    print()
    print("  Longitudinal Trajectory Distribution:")
    for traj, count in trajectory_dist.most_common():
        label = " + ".join(traj)
        print(f"    {label:<35}: {count:5d} projects")

    return {
        "identity_map_path": IDENTITY_MAP_PATH,
        "panel_path": PANEL_PATH,
        "total_observations": len(observations),
        "unique_projects": unique_projects,
        "confidence_counts": conf_counts,
        "trajectory_distribution": trajectory_dist,
        "map_sha256": map_sha256,
        "panel_sha256": panel_sha256,
    }


if __name__ == "__main__":
    resolve_identities()
