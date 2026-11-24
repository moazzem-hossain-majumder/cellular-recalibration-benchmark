import json, re, concurrent.futures
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).parent
DOIS=['10.1109/MCOM.011.2200707','10.1109/OJCOMS.2024.3499370','10.1016/j.comnet.2024.110207','10.1093/jrsssc/qlae054','10.3390/network6040092','10.1145/3339825.3394938','10.1145/3419394.3423629','10.1109/TMLCN.2024.3352541','10.1109/MASS62177.2024.00018','10.1214/23-AOS2276','10.1145/3478535']
PMLR=['v202/zaffran23a','v202/xu23r','v162/zaffran22a','v202/bhatnagar23a','v235/angelopoulos24a','v235/podkopaev24a','v306/ilyas26a','v267/ge25a','v271/hou25a','v306/min26c','v300/gauthier26a']
def fetch(item):
    kind,ident=item
    url='https://api.crossref.org/works/'+ident if kind=='doi' else 'https://proceedings.mlr.press/'+ident+'.html'
    r=requests.get(url,timeout=55);r.raise_for_status()
    if kind=='doi': data=r.json()['message']
    else:
        s=BeautifulSoup(r.text,'html.parser')
        data={'meta':[(x.get('name'),x.get('content')) for x in s.select('meta[name]')], 'text':s.get_text(' ',strip=True)}
    path=ROOT/(ident.replace('/','_')+'.json');path.write_text(json.dumps({'url':url,'data':data},ensure_ascii=False,indent=2),encoding='utf8')
    return ident, data.get('title') or data.get('text','')[:350]
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for f in [pool.submit(fetch,x) for x in [('doi',x) for x in DOIS]+[('pmlr',x) for x in PMLR]]:
            try: print(f.result(),flush=True)
            except Exception as e: print(type(e).__name__,str(e),flush=True)
