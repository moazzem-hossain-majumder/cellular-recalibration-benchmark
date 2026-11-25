"""Validate publication tables by ordered cells and independently aggregate saved forecasts."""
from zipfile import ZipFile
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
    for path in sorted([*list((root/'paper').glob('*.tex')),root/'paper/references.bib',*list((root/'paper/tables').glob('*.tex')),*list((root/'paper/figures').glob('*.pdf'))]):
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

def validate_marur_claims(root):
    """Bind the revised abstract's numerical claims to the authoritative audit."""
    manuscript=(root/'paper/manuscript.tex').read_text(encoding='utf8')
    abstract=manuscript.split(r'\begin{abstract}')[1].split(r'\end{abstract}')[0]
    folder=root/'results/marur_audit'
    summary=pd.read_csv(folder/'matched_cost_summary.csv')
    pairs=pd.read_csv(folder/'matched_cost_pairs.csv')
    original=pd.read_csv(root/'results/marur/summary.csv')
    for value,phrase in [(len(original),'original configurations'),(len(summary),'additional full-suffix replays'),
                         (int(pairs.matched.sum()),'exact-cost contrasts')]:
        if f'{value} {phrase}' not in abstract:
            raise ValueError(f'Abstract configuration/count mismatch: {value} {phrase}')
    chosen=summary[(summary.model=='HistGBM')&(summary.scenario=='Recorded')&(summary.new_query_cap==10)]
    e1=chosen[chosen.cohort=='E1'].set_index('policy')
    ie=chosen[chosen.cohort=='Ireland'].set_index('policy')
    for value in [e1.loc['MARUR','u'],e1.loc['Periodic','u'],e1.loc['MARUR','hi'],e1.loc['Periodic','hi'],
                  ie.loc['MARUR','u'],ie.loc['Periodic','u']]:
        if f'{100*value:.3f}' not in abstract:
            raise ValueError(f'Abstract matched-cost value missing: {100*value:.3f}')
    if ie.loc['MARUR','positive']!=159 or ie.loc['Periodic','positive']!=159:
        raise ValueError('Abstract Ireland shared-offer count changed')
    decomposition=pd.read_csv(folder/'offer_decomposition.csv')
    row=decomposition[(decomposition.cohort=='Ireland')&(decomposition.model=='HistGBM')&
        (decomposition.scenario=='Recorded')&(decomposition.new_query_cap==10)&(decomposition.baseline=='Periodic')]
    if len(row)!=1 or row.iloc[0].shared_offers!=159 or row.iloc[0].shared_failure_delta!=-14:
        raise ValueError('Abstract Ireland fourteen-failure attribution changed')
    trip=pd.read_csv(root/'results/diagnostics/trip_level_inference.csv')
    comb=trip[(trip.scope=='Combined_CampaignDates')&(trip.model=='HistGBM')&(trip.scenario=='Recorded')&(trip.new_query_cap==10)&(trip.baseline=='Periodic')].iloc[0]
    if int(comb.clusters)!=16 or f'{100*comb.eq_du_mean:+.2f}' not in abstract:
        raise ValueError('Abstract campaign-date cluster inference mismatch')
    if not (root/'LICENSE').is_file():
        raise ValueError('Missing repository LICENSE file')


