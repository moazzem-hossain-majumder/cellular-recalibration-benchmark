"""Acquire and verify active measurements; preserve metadata and verify bytes."""
import argparse
import hashlib
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    '8224890': {
        'Throughput Tests - Speedtest - Active Measurements.csv': '4c6d46d645df9fbd7b050e4464040b5f',
        'description.pdf': 'cb10809b854ecfd3f97a74d91c42e163',
    },
    '14073311': {
        'Active Performance Dataset - 1.zip': '59684dec4e26bd882cf6e6551cce50ad'
    },
}

def digest(path, algorithm):
    h = hashlib.new(algorithm)
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def fetch(url, path):
    partial = path.with_name(path.name + '.part')
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'TelecomResearch-Phase3/1.0'})
            with urllib.request.urlopen(request, timeout=120) as response, partial.open('wb') as out:
                while block := response.read(1024 * 1024):
                    out.write(block)
            return partial
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true', help='Verify local files against pinned metadata without networking')
    args = parser.parse_args()
    metadata = ROOT / 'data' / 'metadata'
    metadata.mkdir(parents=True, exist_ok=True)
    manifest = []

    for record, selected in FILES.items():
        meta_path = metadata / f'zenodo_{record}.json'
        if not meta_path.exists():
            if args.verify_only:
                raise FileNotFoundError(f'Metadata not found: {meta_path}')
            print(f'Fetching metadata for Zenodo record {record}...')
            fetch(f'https://zenodo.org/api/records/{record}', meta_path).replace(meta_path)
        info = json.loads(meta_path.read_text(encoding='utf-8'))
        assert info['metadata']['license']['id'] == 'cc-by-4.0', 'Review changed license'
        inventory = {entry['key']: entry for entry in info['files']}

        for name, expected_md5 in selected.items():
            entry = inventory[name]
            assert entry['checksum'] == 'md5:' + expected_md5, 'Publisher version changed; review required'
            path = ROOT / 'data' / 'raw' / record / name
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_name(name + '.part')

            # Adopt completed partial download if present and valid
            if not path.exists() and partial.exists():
                if partial.stat().st_size == entry['size'] and digest(partial, 'md5') == expected_md5:
                    print(f'Adopting complete partial download {partial.name} -> {name}')
                    partial.replace(path)

            if not path.exists():
                if args.verify_only:
                    raise FileNotFoundError(f'Raw file missing: {path}')
                print(f'Downloading {record}/{name}', flush=True)
                download_url = f'https://zenodo.org/records/{record}/files/{urllib.parse.quote(name)}?download=1'
                part = fetch(download_url, path)
                if part.stat().st_size != entry['size'] or digest(part, 'md5') != expected_md5:
                    raise ValueError(f'Integrity failure: {part}; retained for inspection')
                part.replace(path)

            if path.stat().st_size != entry['size'] or digest(path, 'md5') != expected_md5:
                raise ValueError(f'Local integrity failure: {path}; not overwritten')

            sha256_hash = digest(path, 'sha256')
            manifest.append({
                'record': record,
                'file': str(path.relative_to(ROOT)).replace('\\', '/'),
                'source': entry['links']['self'],
                'doi': info['metadata']['doi'],
                'license': info['metadata']['license']['id'],
                'bytes': path.stat().st_size,
                'md5': expected_md5,
                'sha256': sha256_hash,
                'verified_utc': datetime.now(timezone.utc).isoformat()
            })
            print(f'Verified {name} (bytes={path.stat().st_size}, sha256={sha256_hash[:8]}...)', flush=True)

    manifest_path = metadata / 'acquisition_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Acquisition manifest written to {manifest_path.relative_to(ROOT)}')

if __name__ == '__main__':
    main()
