"""Fetch and authenticate release files against pinned Git LFS pointers."""
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

from validate_nuwins_drive2 import COMMIT, ROOT, RAW


def acquire(item):
    rel = item['path']
    path = RAW / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    url = f'https://media.githubusercontent.com/media/NUWiNS/pam2025-multi-carrier-dataset/{COMMIT}/{rel}'
    for attempt in range(4):
        try:
            target = path if path.exists() else path.with_suffix('.part')
            if target != path:
                with urlopen(url+'?download=1', timeout=100) as source, target.open('wb') as out:
                    while chunk := source.read(1024*1024):
                        out.write(chunk)
            with target.open('rb') as f:
                sha = hashlib.file_digest(f,'sha256').hexdigest()
            size = target.stat().st_size
            pointer = f'version https://git-lfs.github.com/spec/v1\noid sha256:{sha}\nsize {size}\n'.encode()
            if hashlib.sha1(f'blob {len(pointer)}\0'.encode()+pointer).hexdigest() != item['sha']:
                raise ValueError(f'Invalid release object {rel} ({size} bytes)')
            if target != path:
                target.replace(path)
            print(path.name, size, flush=True)
            return path
        except (ValueError, OSError) as error:
            if attempt == 3 or path.exists():
                raise
            print('Retrying', rel, error, flush=True)
            time.sleep(2**attempt)


def main():
    items=json.loads((ROOT/'data/metadata/nuwins_drive3_inputs.json').read_text(encoding='utf-8-sig'))
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(acquire,items))


if __name__=='__main__':
    main()