def validate_pacer_claims(root):
    """Bind Path A Theorem 1 and untouched-cohort claims to locked PACER artifacts."""
    source=(root/'paper/manuscript.tex').read_text(encoding='utf8')
    report=read_json(root/'results/pacer/pacer_audit_report.json')
    if not report['preregistration_lock_verified'] or report['prospective_trips_collected']!=0:
        raise ValueError('PACER pre-registration lock or zero-prospective check failed')
    if not report['theorem1_mean_excess_checks']['all_within_bound'] or report['theorem1_mean_excess_checks']['total_cells']!=40:
        raise ValueError('Theorem 1 verification count mismatch')
    if report['physical_clusters']['untouched_heldout']!=26 or report['physical_clusters']['retrospective']!=16:
        raise ValueError('Physical cluster count mismatch for Path A')
    con=pd.read_csv(root/'results/pacer/pacer_paired_contrasts.csv')
    c_unt=con[(con.scope=='UntouchedHeldOut')&(con.model=='HistGBM')&(con.scenario=='Recorded')&(con.cap_new==10)&(con.reference=='Periodic')].iloc[0]
    p_per=con[(con.scope=='AllCohortsPooled')&(con.model=='Persistence')&(con.scenario=='Recorded')&(con.cap_new==40)&(con.reference=='Frozen')].iloc[0]
    if f'{100*c_unt.pool_dpos_hi:+.2f}' not in source or f'{100*p_per.pool_du:+.2f}' not in source or '40/40' not in source or '26' not in source or '42' not in source:
        raise ValueError('PACER numerical claims missing or mismatched in manuscript')


def validate(root=ROOT):
    validate_marur_claims(root)
    validate_reviewer_claims(root)
    validate_pacer_claims(root)
    verify_clock_frontier(root)
    verify_revision_ledgers(root)
    verify_drive3(root)
    verify_playback_and_irish(root)
    verify_campaign_sensitivity(root)
    from scripts.validate_marur import validate as validate_marur
    validate_marur(root)
    specs = tables(root)
    verify_metrics(root)
    diag = root/'results/diagnostics'
    ext = root/'results/external_validation'
    issued = pd.read_csv(diag/'clock_issued.csv')
    irish = pd.read_csv(ext/'irish_group_forecasts.csv.gz',float_precision='round_trip')
    for record in read_json(ext/'irish_group_validation.json'):
        b = irish[(irish.k==record['k']) & (irish.method==record['method'])]
        assert len(b)==record['n'] and not b.duplicated(['trace_id','row_in_trace']).any()
        v = (b.lower>b.y).mean()
        np.testing.assert_allclose([record[k] for k in ['coverage','violation','supported','mae']],
                                   [1-v,v,np.minimum(b.lower,b.y).sum()/b.y.sum(),(b.point-b.y).abs().mean()])
    for record in read_json(diag/'prediction_time_validity.json'):
        b = issued[issued.setting==record['setting']]
        assert (len(b),b.y.isna().sum(),b.y.count())==(record['issued'],record['unscored'],record['n'])
    for rows,stats in [(diag/'clock_forecasts.csv', read_json(diag/'prediction_time_validity.json')),
                       (ext/'norway_forecasts.csv', pd.read_csv(ext/'norway_metrics.csv').to_dict('records'))]:
        data = pd.read_csv(rows,float_precision='round_trip')
        for record in stats:
            b = data[(data.setting==record['setting']) & (data.method==record['method'])]
            assert len(b)==record['n']
            v = (b.lower>b.y).mean()
            np.testing.assert_allclose(b.lower,np.maximum(0,b.point-record['q']),atol=1e-12)
            np.testing.assert_allclose([record[k] for k in ['violation','coverage','mae','supported']],
                                       [v,1-v,(b.point-b.y).abs().mean(),np.minimum(b.lower,b.y).sum()/b.y.sum()])
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
    supplement=(root/'paper/supplementary.tex').read_text(encoding='utf8')
    combined=manuscript+'\n'+supplement
    referenced = re.findall(r'\\includegraphics(?:\[[^\]]+\])?\{(figures/[^}]+\.pdf)\}',combined)
    if len(set(referenced))!=9:
        raise ValueError('Incomplete manuscript figure set')
    for fig in referenced:
        for suffix in ['.pdf','.png']:
            name = Path(fig).with_suffix(suffix)
            if (root/'paper'/name).read_bytes()!=(root/'results'/name).read_bytes():
                raise ValueError(f'Figure mismatch: {name}')
    html = BeautifulSoup((root/'paper/supplementary.html').read_text(encoding='utf8')+(root/'paper/manuscript.html').read_text(encoding='utf8'),'html.parser')
    html_tables = [[[c.get_text(strip=True) for c in tr.find_all(['td','th'])] for tr in tab.find_all('tr')] for tab in html.find_all('table')]
    md = (root/'paper/supplementary.md').read_text(encoding='utf8')+'\n'+(root/'paper/manuscript.md').read_text(encoding='utf8')
    md_tables = []
    for block in re.findall(r'(?:^\|[^\n]*\n)+',md,re.M):
        md_tables.append([[c.strip() for c in line.strip('|').split('|')] for line in block.splitlines() if not re.fullmatch(r'[|: \-]+',line)])
    expected = [[head,*data] for _,head,data in specs.values()]
    known_headers=[x[0] for x in expected]
    html_tables=[t for t in html_tables if t and t[0] in known_headers]
    md_tables=[t for t in md_tables if t and t[0] in known_headers]
    check_rows(html_tables,expected,'HTML')
    check_rows(md_tables,expected,'Markdown')
    for name,(_,header,rows) in specs.items():
        if combined.count(r'\input{tables/'+name+'}') != 1:
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
    main_specs={k:v for k,v in specs.items() if r'\input{tables/'+k+'}' in manuscript}
    supplementary_specs={k:v for k,v in specs.items() if k not in main_specs}
    pages = pdf_tables(root/'paper/manuscript.pdf',main_specs,digest)
    pdf_tables(root/'paper/supplementary.pdf',supplementary_specs,digest)
    package = pdf_tables(root/'paper/submission_package.pdf',main_specs,digest)
    if package[1:] != pages or 'Dear Editor' not in package[0]:
        raise ValueError('Package must contain cover and exact manuscript pages')
    with pymupdf.open(root/'paper/manuscript.pdf') as manuscript_pdf, pymupdf.open(root/'paper/submission_package.pdf') as package_pdf:
        for i,page in enumerate(manuscript_pdf):
            if page.get_pixmap().digest != package_pdf[i+1].get_pixmap().digest:
                raise ValueError(f'Package rendering mismatch on manuscript page {i+1}')
    with ZipFile(root/'paper/submission_package.zip') as archive:
        required = {'manuscript.pdf','supplementary.pdf','supplementary.tex','related_work.tex','submission_package.pdf','cover_letter.tex','manuscript.tex','references.bib','supplement/REPRODUCE.md'}
        required.update('tables/'+name+'.tex' for name in specs)
        required.update(referenced)
        if required.difference(archive.namelist()):
            raise ValueError('Incomplete submission ZIP')
        for name in archive.namelist():
            target = root/'paper'/name
            if name.startswith('supplement/'):
                file = Path(name).name
                target = root/'README.md' if file=='REPRODUCE.md' else root/'docs'/file
            stored, current = archive.read(name),target.read_bytes()
            if target.suffix in {'.md','.tex','.bib'}:
                stored,current = [x.replace(b'\r\n',b'\n') for x in [stored,current]]
            if stored!=current:
                raise ValueError(f'Stale submission ZIP entry: {name}')
    print(f'Validated {len(specs)} tables, forecast-level aggregates, manuscript and package.')

