"""Fetch original Irish inputs if absent; validate production data and released code."""
import hashlib
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.compare_sirhan_external import PINS


def acquire(path,url):
    if path.exists():
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(dir=path.parent) as directory:
        temp = Path(directory)/'archive.zip'
        subprocess.run(['curl','-fL','--retry','2',url,'-o',str(temp)],check=True)
        with ZipFile(temp) as archive:
            if archive.testzip() is not None:
                raise ValueError('Archive is corrupt')
        temp.replace(path)


def main():
    raw = ROOT/'data/raw'
    data = raw/'ucc-external/5G-production-dataset.zip'
    acquire(data,'https://raw.githubusercontent.com/uccmisl/5Gdataset/306d92eba81cb4f1195d8b8eba625666a02a10ec/5G-production-dataset.zip')
    expected = 'abc729d696b5e0ba34a9c6ed35a851f2868d2b5071be5efb8a49691c23bb1a9b'
    if hashlib.sha256(data.read_bytes()).hexdigest()!=expected:
        raise ValueError('Unexpected Irish production archive')
    release = raw/'sirhan-v1.zip'
    acquire(release,'https://data.mendeley.com/public-api/zip/ncbdm2c36d/download/1')
    with ZipFile(release) as archive:
        for name,pin in PINS.items():
            member, = [p for p in archive.namelist() if p.endswith('/'+name)]
            if hashlib.sha256(archive.read(member)).hexdigest()!=pin:
                raise ValueError(name)


if __name__=='__main__':
    main()
