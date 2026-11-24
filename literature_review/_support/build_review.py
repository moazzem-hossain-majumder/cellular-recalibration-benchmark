"""Build bibliographic deliverables from archived publisher metadata."""
import json,re,html
from pathlib import Path
P=Path(__file__).parent; OUT=P.parent
records=[]
def add(key,source,theme,method,limitation):
    raw=json.loads((P/(source+'.json')).read_text(encoding='utf8'))
    d=raw.get('data',raw); f={};typ='inproceedings'
    if source.startswith('10.'):
        typ='article' if d['type']=='journal-article' else 'inproceedings'
        f={'author':' and '.join(a.get('given','')+' '+a.get('family','') for a in d['author']), 'title':d['title'][0]+(': '+d['subtitle'][0] if d.get('subtitle') else ''),'journal' if typ=='article' else 'booktitle':d['container-title'][0], 'year':str(d['published']['date-parts'][0][0]),'volume':d.get('volume',''),'number':d.get('issue',''),'pages':d.get('page','').replace('-','--'),'doi':d['DOI'],'url':'https://doi.org/'+d['DOI']}
        if key=='jacobson2025': f['year']='2025' # final issue year; online-first 2024
        if key=='caso2024':
            f['author']=f['author'].replace('Luca De Nardis','Luca {De Nardis}').replace('Maria-Gabriella Di Benedetto','Maria-Gabriella {Di Benedetto}')
    elif source.startswith('v'):
        m=dict(d['meta']);f={'author':' and '.join(v for k,v in d['meta'] if k=='citation_author'),'title':m['citation_title'].strip(),'booktitle':'Proceedings of the '+m['citation_conference_title'],'year':m['citation_publication_date'][:4], 'volume':source.split('_')[0][1:],'number':'','pages':m['citation_firstpage']+'--'+m['citation_lastpage'],'doi':'','series':'Proceedings of Machine Learning Research','url':raw['url']}
    elif 'bib' in d:
        for k in ['author','title','booktitle','year','volume','pages','doi']:
            match=re.search(r'\b'+k+r'\s*=\s*\{(.*?)\},?\n',d['bib']);f[k]=match.group(1) if match else ''
        f['number']='';f['url']=raw['url']
    else:
        m=dict(d['meta']);typ='article';f={'author':' and '.join(v for k,v in d['meta'] if k=='citation_author'),'title':m['citation_title'],'journal':m['citation_journal_title'],'year':m['citation_publication_date'],'volume':m['citation_volume'],'number':m['citation_issue'],'pages':m['citation_firstpage']+'--'+m['citation_lastpage'],'doi':'','url':raw['url']}
    records.append(dict(key=key,type=typ,fields=f,source=raw['url'],theme=theme,method=method,limitation=limitation))
