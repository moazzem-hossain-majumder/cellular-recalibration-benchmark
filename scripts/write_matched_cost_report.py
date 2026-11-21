"""Render all exact-cost audit configurations without selecting winners."""
from pathlib import Path
import re
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def write():
    out=ROOT/'results/marur_audit'
    s=pd.read_csv(out/'matched_cost_summary.csv')
    p=pd.read_csv(out/'matched_cost_pairs.csv')
    text=['# Matched realized-cost analysis',
        'November 21, 2026. Every result is exploratory: the archived outcomes were already inspected before this audit. No policy, cap or hypothesis was selected for a confirmatory claim.',
        '## Design and interpretation',
        'We reran Frozen, Periodic, Early, the modified ACI and MARUR on each full cohort suffix at fixed NEW-query caps 0, 1, 5, 10, 20 and 40. Both frozen point predictors and both feedback scenarios are retained. Ten initial successful calibration observations are identical within each cohort/model and have unknown historical acquisition cost. The grid is an audit sensitivity analysis, not a new deployment design.',
        f'The replay contains {len(s)} configurations and {int(p.matched.sum())} exact-cost MARUR/baseline pairs, including zero-cost pairs. A row is exact only if its realized new queries equal the stated cap. Compare two policies at equal realized cost only when both are exact at that cap. Rows failing to consume their cap remain visible. No interpolation or shortened suffix is used.',
        'Frozen always makes zero new requests. Thus a five-way positive-cost match is impossible without redefining Frozen or charging it for unused measurements. It is an exact-cost comparator at zero only; elsewhere it is a lower-cost reference. MARUR can differ from Frozen even at zero cost because its pattern gate/grouping still operates.',
        'The CSVs matched_cost_summary.csv and matched_cost_pairs.csv contain all metrics and paired contrasts. matched_cost_actions.csv.gz and matched_cost_responses.csv.gz preserve each replay. offer_decomposition.csv separates removed/added offers from failure changes on shared offers. matched_cost_dates.csv retains date-level summaries; effective_updates there is cumulative, not additive over dates. scripts/validate_marur_audit.py independently recomputes cost, risk, utility and offer decomposition identities.',
        '## Denominators and accounting',
        'U is measured supported throughput in percent. All risk is [observed failures / eligible issued forecasts, (failures + unresolved positive offers) / eligible issued forecasts]. Positive risk uses all positive offers as its denominator. These are finite-record identification bounds, not confidence intervals. Offer% uses all scheduled ticks; Abstain counts zero commitments including no-lag ticks. Dates+ counts dates with at least one positive commitment, not independent campaigns.',
        'Cost columns: Q = new query attempts; OK = successful feedback; Fail = unsuccessful feedback; Admit = residual-buffer insertions, including conservative missing scores where used; Used = admitted updates available by a subsequent forecast. Initial successful observations = 10 in every row, separately from Q. The total physical acquisition cost is unknown. Frozen has Q=OK=Fail=Admit=Used=0.',
        '## Interpretation across costs',
        'The main critical audit explains the common ten-query HistGBM/Recorded slice cohort by cohort, including every baseline and the offer-decomposition mechanism. The full grid below includes adverse and favorable outcomes and all unmatched rows. Finite-record all-issued upper risk equals positive-offer frequency among eligible predictions times positive-conditional upper risk; it can decrease solely because service disappears. Neither a small all-issued fraction nor a single favorable matched-cost point establishes superiority.',
        'QueryCensor20 suppresses labels at eligible positions divisible by five. It is not exactly 20% failed queries; periodic positions 1,16,31,... avoid this synthetic mask. Successful feedback can therefore differ at equal attempts, and equality of attempts is not equality of useful labels. Do not match on successful labels after observing outcomes.',
        '## Complete results']
    def pct(v):
        return 'undefined' if pd.isna(v) else f'{100*v:.3f}'
    for key,g in s.groupby(['cohort','model','scenario'],sort=True):
        text+=['### '+ ' / '.join(key),
            '| New cap | Policy | Exact | U% | All risk% | Positive risk% | Offer% | Abstain | Q | OK | Fail | Admit | Used | Dates+ |',
            '|---:|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
        for r in g.itertuples():
            values=[r.new_query_cap,r.policy,'yes' if r.exact_cost else 'no',pct(r.u),
                f'{pct(r.lo)}–{pct(r.hi)}',f'{pct(r.positive_low)}–{pct(r.positive_high)}',
                pct(r.commitment_coverage),r.abstained,r.new_query_attempts,r.successful_responses,
                r.unsuccessful_responses,r.admitted_calibration_updates,r.effective_updates,r.positive_dates]
            text.append('| '+' | '.join(map(str,values))+' |')
        text.append('')
    rendered=re.sub(r'\|\n\n(?=\|)','|\n','\n\n'.join(text))
    (ROOT/'docs/MATCHED_COST_ANALYSIS.md').write_text(rendered+'\n',encoding='utf8')

if __name__=='__main__':
    write()
