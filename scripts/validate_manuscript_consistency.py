"""Validate publication tables by ordered cells and independently aggregate saved forecasts."""
import hashlib
import re
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pymupdf
from pypdf import PdfReader
from bs4 import BeautifulSoup
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.publication_tables import ROOT, METHODS, tables, read_json

def source_digest(root):
    h = hashlib.sha256()
    for path in sorted([root/'paper/manuscript.tex',root/'paper/references.bib',root/'paper/cover_letter.tex',*list((root/'paper/tables').glob('*.tex')),*list((root/'paper/figures').glob('*.pdf'))]):
        payload = path.read_bytes()
        if path.suffix in {'.tex','.bib'}:
            payload = payload.replace(b'\r\n',b'\n')
        h.update(path.relative_to(root).as_posix().encode()+b'\0'+payload)
    return h.hexdigest()

def check_rows(actual,expected,where):
    if actual != expected:
        for i,(a,b) in enumerate(zip(actual,expected)):
            if a != b:
                raise ValueError(f'{where}: row {i} {a} != {b}')
        raise ValueError(f'{where}: expected {len(expected)} rows, found {len(actual)}')

def tex_rows(text):
    return [[x.strip() for x in line[:-2].split('&')] for line in text.splitlines() if line.rstrip().endswith(r'\\')]

def pdf_tables(path,specs,digest):
    if PdfReader(path).metadata.get('/SourceDigest') != digest:
        raise ValueError(f'Stale PDF: {path}')
    with pymupdf.open(path) as doc:
        pages = [page.get_text(sort=True) for page in doc]
    for title,(_,header,rows) in specs.items():
        expected = [header,*rows]
        # A single published table occupies one page. Matching entire lines binds
        # values to named columns and detects inserted, missing and swapped rows.
        found = []
        for page in pages:
            lines = [' '.join(line.split()) for line in page.splitlines() if line.strip()]
            for i,line in enumerate(lines):
                if line == ' '.join(header):
                    found.append(lines[i:i+len(expected)])
        check_rows(found,[[' '.join(row) for row in expected]],f'{path.name}/{title}')
    return pages

def verify_metrics(root):
    frame = pd.read_csv(root/'results/diagnostics/test_forecasts.csv',float_precision='round_trip')
    metrics = pd.read_csv(root/'results/metrics/calibration_budget_results.csv',float_precision='round_trip').set_index(['regime','budget_K','method'])
    if not metrics.index.is_unique:
        raise ValueError('Duplicate metrics key')
    observed = set()
    for (reg,k),block in frame.groupby(['regime','budget_K']):
        if block.session_id.duplicated().any():
            raise ValueError('Duplicate test session')
        y = block.target
        for method in METHODS:
            key = (reg,k,method)
            observed.add(key)
            lower = block[method]
            row = metrics.loc[key]
            values = [len(y),(lower>y).mean(),np.minimum(lower,y).sum()/y.sum(),lower.mean(),(lower<=1e-6).mean(),np.maximum(0,lower-y).mean()]
            cols = ['test_samples','violation_rate','supported_fraction','mean_lower_bound','zero_bound_fraction','mean_overcommitment']
            np.testing.assert_allclose(row[cols].astype(float),values,rtol=1e-11,atol=1e-12)
            if method == 'Proposed_Missingness_Aware':
                for group,label in [(2,'LTE_only'),(3,'Dual_NR')]:
                    mask = block.group_id==group
                    sub_y,sub_b = y[mask],lower[mask]
                    if mask.any():
                        np.testing.assert_allclose([row['subgroup_V_'+label],row['subgroup_U_'+label]],[(sub_b>sub_y).mean(),np.minimum(sub_b,sub_y).sum()/sub_y.sum()],atol=1e-12)
    if observed != set(metrics.index):
        raise ValueError('Forecast keys differ from metric keys')

