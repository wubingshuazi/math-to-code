"""Prepare pinned upstream lazy-scs sources and a checked experimental patch.

Requires Git; downloads only public, hash-pinned source files. New preparation
engineering: 100% GPT-generated. Original implementation/credits remain MIT.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import urllib.request


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare(directory: Path, variant: str, source_cache: Path | None = None) -> dict:
    patches = Path(__file__).resolve().parent / 'patches/lazy-scs'
    index_path = patches / 'source_index.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    if variant not in index['variants']:
        raise ValueError(f'unknown variant {variant}')
    destination = directory.absolute()
    if destination.exists():
        raise FileExistsError('Use a new directory; earlier snapshots are preserved.')
    destination.mkdir(parents=True)
    expected_paths = {record['path'] for record in index['files']}
    for record in index['files']:
        relative = PurePosixPath(record['path'])
        if relative.is_absolute() or '..' in relative.parts or not relative.parts:
            raise ValueError('unsafe source path')
        if source_cache is None:
            url = f"https://raw.githubusercontent.com/{index['repository']}/{index['commit']}/{record['path']}"
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read()
        else:
            data = (source_cache / record['path']).read_bytes()
        if digest(data) != record['sha256'] or len(data) != record['bytes']:
            raise ValueError(f"pinned source mismatch: {record['path']}")
        output = destination / record['path']
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    applied = []
    for patch_name in index['variants'][variant]['patches']:
        patch = patches / patch_name
        data = patch.read_bytes()
        if digest(data) != index['patch_sha256'][patch_name]:
            raise ValueError(f'patch checksum mismatch: {patch_name}')
        for line in data.decode('utf-8').splitlines():
            if line.startswith(('--- a/', '+++ b/')) and line[6:] not in expected_paths:
                raise ValueError('patch contains an unexpected path')
        env = os.environ.copy()
        # Apply as a standalone file tree, without discovering the parent repo.
        env['GIT_CEILING_DIRECTORIES'] = str(destination.parent)
        for check in [True, False]:
            command = ['git', '-c', 'core.autocrlf=false', '-c', 'core.eol=lf',
                       'apply', '--whitespace=nowarn']
            if check:
                command.append('--check')
            command.append(str(patch.absolute()))
            subprocess.run(command, cwd=destination, env=env, check=True)
        applied.append({'patch': patch_name, 'sha256': digest(data)})
    for path, expected in index['variants'][variant]['file_sha256'].items():
        if digest((destination / path).read_bytes()) != expected:
            raise ValueError(f'prepared variant checksum mismatch: {path}')
    notices = destination / 'third-party-notices'
    shutil.copytree(patches / 'licenses', notices)
    provenance = {
        'repository': index['repository'], 'commit': index['commit'], 'variant': variant,
        'source_index_sha256': digest(index_path.read_bytes()), 'applied_patches': applied,
        'all_prepared_source_hashes_verified': True,
        'attribution': index['attribution'],
    }
    (destination / 'source_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    return provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--variant', default='aho-trim')
    parser.add_argument('--source-cache', type=Path, help='optional local original files, verified against the same hashes')
    args = parser.parse_args()
    print(json.dumps(prepare(args.directory, args.variant, args.source_cache), indent=2))


if __name__ == '__main__':
    main()
