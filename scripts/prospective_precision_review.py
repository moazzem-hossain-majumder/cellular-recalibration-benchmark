"""Assumption sensitivity only: no acquired trips or risk certification."""
import math,json
from pathlib import Path
import pandas as pd
from scipy.stats import t,norm
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/prospective_planning';OUT.mkdir(parents=True,exist_ok=True)
rows=[]
for sd in [.05,.10,.15,.20]:
    for halfwidth in [.025,.05]:
        n=next(n for n in range(3,10000) if t.ppf(.975,n-1)*sd/math.sqrt(n)<=halfwidth)
        rows.append(dict(paired_sd=sd,halfwidth=halfwidth,independent_complete_trip_pairs=n,assumption='t precision for independent regular trip differences'))
pd.DataFrame(rows).to_csv(OUT/'utility_precision.csv',index=False)
rows=[]
for p in [.025,.05,.10]:
    for m in [40,80]:
        for rho in [.01,.05,.10,.20]:
            for h in [.025,.05]:
                deff=1+(m-1)*rho;n=math.ceil(norm.ppf(.975)**2*p*(1-p)*deff/(m*h*h))
                rows.append(dict(anticipated_violation_probability=p,positive_offers_per_trip=m,intratrip_correlation=rho,halfwidth=h,design_effect=deff,approximate_trips=n,assumption='normal cluster-design approximation; equal cluster sizes; not certification or power'))
pd.DataFrame(rows).to_csv(OUT/'risk_precision_sensitivity.csv',index=False)
profile=json.loads((ROOT/'configs/prospective_video_profile.json').read_text())
required=['network_operator','location_and_route_strata','device_and_modem','approved_measurement_endpoint','model_sha256','initial_observation_ids','registered_protocol_url','requirements_validated_by_application_owner','field_feature_mapping_verified']
missing=[k for k in required if not profile[k]]
(OUT/'readiness.json').write_text(json.dumps(dict(status='not_ready_for_collection',missing=missing,prospective_trips_collected=0,zero_failures_independent_Bernoulli_n_for_5percent=math.ceil(math.log(.05)/math.log(.95)),warning='59 independent fully observed Bernoulli outcomes with zero failures is not 59 correlated ticks or a sample-size justification for this trip study'),indent=2)+'\n')
print('Planning grids saved; collection prerequisites missing:',', '.join(missing))
