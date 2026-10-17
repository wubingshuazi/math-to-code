"""Prepare the fixed, unused Adobe holdout inputs without running a solver.

New engineering: 100% GPT-generated. Uses the already pinned corpus loader
and list/file hash formats from scs_native_cases.py. No benchmark or solver
import occurs. Preserve the downloaded Adobe source and BSD-3-Clause notice
alongside any redistribution of the derived input files.

Run from the repository root, after freezing the native candidate:

    python experiments/prepare_scs_holdout.py --output-dir .verification/scs-native-inputs/heldout-001

The two predetermined cases contain 512 glyph names and the complete 2,092
name holdout split, selected with seed 1282026. This script refuses an
existing output directory, including an empty one. To reproduce without
overwriting the first record, pass a different unused --output-dir.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

if __package__:
    from .scs_native_cases import (
        SOLVER_COMMIT, input_digest, load_adobe_glyph_names, native_line_bytes,
    )
else:
    from scs_native_cases import (
        SOLVER_COMMIT, input_digest, load_adobe_glyph_names, native_line_bytes,
    )


SEED = 1282026
HOLDOUT_LIMITS = (512, 2092)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)


def prepare_holdout(out_dir: Path | str) -> dict[str, Any]:
    """Emit exactly two fixed holdout cases, original sources and manifest."""
    output = Path(out_dir)
    # Check before downloading or creating files; mkdir's exist_ok=False
    # also protects against a competing process creating the same directory.
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing holdout directory: {output}")
    output.mkdir(parents=True, exist_ok=False)
    cache = output / "adobe-source-and-license"
    development, dev_provenance = load_adobe_glyph_names(cache, split="development", seed=SEED)
    holdout, hold_provenance = load_adobe_glyph_names(cache, split="holdout", seed=SEED)
    if len(development) != 2189 or len(holdout) != 2092:
        raise ValueError("pinned corpus no longer has the expected 2189/2092 partition")
    development_set, holdout_set = set(development), set(holdout)
    if development_set & holdout_set:
        raise ValueError("development and holdout dictionaries intersect")
    if len(development_set | holdout_set) != 4281:
        raise ValueError("development/holdout union does not reproduce the pinned dictionary")

    cases = []
    for limit in HOLDOUT_LIMITS:
        words, provenance = load_adobe_glyph_names(cache, limit=limit, split="holdout", seed=SEED)
        if len(words) != limit or not set(words) <= holdout_set or set(words) & development_set:
            raise ValueError("selected case is not the requested disjoint holdout subset")
        name = f"adobe-glyphs-holdout-{limit}"
        path = output / (name + ".txt")
        raw = native_line_bytes(words)
        _write_new(path, raw)
        cases.append({
            "name": name,
            "path": path.name,
            "strings": len(words),
            "input_chars": sum(map(len, words)),
            "unique_strings": len(set(words)),
            "alphabet_cardinality": len(set(b"".join(words))),
            "input_sha256": input_digest(words),
            "file_sha256": _sha(raw),
            "file_bytes": len(raw),
            "kind": "adobe_glyph_names",
            "source": "real_dictionary",
            "dataset_role": "heldout",
            "provenance": provenance,
        })

    generator_path = Path(__file__).with_name("scs_native_cases.py")
    manifest = {
        "schema_version": 1,
        "engineering_attribution": "100% GPT-generated; original corpus and solver attribution preserved",
        "target_repository": "https://github.com/nurric-ai/lazy-scs",
        "target_commit": SOLVER_COMMIT,
        "generator_sha256": _sha(generator_path.read_bytes()),
        "preparer_sha256": _sha(Path(__file__).read_bytes()),
        "native_input_note": "UTF-8 lines containing ASCII glyph names; no FASTA markers, CR/LF or whitespace inside names",
        "dataset_role": "heldout; no solver runs are performed by this preparer",
        "seed": SEED,
        "fixed_selection_limits": list(HOLDOUT_LIMITS),
        "development_disjointness": {
            "checked": True,
            "development_names": len(development),
            "holdout_names": len(holdout),
            "intersection_names": 0,
            "union_names": 4281,
            "development_input_sha256": input_digest(development),
            "holdout_input_sha256": input_digest(holdout),
            "split_method": dev_provenance["split_method"],
            "corpus_commit": hold_provenance["commit"],
        },
        "case_count": len(cases),
        "cases": cases,
    }
    _write_new(output / "manifest.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(".verification/scs-native-inputs/heldout-001"))
    args = parser.parse_args()
    manifest = prepare_holdout(args.output_dir)
    print(json.dumps({
        "manifest": str(args.output_dir / "manifest.json"),
        "manifest_sha256": _sha((args.output_dir / "manifest.json").read_bytes()),
        "case_count": manifest["case_count"],
        "cases": [{key: case[key] for key in ("name", "strings", "input_chars", "input_sha256", "file_sha256")}
                  for case in manifest["cases"]],
        "development_disjointness": manifest["development_disjointness"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