A='Cellular measurement and throughput decisions';B='Missingness and nonexchangeable calibration';C='Online adaptation and limited feedback';D='Selective risk and decision objectives'
add('kousias2024data','10.1109_MCOM.011.2200707',A,'Multi-technology operational measurements with radio and throughput context','Dataset contribution; does not establish an attempt-budgeted commitment policy')
add('caso2024','10.1109_OJCOMS.2024.3499370',A,'Longitudinal empirical characterization of 5G NSA service evolution','Observed service changes do not establish reliability of sparse-feedback commitments')
add('kousias2024model','10.1016_j.comnet.2024.110207',A,'Empirical 5G NSA performance analysis and supervised ML modeling','Point-prediction accuracy is distinct from positive-commitment violation risk')
add('jacobson2025','10.1093_jrsssc_qlae054',A,'BAMMO componentwise boosting with missing predictors and variable importance','Missing covariates are handled; failed acquisition of calibration labels is a different problem')
add('sirhan2026','10.3390_network6040092',A,'Global and handover/RAT-conditioned conformal bounds with risk-sensitive rate selection','Trace-based operational analysis does not certify MARUR under attempt-limited missing feedback')
add('raca2020','10.1145_3339825.3394938',A,'5G channel/context dataset for throughput and application research','Collection conditions and correlated observations constrain generalization')
add('narayanan2020','10.1145_3419394.3423629',A,'Commercial mmWave measurement mapping and throughput prediction','Prediction performance alone does not quantify cost of obtaining calibration feedback')
add('raca2024','10.1109_TMLCN.2024.3352541',A,'Real-time smartphone throughput prediction and real-network streaming evaluation','Operational deployment evidence does not imply a conformal positive-conditional risk guarantee')
add('basit2024','10.1109_MASS62177.2024.00018',A,'Fine-grained cellular prediction feasibility study using MLP MVTS and GBDT','Conflicting histories limit fine-grained predictability; no universal accuracy conclusion across horizons')
add('zaffran2023','v202_zaffran23a',B,'Conformal intervals with missing covariates and missing-pattern conditioning','Covariate-missingness assumptions do not license treating unobserved outcomes as successes')
add('barber2023','10.1214_23-AOS2276',B,'Weighted conformal inference and coverage degradation beyond exchangeability','Validity depends on the stated weighting and distribution-shift conditions')
add('tibshirani2019','tibshirani2019',B,'Likelihood-ratio weighted conformal prediction under covariate shift','Requires covariate-shift structure and suitable density-ratio information')
add('xu2023','v202_xu23r',B,'Sequential prediction of conditional residual quantiles for time series','Asymptotic conditional validity relies on quantile estimation conditions; not arbitrary missing feedback')
add('zaffran2022','v162_zaffran22a',B,'AgACI aggregation of adaptive conformal procedures for time series','Electricity-price and simulated-series evidence does not establish cellular commitment performance')
add('gibbs2024','gibbs2024',B,'Online conformal inference robust to arbitrary distribution shifts','Long-run coverage target differs from finite-trip positive-conditional risk')
add('lin2022','lin2022',B,'Temporal quantile adjustment for longitudinal and cross-sectional calibration','Repeated-series calibration setting differs from unsuccessful requested cellular feedback')
add('gibbs2021','gibbs2021',C,'Adaptive miscoverage-level updates under distribution shift','Feedback-dependent long-run calibration does not automatically hold after selective missing-label substitution')
add('bhatnagar2023','v202_bhatnagar23a',C,'Strongly adaptive online learning for locally adaptive conformal intervals','Local adaptation bounds are not a guarantee for the implemented MARUR heuristic')
add('pid2023','pid2023',C,'Proportional-integral-derivative-inspired online quantile control','Score-feedback assumptions must be checked before deployment with failed responses')
add('angelopoulos2024online','v235_angelopoulos24a',C,'Online conformal calibration using decaying step sizes','Asymptotic calibration and stationary convergence do not certify finite sparse-feedback trips')
add('podkopaev2024','v235_podkopaev24a',C,'Betting-based parameter-free adaptive conformal inference','Adaptive calibration does not itself account for cellular measurement-attempt costs')
add('ilyas2026','v306_ilyas26a',C,'Stopping rule balancing iid calibration-label cost and prediction-set efficiency','Upfront iid calibration differs from delayed unsuccessful queries under temporal drift')
add('ge2025','v267_ge25a',C,'Stochastic online conformal prediction with semi-bandit feedback and regret analysis','Labels revealed through prediction-set inclusion differ from independently failing radio probes')
add('hou2025','v271_hou25a',C,'Online calibration of probabilistic linear solvers with sporadic cloud feedback','Linear-system solution coverage and cloud cost differ from cellular throughput commitments')
add('geifman2017','geifman2017',D,'Selective classification with abstention and risk-coverage trade-offs','Classification selective risk is not a guarantee for throughput lower bounds')
add('bates2021','10.1145_3478535',D,'Distribution-free risk-controlling prediction sets','Risk-control conditions do not transfer unchanged to adaptive missing-feedback time series')
add('gibbs2025','10.1093_jrsssb_qkaf008',D,'Conformal guarantees over specified classes of covariate shifts and subgroups','Finite-dimensional or approximation conditions are required; not universal conditional coverage')
add('min2026','v306_min26c',D,'Counterexamples to coverage-length evaluation and interval-stability diagnostic','Metric critique does not prescribe a cellular query policy or prove utility improvements')
add('gauthier2026','v300_gauthier26a',D,'E-value/post-hoc conformal adaptive coverage policies trained with leave-one-out','Formal adaptive coverage construction is distinct from MARUR pattern gating')
records.append(dict(key='angelopoulos2024risk',type='inproceedings',fields={'author':'Anastasios N. Angelopoulos and Stephen Bates and Adam Fisch and Lihua Lei and Tal Schuster','title':'Conformal Risk Control','booktitle':'Proceedings of the International Conference on Learning Representations','year':'2024','volume':'','number':'','pages':'','doi':'','url':'https://openreview.net/forum?id=33XGfHLtZg'},source='https://openreview.net/pdf?id=33XGfHLtZg',theme=D,method='Finite-sample control of expected monotone loss via conformal calibration',limitation='Expected-loss guarantees require the stated sampling and loss assumptions; not arbitrary selective conditional risk'))
assert len(records)==30
def latex(s):
    return html.unescape(s).replace('&',r'\&').replace('è',r"{\`e}").replace('é',r"{\'e}").replace('ö',r'{\"o}').replace('–','--')
parts=['% Exactly 30 peer-reviewed publications. Empty optional fields mean not supplied\n% by the verified publication record; see README.md and _support/verification_sources.json.']
for r in records:
    f=r['fields'];f['title']='{'+latex(f['title'])+'}'
    parts.append('@'+r['type']+'{'+r['key']+',\n'+',\n'.join('  '+k+' = {'+(v if k=='title' else latex(v))+'}' for k,v in f.items())+'\n}')
(OUT/'references.bib').write_text('\n\n'.join(parts)+'\n',encoding='utf8')
rows=[['Citation_Key','Title','Year','Venue','Sub_Theme','Core_Methodology','Key_Limitation']]
for r in records:
    f=r['fields'];title=f['title'][1:-1]
    rows.append([r['key'],title,int(f['year']),f.get('journal',f.get('booktitle')),r['theme'],r['method'],r['limitation']])
(P/'matrix_rows.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
(P/'verification_sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
print('Papers:',len(records),'Recent:',sum(int(r['fields']['year'])>=2022 for r in records))
