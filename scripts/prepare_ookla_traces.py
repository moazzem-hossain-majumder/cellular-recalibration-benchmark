"""Materialize only the 43 benchmark CSVs and verify each against its pinned archive."""
from pathlib import Path
from zipfile import ZipFile
import hashlib

ROOT = Path(__file__).resolve().parents[1]
folder = 'Active Performance Dataset - 1/Ookla Speedtests/Op1 and Op2 - Italy/'
def main():
    archive = ROOT/'data/raw/14073311/Active Performance Dataset - 1.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != 'f8bc2a621268775d0cf983524f062d1ffbddd365af1166c6b93e76991c881155':
        raise ValueError('Unexpected archive hash')
    dest = ROOT/'data/extracted/14073311'/folder
    dest.mkdir(parents=True,exist_ok=True)
    with ZipFile(archive) as z:
        names = [n for n in z.namelist() if n.startswith(folder) and Path(n).suffix.lower()=='.csv' and n==folder+Path(n).name]
        if len(names)!=43 or len(set(names))!=43:
            raise ValueError('Unexpected member inventory')
        for n in names:
            contents = z.read(n)
            target = dest/Path(n).name
            if target.exists() and target.read_bytes()!=contents:
                raise ValueError(f'Extracted trace differs from archive: {target.name}')
            if not target.exists():
                target.write_bytes(contents)
        if set(p.name for p in dest.glob('*.csv')) != {Path(n).name for n in names}:
            raise ValueError('Unexpected additional trace')
    print('43 extracted trace files match the pinned archive.')
if __name__=='__main__':
    main()