def verify_campaign_sensitivity(root):
    folder=root/'results/external_validation'
    blocks=pd.read_csv(folder/'playback_sensitivity.csv.gz')
    dates=pd.read_csv(folder/'playback_sensitivity_dates.csv')
    keys=['segment_s','request_delay_s','date','policy']
    totals=blocks.groupby(keys)[['stall_s','post_start_s','segments','media_mbit']].sum().sort_index()
    actual=dates.set_index(keys).sort_index()
    assert totals.index.equals(actual.index)
    np.testing.assert_allclose(actual.risk,totals.stall_s/totals.post_start_s,equal_nan=True)
    duration=totals.index.get_level_values('segment_s')
    np.testing.assert_allclose(actual.bitrate,totals.media_mbit/(duration*totals.segments),equal_nan=True)
    summary=pd.read_csv(folder/'playback_sensitivity_summary.csv')
    assert len(summary)==9
    for r in summary.itertuples():
        d=dates[(dates.segment_s==r.segment_s)&(dates.request_delay_s==r.request_delay_s)]
        pairs=d.pivot(index='date',columns='policy',values=['risk','bitrate'])
        assert r.dates==len(pairs)
        assert r.lower_stall_dates==(pairs.risk.TreeLower<pairs.risk.Tree).sum()
        assert r.lower_bitrate_dates==(pairs.bitrate.TreeLower<pairs.bitrate.Tree).sum()
        np.testing.assert_allclose([r.median_stall_delta,r.median_bitrate_delta],
            [(pairs.risk.TreeLower-pairs.risk.Tree).median(),(pairs.bitrate.TreeLower-pairs.bitrate.Tree).median()])
    dates=pd.read_csv(folder/'cross_campaign_dates.csv')
    sensitivity=pd.read_csv(folder/'cross_campaign_date_sensitivity.csv')
    for r in sensitivity.itertuples():
        d=dates[(dates.cohort==r.cohort)&(dates.model==r.model)]
        if r.omit_date!='none':
            d=d[d.date!=r.omit_date]
        assert r.dates==len(d) and r.positive_dates==(d.positive>0).sum()
        np.testing.assert_allclose([r.equal_date_low,r.equal_date_high,r.equal_date_utility,r.pooled_low],
            [(d.errors/d.issued).mean(),((d.errors+d.unresolved)/d.issued).mean(),
             (d.support/d.observed).mean(),d.errors.sum()/d.issued.sum()])


