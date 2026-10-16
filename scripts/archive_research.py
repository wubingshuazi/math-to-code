"""Preserve the full worker journals as a compact release artifact."""

import hashlib
import json
from pathlib import Path
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    directory = ROOT / "results/sharpness_journals"
    files = sorted(directory.glob("start_*.jsonl"))
    if not files:
        raise SystemExit("No local worker journals found.")
    archive = ROOT / ".buildcheck/thermal_search_journals.zip"
    archive.parent.mkdir(exist_ok=True)
    members = []
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            data = path.read_bytes()
            member_name = "sharpness_journals/" + path.name
            # Fixed ZIP metadata permits byte-identical re-archiving.
            info = zipfile.ZipInfo(member_name, date_time=(2026, 10, 17, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members.append({"path": member_name, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()})
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
        for member in members:
            if hashlib.sha256(bundle.read(member["path"])).hexdigest() != member["sha256"]:
                raise ValueError("Archived journal hash differs")
    report = {
        "artifact": "thermal_search_journals.zip",
        "release_asset": "https://github.com/wubingshuazi/math-to-code/releases/download/v0.2.0/thermal_search_journals.zip",
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "archive_bytes": archive.stat().st_size,
        "compression": {"method": "deflate", "level": 9, "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION},
        "uncompressed_bytes": sum(member["bytes"] for member in members),
        "worker_journals": len(members),
        "members": members,
    }
    (ROOT / "results/research_artifacts.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "members"}, indent=2))


if __name__ == "__main__":
    main()
