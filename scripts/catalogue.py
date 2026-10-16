#!/usr/bin/env python3
"""Rebuild a complete, commit-pinned metadata catalogue using only the stdlib.

This is a triage aid. Keyword matches and the manual shortlist are not evidence
that a theorem is correct, practically efficient, new, or unimplemented.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote


UPSTREAM_COMMIT = "1581d4cbdd69a0faf34b2089614fe2a814316a6a"
AUDIT_DATE = "2026-10-17"
ROOT = Path(__file__).resolve().parents[1]

# Intentionally broad and disclosed. Apply to family title, summary, paper titles,
# and abstracts. A hit only means that the metadata merits human/paper review.
KEYWORDS = {
    "algorithm": r"\balgorithms?\b",
    "complexity_or_runtime": r"\b(?:computational|complexity|running.time|bit.time|polynomial.time|word.time)\b",
    "sampling_or_counting": r"\b(?:sampl(?:e|es|ing)|counting|decoder|reconstruction)\b",
    "approximation": r"\b(?:approximat(?:e|es|ion)|derandomization|identity.testing)\b",
    "numerical_formula": r"\b(?:one.variable|explicit.formula|variational.formula|exact.coefficient|capacity)\b",
    "construction": r"\b(?:deterministic.construction|constructive|constructively)\b",
}

# Deliberately manual, bounded follow-up set, selected after reading the metadata.
# This is not an exhaustive count of useful applications. Only 276 is selected
# as a small scalar-formula pilot; the others require full-paper feasibility work.
PRIMARY = {
    "104": ("Game solver", "Exact mean-payoff/stochastic/parity game outputs; inspect constants and implementable subroutines."),
    "110": ("Online k-server experiment", "Finite rational metrics have a stated polynomial implementation; audit preprocessing and movement constants."),
    "113": ("Perfect-matching counter", "FPRAS and exact zero detection; compare against exact enumeration on small graphs."),
    "114": ("Polymatroid-base counter", "FPRAS in a rank-oracle model; charge oracle work explicitly in experiments."),
    "115": ("Contingency-table sampler/counter", "Useful finite inputs and structural zeros; audit transition details and polynomial constants."),
    "116": ("Noncommutative identity tester", "Construct explicit hitting tuples; audit field representations and output sizes."),
    "120": ("General-graph matching solver", "Concrete output and near-linear asymptotic claim; audit crossover sizes and randomized failure checks."),
    "121": ("Edit-distance approximator", "Compare accuracy/time with exact dynamic programming; asymptotic fixed-epsilon guarantee does not establish practical speed."),
    "125": ("Metric k-median approximator", "Finite rational facility instances; inspect dependence on epsilon and algorithmic constants."),
    "128": ("Shortest-common-superstring approximation", "Concrete string output with a claimed factor-two guarantee. Existing implementations include [nurric-ai/lazy-scs](https://github.com/nurric-ai/lazy-scs) and [buberlo/veriscs](https://github.com/buberlo/veriscs); this is not an empty implementation gap. Audit and compare existing work first."),
    "131": ("Fixed-degree graph sampler", "Edge-switch chain is directly experimentable; O(n^8) worst-case mixing is not a practical runtime promise."),
    "138": ("Subset-sum solver", "Compare against meet-in-the-middle on fixed inputs; exponential memory, constants and word assumptions need auditing."),
    "142": ("Prime-field polynomial factorizer", "Concrete coefficients/factors; benchmark against existing factorization libraries and inspect polynomial exponent."),
    "174": ("Thin spanning-tree constructor", "Concrete tree and cut inequalities; inspect the universal constant and construction overhead."),
    "178": ("Ramanujan-graph constructor", "Concrete adjacency list; fixed-degree exponent and sufficiently-large-n threshold require auditing."),
    "276": ("Generalized amplitude-damping one-use Holevo calculator and conditional capacity audit", "Explicit one-variable maximization has a small numerical implementation surface; validate endpoints and Holevo ensembles. Related one-use formulas already exist. Any interpretation as regularized classical capacity is conditional on the upstream theorem; this is an engineering/audit pilot, not a novelty claim."),
}

DEFERRED = {
    "102": "Hardness/approximation thresholds constrain algorithms; they are not an algorithmic speedup.",
    "103": "An effective log-space compiler is stated, but the metadata does not make its polynomial exponent or practical compilation cost usable.",
    "107": "An arithmetic matrix-multiplication exponent is not evidence of a usable BLAS replacement; tensor sizes, constants and numerical stability need review.",
    "109": "The exponent saving is kappa = 2^-182; no useful finite-input speedup follows from the asymptotic statement.",
    "111": "The metadata explicitly says no polynomial-time implementation is asserted.",
    "122": "General fixed-deletion trace reconstruction has quasipolynomial bounds and a superpolynomial sample lower bound; not a low-cost first pilot.",
    "124": "The linked paper's stated bound is O((L+2)^150020) deterministic multitape steps; polynomial does not mean practical.",
    "130": "The exponent saving is delta = 10^-13 in exact complex arithmetic with unrestricted coefficients; no practical FFT improvement is established.",
    "137": "Space improves but simulation time is explicitly unrestricted.",
    "139": "Only exact value-and-gradient oracle-query complexity is bounded; computation between queries is unrestricted.",
    "141": "A counting-hierarchy membership theorem is not a practical real-polynomial solver.",
    "283": "The target-dependent Boolean oracle may have an unrestricted truth table; efficient construction is not asserted.",
}


def plain(text: str) -> str:
    """Readable text while preserving mathematical notation and raw source too."""
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def pinned_url(path: str, commit: str) -> str:
    return f"https://github.com/openai/math/blob/{commit}/" + quote(path, safe="/")


def parse_contents(source: str, commit: str) -> list[dict]:
    families: list[dict] = []
    family_re = re.compile(r"^\*\*(\d{3})\. (.*?)\.\*\*\s*(.*)$", re.S)
    paper_re = re.compile(r"^&emsp;\[([^\n]*)\]\((preprints/[^\n]+\.pdf)\)([^\n]*)\n\s*(.*)$", re.S)
    for match in re.finditer(r"<td>\s*(.*?)\s*</td>", source, re.S):
        block = match.group(1).strip()
        line = source.count("\n", 0, match.start(1)) + 1
        family = family_re.fullmatch(block)
        if family:
            family_id, title, summary = family.groups()
            families.append({
                "id": family_id,
                "title": plain(title),
                "title_markdown": title,
                "summary": plain(summary),
                "summary_markdown": summary,
                "contents_line": line,
                "papers": [],
            })
            continue
        paper = paper_re.fullmatch(block)
        if paper:
            if not families:
                raise ValueError("Manuscript appears before its family")
            title, path, note, abstract = paper.groups()
            if not abstract.strip():
                raise ValueError(f"Empty manuscript abstract: {path}")
            families[-1]["papers"].append({
                "title": plain(title),
                "title_markdown": title,
                "manuscript_note": plain(note),
                "path": path,
                "pdf_url": pinned_url(path, commit),
                "raw_pdf_url": f"https://raw.githubusercontent.com/openai/math/{commit}/" + quote(path, safe="/"),
                "abstract": plain(abstract),
                "abstract_markdown": abstract,
                "contents_line": line,
            })
            continue
        raise ValueError(f"Unrecognized catalogue table row at line {line}: {block[:100]!r}")
    return families


def overview_subjects(source: str) -> dict[str, str]:
    subjects: dict[str, str] = {}
    current = None
    for line in source.splitlines():
        section = re.match(r"\\cataloguesection\{([^}]+)\}", line)
        if section:
            current = section.group(1)
        entry = re.match(r"\\resultentry\{(\d{3})\}", line)
        if entry:
            if current is None:
                raise ValueError("Overview entry has no subject")
            subjects[entry.group(1)] = current
    return subjects


def make_report(data: dict) -> str:
    counts = data["counts"]
    families = {family["id"]: family for family in data["families"]}
    lines = [
        "# Reproducible mathematics-to-code screening",
        "",
        f"Audit date: {AUDIT_DATE} (Asia/Shanghai). Upstream commit: `{data['source']['commit']}`.",
        f"[Pinned CONTENTS.md]({data['source']['contents_url']}); [pinned overview.tex]({data['source']['overview_url']}).",
        "The overview itself is dated October 6, 2026. The audit date is not the publication date of each paper.",
        "",
        f"Parsed **{counts['manuscripts']} manuscripts in {counts['families']} result families**, with every title, PDF URL and abstract retained in `catalogue.json`.",
        f"Family identifiers run from {counts['minimum_family_id']} to {counts['maximum_family_id']}; omitted identifiers are {', '.join(counts['missing_family_ids'])}. Identifiers are preserved, not renumbered.",
        "The user's figure of 722 is not the manuscript count in this pinned snapshot. Revisions can change counts.",
        "",
        "## What the counts do and do not establish",
        "",
        f"The disclosed metadata heuristic flags **{counts['keyword_hit_families']} families**. A manually selected follow-up set contains **{counts['manual_primary_families']} families**. Neither number counts proven practical applications.",
        "The number of results with practical programming value is **unknown**. The number whose applications nobody has implemented is **unknown**. This screening neither establishes theorem correctness nor performs a worldwide novelty search.",
        "The upstream README says the collection is at different verification stages and some unformalized results could have issues. A catalogue assertion is not an independent correctness audit.",
        "",
        "## Manual follow-up candidates",
        "",
        "These are candidate experiments, not implementation-completeness or usefulness claims. Only family 276 is selected as the initial small one-use Holevo scalar-formula pilot; its regularized-capacity interpretation is conditional on the upstream theorem. The other entries need full-paper review before implementation commitments.",
        "",
        "| Family | Possible executable artifact | Why review / limitation |",
        "|---|---|---|",
    ]
    for family_id, (artifact, note) in PRIMARY.items():
        url = families[family_id]["papers"][0]["pdf_url"]
        lines.append(f"| [{family_id}]({url}) | {artifact} | {note} |")
    lines += [
        "",
        "## Deferred or excluded from the first practical pilot",
        "",
        "These exclusions concern the first engineering pilot, not the mathematical importance of the research.",
        "",
        "| Family | Reason |",
        "|---|---|",
    ]
    for family_id, reason in DEFERRED.items():
        url = families[family_id]["papers"][0]["pdf_url"]
        lines.append(f"| [{family_id}]({url}) | {reason} |")
    lines += [
        "",
        "## Transparent heuristic",
        "",
        "Case-insensitive regular expressions are applied to the concatenated family title, summary, manuscript titles and abstracts. All matching rule names are recorded per family. No score or probability is inferred. The full regex strings are recorded in `catalogue.json` and in `scripts/catalogue.py`.",
        "",
        "| Rule | Regex |",
        "|---|---|",
    ]
    for name, pattern in KEYWORDS.items():
        escaped_pattern = pattern.replace("|", "\\|")
        lines.append(f"| {name} | `{escaped_pattern}` |")
    lines += [
        "",
        "Known limitations: keyword false positives include hardness theorems, existence results and mathematical approximation unrelated to an efficient program. False negatives include useful implicit constructions or numerical bounds without these words. Manual candidates reflect a bounded audit, not exhaustive review.",
        "",
        "## Reproduce and query",
        "",
        "No network access or third-party packages are required after downloading the pinned input files. From the repository root:",
        "",
        "```text",
        "python scripts/catalogue.py",
        "python scripts/catalogue.py --family 276",
        "python scripts/catalogue.py --query sampling",
        "```",
        "",
        "The first command rebuilds both generated outputs and checks the header counts, all family IDs, unique manuscript paths, nonempty abstracts and subject coverage. `--family` and `--query` only print existing catalogue records and do not change files. Input SHA-256 hashes are stored in `catalogue.json` so snapshot drift is detectable. All generated PDF links pin the exact upstream commit.",
        "",
        "Candidate queries for a separate prior-art review (record search date and inspected results): `\"generalized amplitude damping\" capacity python`, `\"generalized amplitude damping\" Holevo`, and the exact manuscript title plus `implementation` or `GitHub`. An absent search hit cannot establish that nobody has implemented something.",
        "",
        "## All heuristic hits",
        "",
        "| Family | Title | Matching rules | Manual status |",
        "|---|---|---|---|",
    ]
    for family in data["families"]:
        if family["screening"]["keyword_hits"]:
            title = family["title"].replace("|", "\\|")
            rules = ", ".join(family["screening"]["keyword_hits"])
            lines.append(f"| {family['id']} | {title} | {rules} | {family['screening']['manual_status']} |")
    return "\n".join(lines) + "\n"


def build(contents_path: Path, overview_path: Path, commit: str) -> dict:
    contents_bytes = contents_path.read_bytes()
    overview_bytes = overview_path.read_bytes()
    contents = contents_bytes.decode("utf-8-sig")
    overview = overview_bytes.decode("utf-8-sig")
    families = parse_contents(contents, commit)
    subjects = overview_subjects(overview)
    ids = [family["id"] for family in families]
    manuscript_paths = [paper["path"] for family in families for paper in family["papers"]]
    declared = re.search(r"\*\*(\d+) manuscripts covering (\d+) result families\.\*\*", contents)
    if declared is None:
        raise ValueError("Declared counts not found")
    expected_manuscripts, expected_families = map(int, declared.groups())
    checks = {
        "declared_family_count_matches": len(families) == expected_families,
        "declared_manuscript_count_matches": len(manuscript_paths) == expected_manuscripts,
        "unique_family_ids": len(ids) == len(set(ids)),
        "unique_manuscript_paths": len(manuscript_paths) == len(set(manuscript_paths)),
        "every_family_has_manuscripts": all(family["papers"] for family in families),
        "overview_family_ids_match": set(ids) == set(subjects),
        "manual_ids_exist": (set(PRIMARY) | set(DEFERRED)) <= set(ids),
    }
    if not all(checks.values()):
        raise ValueError(f"Catalogue validation failed: {checks}")
    for family in families:
        family["subject"] = subjects[family["id"]]
        haystack = " ".join([family["title"], family["summary"]] + [paper["title"] + " " + paper["abstract"] for paper in family["papers"]])
        family["screening"] = {
            "keyword_hits": [name for name, pattern in KEYWORDS.items() if re.search(pattern, haystack, re.I)],
            "manual_status": "follow_up_candidate" if family["id"] in PRIMARY else "deferred_first_pilot" if family["id"] in DEFERRED else "not_manually_reviewed",
            "manual_note": PRIMARY[family["id"]][1] if family["id"] in PRIMARY else DEFERRED.get(family["id"]),
            "practical_usefulness_proved": False,
            "absence_of_prior_implementation_established": False,
        }
    return {
        "schema_version": 1,
        "source": {
            "repository": "https://github.com/openai/math",
            "commit": commit,
            "audit_date": AUDIT_DATE,
            "audit_timezone": "Asia/Shanghai",
            "overview_document_date": "2026-10-06",
            "contents_url": pinned_url("CONTENTS.md", commit),
            "overview_url": pinned_url("overview.tex", commit),
            "contents_sha256": hashlib.sha256(contents_bytes).hexdigest(),
            "overview_sha256": hashlib.sha256(overview_bytes).hexdigest(),
            "claim_status": "Metadata records upstream assertions, not independently verified theorems.",
        },
        "counts": {
            "families": len(families),
            "manuscripts": len(manuscript_paths),
            "minimum_family_id": min(ids),
            "maximum_family_id": max(ids),
            "missing_family_ids": [f"{number:03}" for number in range(int(min(ids)), int(max(ids)) + 1) if f"{number:03}" not in ids],
            "keyword_hit_families": sum(bool(family["screening"]["keyword_hits"]) for family in families),
            "manual_primary_families": len(PRIMARY),
            "practically_useful_families": None,
            "unimplemented_practically_useful_families": None,
        },
        "method": {
            "heuristic_fields": ["family title", "family summary", "paper titles", "paper abstracts"],
            "case_sensitive": False,
            "regex_rules": KEYWORDS,
            "primary_candidate_ids": list(PRIMARY),
            "first_pilot_id": "276",
            "deferred_first_pilot_ids": list(DEFERRED),
            "limitations": "Non-exhaustive metadata triage; no correctness, practical-efficiency, or worldwide implementation-novelty certification.",
        },
        "validation": checks,
        "families": families,
    }


def main() -> None:
    # Windows terminals may otherwise use GBK, which cannot print every title.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contents", type=Path, default=ROOT / "research/upstream-contents.md")
    parser.add_argument("--overview", type=Path, default=ROOT / "research/upstream-overview.tex")
    parser.add_argument("--commit", default=UPSTREAM_COMMIT)
    parser.add_argument("--output", type=Path, default=ROOT / "research/catalogue.json")
    parser.add_argument("--report", type=Path, default=ROOT / "research/screening.md")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--family", help="Print one existing family record, for example 276")
    group.add_argument("--query", help="Case-insensitive substring search of all existing metadata")
    args = parser.parse_args()
    if args.family is not None or args.query is not None:
        data = json.loads(args.output.read_text(encoding="utf-8"))
        if args.family is not None:
            family_id = args.family.zfill(3)
            results = [family for family in data["families"] if family["id"] == family_id]
        else:
            results = [family for family in data["families"] if args.query.casefold() in json.dumps(family, ensure_ascii=False).casefold()]
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    data = build(args.contents, args.overview, args.commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.write_text(make_report(data), encoding="utf-8")
    print(json.dumps({"counts": data["counts"], "validation": data["validation"]}, indent=2))


if __name__ == "__main__":
    main()