def verify_playback_and_irish(root):
    folder = root/'results/external_validation'
    blocks = pd.read_csv(folder/'playback_runs.csv')
    dates = pd.read_csv(folder/'playback_dates.csv')
    keys=['route','date','policy']
    totals=blocks.groupby(keys)[['segments','media_mbit','stall_s','post_start_s']].sum()
    reported=dates.set_index(keys).sort_index()
    assert totals.index.equals(reported.index)
    np.testing.assert_allclose(reported.stall_fraction,totals.stall_s/totals.post_start_s)
    np.testing.assert_allclose(reported.mean_bitrate,totals.media_mbit/(2*totals.segments))
    ticks=pd.read_csv(folder/'ireland_drive_ticks.csv',float_precision='round_trip')
    stats=pd.read_csv(folder/'ireland_drive_summary.csv')
    cal=ticks[ticks.partition=='cal']
    test=ticks[ticks.partition=='test']
    assert len(cal)==10 and cal.end.max()<test.issue.min()
    for r in stats.itertuples():
        group=test if r.date=='all' else test[test.date==r.date]
        part=group.dropna(subset=['y_lag1'])
        offset=(cal[r.model]-cal.y).max()
        lower=(part[r.model]-offset).clip(lower=0)
        assert (len(part),part.y.count(),(lower>part.y).sum(),((lower>0)&part.y.isna()).sum())==(
            r.issued,r.scored,r.violations,r.unresolved)
        np.testing.assert_allclose(part[r.model+'_lower'],lower)
        np.testing.assert_allclose(r.u,np.minimum(lower,part.y).sum()/part.y.sum())


def verify_drive3(root):
    folder = root/'results/external_validation'
    ledger = pd.read_csv(folder/'drive3_forecasts.csv',float_precision='round_trip')
    stats = pd.read_csv(folder/'drive3_results.csv')
    assert len(stats)==len(stats.drop_duplicates(['carrier','date','model']))
    expected={(name,day,model) for name, cohort in ledger.groupby('carrier')
              for day in ['all',*cohort.loc[cohort.partition=='test','date'].unique()]
              for model in ['Persistence','Tree','Tree_noNR']}
    assert set(stats[['carrier','date','model']].itertuples(index=False,name=None))==expected
    for r in stats.itertuples():
        cohort = ledger[ledger.carrier==r.carrier]
        cal = cohort[cohort.partition=='cal']
        test = cohort[cohort.partition=='test']
        assert len(cal)==10 and cal.target_time.max()<test.issue.min()
        if r.date!='all':
            test=test[test.date==r.date]
        issued=test.dropna(subset=['y_lag1'])
        observed=issued.dropna(subset=['y'])
        assert len(test)==r.ticks and len(issued)==r.issued
        if issued.empty:
            continue
        assert (issued.lag_time<issued.issue).all() and (observed.target_time>=observed.issue).all()
        model=r.model
        ref='Tree' if model=='Tree_noNR' else model
        q=(cal[ref]-cal.y).max()
        lower=issued[model+'_lower']
        np.testing.assert_allclose([r.offset],[q])
        np.testing.assert_allclose(lower,np.maximum(0,issued[model]-q))
        pos=lower>0
        failures=(lower>issued.y).sum()
        missing=(pos & issued.y.isna()).sum()
        assert (pos.sum(),failures,missing,observed.shape[0])==(r.positive,r.violations,r.unresolved,r.scored)
        if len(observed):
            np.testing.assert_allclose(r.u,np.minimum(lower,issued.y).sum()/observed.y.sum())


