from fetch_metadata import fetch, ROOT
import requests,json
from bs4 import BeautifulSoup
for doi in ['10.3390/network6040092','10.1093/jrsssb/qkaf008']:
    try: print(fetch(('doi',doi)))
    except Exception as e: print(e)
items={
'tibshirani2019':('2019','8fb21ee7a2207526da55a679f0332de2',False),
'geifman2017':('2017','4a8423d5e91fda00bb7e46540e2b0cf1',False),
'gibbs2021':('2021','0d441de75945e5acbc865406fc9a2559',False),
'lin2022':('2022','c8d2860e1b51a1ffadc7ed0a06f8d8f5',True),
'pid2023':('2023','47f2fad8c1111d07f83c91be7870f8db',True)}
for key,(year,h,conf) in items.items():
    url=f'https://proceedings.neurips.cc/paper_files/paper/{year}/hash/{h}-Abstract'+('-Conference' if conf else '')+'.html'
    r=requests.get(url,timeout=35);r.raise_for_status();r.encoding='utf8';s=BeautifulSoup(r.text,'html.parser')
    bib=next((a['href'] for a in s.select('a[href]') if 'bib' in a.get_text().lower()),None)
    from urllib.parse import urljoin
    data={'url':url,'text':s.get_text(' ',strip=True),'bib':requests.get(urljoin(url,bib),timeout=35).text if bib else ''}
    (ROOT/(key+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');print(key,data['bib'])
url='https://jmlr.org/papers/v25/22-1218.html'
r=requests.get(url,timeout=35);s=BeautifulSoup(r.content,'html.parser');data={'url':url,'text':s.get_text(' ',strip=True),'meta':[(m.get('name'),m.get('content')) for m in s.select('meta[name]')]}
(ROOT/'gibbs2024.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');print('gibbs2024',data['text'][-1700:])
