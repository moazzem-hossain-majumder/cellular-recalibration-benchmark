import json,requests,concurrent.futures
from pathlib import Path
from pypdf import PdfReader
from io import BytesIO
ROOT=Path(__file__).parent
urls={}
for f in ROOT.glob('v*.json'):
    d=dict(json.loads(f.read_text(encoding='utf8'))['data']['meta']);urls[f.stem]=d['citation_pdf_url']
urls.update({'crc2024':'https://openreview.net/pdf?id=33XGfHLtZg','basit2024':'https://ece.northeastern.edu/fac-ece/dkoutsonikolas/publications/mass24.pdf','gibbs2024':'https://jmlr.org/papers/volume25/22-1218/22-1218.pdf'})
def run(item):
    key,url=item
    r=requests.get(url,timeout=40);r.raise_for_status()
    reader=PdfReader(BytesIO(r.content));text='\n'.join(p.extract_text() or '' for p in reader.pages)
    (ROOT/(key+'.txt')).write_text(text,encoding='utf8');return key,len(reader.pages),len(text)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    for f in [pool.submit(run,x) for x in urls.items()]:
        try: print(f.result(),flush=True)
        except Exception as e: print(str(e),flush=True)
