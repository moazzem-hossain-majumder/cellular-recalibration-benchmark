"""Budgeted delayed-feedback controllers for empirical throughput commitments."""
from collections import deque

import numpy as np
import pandas as pd

from src.evaluation.conformal import compute_conformal_quantile


def offset(samples, alpha):
    if alpha <= 0 or not samples:
        return float('inf')
    if alpha >= 1:
        return float('-inf')
    return compute_conformal_quantile(np.array([s['score'] for s in samples]),alpha)


def replay(initial, stream, policy, budget, config, scenario='Recorded', *, feedback_unavailable_ids=None):
    """Replay with a hybrid cap: initial successful labels plus NEW query attempts.

    Historical acquisition attempts are unknown. `attempts` is a legacy ledger
    alias for this hybrid count, not a total measurement-attempt count.
    last_ready/last_pattern describe the latest COMPLETED request, including
    missing responses discarded by MARUR_DropMissing; they are not admission age.
    Optional experimental freshness_clock changes only the age trigger; pattern
    changes still use the last completed response. External feedback masks are
    consulted only when a requested horizon closes, never for query selection.
    """
    first = initial.sort_values(['issue','id']).head(config['initial_labels'])
    stream = stream.sort_values(['issue','id']).reset_index(drop=True)
    if len(first)!=config['initial_labels'] or first.y.isna().any():
        raise ValueError('The shared initial labels must be complete')
    if first.ready.max()>stream.issue.min():
        raise ValueError('Initial labels are not available before the suffix')
    if budget<len(first):
        raise ValueError('Budget must cover initial labels')
    window=deque((dict(score=r.point-r.y,pattern=r.pattern,ready=r.ready,id=r.id)
                  for r in first.itertuples()),maxlen=config['window'])
    attempts=len(first)
    alpha=config['alpha']
    pending=[]
    actions=[]
    responses=[]
    ordinal=0
    updates=0
    last_ready=first.ready.max()
    last_observed_ready=last_ready
    last_admitted_ready=last_ready
    last_attempt=None
    feedback_unavailable_ids=set(feedback_unavailable_ids or ())
    freshness=config.get('freshness_clock','completed')
    if freshness not in ('completed','observed'):
        raise ValueError('freshness_clock must be completed or observed')
    backoff=config.get('minimum_attempt_spacing_minutes',0)*60
    if backoff<0:
        raise ValueError('minimum attempt spacing must be nonnegative')
    last_pattern=first.iloc[-1].pattern
    adaptive=policy.startswith('MARUR')
    patterned=adaptive and policy!='MARUR_NoPattern'
    scope=config.get('calibration_scope','pattern')
    if scope not in ('pattern','pooled'):
        raise ValueError('calibration_scope must be pattern or pooled')
    random_ids=set(config.get('query_schedule_ids',()))
    online_q=offset(list(window),config['alpha'])
    online_scale=max(1.,max(abs(s['score']) for s in window))
    online_step=0

    def receive(now):
        nonlocal alpha,updates,last_ready,last_pattern,last_observed_ready,last_admitted_ready,online_q,online_step
        due=[p for p in pending if p['ready']<=now]
        for request in due:
            row=stream.iloc[request['position']]
            # Evaluation labels are accessed only after the requested horizon closes.
            censored=(scenario=='QueryCensor20' and request['ordinal']%5==0) or row.id in feedback_unavailable_ids
            y=np.nan if censored else row.y
            observed=pd.notna(y)
            score=row.point-y if observed else row.point
            admitted=observed or policy!='MARUR_DropMissing'
            if admitted:
                window.append(dict(score=score,pattern=row.pattern,ready=row.ready,id=row.id))
                updates+=1
                last_admitted_ready=row.ready
            if observed:
                last_observed_ready=row.ready
            if policy=='ACI':
                error=float(request['lower']>y) if observed else float(request['lower']>0)
                alpha+=config['aci_step']*(config['alpha']-error)
            if policy=='DecayingOGD':
                online_step+=1
                online_q+=online_scale/(online_step**0.6)*(float(score>request['q'])-config['alpha'])
            last_ready=row.ready
            last_pattern=row.pattern
            responses.append(dict(id=row.id,query_time=row.issue,ready=row.ready,observed=observed,
                                  censored=censored,score=score,admitted=admitted,alpha_after=alpha))
            pending.remove(request)

    for issue,batch in stream.groupby('issue',sort=True):
        receive(issue)
        # Simultaneous rows share the same window; requests reserve budget in roster order.
        for position,row in batch.iterrows():
            eligible=pd.notna(row.point)
            pattern_samples=[s for s in window if s['pattern']==row.pattern]
            use=pattern_samples if patterned and scope=='pattern' and len(pattern_samples)>=9 else list(window)
            q=online_q if policy=='DecayingOGD' else offset(use,alpha if policy=='ACI' else config['alpha'])
            lower=max(0.,row.point-q) if eligible else 0.
            if policy=='ACI' and eligible:
                lower=min(row.point,lower)
            reason='positive' if lower>0 else 'nonpositive_bound'
            if not eligible:
                reason='no_lag'
            elif patterned and config.get('pattern_gate',True) and len(pattern_samples)<config['minimum_pattern_support']:
                lower=0.
                reason='unsupported_pattern'
            request=False
            trigger='none'
            if eligible:
                ordinal+=1
                age_origin=last_ready if freshness=='completed' else last_observed_ready
                stale=(issue-age_origin)>=config['max_age_minutes']*60
                changed=patterned and row.pattern!=last_pattern
                periodic=(ordinal-1)%config['period_ticks']==0
                wants=(policy=='Early' or
                       (policy in ['Periodic','ACI','DecayingOGD','MARUR_Periodic'] and periodic) or
                       (policy=='Random' and row.id in random_ids) or
                       (adaptive and policy!='MARUR_Periodic' and (stale or changed)))
                spacing_ok=last_attempt is None or issue-last_attempt>=backoff
                if wants and attempts<budget and not pending and spacing_ok:
                    request=True
                    trigger='pattern' if changed else 'age' if stale and adaptive else 'schedule'
                    attempts+=1
                    last_attempt=issue
                    pending.append(dict(position=position,ready=row.ready,ordinal=ordinal,lower=lower,q=q))
            actions.append(dict(id=row.id,date=row.date,issue=issue,ready=row.ready,pattern=row.pattern,
                point=row.point,eligible=eligible,lower=lower,reason=reason,query=request,trigger=trigger,
                attempts=attempts,updates=updates,alpha=alpha,window_size=len(window),
                pattern_support=len(pattern_samples),last_feedback=last_ready))
            if config.get('log_information_clocks',False):
                actions[-1].update(last_query_attempt=last_attempt,last_completed_response=last_ready,
                                  last_observed_label=last_observed_ready,last_admitted_score=last_admitted_ready)
            if config.get('log_score_diagnostics',False):
                actions[-1].update(offset=q,calibration_count=len(use),online_step=online_step,
                                  oldest_score_ready=min(s['ready'] for s in use),
                                  quantile_source='pattern' if use is pattern_samples else 'pooled')
    # Paid requests remain in the receipt even when they mature beyond the last forecast.
    if pending:
        receive(max(p['ready'] for p in pending))
    ledger=pd.DataFrame(actions)
    ledger['y']=stream.y.to_numpy()
    return ledger,pd.DataFrame(responses,columns=['id','query_time','ready','observed','censored','score','admitted','alpha_after'])