def validate(root=ROOT):
    specs = tables(root)
    verify_metrics(root)
    external = root/'results/exploratory/sirhan_external'
    totals = pd.read_csv(external/'fixed_trace_totals.csv')
    if totals.duplicated(['seed','trace_id','method']).any():
        raise ValueError('Duplicate trace contribution')
    counts = totals.groupby(['seed','method'])[['n','violations','delivered','observed']].sum()
    curve = pd.read_csv(external/'decision_curves.csv')
    fixed = curve.loc[np.isclose(curve.beta,.1)].set_index(['seed','method']).sort_index()
    pd.testing.assert_index_equal(counts.index,fixed.index)
    np.testing.assert_array_equal(counts.n,fixed.n)
    np.testing.assert_allclose(counts.violations/counts.n,fixed.V,atol=1e-12)
    np.testing.assert_allclose(counts.delivered/counts.observed,fixed.U,atol=1e-12)
    frontier = pd.read_csv(external/'matched_frontier.csv')
    for budget, block in frontier.groupby('budget'):
        ref = curve[curve.V<=budget].groupby(['seed','method']).U.max()
        published = block.set_index(['seed','method']).U
        np.testing.assert_allclose(ref.reindex(published.index),published,equal_nan=True)
    influence = pd.read_csv(external/'trace_influence.csv').set_index('trace_id')
    if set(influence.index)!=set(totals.trace_id) or len(influence)!=83:
        raise ValueError('Incomplete trace inventory')
    for trace_id, group in totals.groupby('trace_id'):
        reduced = counts.subtract(group.set_index(['seed','method'])[counts.columns], fill_value=0)
        rate = (reduced.delivered/reduced.observed).unstack()
        np.testing.assert_allclose(100*(rate.persistence-rate['global']).mean(),influence.loc[trace_id,'omit_gain_pp'])
    downloads = influence.loc[influence.app=='Download']
    exclusions = pd.read_csv(external/'trace_exclusions.csv').set_index('sample')
    for label,ids in [('All',[]),('OmitTop5',downloads.observed.nlargest(5).index),('OmitDownloads',downloads.index)]:
        scored = totals[~totals.trace_id.isin(ids)].groupby(['seed','method']).sum(numeric_only=True)
        util = (scored.delivered/scored.observed).unstack()
        risk = (scored.violations/scored.n).unstack()
        delta = util.persistence-util['global']
        np.testing.assert_allclose(exclusions.loc[label,['excluded','mean_gain_pp','positive_splits','tree_v','persistence_v']],
                                   [len(ids),100*delta.mean(),(delta>0).sum(),risk['global'].mean(),risk.persistence.mean()])
    manuscript = (root/'paper/manuscript.tex').read_text(encoding='utf8')
    html = BeautifulSoup((root/'paper/manuscript.html').read_text(encoding='utf8'),'html.parser')
    html_tables = [[[c.get_text(strip=True) for c in tr.find_all(['td','th'])] for tr in tab.find_all('tr')] for tab in html.find_all('table')]
    md = (root/'paper/manuscript.md').read_text(encoding='utf8')
    md_tables = []
    for block in re.findall(r'(?:^\|[^\n]*\n)+',md,re.M):
        md_tables.append([[c.strip() for c in line.strip('|').split('|')] for line in block.splitlines() if not re.fullmatch(r'[|: \-]+',line)])
    expected = [[head,*data] for _,head,data in specs.values()]
    check_rows(html_tables,expected,'HTML')
    check_rows(md_tables,expected,'Markdown')
    for name,(_,header,rows) in specs.items():
        if manuscript.count(r'\input{tables/'+name+'}') != 1:
            raise ValueError(f'Missing or duplicated table {name}')
        for folder in ['results/tables','paper/tables']:
            check_rows(tex_rows((root/folder/(name+'.tex')).read_text(encoding='utf8')),[header,*rows],name)
    for fig in (root/'results/figures').glob('*'):
        if (root/'paper/figures'/fig.name).read_bytes() != fig.read_bytes():
            raise ValueError(f'Stale paper figure: {fig.name}')
    diagnostics = root/'results/diagnostics'
    seg = read_json(diagnostics/'session_boundary_sensitivity.json')
    for method,summary in seg.items():
        units = pd.read_csv(diagnostics/f'segments_{method}.csv')
        if len(units)!=summary['total_extracted_sessions'] or int((units.target_y==0).sum())!=summary['throughput_distribution']['zero_throughput_sessions']:
            raise ValueError(f'Segment inventory differs: {method}')
        for op,domain in [('Op1','e1_campaign_transfer'),('Op2','e3_joint_shift')]:
            pairs = pd.read_csv(diagnostics/f'sensitivity_predictions_{method}_{op}.csv',float_precision='round_trip')
            values = summary['downstream_evaluation'][domain]
            if len(pairs)!=values['instance_count'] or round(float((pairs.lower_bound>pairs.target_y).mean()),4)!=values['conformal_violation_rate_k0']:
                raise ValueError(f'Sensitivity mismatch: {method} {op}')
    from src.evaluation.metrics import paired_day_cluster_bootstrap
    forecasts = pd.read_csv(diagnostics/'test_forecasts.csv',float_precision='round_trip')
    ci = read_json(root/'results/metrics/bootstrap_significance_tests.json')
    for regime,b in forecasts[forecasts.budget_K==10].groupby('regime'):
        b=b.reset_index(drop=True)
        estimates = paired_day_cluster_bootstrap(b,b.target.to_numpy(),b.Global_Conformal.to_numpy(),b.Proposed_Missingness_Aware.to_numpy())
        for metric,field in [('delta_violation_rate','delta_V'),('delta_supported_fraction','delta_U')]:
            actual = ci[regime][field]
            check_rows([actual['point'],*actual['ci_95']],[round(float(x),4) for x in estimates[metric]],regime)
    summary_lines = (root/'README.md').read_text(encoding='utf8').splitlines()
    summary = [[c.strip() for c in line.strip('|').split('|')] for line in summary_lines if re.match(r'^\| E[0-3],',line)]
    expected_summary = []
    by_regime = read_json(diagnostics/'split_summary.json')
    for reg,label in zip(sorted(by_regime),['E0, within earlier Op1','E1, later Op1','E2, earlier Op2','E3, later Op2']):
        part = by_regime[reg]['partitions']['target_test']
        rows = specs['table2_main_benchmark'][2]
        source, = [row for row in rows if row[0]==reg[:2]+'K0']
        ten, = [row for row in rows if row[0]==reg[:2]+'K10']
        expected_summary.append([label,f"{part['n_samples']} / {part['n_days']}",source[2],source[4],ten[4],ten[5]])
    check_rows(summary,expected_summary,'README')
    digest = source_digest(root)
    pages = pdf_tables(root/'paper/manuscript.pdf',specs,digest)
    package = pdf_tables(root/'paper/submission_package.pdf',specs,digest)
    if package[1:] != pages or 'Dear Editor' not in package[0]:
        raise ValueError('Package must contain cover and exact manuscript pages')
    with pymupdf.open(root/'paper/manuscript.pdf') as manuscript_pdf, pymupdf.open(root/'paper/submission_package.pdf') as package_pdf:
        for i,page in enumerate(manuscript_pdf):
            if page.get_pixmap().digest != package_pdf[i+1].get_pixmap().digest:
                raise ValueError(f'Package rendering mismatch on manuscript page {i+1}')
    print(f'Validated {len(specs)} tables, forecast-level aggregates, manuscript and package.')

if __name__ == '__main__':
    validate()