def verify_revision_ledgers(root):
    folder = root/'results/clock_histgbm'
    ledger = pd.read_csv(folder/'simulated_nr_forecasts.csv.gz', float_precision='round_trip')
    summaries = pd.read_csv(folder/'simulated_nr_metrics.csv').set_index(['regime','scenario','seed'])
    grouped = ledger.groupby(['regime','scenario','seed'])
    assert set(grouped.groups) == set(summaries.index)
    for key, rows in grouped:
        summary = summaries.loc[key]
        positive = rows.lower > 0
        failed = rows.lower > rows.y
        missing = positive & rows.y.isna()
        assert (len(rows),rows.y.count(),positive.sum(),failed.sum(),missing.sum()) == (
            summary.issued,summary.scored,summary.positive,summary.violations,summary.unresolved)
        np.testing.assert_allclose(summary.u,np.minimum(rows.lower,rows.y).sum()/rows.y.sum())
    external = root/'results/external_validation'
    records = pd.read_csv(external/'nuwins_drive2_forecasts.csv',float_precision='round_trip')
    result = read_json(external/'nuwins_drive2_summary.json')
    cal = records[records.partition=='cal_used']
    test = records[records.partition=='test']
    issued = test.dropna(subset=['point'])
    observed = issued.dropna(subset=['y'])
    assert len(cal)==10 and cal.target_time.max()<test.issue.min()
    assert (issued.lag_time<issued.issue).all() and (observed.target_time>=observed.issue).all()
    offset = (cal.point-cal.y).max()
    np.testing.assert_allclose(result['offset_mbps'],offset)
    np.testing.assert_allclose(issued.lower,np.maximum(0,issued.point-offset))
    stats = result['test']
    assert (len(test),len(issued),len(observed),sum(issued.lower>0),sum(observed.lower>observed.y)) == (
        stats['ticks'],stats['issued'],stats['scored'],stats['positive'],stats['violations'])
    np.testing.assert_allclose(stats['supported'],np.minimum(observed.lower,observed.y).sum()/observed.y.sum())


def verify_clock_frontier(root):
    folder = root/'results/clock_histgbm'
    ticks = pd.read_csv(folder/'ticks.csv',float_precision='round_trip')
    curve = pd.read_csv(folder/'frontier.csv',float_precision='round_trip')
    ledger = pd.read_csv(folder/'issued_k10.csv',float_precision='round_trip')
    previous = pd.read_csv(root/'results/diagnostics/clock_issued.csv',float_precision='round_trip')
    for (reg,model,policy),rows in curve.groupby(['regime','model','policy']):
        b = ticks[ticks.regime==reg].sort_values(['time','trace'])
        cal = b[b.partition.eq('calibration') & b.y.notna()]
        test = b[b.partition.eq('test')]
        ref = previous[previous.setting==reg].sort_values(['time','trace'])
        assert list(test[['time','trace']].itertuples(index=False,name=None))==list(ref[['time','trace']].itertuples(index=False,name=None))
        np.testing.assert_allclose(test.y,ref.y,equal_nan=True)
        assert cal.end.max()<=test.time.min()
        np.testing.assert_array_equal(rows.k,range(len(cal)+1))
        scores = (cal[model]-cal.y).to_numpy()
        def offset(s):
            rank = ((len(s)+1)*9+9)//10
            return np.sort(s)[rank-1]
        for r in rows.itertuples():
            s = scores[:r.k]
            q = np.full(len(test),offset(s) if len(s)>=9 else r.source_q)
            if policy=='Grouped':
                for group in test.group_id.unique():
                    sub = s[cal.group_id.to_numpy()[:r.k]==group]
                    if len(sub)>=9:
                        q[test.group_id==group] = offset(sub)
            lower = np.maximum(0,test[model].to_numpy()-q)
            errors = int((lower>test.y).sum())
            missing = int(((lower>0)&test.y.isna()).sum())
            positive = int((lower>0).sum())
            measured = positive-missing
            assert (positive,measured,measured-errors)==(r.positive,r.positive_scored,r.positive_covered)
            np.testing.assert_allclose([r.positive_rate,r.v_given_positive,r.positive_low,r.positive_high],
                [positive/len(test),errors/measured if measured else np.nan,
                 errors/positive if positive else np.nan,(errors+missing)/positive if positive else np.nan],
                equal_nan=True)
            assert (len(test),int(test.y.count()),errors,missing)==(r.issued,r.scored,r.violations,r.unresolved)
            np.testing.assert_allclose([r.lo,r.hi,r.v,r.u],[errors/len(test),(errors+missing)/len(test),
                errors/test.y.count(),np.nansum(np.minimum(lower,test.y))/test.y.sum()],atol=1e-12)
            if r.k==10:
                actual = ledger[(ledger.regime==reg)&(ledger.model==model)&(ledger.policy==policy)].sort_values(['time','trace'])
                np.testing.assert_allclose(actual.lower,lower,atol=1e-12)


def validate_reviewer_claims(root):
    """Bind new manuscript counts and mechanisms to saved experimental evidence."""
    source=(root/'paper/manuscript.tex').read_text(encoding='utf8')
    folder=root/'results/exploratory/reviewer_baselines'
    summary=pd.read_csv(folder/'summary.csv')
    if len(summary)!=792 or '792 configurations' not in source:
        raise ValueError('Reviewer baseline count mismatch')
    pairs=pd.read_csv(folder/'classified_contrasts.csv')
    pooled=pairs[(pairs.candidate=='MARUR_Pooled')&(pairs.reference=='MARUR')]
    if len(pooled)!=72 or not (pooled.outcome=='unchanged').all() or 'all 72 paired configurations' not in source:
        raise ValueError('Pattern-quantile claim mismatch')
    counts=pairs[(pairs.candidate=='DecayingOGD')&(pairs.reference=='Periodic')].outcome.value_counts()
    expected={'utility gain without higher risk bound':9,'utility loss without lower risk bound':18,'trade-off or risk-only change':45}
    if counts.to_dict()!=expected:raise ValueError('Decaying baseline claim mismatch')
    scores=pd.read_csv(folder/'window_score_diagnostics.csv')
    row=scores[(scores.cohort=='Verizon')&(scores.model=='HistGBM')&(scores.scenario=='Recorded')&(scores.new_query_cap==40)&(scores.variant=='completed_W20')]
    if len(row)!=1 or tuple(row.iloc[0][['binding_missing','bound_zero_with_binding_missing','eligible']])!=(159,159,287) or '159 of 287' not in source:
        raise ValueError('Binding missing-score claim mismatch')
    related=(root/'paper/related_work.tex').read_text(encoding='utf8')
    bib=(root/'paper/references.bib').read_text(encoding='utf8')
    keys=re.findall(r'@\w+\{([^,]+)',bib)
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate bibliography keys')
    cited={k.strip() for group in re.findall(r'\\cite\{([^}]+)\}',related) for k in group.split(',')}
    if len(cited)!=30 or not cited<=set(keys):raise ValueError('Related-work citation mismatch')


if __name__ == '__main__':
    validate()
